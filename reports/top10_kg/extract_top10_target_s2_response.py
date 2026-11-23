"""Extract LINCS COMPZ values for sourced Top10 target assertions."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "reports/top10_kg"
BUNDLE = BASE / "top10_graph_bundle/3928c54d_external_v1"
S2 = ROOT / "s2_lincs"
csv.field_size_limit(min(sys.maxsize, 2_147_483_647))


def main() -> None:
    frozen = json.loads((BASE / "02_top10_frozen_manifest.json").read_text(encoding="utf-8"))
    edges = pd.read_csv(BUNDLE / "subgraph_edges.csv", dtype=str, keep_default_na=False)
    nodes = pd.read_csv(BUNDLE / "subgraph_nodes.csv", dtype=str, keep_default_na=False)
    gene_props = {r.id: json.loads(r.properties_json) for r in nodes.itertuples(index=False) if r.type == "Gene"}
    drug_by_pert: dict[str, str] = {}
    for row in csv.DictReader((BUNDLE / "candidate_mapping_audit.csv").open(encoding="utf-8-sig", newline="")):
        drug_by_pert[row["pert_id"]] = row["graph_drug_id"]

    target_rows = []
    evidence_rows = pd.read_csv(BUNDLE / "evidence_records.csv", dtype=str, keep_default_na=False).to_dict("records")
    allowed = {"TARGET", "INHIBITOR", "AGONIST", "ANTAGONIST", "PARTIAL_AGONIST", "BLOCKER", "ACTIVATOR", "INVERSE_AGONIST", "BINDER"}
    for e in edges[edges.label.eq("DRG-GEN")].to_dict("records"):
        drug_id = e["from"]
        pert_id = next((p for p, d in drug_by_pert.items() if d == drug_id), "")
        if not pert_id:
            continue
        props = json.loads(e["properties_json"])
        assertions = [a for a in (props.get("relation_assertions") or []) if a.get("relation", "").upper() in allowed]
        if not assertions:
            continue
        target_rows.append({"pert_id": pert_id, "drug_id": drug_id, "gene_id": e["to"],
                            "symbol": gene_props.get(e["to"], {}).get("symbol", ""),
                            "assertions": assertions, "source_record_id": props.get("source_record_id", ""),
                            "evidence_ids": [x["evidence_id"] for x in evidence_rows
                                             if x["subject_id"] == drug_id and x["object_id"] == e["to"] and x["predicate"].upper() in allowed]})

    # S1 target direction and effect size from provenance-preserving project edges.
    s1 = {}
    for e in edges[edges.label.eq("PROJECT-HAS_DEG")].to_dict("records"):
        p = json.loads(e["properties_json"])
        s1[e["to"]] = {"direction": p.get("direction", ""), "logFC": p.get("logFC"), "FDR": p.get("adj.P.Val")}

    sigs = pd.read_csv(ROOT / "experiments/final_results/results/final_signature_scores.csv")
    sig_by_pert = {}
    for item in frozen["items"]:
        subset = sigs[(sigs.pert_id == item["pert_id"]) & (sigs.sig_id == item["sig_id"])]
        if len(subset) != 1:
            raise ValueError(f"Expected one exact signature row for {item['pert_id']}")
        sig_by_pert[item["pert_id"]] = item["sig_id"]

    gene_info = pd.read_csv(next((S2 / "data").glob("*gene_info*.gz")), sep="\t", dtype={"pr_gene_id": str}, low_memory=False)
    gene_info["symbol_norm"] = gene_info.pr_gene_symbol.fillna("").astype(str).str.strip().str.upper()
    gene_to_symbols = gene_info.drop_duplicates(["pr_gene_id", "symbol_norm"]).groupby("pr_gene_id").symbol_norm.apply(list).to_dict()
    sig_path = next((S2 / "work").glob("*.gctx"))
    output = []
    with h5py.File(sig_path, "r") as h:
        matrix = h["0"]["DATA"]["0"]["matrix"]
        sig_ids = [x.decode() if isinstance(x, bytes) else str(x) for x in h["0"]["META"]["COL"]["id"][:]]
        gene_ids = [x.decode() if isinstance(x, bytes) else str(x) for x in h["0"]["META"]["ROW"]["id"][:]]
        sig_pos = {value: i for i, value in enumerate(sig_ids)}
        row_gene = pd.DataFrame({"gene_id": gene_ids})
        row_gene["symbol_norm"] = row_gene.gene_id.map(lambda x: gene_to_symbols.get(str(x), [""])[0]).fillna("")
        pos_by_symbol = row_gene.groupby("symbol_norm", sort=False).indices
        vector_cache = {}
        for item in frozen["items"]:
            pid = item["pert_id"]
            sig = sig_by_pert[pid]
            if sig not in sig_pos:
                raise ValueError(f"LINCS signature absent from GCTX: {sig}")
            vector_cache[sig] = np.asarray(matrix[sig_pos[sig], :], dtype=np.float32)
        for item in frozen["items"]:
            pid, sig = item["pert_id"], sig_by_pert[item["pert_id"]]
            targets = [x for x in target_rows if x["pert_id"] == pid]
            if not targets:
                output.append({"rank": item["rank"], "pert_id": pid, "drug": item["pert_iname"], "sig_id": sig,
                               "target_symbol": "", "relation_assertions": "", "COMPZ": "", "S1_direction": "",
                               "S2_S1_relation": "not assessable", "evidence_ids": "", "source_record_id": "",
                               "interpretation_limit": "No sourced target-semantic relation in this bundle."})
                continue
            for target in targets:
                locations = pos_by_symbol.get(str(target["symbol"]).upper(), []) if target["symbol"] else []
                vals = [float(vector_cache[sig][i]) for i in locations if np.isfinite(vector_cache[sig][i])]
                compz = float(np.median(vals)) if vals else np.nan
                s1row = s1.get(target["gene_id"], {})
                direction = s1row.get("direction", "")
                if not vals:
                    relation = "target not measured in LINCS GCTX"
                elif not direction or compz == 0:
                    relation = "measured; no significant S1 direction or neutral response"
                elif (direction == "UP" and compz < 0) or (direction == "DOWN" and compz > 0):
                    relation = "opposite expression direction (descriptive)"
                else:
                    relation = "same expression direction (descriptive)"
                output.append({"rank": item["rank"], "pert_id": pid, "drug": item["pert_iname"], "sig_id": sig,
                               "target_gene_id": target["gene_id"], "target_symbol": target["symbol"],
                               "relation_assertions": "; ".join(a["source"] + ":" + a["relation"] for a in target["assertions"]),
                               "COMPZ": compz if np.isfinite(compz) else "", "S1_direction": direction,
                               "S1_logFC": s1row.get("logFC", ""), "S1_FDR": s1row.get("FDR", ""),
                               "S2_S1_relation": relation, "evidence_ids": "|".join(target["evidence_ids"]),
                               "source_record_id": target["source_record_id"],
                               "interpretation_limit": "COMPZ is target transcript response, not binding or target activity; directional overlap is descriptive, not causal efficacy evidence."})
    out = BASE / "08_target_s2_response.csv"
    pd.DataFrame(output).to_csv(out, index=False)
    print(pd.DataFrame(output).groupby(["rank", "pert_id", "drug"], dropna=False).agg(
        target_rows=("target_gene_id", "count"), measured=("COMPZ", lambda x: int(pd.to_numeric(x, errors="coerce").notna().sum())),
        opposite=("S2_S1_relation", lambda x: int(x.eq("opposite expression direction (descriptive)").sum())),
        same=("S2_S1_relation", lambda x: int(x.eq("same expression direction (descriptive)").sum()))).to_string())


if __name__ == "__main__":
    main()
