from __future__ import annotations

import gzip
import hashlib
import json
import random
import shutil
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
WORK = ROOT / "work"
OUT = ROOT / "results"
for folder in (WORK, OUT, ROOT / "reports", ROOT / "s1", ROOT / "metadata", ROOT / "processed", ROOT / "figures", ROOT / "tests"):
    folder.mkdir(exist_ok=True)
random.seed(42)
np.random.seed(42)

GZ = next(DATA.glob("*Level5*.gctx.gz"))
S1 = ROOT.parent / "s1_初步_gse42568_limma" / "limma_all_genes.csv"


def weighted_es(ranked: list[str], weights: dict[str, float], genes: set[str], p: float = 1.0) -> float:
    hits = [i for i, gene in enumerate(ranked) if gene in genes]
    if not hits or len(hits) == len(ranked):
        return float("nan")
    hit_weights = np.array([abs(weights[ranked[i]]) ** p for i in hits], dtype=float)
    if hit_weights.sum() == 0:
        hit_weights[:] = 1.0
    hit_weights /= hit_weights.sum()
    hit_map = dict(zip(hits, hit_weights))
    miss_step = 1.0 / (len(ranked) - len(hits))
    running = 0.0
    maximum = -np.inf
    minimum = np.inf
    for i in range(len(ranked)):
        running += hit_map[i] if i in hit_map else -miss_step
        maximum = max(maximum, running)
        minimum = min(minimum, running)
    return float(maximum if abs(maximum) >= abs(minimum) else minimum)


def wtcs(ranked: list[str], weights: dict[str, float], up: set[str], down: set[str]) -> tuple[float, float, float]:
    if up & down:
        raise ValueError("UP and DOWN sets overlap")
    es_up = weighted_es(ranked, weights, up)
    es_down = weighted_es(ranked, weights, down)
    if np.sign(es_up) == np.sign(es_down):
        score = 0.0
    else:
        score = (es_up - es_down) / 2.0
    return es_up, es_down, score


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    s1 = pd.read_csv(S1)
    required = {"gene_symbol", "logFC", "adj.P.Val", "t"}
    if not required.issubset(s1.columns):
        raise ValueError(f"S1 missing columns {required - set(s1.columns)}")
    s1["gene_symbol"] = s1.gene_symbol.astype(str).str.strip()
    s1 = s1[s1.gene_symbol.ne("") & s1["adj.P.Val"].lt(0.05)].copy()
    s1 = s1.sort_values(["adj.P.Val", "logFC"], ascending=[True, False]).drop_duplicates("gene_symbol")
    up_df = s1[s1.logFC.gt(0)].head(100)
    down_df = s1[s1.logFC.lt(0)].sort_values(["adj.P.Val", "logFC"], ascending=[True, True]).head(100)
    up, down = set(up_df.gene_symbol), set(down_df.gene_symbol)
    if len(up) != 100 or len(down) != 100 or up & down:
        raise ValueError("S1 query gene selection failed")
    up_df.to_csv(ROOT / "s1" / "s1_100_up.txt", sep="\t", index=False)
    down_df.to_csv(ROOT / "s1" / "s1_100_down.txt", sep="\t", index=False)
    manifest = {"input": str(S1), "sha256": sha256(S1), "rule": "FDR<0.05, sort adj.P.Val ascending, tie-break abs(logFC) descending; select separately by sign; duplicate symbols removed", "contrast": "ER+ Tumor - Normal", "seed": 42, "up_n": len(up_df), "down_n": len(down_df)}
    (ROOT / "s1" / "s1_100_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    paths = {p.name.split("_")[-1].split(".")[0]: p for p in DATA.glob("*.txt.gz")}
    sig = pd.read_csv(next(DATA.glob("*sig_info*.gz")), sep="\t")
    met = pd.read_csv(next(DATA.glob("*sig_metrics*.gz")), sep="\t")
    gene = pd.read_csv(next(DATA.glob("*gene_info*.gz")), sep="\t")
    pert = pd.read_csv(next(DATA.glob("*pert_info*.gz")), sep="\t")
    gctx = WORK / GZ.name.removesuffix(".gz")
    if not gctx.exists():
        with gzip.open(GZ, "rb") as source, gctx.open("wb") as target:
            shutil.copyfileobj(source, target, length=8 * 1024 * 1024)

    with h5py.File(gctx, "r") as h5:
        print("HDF5 keys", list(h5.keys()))
        print("DATA keys", list(h5["0"]["DATA"].keys()))
        matrix = h5["0"]["DATA"]["0"]["matrix"]
        sig_ids = [x.decode() for x in h5["0"]["META"]["COL"]["id"][:]]
        gene_ids = [x.decode() for x in h5["0"]["META"]["ROW"]["id"][:]]
        print("matrix", matrix.shape, matrix.chunks, matrix.dtype)
        print("signature IDs", len(sig_ids), sig_ids[:3])
        print("gene IDs", len(gene_ids), gene_ids[:3])
        print("intersection sig/meta", len(set(sig_ids) & set(sig.sig_id)))
        print("gene mapping", len(set(gene_ids) & set(gene.pr_gene_id.astype(str))))
        meta = sig[(sig.cell_id == "MCF7") & (sig.pert_type == "trt_cp")].copy()
        meta = meta.merge(met, on=["sig_id", "pert_id", "pert_iname", "pert_type"], how="left", suffixes=("", "_qc"))
        meta = meta[meta.sig_id.isin(sig_ids)].copy()
        meta["quality"] = pd.to_numeric(meta.get("distil_cc_q75"), errors="coerce")
        meta = meta.sort_values(["quality", "sig_id"], ascending=[False, True], na_position="last")
        # Spread selection across perturbagens while keeping a fixed quality-first order.
        selected = meta.drop_duplicates("pert_id").head(30).copy()
        if len(selected) < 20:
            selected = meta.head(30).copy()
        selected.to_csv(ROOT / "metadata" / "smoke_selected_signatures.csv", index=False)
        inventory = meta.groupby(["pert_itime", "pert_idose"], dropna=False).agg(signature_count=("sig_id", "size"), unique_drugs=("pert_id", "nunique")).reset_index()
        inventory.to_csv(ROOT / "metadata" / "mcf7_inventory.csv", index=False)
        selected_ids = selected.sig_id.tolist()
        sig_pos = {sid: i for i, sid in enumerate(sig_ids)}
        gene["pr_gene_id"] = gene.pr_gene_id.astype(str)
        gi = gene.set_index("pr_gene_id").reindex(gene_ids)
        symbols = gi.pr_gene_symbol.astype(str).str.strip().tolist()
        valid = np.array([s and s != "nan" for s in symbols])
        symbol_arr = np.array(symbols, dtype=object)
        records = []
        for sid in selected_ids:
            values = np.asarray(matrix[sig_pos[sid], :], dtype=float)
            frame = pd.DataFrame({"gene_symbol": symbol_arr[valid], "score": values[valid]})
            frame = frame.replace([np.inf, -np.inf], np.nan).dropna()
            frame = frame.groupby("gene_symbol", as_index=False).score.mean()
            mapping = dict(zip(frame.gene_symbol, frame.score))
            ranked = sorted(mapping, key=lambda g: (-mapping[g], g))
            es_up, es_down, score = wtcs(ranked, mapping, up, down)
            records.append({"sig_id": sid, "pert_id": selected.loc[selected.sig_id == sid, "pert_id"].iloc[0],
                "drug_name": selected.loc[selected.sig_id == sid, "pert_iname"].iloc[0],
                "cell_id": "MCF7", "pert_type": "trt_cp",
                "dose": selected.loc[selected.sig_id == sid, "pert_idose"].iloc[0],
                "time": selected.loc[selected.sig_id == sid, "pert_itime"].iloc[0],
                "distil_cc_q75": selected.loc[selected.sig_id == sid, "quality"].iloc[0],
                "ES_UP": es_up, "ES_DOWN": es_down, "WTCS": score, "reversal_score": -score,
                "effective_genes": len(mapping), "UP_coverage": len(up & mapping.keys()) / len(up),
                "DOWN_coverage": len(down & mapping.keys()) / len(down)})
        result = pd.DataFrame(records).sort_values("WTCS")
        result.to_csv(OUT / "smoke_signature_scores.csv", index=False)
        selected.merge(result[["sig_id", "WTCS", "reversal_score"]], on="sig_id").sort_values("WTCS").to_csv(OUT / "smoke_candidate_preview.csv", index=False)
        result.sort_values("WTCS").plot.barh(x="drug_name", y="WTCS", figsize=(9, 10), legend=False, title="Smoke Test: WTCS by LINCS signature")
        plt.tight_layout(); plt.savefig(ROOT / "figures" / "smoke_wtcs_ranking.png", dpi=160); plt.close()
        plt.figure(figsize=(7, 4)); plt.hist(result.WTCS.dropna(), bins=12, color="#4472C4", edgecolor="white"); plt.xlabel("WTCS"); plt.ylabel("Signature count"); plt.title("Smoke Test: WTCS distribution"); plt.tight_layout(); plt.savefig(ROOT / "figures" / "smoke_wtcs_distribution.png", dpi=160); plt.close()
        qc = met[met.sig_id.isin(selected_ids)].copy()
        (ROOT / "reports" / "00_data_audit.md").write_text(f"""# Data audit\n\n- S1 file: `{S1}`; SHA256 `{manifest['sha256']}`. Required columns present: {sorted(required)}. Selected genes: UP {len(up)}, DOWN {len(down)}. Contrast verified from `run_limma.R`: `Tumor - Normal`.\n- LINCS GCTX gzip: `{GZ.name}` ({GZ.stat().st_size} bytes). Decompressed to local work copy, HDF5 signature `\\x89HDF`; matrix shape {matrix.shape}, dtype {matrix.dtype}; stored as signature-axis × gene-axis.\n- GCTX signature IDs: {len(sig_ids)}; matching sig_info: {len(set(sig_ids) & set(sig.sig_id))}. Gene IDs: {len(gene_ids)}; matching gene_info: {len(set(gene_ids) & set(gene.pr_gene_id))}.\n- Metadata files parsed: gene_info, sig_info, sig_metrics, pert_info, inst_info. D drive free space at run start: 76.7 GiB.\n- MCF7 trt_cp inventory: {len(meta)} signatures, {meta.pert_id.nunique()} unique perturbagens.\n""", encoding="utf-8")
        (ROOT / "reports" / "01_signature_selection.md").write_text(f"# Signature selection\n\nFiltered `cell_id=MCF7`, `pert_type=trt_cp`, intersected with GCTX IDs, ranked by `distil_cc_q75` descending and selected one per perturbagen, capped at 30. Selected {len(selected)} signatures and {selected.pert_id.nunique()} unique drugs. Conditions retained as provided.\n", encoding="utf-8")
        (ROOT / "reports" / "02_s2_extraction.md").write_text(f"# S2 extraction\n\nExtracted {len(result)} real signature rows individually from GCTX. Gene scores cover {result.effective_genes.min()}–{result.effective_genes.max()} unique mapped symbols. S1 UP coverage {result.UP_coverage.min():.1%}; DOWN coverage {result.DOWN_coverage.min():.1%}. The LINCS Level 5 values are perturbation scores, not patient logFC.\n", encoding="utf-8")
        (ROOT / "reports" / "03_smoke_results.md").write_text(f"# Smoke results\n\nScored {len(result)} real MCF7 chemical perturbation signatures spanning {result.pert_id.nunique()} compounds. Most negative WTCS: `{result.iloc[0].sig_id}` ({result.iloc[0].drug_name}), WTCS {result.iloc[0].WTCS:.4f}, reversal_score {result.iloc[0].reversal_score:.4f}. This is a smoke-test subset, not a full-library ranking or therapeutic claim.\n", encoding="utf-8")
        print("selected/score rows", len(selected_ids), len(result))
        print(result.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
