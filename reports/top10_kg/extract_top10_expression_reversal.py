"""Join frozen Top 10 LINCS signatures to the existing S1 differential results."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "reports" / "top10_kg"
S2 = ROOT / "s2_lincs"
csv.field_size_limit(min(sys.maxsize, 2_147_483_647))


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def decode(value: object) -> str:
    return value.decode() if isinstance(value, bytes) else str(value)


def main() -> None:
    frozen_path = BASE / "02_top10_frozen_manifest.json"
    s1_path = BASE / "input_snapshot" / "limma_all_genes.csv"
    mapping_path = BASE / "input_snapshot" / "gene_mapping_audit.csv"
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    s1 = pd.read_csv(s1_path, dtype={"gene_id": str})
    mapping = pd.read_csv(mapping_path, dtype={"gene_id": str, "ensembl_gene_ids": str})
    s1 = s1.merge(mapping[["gene_id", "gene_symbol", "ensembl_gene_ids", "mapping_status"]], on="gene_id", how="left")
    s1["symbol_norm"] = s1["gene_symbol"].fillna(s1["gene_id"]).astype(str).str.strip().str.upper()
    s1["FDR"] = pd.to_numeric(s1["adj.P.Val"], errors="coerce")
    s1["logFC"] = pd.to_numeric(s1["logFC"], errors="coerce")
    s1["S1_direction"] = np.where((s1.FDR < 0.05) & (s1.logFC > 0), "UP", np.where((s1.FDR < 0.05) & (s1.logFC < 0), "DOWN", "NOT_SIGNIFICANT"))
    # Collapse duplicate aliases only when a canonical symbol is shared; retain source gene IDs.
    s1_by_symbol = {symbol: group for symbol, group in s1.groupby("symbol_norm", sort=False)}

    gene_info_path = next((S2 / "data").glob("*gene_info*.gz"))
    gene_info = pd.read_csv(gene_info_path, sep="\t", dtype={"pr_gene_id": str}, low_memory=False)
    gene_info["symbol_norm"] = gene_info.pr_gene_symbol.fillna("").astype(str).str.strip().str.upper()
    gene_to_symbols = gene_info.drop_duplicates(["pr_gene_id", "symbol_norm"]).groupby("pr_gene_id").symbol_norm.apply(list).to_dict()
    gctx_path = next((S2 / "work").glob("*.gctx"))
    rows: list[dict[str, object]] = []
    sigs = [item["sig_id"] for item in frozen["items"]]
    with h5py.File(gctx_path, "r") as handle:
        matrix = handle["0"]["DATA"]["0"]["matrix"]
        sig_ids = [decode(x) for x in handle["0"]["META"]["COL"]["id"][:]]
        gene_ids = [decode(x) for x in handle["0"]["META"]["ROW"]["id"][:]]
        if matrix.shape != (len(sig_ids), len(gene_ids)):
            raise ValueError(f"Unexpected GCTX shape {matrix.shape}; metadata has {len(sig_ids)} signatures / {len(gene_ids)} genes")
        sig_pos = {value: i for i, value in enumerate(sig_ids)}
        gene_symbols = [gene_to_symbols.get(gene_id, [""])[0] for gene_id in gene_ids]
        positions: dict[str, list[int]] = {}
        for index, symbol in enumerate(gene_symbols):
            if symbol:
                positions.setdefault(symbol, []).append(index)
        for item in frozen["items"]:
            sig = item["sig_id"]
            if sig not in sig_pos:
                raise ValueError(f"Frozen signature missing from GCTX: {sig}")
            vector = np.asarray(matrix[sig_pos[sig], :], dtype=np.float32)
            for symbol, gene_positions in positions.items():
                values = vector[gene_positions]
                values = values[np.isfinite(values)]
                if not len(values):
                    continue
                compz = float(np.median(values))
                s1_group = s1_by_symbol.get(symbol)
                if s1_group is None:
                    s1_direction, logfc, fdr, gene_ids_s1, mapping_status = "NOT_IN_S1", "", "", "", ""
                else:
                    significant = s1_group[s1_group.S1_direction.isin(["UP", "DOWN"])]
                    if significant.empty:
                        s1_direction = "NOT_SIGNIFICANT"
                        best = s1_group.sort_values("FDR").iloc[0]
                    else:
                        # Conflicting S1 probe mappings remain explicit and are not averaged away.
                        directions = sorted(set(significant.S1_direction))
                        s1_direction = directions[0] if len(directions) == 1 else "CONFLICTING_S1_PROBES"
                        best = significant.sort_values("FDR").iloc[0]
                    logfc, fdr = float(best.logFC), float(best.FDR)
                    gene_ids_s1 = "|".join(sorted(set(s1_group.gene_id.astype(str))))
                    mapping_status = "|".join(sorted(set(s1_group.mapping_status.fillna("").astype(str))))
                if s1_direction == "UP":
                    relation = "OPPOSITE" if compz < 0 else "SAME" if compz > 0 else "NEUTRAL"
                elif s1_direction == "DOWN":
                    relation = "OPPOSITE" if compz > 0 else "SAME" if compz < 0 else "NEUTRAL"
                else:
                    relation = "NOT_ASSESSABLE"
                rows.append({"rank": item["rank"], "pert_id": item["pert_id"], "drug_name": item["pert_iname"],
                             "sig_id": sig, "cell_line": item["cell_line"], "dose": item["dose"],
                             "treatment_time": item["treatment_time"], "lincs_gene_id": "|".join(gene_ids[i] for i in gene_positions),
                             "gene_symbol": symbol, "s1_gene_ids": gene_ids_s1, "s1_mapping_status": mapping_status,
                             "S1_direction": s1_direction, "S1_logFC": logfc, "S1_FDR": fdr,
                             "S2_COMPZ_median": compz, "S1_S2_direction_relation": relation,
                             "interpretation_limit": "S2 is one frozen Level 5 consensus signature per candidate; COMPZ is a transcript response, not target engagement or efficacy. Opposite direction is descriptive and is not an inferred drug-target edge."})
    out_path = BASE / "top10_s1_s2_expression_reversal.csv"
    pd.DataFrame(rows).to_csv(out_path, index=False)
    summary = []
    frame = pd.DataFrame(rows)
    for item in frozen["items"]:
        selected = frame[frame.pert_id == item["pert_id"]]
        significant = selected[selected.S1_direction.isin(["UP", "DOWN"])]
        summary.append({"rank": item["rank"], "pert_id": item["pert_id"], "drug_name": item["pert_iname"],
                        "measured_gene_symbols": int(len(selected)), "S1_significant_overlap": int(len(significant)),
                        "opposite_direction": int(significant.S1_S2_direction_relation.eq("OPPOSITE").sum()),
                        "same_direction": int(significant.S1_S2_direction_relation.eq("SAME").sum()),
                        "neutral": int(significant.S1_S2_direction_relation.eq("NEUTRAL").sum()),
                        "S1_not_significant_or_absent": int(selected.S1_direction.isin(["NOT_SIGNIFICANT", "NOT_IN_S1", "CONFLICTING_S1_PROBES"]).sum())})
    summary_path = BASE / "top10_s1_s2_expression_reversal_summary.csv"
    pd.DataFrame(summary).to_csv(summary_path, index=False)
    manifest = {"status": "validated_exact_frozen_signature_expression_join", "frozen_top10_sha256": frozen["source_sha256"],
                "record_count": len(rows), "candidate_count": len(summary), "gctx_signature_count": len(sigs),
                "gctx_gene_count": len(gene_ids), "source_hashes": {str(path.relative_to(ROOT)): sha(path) for path in [frozen_path, s1_path, mapping_path, gene_info_path, gctx_path]},
                "outputs": {out_path.name: sha(out_path), summary_path.name: sha(summary_path)},
                "policy": "Exact frozen sig_id only; no dose or time aggregation; direction opposite is descriptive and not causality or efficacy."}
    (BASE / "top10_s1_s2_expression_reversal_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(pd.DataFrame(summary).to_string(index=False))


if __name__ == "__main__":
    main()
