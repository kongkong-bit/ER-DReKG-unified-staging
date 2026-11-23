from __future__ import annotations

import csv
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parents[1]
S2 = ROOT / "s2_lincs"


def main() -> None:
    top = pd.read_csv(OUT / "results" / "final_top10.csv")
    scores = pd.read_csv(OUT / "results" / "final_signature_scores.csv")
    targets = pd.read_csv(OUT / "mechanism" / "final_neo4j_direct_targets.csv")
    genes = pd.read_csv(next((S2 / "data").glob("*gene_info*.gz")), sep="\t", dtype={"pr_gene_id": str}, low_memory=False)
    genes["symbol_norm"] = genes.pr_gene_symbol.fillna("").astype(str).str.strip().str.upper()
    gene_symbols = genes.drop_duplicates(["pr_gene_id", "symbol_norm"])
    sig_path = next((S2 / "work").glob("*.gctx"))
    gene_info = genes.set_index("pr_gene_id").symbol_norm
    gene_target_pairs = targets[["pert_id", "drug_name", "target_gene_id", "target_symbol", "s1_direction", "s1_logFC", "s1_FDR"]].drop_duplicates()
    gene_target_pairs["target_symbol_norm"] = gene_target_pairs.target_symbol.fillna("").astype(str).str.strip().str.upper()
    output = []
    all_score_rows = scores.merge(top[["pert_id", "dose", "time", "rank"]], on=["pert_id", "dose", "time"], how="inner", validate="many_to_one")
    with h5py.File(sig_path, "r") as h:
        matrix = h["0"]["DATA"]["0"]["matrix"]
        sig_ids = [x.decode() if isinstance(x, bytes) else str(x) for x in h["0"]["META"]["COL"]["id"][:]]
        gene_ids = [x.decode() if isinstance(x, bytes) else str(x) for x in h["0"]["META"]["ROW"]["id"][:]]
        sig_pos = {value: i for i, value in enumerate(sig_ids)}
        row_gene = pd.DataFrame({"gene_id": gene_ids})
        row_gene["symbol_norm"] = row_gene.gene_id.map(gene_info).fillna("")
        positions_by_symbol = row_gene.groupby("symbol_norm", sort=False).indices
        vectors = {sig: np.asarray(matrix[sig_pos[sig], :], dtype=np.float32) for sig in all_score_rows.sig_id.unique()}
        for drug in top.itertuples(index=False):
            signatures = all_score_rows[all_score_rows.pert_id.eq(drug.pert_id)]
            candidate_targets = gene_target_pairs[gene_target_pairs.pert_id.eq(drug.pert_id)]
            if candidate_targets.empty:
                output.append({"rank": drug.rank, "pert_id": drug.pert_id, "drug_name": drug.drug_name,
                               "signature_count": len(signatures), "target_gene_id": "", "target_symbol": "",
                               "mapping_status": "no direct target in current GraphBuild", "s1_direction": "",
                               "s1_logFC": np.nan, "s1_FDR": np.nan, "sig_id": "", "COMPZ": np.nan,
                               "S2_directional_relation": "not assessable"})
                continue
            for target in candidate_targets.itertuples(index=False):
                locations = positions_by_symbol.get(target.target_symbol_norm, []) if target.target_symbol_norm else []
                if not locations:
                    output.append({"rank": drug.rank, "pert_id": drug.pert_id, "drug_name": drug.drug_name,
                                   "signature_count": len(signatures), "target_gene_id": target.target_gene_id, "target_symbol": target.target_symbol,
                                   "mapping_status": "target not measured in GSE70138 Level 5", "s1_direction": target.s1_direction,
                                   "s1_logFC": target.s1_logFC, "s1_FDR": target.s1_FDR, "sig_id": "", "COMPZ": np.nan,
                                   "S2_directional_relation": "not assessable"})
                    continue
                for sig in signatures.itertuples(index=False):
                    values = [float(vectors[sig.sig_id][index]) for index in locations if np.isfinite(vectors[sig.sig_id][index])]
                    compz = float(np.median(values)) if values else np.nan
                    if not np.isfinite(compz) or not target.s1_direction in ("UP", "DOWN") or compz == 0:
                        relation = "neutral or no S1 DEG"
                    elif (target.s1_direction == "UP" and compz < 0) or (target.s1_direction == "DOWN" and compz > 0):
                        relation = "opposite expression direction (descriptive)"
                    else:
                        relation = "same expression direction (descriptive)"
                    output.append({"rank": drug.rank, "pert_id": drug.pert_id, "drug_name": drug.drug_name,
                                   "signature_count": len(signatures), "target_gene_id": target.target_gene_id, "target_symbol": target.target_symbol,
                                   "mapping_status": "mapped by exact LINCS gene symbol", "s1_direction": target.s1_direction,
                                   "s1_logFC": target.s1_logFC, "s1_FDR": target.s1_FDR, "sig_id": sig.sig_id,
                                   "COMPZ": compz, "S2_directional_relation": relation})
    out = pd.DataFrame(output)
    out.to_csv(OUT / "mechanism" / "final_top10_target_s2_expression.csv", index=False)
    summary = out.groupby(["rank", "pert_id", "drug_name"], dropna=False).agg(
        target_rows=("target_gene_id", "count"), target_measured=("mapping_status", lambda x: int(x.eq("mapped by exact LINCS gene symbol").sum())),
        opposite_direction=("S2_directional_relation", lambda x: int(x.eq("opposite expression direction (descriptive)").sum())),
        same_direction=("S2_directional_relation", lambda x: int(x.eq("same expression direction (descriptive)").sum())),
    ).reset_index()
    summary.to_csv(OUT / "mechanism" / "final_top10_target_s2_summary.csv", index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
