"""Run a project-specific MCF7 LINCS screen from a completed S1 DEG table.

This CLI reads each eligible Level 5 GCTX signature row independently. It never
loads the full GCTX matrix, and it retains dose/time strata through aggregation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import h5py
import numpy as np
import pandas as pd

from scoring import wtcs


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
WORK = ROOT / "work"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _norm_symbol(value: object) -> str:
    return str(value).strip().upper() if pd.notna(value) else ""


def _read_bing_gene_info(path: Path) -> tuple[pd.DataFrame, dict[str, str], dict[str, set[str]]]:
    genes = pd.read_csv(path, sep="\t", dtype={"pr_gene_id": str}, low_memory=False)
    required = {"pr_gene_id", "pr_gene_symbol", "pr_is_bing"}
    if not required.issubset(genes.columns):
        raise ValueError(f"gene_info 缺少字段：{sorted(required - set(genes.columns))}")
    genes["pr_gene_id"] = genes.pr_gene_id.astype(str).str.strip()
    genes["symbol_norm"] = genes.pr_gene_symbol.map(_norm_symbol)
    genes["is_bing"] = pd.to_numeric(genes.pr_is_bing, errors="coerce").eq(1)
    bing = genes[genes.is_bing & genes.pr_gene_id.ne("") & genes.symbol_norm.ne("")].copy()
    id_groups = bing.groupby("pr_gene_id").symbol_norm.nunique()
    id_to_symbol = {
        gene_id: str(group.symbol_norm.iloc[0])
        for gene_id, group in bing.groupby("pr_gene_id")
        if id_groups.loc[gene_id] == 1
    }
    symbols_to_ids = bing.groupby("symbol_norm").pr_gene_id.apply(lambda values: set(values.astype(str))).to_dict()
    return bing, id_to_symbol, symbols_to_ids


def map_and_select_s1(
    s1_path: Path,
    gene_info_path: Path,
    identifier_type: str,
    *,
    fdr_threshold: float,
    top_n: int,
) -> tuple[set[str], set[str], pd.DataFrame, dict]:
    if identifier_type not in {"symbol", "entrez", "ensembl"}:
        raise ValueError("identifier_type 只能是 symbol、entrez 或 ensembl")
    s1 = pd.read_csv(s1_path, dtype={"gene_id": str}, low_memory=False)
    required = {"gene_id", "logFC", "adj.P.Val", "t"}
    if not required.issubset(s1.columns):
        raise ValueError(f"S1 表缺少字段：{sorted(required - set(s1.columns))}")
    s1["gene_id"] = s1.gene_id.fillna("").astype(str).str.strip()
    for column in ("logFC", "adj.P.Val", "t"):
        s1[column] = pd.to_numeric(s1[column], errors="coerce")
    s1 = s1[s1.gene_id.ne("") & np.isfinite(s1.logFC) & np.isfinite(s1["adj.P.Val"]) & np.isfinite(s1.t)].copy()
    if (s1["adj.P.Val"].lt(0) | s1["adj.P.Val"].gt(1)).any():
        raise ValueError("S1 表包含 [0, 1] 范围外的 adj.P.Val")
    bing, id_to_symbol, symbols_to_ids = _read_bing_gene_info(gene_info_path)
    if identifier_type == "symbol":
        source_key = s1.gene_id.map(_norm_symbol)
        matches = source_key.map(symbols_to_ids)
    elif identifier_type == "entrez":
        source_key = s1.gene_id.astype(str).str.strip()
        matches = source_key.map(lambda key: {key} if key in id_to_symbol else set())
    else:
        source_key = s1.gene_id.astype(str).str.strip()
        matches = source_key.map(lambda _: set())
    mapped_ids: list[str | None] = []
    mapped_symbols: list[str | None] = []
    statuses: list[str] = []
    for match in matches:
        identifiers = match if isinstance(match, set) else set()
        if len(identifiers) == 1:
            gene_id = next(iter(identifiers))
            mapped_ids.append(gene_id)
            mapped_symbols.append(id_to_symbol.get(gene_id))
            statuses.append("mapped_unique_bing")
        elif len(identifiers) > 1:
            mapped_ids.append(None)
            mapped_symbols.append(None)
            statuses.append("ambiguous_symbol_multiple_bing_ids")
        else:
            mapped_ids.append(None)
            mapped_symbols.append(None)
            statuses.append("unsupported_identifier_type_ensembl_no_crosswalk" if identifier_type == "ensembl" else "not_found_in_lincs_bing")
    audit = s1.copy()
    audit["identifier_type"] = identifier_type
    audit["lincs_gene_id"] = mapped_ids
    audit["lincs_gene_symbol"] = mapped_symbols
    audit["mapping_status"] = statuses
    audit["selected_for_query"] = False
    eligible = audit[(audit.mapping_status == "mapped_unique_bing") & audit["adj.P.Val"].lt(fdr_threshold)].copy()
    eligible["direction"] = np.where(eligible.logFC > 0, "up", np.where(eligible.logFC < 0, "down", "unchanged"))
    eligible = eligible[eligible.direction.isin(["up", "down"])].copy()
    eligible = eligible.sort_values(["adj.P.Val"], ascending=True)
    eligible["abs_logFC"] = eligible.logFC.abs()
    eligible = eligible.sort_values(["adj.P.Val", "abs_logFC", "gene_id"], ascending=[True, False, True]).drop_duplicates("lincs_gene_id")
    up_rows = eligible[eligible.direction == "up"].head(top_n)
    down_rows = eligible[eligible.direction == "down"].head(top_n)
    selected = set(up_rows.index) | set(down_rows.index)
    audit.loc[list(selected), "selected_for_query"] = True
    up = set(up_rows.lincs_gene_symbol.dropna().astype(str))
    down = set(down_rows.lincs_gene_symbol.dropna().astype(str))
    overlap = up & down
    if overlap:
        up -= overlap
        down -= overlap
        audit.loc[audit.lincs_gene_symbol.isin(overlap), "mapping_status"] = "conflicting_up_down_mapping_removed"
        audit.loc[audit.lincs_gene_symbol.isin(overlap), "selected_for_query"] = False
    audit["direction"] = np.where(audit.logFC > 0, "up", np.where(audit.logFC < 0, "down", "unchanged"))
    mapping_summary = {
        "s1_rows": int(len(audit)),
        "unique_bing_ids_mapped": int(audit.loc[audit.mapping_status == "mapped_unique_bing", "lincs_gene_id"].nunique()),
        "mapping_rate_all_s1": float(audit.mapping_status.eq("mapped_unique_bing").mean()) if len(audit) else 0.0,
        "ambiguous_rows": int(audit.mapping_status.eq("ambiguous_symbol_multiple_bing_ids").sum()),
        "unmatched_rows": int(audit.mapping_status.eq("not_found_in_lincs_bing").sum()),
        "up_query_genes": len(up),
        "down_query_genes": len(down),
        "up_selected_gene_ids": sorted(up_rows.lincs_gene_id.dropna().astype(str).tolist()),
        "down_selected_gene_ids": sorted(down_rows.lincs_gene_id.dropna().astype(str).tolist()),
    }
    return up, down, audit, mapping_summary


def _decode_ids(dataset) -> list[str]:
    values = dataset[:]
    return [value.decode("utf-8") if isinstance(value, bytes) else str(value) for value in values]


def screen_project(
    *,
    s1_path: Path,
    identifier_type: str,
    output_dir: Path,
    fdr_threshold: float = 0.05,
    top_n: int = 100,
    cell_id: str = "MCF7",
    perturbation_type: str = "trt_cp",
    time: str = "24 h",
    min_distil_cc_q75: float = 0.2,
    max_signatures: int | None = None,
    test_only: bool = False,
    project_id: str | None = None,
    s1_analysis_run_id: str | None = None,
    analysis_run_id: str | None = None,
) -> dict:
    if top_n < 1 or not 0 < fdr_threshold <= 1 or not 0 <= min_distil_cc_q75 <= 1:
        raise ValueError("top_n、FDR 阈值或质量阈值无效")
    gene_info_path = next(DATA.glob("*gene_info*.gz"))
    if analysis_run_id is None:
        run_token = uuid4().hex
        analysis_run_id = f"ANALYSIS_RUN:S2_LINCS:{run_token}"
    else:
        prefix = "ANALYSIS_RUN:S2_LINCS:"
        if not analysis_run_id.startswith(prefix):
            raise ValueError(f"analysis_run_id 必须以 {prefix} 开头")
        try:
            run_token = str(UUID(analysis_run_id[len(prefix):]))
        except ValueError as error:
            raise ValueError("analysis_run_id 后缀必须为 UUID") from error
        if analysis_run_id != f"{prefix}{run_token}":
            raise ValueError("analysis_run_id 中的 UUID 必须使用标准连字符格式")
    if project_id and not s1_analysis_run_id:
        raise ValueError("指定 project_id 时必须提供来源 S1 AnalysisRun ID")
    if project_id:
        UUID(project_id)
        result_dir = output_dir / run_token
    else:
        result_dir = output_dir
    up, down, mapping_audit, mapping_summary = map_and_select_s1(
        s1_path, gene_info_path, identifier_type, fdr_threshold=fdr_threshold, top_n=top_n
    )
    if not up or not down:
        result_dir.mkdir(parents=True, exist_ok=False)
        mapping_audit.to_csv(result_dir / "s1_gene_mapping_audit.csv", index=False)
        blocked = {
            "analysis_run_id": analysis_run_id,
            "project_id": project_id,
            "s1_analysis_run_id": s1_analysis_run_id,
            "s1_input_path": str(s1_path),
            "s1_input_sha256": sha256(s1_path),
            "status": "BLOCKED",
            "test_only": bool(test_only),
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "software_versions": {"python": sys.version.split()[0], "pandas": pd.__version__, "numpy": np.__version__, "h5py": h5py.__version__},
            "reason": "完成 S1→LINCS BING 映射审计后，至少一个方向没有可用于 WTCS 的基因；没有计算或伪造 S2 分数。",
            "parameters": {"identifier_type": identifier_type, "fdr_threshold": fdr_threshold, "top_n_per_direction": top_n},
            "mapping_summary": mapping_summary,
            "inputs": {str(path): {"bytes": path.stat().st_size, "sha256": sha256(path)} for path in [s1_path, gene_info_path]},
            "outputs": {"s1_gene_mapping_audit.csv": {"bytes": (result_dir / "s1_gene_mapping_audit.csv").stat().st_size, "sha256": sha256(result_dir / "s1_gene_mapping_audit.csv")}},
        }
        outpath = result_dir / "run_manifest.json"
        outpath.write_text(json.dumps(blocked, ensure_ascii=False, indent=2), encoding="utf-8")
        return blocked
    sig_info_path = next(DATA.glob("*sig_info*.gz"))
    sig_metrics_path = next(DATA.glob("*sig_metrics*.gz"))
    gctx_path = next(WORK.glob("*.gctx"))
    sig_info = pd.read_csv(sig_info_path, sep="\t", dtype={"sig_id": str, "pert_id": str}, low_memory=False)
    metrics = pd.read_csv(sig_metrics_path, sep="\t", dtype={"sig_id": str, "pert_id": str}, low_memory=False)
    if sig_info.sig_id.duplicated().any() or metrics.sig_id.duplicated().any():
        raise ValueError("LINCS sig_info 或 sig_metrics 中存在重复 sig_id，拒绝任意保留")
    if "distil_cc_q75" not in metrics.columns:
        raise ValueError("sig_metrics 缺少 distil_cc_q75 质量字段")
    meta = sig_info.merge(metrics, on="sig_id", how="left", suffixes=("", "_metric"), validate="one_to_one")
    for column in ("cell_id", "pert_type", "pert_itime", "pert_idose", "pert_iname"):
        if column not in meta.columns:
            raise ValueError(f"sig_info 缺少筛选字段 {column}")
    meta["distil_cc_q75"] = pd.to_numeric(meta.distil_cc_q75, errors="coerce").replace(-666, np.nan)
    meta["time_norm"] = meta.pert_itime.astype(str).str.strip().str.casefold()
    meta["cell_norm"] = meta.cell_id.astype(str).str.strip().str.casefold()
    meta["type_norm"] = meta.pert_type.astype(str).str.strip().str.casefold()
    time_norm = time.strip().casefold()
    all_mcf7_cp = meta[(meta.cell_norm == cell_id.casefold()) & (meta.type_norm == perturbation_type.casefold())]
    at_time = all_mcf7_cp[all_mcf7_cp.time_norm == time_norm]
    quality_pass = at_time[at_time.distil_cc_q75.ge(min_distil_cc_q75)].copy()
    quality_pass = quality_pass.sort_values(["pert_id", "pert_idose", "sig_id"], kind="stable")

    bing, id_to_symbol, _ = _read_bing_gene_info(gene_info_path)
    with h5py.File(gctx_path, "r") as handle:
        required_h5 = ["0/META/COL/id", "0/META/ROW/id", "0/DATA/0/matrix"]
        if any(path not in handle for path in required_h5):
            raise ValueError("GCTX 缺少预期的 Level 5 signature/gene/matrix 数据集")
        matrix = handle["0"]["DATA"]["0"]["matrix"]
        signature_ids = _decode_ids(handle["0"]["META"]["COL"]["id"])
        gene_ids = _decode_ids(handle["0"]["META"]["ROW"]["id"])
        if matrix.ndim != 2 or matrix.shape != (len(signature_ids), len(gene_ids)):
            raise ValueError(f"GCTX matrix 与 metadata 维度不一致：{matrix.shape}")
        signature_position = {sig_id: index for index, sig_id in enumerate(signature_ids)}
        id_positions = {gene_id: index for index, gene_id in enumerate(gene_ids)}
        gctx_bing_ids = [gene_id for gene_id in gene_ids if gene_id in id_to_symbol]
        gctx_gene_positions = np.asarray([id_positions[gene_id] for gene_id in gctx_bing_ids], dtype=np.int64)
        gctx_symbols = [id_to_symbol[gene_id] for gene_id in gctx_bing_ids]
        if len(set(gctx_symbols)) < 2:
            raise ValueError("GCTX 与 LINCS BING gene_info 的交集不足")
        quality_pass["in_gctx"] = quality_pass.sig_id.isin(signature_position)
        selected_meta = quality_pass[quality_pass.in_gctx].copy()
        if max_signatures is not None:
            if max_signatures < 1:
                raise ValueError("max_signatures 必须大于 0")
            selected_meta = selected_meta.head(max_signatures).copy()
        if selected_meta.empty:
            raise ValueError("MCF7、trt_cp、指定时间、质量阈值和 GCTX ID 交集为空")
        measured = set(gctx_symbols)
        effective_up, effective_down = up & measured, down & measured
        if not effective_up or not effective_down:
            raise ValueError("当前 GCTX 实际测量的 BING 背景没有覆盖 S1 上下调两组")
        records: list[dict] = []
        for index, (_, row) in enumerate(selected_meta.iterrows(), start=1):
            values = np.asarray(matrix[signature_position[row.sig_id], gctx_gene_positions], dtype=np.float64)
            valid = np.isfinite(values)
            score_frame = pd.DataFrame({"gene_symbol": np.asarray(gctx_symbols, dtype=object)[valid], "score": values[valid]})
            score_frame = score_frame.groupby("gene_symbol", as_index=False, sort=True).score.mean()
            weights = dict(zip(score_frame.gene_symbol.astype(str), score_frame.score.astype(float)))
            ranked = sorted(weights, key=lambda gene: (-weights[gene], gene))
            es_up, es_down, wtcs_value = wtcs(ranked, weights, effective_up, effective_down)
            records.append({
                "sig_id": row.sig_id,
                "pert_id": row.pert_id,
                "drug_name": row.pert_iname,
                "cell_id": row.cell_id,
                "pert_type": row.pert_type,
                "dose": row.pert_idose,
                "time": row.pert_itime,
                "distil_cc_q75": float(row.distil_cc_q75),
                "distil_ss": float(row.distil_ss) if "distil_ss" in row and pd.notna(row.distil_ss) else np.nan,
                "tas": float(row.tas) if "tas" in row and pd.notna(row.tas) else np.nan,
                "distil_nsample": float(row.distil_nsample) if "distil_nsample" in row and pd.notna(row.distil_nsample) else np.nan,
                "ES_UP": es_up,
                "ES_DOWN": es_down,
                "WTCS": wtcs_value,
                "reversal_score": -wtcs_value,
                "effective_bing_genes": len(weights),
                "up_query_genes": len(effective_up),
                "down_query_genes": len(effective_down),
                "up_coverage": len(effective_up) / max(len(up), 1),
                "down_coverage": len(effective_down) / max(len(down), 1),
            })
            if index % 500 == 0:
                print(f"已评分 {index}/{len(selected_meta)} 条 Signature", flush=True)
        scores = pd.DataFrame(records)
        if scores.WTCS.isna().any():
            raise ValueError("至少一条签名 WTCS 无法定义；拒绝静默生成正式结果")
        conditions = ["pert_id", "drug_name", "cell_id", "pert_type", "dose", "time"]
        summary = scores.groupby(conditions, dropna=False).agg(
            n_signatures=("sig_id", "size"),
            WTCS_median=("WTCS", "median"),
            WTCS_mean=("WTCS", "mean"),
            WTCS_sd=("WTCS", "std"),
            WTCS_mad=("WTCS", lambda values: float(np.median(np.abs(values - np.median(values))))),
            quality_cc_median=("distil_cc_q75", "median"),
            TAS_median=("tas", "median"),
            replicates_median=("distil_nsample", "median"),
        ).reset_index()
        summary["rank_within_condition"] = summary.groupby(["cell_id", "pert_type", "dose", "time"], dropna=False).WTCS_median.rank(method="average", ascending=True)
        qc = {
            "mcf7_trt_cp_signatures": int(len(all_mcf7_cp)),
            "requested_time_signatures": int(len(at_time)),
            "quality_pass_signatures": int(len(quality_pass)),
            "quality_pass_with_gctx_id": int(quality_pass.in_gctx.sum()),
            "scored_signatures": int(len(scores)),
            "scored_drugs": int(scores.pert_id.nunique()),
            "dose_time_condition_rows": int(len(summary)),
            "quality_missing_or_below_threshold": int(len(at_time) - len(quality_pass)),
            "quality_threshold": min_distil_cc_q75,
            "cell_id": cell_id,
            "pert_type": perturbation_type,
            "time": time,
            "dose_policy": "retain each dose stratum; never select a per-drug best dose",
            "aggregation_policy": "median WTCS across eligible signatures within exact pert_id/cell/type/dose/time; MAD retained",
            "rank_policy": "rank condition rows only within exact cell/type/dose/time",
            "s1_up_selected": len(up),
            "s1_down_selected": len(down),
            "s1_up_measured_in_gctx": len(effective_up),
            "s1_down_measured_in_gctx": len(effective_down),
        }

    result_dir.mkdir(parents=True, exist_ok=False)
    scores.to_csv(result_dir / "signature_scores.csv", index=False)
    summary.to_csv(result_dir / "drug_condition_summary.csv", index=False)
    mapping_audit.to_csv(result_dir / "s1_gene_mapping_audit.csv", index=False)
    (result_dir / "qc_summary.json").write_text(json.dumps(qc, ensure_ascii=False, indent=2), encoding="utf-8")
    source_paths = [s1_path, gene_info_path, sig_info_path, sig_metrics_path, gctx_path]
    manifest = {
        "analysis_run_id": analysis_run_id,
        "project_id": project_id,
        "s1_analysis_run_id": s1_analysis_run_id,
        "s1_input_path": str(s1_path),
        "s1_input_sha256": sha256(s1_path),
        "status": "completed",
        "test_only": bool(test_only),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "software_versions": {"python": sys.version.split()[0], "pandas": pd.__version__, "numpy": np.__version__, "h5py": h5py.__version__},
        "method": "CMap-style two-sided weighted KS/WTCS over BING genes; signature scores retain original WTCS and reversal_score=-WTCS",
        "parameters": {"identifier_type": identifier_type, "fdr_threshold": fdr_threshold, "top_n_per_direction": top_n, "cell_id": cell_id, "pert_type": perturbation_type, "time": time, "min_distil_cc_q75": min_distil_cc_q75, "max_signatures": max_signatures, "dose_policy": qc["dose_policy"], "aggregation_policy": qc["aggregation_policy"]},
        "mapping_summary": mapping_summary,
        "qc_summary": qc,
        "inputs": {str(path.relative_to(ROOT.parent) if path.is_relative_to(ROOT.parent) else path): {"bytes": path.stat().st_size, "sha256": sha256(path)} for path in source_paths},
        "outputs": {},
        "interpretation": "WTCS is an expression association score, not a treatment efficacy claim. Different doses and times are not pooled.",
    }
    for name in ("signature_scores.csv", "drug_condition_summary.csv", "s1_gene_mapping_audit.csv", "qc_summary.json"):
        path = result_dir / name
        manifest["outputs"][name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    manifest["result_directory"] = str(result_dir.resolve())
    (result_dir / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--s1-table", type=Path, required=True, help="Project-scoped canonical S1 table containing gene_id/logFC/adj.P.Val/t")
    parser.add_argument("--identifier-type", choices=["symbol", "entrez", "ensembl"], required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--project-id")
    parser.add_argument("--s1-analysis-run-id")
    parser.add_argument("--fdr-threshold", type=float, default=0.05)
    parser.add_argument("--top-n", type=int, default=100)
    parser.add_argument("--cell-id", default="MCF7")
    parser.add_argument("--perturbation-type", default="trt_cp")
    parser.add_argument("--time", default="24 h")
    parser.add_argument("--min-distil-cc-q75", type=float, default=0.2)
    parser.add_argument("--max-signatures", type=int)
    parser.add_argument("--test-only", action="store_true")
    parser.add_argument("--analysis-run-id", help="可选的预分配 S2 AnalysisRun ID")
    args = parser.parse_args()
    if args.output_dir is None:
        if not args.project_id:
            parser.error("未指定 project_id 时必须提供 --output-dir")
        args.output_dir = ROOT.parent / "data" / "processed" / "projects" / args.project_id / "s2"
    result = screen_project(
        s1_path=args.s1_table,
        identifier_type=args.identifier_type,
        output_dir=args.output_dir,
        fdr_threshold=args.fdr_threshold,
        top_n=args.top_n,
        cell_id=args.cell_id,
        perturbation_type=args.perturbation_type,
        time=args.time,
        min_distil_cc_q75=args.min_distil_cc_q75,
        max_signatures=args.max_signatures,
        test_only=args.test_only,
        project_id=args.project_id,
        s1_analysis_run_id=args.s1_analysis_run_id,
        analysis_run_id=args.analysis_run_id,
    )
    print(json.dumps({"status": result["status"], "analysis_run_id": result["analysis_run_id"], "project_id": result.get("project_id"), "test_only": result["test_only"], "qc_summary": result.get("qc_summary"), "mapping_summary": result.get("mapping_summary"), "output_dir": result.get("result_directory") or str(args.output_dir.resolve())}, ensure_ascii=False, indent=2))
    if result["status"] != "completed":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
