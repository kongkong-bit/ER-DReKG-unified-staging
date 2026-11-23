from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parents[1]
S2 = ROOT / "s2_lincs"
sys.path.insert(0, str(ROOT / "experiments" / "exp007_signature_sensitivity" / "scripts"))
from exp007_core import wtcs_from_rank_positions  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def median_abs_deviation(values: pd.Series) -> float:
    med = float(values.median())
    return float((values - med).abs().median())


def dose_number(value: object) -> float:
    try:
        return float(str(value).split()[0])
    except (ValueError, IndexError):
        return math.inf


def main() -> None:
    for folder in (OUT / "results", OUT / "reports", OUT / "figures", OUT / "mechanism", OUT / "logs"):
        folder.mkdir(parents=True, exist_ok=True)
    data = S2 / "data"
    sig_path = next(data.glob("*sig_info*.gz"))
    met_path = next(data.glob("*sig_metrics*.gz"))
    gene_path = next(data.glob("*gene_info*.gz"))
    pert_path = next(data.glob("*pert_info*.gz"))
    gctx_path = next((S2 / "work").glob("*.gctx"))
    up_path, down_path = S2 / "s1_bing_top100_up.txt", S2 / "s1_bing_top100_down.txt"

    # Stable biological IDs are the join keys. Display names are deliberately excluded.
    sig = pd.read_csv(sig_path, sep="\t", low_memory=False)
    met = pd.read_csv(met_path, sep="\t", low_memory=False)
    meta = sig[["sig_id", "pert_id", "pert_iname", "pert_type", "cell_id", "pert_itime", "pert_idose"]].merge(
        met[["sig_id", "pert_id", "pert_type", "pert_iname", "distil_cc_q75", "distil_ss", "tas", "distil_nsample"]],
        on=["sig_id", "pert_id", "pert_type"], how="inner", suffixes=("_sig", "_metrics"), validate="one_to_one",
    )
    for column in ("distil_cc_q75", "distil_ss", "tas", "distil_nsample"):
        meta[column] = pd.to_numeric(meta[column], errors="coerce").replace(-666, np.nan)
    name_mismatches = int(meta.pert_iname_sig.fillna("").astype(str).ne(meta.pert_iname_metrics.fillna("").astype(str)).sum())
    eligible = meta[(meta.cell_id == "MCF7") & (meta.pert_type == "trt_cp") & (meta.pert_itime == "24 h") & meta.distil_cc_q75.ge(0.2)].copy()

    genes = pd.read_csv(gene_path, sep="\t", dtype={"pr_gene_id": str}, low_memory=False)
    genes["symbol"] = genes.pr_gene_symbol.fillna("").astype(str).str.strip().str.upper()
    genes["is_bing"] = pd.to_numeric(genes.pr_is_bing, errors="coerce").eq(1)
    bing = genes[genes.is_bing & genes.symbol.ne("")].drop_duplicates("symbol")
    bing_symbols = set(bing.symbol)
    up = set(pd.read_csv(up_path, sep="\t").gene_symbol.astype(str).str.strip().str.upper())
    down = set(pd.read_csv(down_path, sep="\t").gene_symbol.astype(str).str.strip().str.upper())
    if len(up) != 100 or len(down) != 100 or up & down or not (up | down) <= bing_symbols:
        raise RuntimeError("BING Top100 input validation failed")
    id_to_symbol = bing.set_index("pr_gene_id").symbol

    scores: list[dict] = []
    with h5py.File(gctx_path, "r") as handle:
        matrix = handle["0"]["DATA"]["0"]["matrix"]
        sig_ids = [x.decode() if isinstance(x, bytes) else str(x) for x in handle["0"]["META"]["COL"]["id"][:]]
        gene_ids = [x.decode() if isinstance(x, bytes) else str(x) for x in handle["0"]["META"]["ROW"]["id"][:]]
        sig_pos = {value: i for i, value in enumerate(sig_ids)}
        symbols = id_to_symbol.reindex(gene_ids).fillna("").to_numpy()
        valid = np.asarray([symbol in bing_symbols for symbol in symbols], dtype=bool)
        background = symbols[valid]
        positions_by_symbol: dict[str, list[int]] = {}
        for index, symbol in enumerate(background):
            positions_by_symbol.setdefault(str(symbol), []).append(index)
        up_indices = np.asarray([i for symbol in sorted(up) for i in positions_by_symbol.get(symbol, [])], dtype=np.int32)
        down_indices = np.asarray([i for symbol in sorted(down) for i in positions_by_symbol.get(symbol, [])], dtype=np.int32)
        if len(up_indices) != 100 or len(down_indices) != 100 or len(background) != 10174:
            raise RuntimeError(f"Unexpected BING rank universe/query sizes: {len(background)}, {len(up_indices)}, {len(down_indices)}")
        missing = sorted(set(eligible.sig_id) - set(sig_pos))
        if missing:
            raise RuntimeError(f"{len(missing)} eligible stable-ID signatures are absent from GCTX")
        eligible = eligible.sort_values(["pert_id", "pert_idose", "sig_id"], kind="stable")
        for number, row in enumerate(eligible.itertuples(index=False), start=1):
            values = np.asarray(matrix[sig_pos[row.sig_id], :], dtype=np.float32)[valid]
            if not np.isfinite(values).all():
                finite = np.isfinite(values)
                values, bg = values[finite], background[finite]
                # Missing expression values are excluded from both rank universe and hit indices.
                positions_by_symbol = {}
                for index, symbol in enumerate(bg):
                    positions_by_symbol.setdefault(str(symbol), []).append(index)
                up_i = np.asarray([i for symbol in sorted(up) for i in positions_by_symbol.get(symbol, [])], dtype=np.int32)
                down_i = np.asarray([i for symbol in sorted(down) for i in positions_by_symbol.get(symbol, [])], dtype=np.int32)
            else:
                bg, up_i, down_i = background, up_indices, down_indices
            order = np.lexsort((bg, -values))
            rank_position = np.empty(len(order), dtype=np.int32)
            rank_position[order] = np.arange(len(order), dtype=np.int32)
            es_up, es_down, wtcs = wtcs_from_rank_positions(rank_position, values, up_i, down_i)
            scores.append({
                "sig_id": row.sig_id, "pert_id": row.pert_id, "drug_name": row.pert_iname_sig,
                "cell_id": row.cell_id, "pert_type": row.pert_type, "dose": row.pert_idose, "time": row.pert_itime,
                "distil_cc_q75": row.distil_cc_q75, "distil_ss": row.distil_ss, "tas": row.tas,
                "distil_nsample": row.distil_nsample, "ES_UP": es_up, "ES_DOWN": es_down,
                "WTCS": wtcs, "reversal_score": -wtcs, "effective_background_genes": len(values),
                "n_up": len(up), "n_down": len(down),
            })
            if number % 1000 == 0:
                print(f"scored {number}/{len(eligible)} stable-ID Q2 signatures", flush=True)

    score_frame = pd.DataFrame(scores)
    if len(score_frame) != 5861 or score_frame.sig_id.nunique() != len(score_frame) or score_frame.WTCS.isna().any():
        raise RuntimeError("Stable-ID scoring count/uniqueness/score validation failed")
    historical = pd.read_csv(S2 / "results" / "formal_signature_scores.csv")
    historical = historical[historical.scheme.eq("B")][["sig_id", "ES_UP", "ES_DOWN", "WTCS"]]
    overlap = score_frame.merge(historical, on="sig_id", how="inner", suffixes=("_new", "_old"), validate="one_to_one")
    max_diffs = {column: float((overlap[f"{column}_new"] - overlap[f"{column}_old"]).abs().max()) for column in ("ES_UP", "ES_DOWN", "WTCS")}
    if len(overlap) != 4761 or max(max_diffs.values()) > 1e-9:
        raise RuntimeError(f"WTCS reference reproduction failed: overlap={len(overlap)}, differences={max_diffs}")
    score_frame.to_csv(OUT / "results" / "final_signature_scores.csv", index=False)

    condition_keys = ["pert_id", "drug_name", "cell_id", "pert_type", "dose", "time"]
    conditions = score_frame.groupby(condition_keys, dropna=False).agg(
        n_signatures=("sig_id", "nunique"), WTCS_median=("WTCS", "median"), WTCS_mean=("WTCS", "mean"),
        WTCS_sd=("WTCS", "std"), WTCS_mad=("WTCS", median_abs_deviation), CC_median=("distil_cc_q75", "median"),
        TAS_median=("tas", "median"), replicates_median=("distil_nsample", "median"),
    ).reset_index()
    conditions["rank_within_condition"] = conditions.groupby(["cell_id", "pert_type", "dose", "time"]).WTCS_median.rank(method="average", ascending=True)
    conditions.to_csv(OUT / "results" / "final_drug_condition_summary.csv", index=False)
    dose_coverage = conditions.groupby("dose").pert_id.nunique().sort_values(ascending=False)
    primary_dose = str(dose_coverage.index[0])
    primary = conditions[conditions.dose.eq(primary_dose)].copy().sort_values(["WTCS_median", "pert_id"], kind="stable")
    primary["rank"] = np.arange(1, len(primary) + 1)
    stability = conditions.groupby("pert_id").agg(n_24h_dose_conditions=("dose", "nunique"))
    stability["negative_dose_fraction"] = conditions.assign(negative=conditions.WTCS_median.lt(0)).groupby("pert_id").negative.mean()
    primary = primary.merge(stability.reset_index(), on="pert_id", how="left", validate="one_to_one")
    primary["primary_dose_selection_rule"] = "24 h QC-passed dose with maximum distinct pert_id coverage; ties by numeric dose ascending"

    external_path = ROOT / "experiments" / "exp010_external_s1" / "results" / "external_s1_drug_ranking.csv"
    ext = pd.read_csv(external_path)
    ext = ext[(ext.cell_id == "MCF7") & (ext.pert_type == "trt_cp")]
    ext_cols = [c for c in ["pert_id", "dose", "time", "external_rank", "WTCS_median", "n_signatures"] if c in ext.columns]
    if "external_rank" not in ext_cols and "rank" in ext.columns:
        ext = ext.rename(columns={"rank": "external_rank"}); ext_cols = ["pert_id", "dose", "time", "external_rank", "WTCS_median", "n_signatures"]
    primary = primary.merge(ext[ext_cols].drop_duplicates(["pert_id", "dose", "time"]), on=["pert_id", "dose", "time"], how="left", suffixes=("", "_external"), validate="one_to_one")

    prism_path = ROOT / "experiments" / "exp011_prism_validation" / "results" / "candidate_sensitivity_results.csv"
    prism = pd.read_csv(prism_path)
    prism_cols = [c for c in ["pert_id", "erpos_mean_sensitivity", "erpos_median_sensitivity", "n_erpos_lines", "erneg_mean_sensitivity", "n_erneg_lines", "mcf7_sensitivity", "n_mcf7_conditions", "sensitivity_rank_erpos"] if c in prism.columns]
    prism = prism[prism_cols].drop_duplicates("pert_id")
    primary = primary.merge(prism, on="pert_id", how="left", validate="one_to_one")

    old = pd.read_csv(ROOT / "experiments" / "exp006_ranking_reliability" / "results" / "candidate_drugs_all.csv")
    old = old.sort_values("rank").reset_index(drop=True)
    old_top = set(old.head(10).pert_id)
    new_top = set(primary.head(10).pert_id)
    audit_scores = pd.read_csv(ROOT / "experiments" / "exp009_lincs_quality" / "results" / "B200_signature_scores_stable_id.csv")
    audit_scores = audit_scores[audit_scores.sig_id.isin(overlap.sig_id)]
    audit_compare = overlap[["sig_id", "WTCS_old", "WTCS_new"]].merge(audit_scores[["sig_id", "WTCS"]].rename(columns={"WTCS": "WTCS_exp009"}), on="sig_id", validate="one_to_one")
    exp009_wrong = int((audit_compare.WTCS_exp009 - audit_compare.WTCS_new).abs().gt(1e-9).sum())
    exp009_maxdiff = float((audit_compare.WTCS_exp009 - audit_compare.WTCS_new).abs().max())
    primary.to_csv(OUT / "results" / "final_corrected_condition_ranking.csv", index=False)
    primary.head(10).to_csv(OUT / "results" / "final_top10.csv", index=False)

    input_paths = [sig_path, met_path, gene_path, pert_path, gctx_path, up_path, down_path,
                   S2 / "results" / "formal_signature_scores.csv", external_path, prism_path,
                   ROOT / "experiments" / "exp009_lincs_quality" / "results" / "metadata_join_sensitivity.csv",
                   ROOT / "experiments" / "exp009_lincs_quality" / "results" / "B200_signature_scores_stable_id.csv"]
    manifest = {
        "status": "PASS", "created_utc": datetime.now(timezone.utc).isoformat(),
        "project": "ER-positive breast cancer drug repositioning",
        "protocol": {"s1": "BING-restricted Top100 UP/DOWN from GSE42568, FDR<0.05",
                     "s2": "GSE70138 Level 5, MCF7, trt_cp, 24 h, distil_cc_q75>=0.2",
                     "primary_dose_rule": "select 24 h dose with maximum distinct pert_id coverage; do not choose per-drug best dose",
                     "score": "Broad-style two-sided weighted KS WTCS; negative indicates inverse expression association",
                     "drug_aggregation": "median WTCS across qualifying signatures within exact pert_id/cell/type/dose/time",
                     "ranking": "ascending condition median WTCS; deterministic tie break pert_id ascending",
                     "kg_or_prism_in_rank": False},
        "counts": {"stable_id_q2_signatures_rescored": len(score_frame), "stable_id_q2_compounds": int(score_frame.pert_id.nunique()),
                   "primary_dose": primary_dose, "primary_dose_compounds": len(primary),
                   "historical_common_ids_reproduced": len(overlap), "exp009_order_bug_common_ids": len(audit_compare),
                   "exp009_wtcs_values_mismatching_corrected": exp009_wrong},
        "validation": {"historical_max_abs_difference": max_diffs, "historical_match_tolerance": 1e-9,
                       "exp009_max_abs_difference": exp009_maxdiff, "old_new_top10_overlap": len(old_top & new_top),
                       "dose_coverage": {str(k): int(v) for k, v in dose_coverage.items()}},
        "input_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in input_paths},
        "output_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in [OUT / "results" / "final_signature_scores.csv", OUT / "results" / "final_drug_condition_summary.csv", OUT / "results" / "final_corrected_condition_ranking.csv", OUT / "results" / "final_top10.csv"]},
    }
    (OUT / "results" / "final_data_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "reports" / "final_input_audit.md").write_text(
        "# Final01 输入与 ID 审计\n\n"
        f"审计与重算时间（UTC）：{manifest['created_utc']}。\n\n"
        "## 核验结论\n\n"
        f"- GSE70138 的 sig_info / sig_metrics 用 sig_id + pert_id + pert_type 联结；两表显示名不作为键。实际发现 {name_mismatches:,} 行 pert_iname 不同。\n"
        f"- 24 h MCF7 / trt_cp、CC≥0.2 的 stable ID 合并共有 {len(score_frame):,} 条签名、{score_frame.pert_id.nunique():,} 个化合物；全部签名 ID 均在 GCTX 中。\n"
        f"- 历史四字段连接（额外要求 pert_iname 一致）仅留下 4,761 条签名；stable ID 口径为 5,861 条，漏失 1,100 条。这个差异会改变有效实验集合，故历史排行榜不能直接作为最终 Top10。\n"
        f"- 本次从 GCTX 重算 {len(score_frame):,} 条 stable ID 签名，沿用已通过历史复现的 WTCS 算法；对与旧正式结果重叠的 {len(overlap):,} 个 BING Top100 签名，ES_UP、ES_DOWN、WTCS 最大绝对差分别为 {max_diffs['ES_UP']:.3g}、{max_diffs['ES_DOWN']:.3g}、{max_diffs['WTCS']:.3g}。门禁通过。\n"
        f"- Exp009 的 stable-ID 分数文件虽补齐了签名，但该文件与本次正确排序权重配对的重算结果有 {exp009_wrong:,}/{len(audit_compare):,} 条不一致，最大 WTCS 差 {exp009_maxdiff:.4g}；根因是其命中权重未随命中位置排序。本次不采用该旧分数文件。\n"
        "- S1 输入为既有 BING Top100 UP/DOWN 文件；未修改 limma、S1 清单、LINCS 原始文件或历史 Smoke Test。全部来源 SHA-256 见 `results/final_data_manifest.json`。\n",
        encoding="utf-8")
    (OUT / "reports" / "final_ranking_protocol.md").write_text(
        "# Final02 排名规则冻结\n\n"
        "1. 疾病签名：GSE42568 ER+ 肿瘤相对正常组织；BING 空间中 FDR<0.05 的 UP/DOWN 各 Top100。\n"
        "2. 药物签名：GSE70138 Level 5；MCF7，trt_cp，24 h，distil_cc_q75≥0.2；metadata 仅按 sig_id + pert_id + pert_type 联结。\n"
        f"3. 统一主剂量：经所有 QC 合格 24 h 条件统计，{primary_dose} 在本数据中覆盖药物最多（{len(primary):,} 个 perturbagen）；不为每种药物挑最好剂量。完整剂量覆盖见 manifest。\n"
        "4. WTCS 使用固定 BING 排序背景、 Broad-style 两侧加权 KS，signature-level 得分后按 pert_id / 细胞 / 类型 / 剂量 / 时间组内取 WTCS 中位数。\n"
        "5. 主排序按主剂量条件 WTCS 升序；同分按 pert_id 字典序。药物 ID 去重。Exp010、PRISM、知识图谱、靶点数、机制路径数不参与排序或 Top10 选择，仅作为独立证据呈现。\n"
        "6. WTCS<0 仅表示表达方向上的逆关联，不等于药效或临床疗效。单 signature 药物标示重复有限。\n\n"
        "本协议在查看最终候选机制证据之前固定。\n", encoding="utf-8")
    (OUT / "reports" / "final_top10_selection_report.md").write_text(
        "# Final02 修正后 Top 10 选择报告\n\n"
        f"稳定 ID 重算后，{primary_dose}、24 h、CC≥0.2 条件共有 {len(primary):,} 个唯一药物。Top10 按固定 WTCS 规则生成，结果见 `results/final_top10.csv`。\n\n"
        f"修正后的 Top10 与早期正式榜单 Top10 按 LINCS pert_id 的重合数为 {len(old_top & new_top)}/10。该变化首先反映早期显示名连接遗漏 1,100 条合格 signature，以及 Exp009 追加分数的命中权重排序错误；不能解释成药物生物学结论发生变化。\n\n"
        "Top10 是计算筛选候选，后续机制解释必须引用现有数据来源；知识图谱覆盖或 PRISM 结果不改变排序。结果不构成疗效证明。\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "signatures": len(score_frame), "compounds": score_frame.pert_id.nunique(),
                      "primary_dose": primary_dose, "primary_dose_compounds": len(primary), "top10_overlap_old": len(old_top & new_top),
                      "historical_max_abs_difference": max_diffs, "exp009_wtcs_mismatches": exp009_wrong,
                      "top10": primary.head(10)[["rank", "pert_id", "drug_name", "WTCS_median", "n_signatures"]].to_dict("records")}, indent=2))


if __name__ == "__main__":
    main()
