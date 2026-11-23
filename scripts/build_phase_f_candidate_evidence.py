"""Append GraphBundle evidence to the Exp006–Exp011 matrix by stable LINCS ID."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
csv.field_size_limit(min(sys.maxsize, 2_147_483_647))
PROJECT_ID = "3f18f4c1-713d-58c5-8a53-38eca5a5aaf9"
BUNDLE_RUN_ID = "ANALYSIS_RUN:KG_GRAPH_BUNDLE:8eda9601-2fd3-48cc-9a45-74809870a480"
GRAPH_BUILD_ID = f"GRAPH_BUILD:{PROJECT_ID}:a6aabb2147cb5f5e"
MATRIX = ROOT / "experiments/second_round_summary/results/candidate_evidence_integrated.csv"
FORMAL_CONDITION_RANKING = ROOT / "s2_lincs/results/formal_drug_condition_ranking.csv"
SECOND_ROUND_MANIFEST = ROOT / "experiments/second_round_summary/results/second_round_manifest.json"
BUNDLE_DIR = ROOT / f"data/processed/projects/{PROJECT_ID}/graph_bundle/runs/8eda9601-2fd3-48cc-9a45-74809870a480"
OUTPUT_DIR = ROOT / "experiments/phase_f_integrated_evidence"
OUTPUT_CSV = OUTPUT_DIR / "candidate_evidence_with_kg.csv"
OUTPUT_JSON = OUTPUT_DIR / "phase_f_manifest.json"
OUTPUT_MD = OUTPUT_DIR / "phase_f_report.md"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, records: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    second_manifest = json.loads(SECOND_ROUND_MANIFEST.read_text(encoding="utf-8"))
    expected_matrix_hash = second_manifest["outputs"]["candidate_evidence_integrated.csv"]
    if sha256(MATRIX) != expected_matrix_hash:
        raise ValueError("综合证据矩阵 SHA-256 与第二轮实验 manifest 不一致")

    bundle_manifest_path = BUNDLE_DIR / "bundle_manifest.json"
    bundle_manifest = json.loads(bundle_manifest_path.read_text(encoding="utf-8"))
    if bundle_manifest.get("status") != "validated" or bundle_manifest.get("analysis_run_id") != BUNDLE_RUN_ID:
        raise ValueError("GraphBundle 未通过验证或 AnalysisRun ID 不匹配")
    for filename, expected_hash in bundle_manifest["output_hashes"].items():
        if sha256(BUNDLE_DIR / filename) != expected_hash:
            raise ValueError(f"GraphBundle 输出哈希不匹配：{filename}")

    project_s2_summary = ROOT / f"data/processed/projects/{PROJECT_ID}/s2/c922f2b0-242e-5991-9f76-dcbc8f66ce57/drug_condition_summary.csv"
    project_s2_key = project_s2_summary.relative_to(ROOT).as_posix()
    expected_s2_hash = bundle_manifest["input_hashes"].get(project_s2_key)
    if not expected_s2_hash or sha256(project_s2_summary) != expected_s2_hash:
        raise ValueError("项目 S2 条件表未在 GraphBundle 输入清单中登记或哈希不匹配")
    project_s2_rows = rows(project_s2_summary)
    formal_b_rows = rows(FORMAL_CONDITION_RANKING)
    formal_b = {
        (row["pert_id"], row["cell_id"], row["pert_type"], row["dose"], row["time"]): row
        for row in formal_b_rows if row["scheme"] == "B"
    }
    comparison_fields = [
        ("n_signatures", "n_signatures"), ("WTCS_median", "WTCS_median"), ("WTCS_mean", "WTCS_mean"),
        ("WTCS_sd", "WTCS_sd"), ("WTCS_mad", "WTCS_mad"), ("quality_cc_median", "quality_cc_median"),
        ("TAS_median", "TAS_median"), ("replicates_median", "replicates_median"),
        ("rank_within_condition", "rank_condition"),
    ]
    matched_formal = 0
    for item in project_s2_rows:
        key = tuple(item[name] for name in ("pert_id", "cell_id", "pert_type", "dose", "time"))
        original = formal_b.get(key)
        if original is None:
            raise ValueError(f"项目 S2 条件在正式 scheme B 汇总中未找到：{key}")
        matched_formal += 1
        for actual_name, source_name in comparison_fields:
            actual, source = item[actual_name], original[source_name]
            if actual == source or (actual == "" and source == ""):
                continue
            try:
                equal = abs(float(actual) - float(source)) <= 1e-12 * max(1.0, abs(float(source)))
            except ValueError:
                equal = False
            if not equal:
                raise ValueError(f"项目 S2 与正式 scheme B 的 {actual_name} 不一致：{key}: {actual} != {source}")
    project_s2_by_pert: dict[str, list[dict[str, str]]] = defaultdict(list)
    for item in project_s2_rows:
        project_s2_by_pert[item["pert_id"]].append(item)

    matrix_rows = rows(MATRIX)
    pert_ids = [row.get("pert_id", "").strip() for row in matrix_rows]
    if not pert_ids or any(not pert_id for pert_id in pert_ids) or len(set(pert_ids)) != len(pert_ids):
        raise ValueError("综合证据矩阵 perturbagen ID 缺失或重复")

    mapping = {row["pert_id"]: row for row in rows(BUNDLE_DIR / "candidate_mapping_audit.csv")}
    route_rows = rows(BUNDLE_DIR / "candidate_target_pathway_routes.csv")
    routes_by_pert: dict[str, list[dict[str, str]]] = defaultdict(list)
    for route in route_rows:
        routes_by_pert[route["pert_id"]].append(route)

    evidence_rows = rows(BUNDLE_DIR / "evidence_records.csv")
    target_evidence: dict[tuple[str, str], set[str]] = defaultdict(set)
    pathway_gene_evidence: dict[tuple[str, str], set[str]] = defaultdict(set)
    for record in evidence_rows:
        if record["source_release"] == "OptimusKG 3.2":
            target_evidence[(record["subject_id"], record["object_id"])].add(record["evidence_id"])
        if record["predicate"] == "HAS_ENRICHED_GENE":
            pathway_gene_evidence[(record["subject_id"], record["object_id"])].add(record["evidence_id"])

    output_fields = list(matrix_rows[0]) + [
        "kg_graph_build_id", "kg_candidate_seeded", "kg_mapping_status", "kg_mapping_method",
        "kg_graph_drug_id", "kg_supported_route_count", "kg_unique_target_gene_count",
        "kg_unique_pathway_count", "kg_target_gene_ids", "kg_pathway_ids",
        "kg_supporting_evidence_ids", "kg_interpretation",
        "project_s2_condition_count", "project_s2_distinct_doses", "project_s2_condition_data_json",
    ]
    output: list[dict[str, str]] = []
    unmatched_seed: list[str] = []
    exact_mapped_seed_without_routes: list[str] = []
    mapped_with_routes: set[str] = set()
    route_target_evidence_missing = 0
    route_pathway_evidence_missing = 0
    for source in matrix_rows:
        pert_id = source["pert_id"].strip()
        mapping_row = mapping.get(pert_id)
        selected_routes = routes_by_pert.get(pert_id, [])
        selected_conditions = sorted(project_s2_by_pert.get(pert_id, []), key=lambda row: (row["time"], row["cell_id"], row["pert_type"], row["dose"]))
        target_ids = sorted({row["target_gene_id"] for row in selected_routes})
        pathway_ids = sorted({row["pathway_id"] for row in selected_routes})
        supporting_ids: set[str] = set()
        for route in selected_routes:
            target_ids_for_route = target_evidence.get((route["drug_id"], route["target_gene_id"]), set())
            pathway_ids_for_route = pathway_gene_evidence.get((route["pathway_id"], route["target_gene_id"]), set())
            route_target_evidence_missing += not bool(target_ids_for_route)
            route_pathway_evidence_missing += not bool(pathway_ids_for_route)
            supporting_ids.update(target_ids_for_route)
            supporting_ids.update(pathway_ids_for_route)

        if mapping_row is None:
            mapping_status = "not_seeded_into_this_graph_build"
            interpretation = "未进入 Exp006 Top50 图谱种子；本轮未评估公共知识图谱路径"
        elif mapping_row["mapping_status"] != "matched_exact_inchikey":
            mapping_status = mapping_row["mapping_status"]
            interpretation = "候选已进入图谱种子，但没有精确 InChIKey 公共药物映射"
            unmatched_seed.append(pert_id)
        elif not selected_routes:
            mapping_status = "matched_exact_inchikey_no_supported_path"
            interpretation = "化合物精确映射成功，但当前受限子图中无支持的靶点—通路交汇路径"
            exact_mapped_seed_without_routes.append(pert_id)
        else:
            mapping_status = "matched_exact_inchikey_with_supported_path"
            interpretation = "精确结构映射且存在来源支持的靶点—S1 通路基因交汇；不是因果或疗效证据"
            mapped_with_routes.add(pert_id)
        output.append({
            **source,
            "kg_graph_build_id": GRAPH_BUILD_ID,
            "kg_candidate_seeded": str(mapping_row is not None).lower(),
            "kg_mapping_status": mapping_status,
            "kg_mapping_method": mapping_row.get("mapping_method", "") if mapping_row else "",
            "kg_graph_drug_id": mapping_row.get("graph_drug_id", "") if mapping_row else "",
            "kg_supported_route_count": str(len(selected_routes)),
            "kg_unique_target_gene_count": str(len(target_ids)),
            "kg_unique_pathway_count": str(len(pathway_ids)),
            "kg_target_gene_ids": ";".join(target_ids),
            "kg_pathway_ids": ";".join(pathway_ids),
            "kg_supporting_evidence_ids": ";".join(sorted(supporting_ids)),
            "kg_interpretation": interpretation,
            "project_s2_condition_count": str(len(selected_conditions)),
            "project_s2_distinct_doses": ";".join(sorted({row["dose"] for row in selected_conditions})),
            "project_s2_condition_data_json": json.dumps(selected_conditions, ensure_ascii=False, separators=(",", ":")),
        })

    if len(output) != len(matrix_rows) or len({row["pert_id"] for row in output}) != len(output):
        raise AssertionError("整合结果行数或 perturbagen 唯一性校验失败")
    if route_target_evidence_missing or route_pathway_evidence_missing:
        raise AssertionError(f"有路径缺少来源证据：target={route_target_evidence_missing}, pathway_gene={route_pathway_evidence_missing}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT_CSV, output, output_fields)
    generated_at = datetime.now(timezone.utc).isoformat()
    counts = {
        "integrated_candidates": len(output),
        "graph_seed_candidates": len(mapping),
        "graph_seed_exact_inchikey_matches": sum(r["mapping_status"] == "matched_exact_inchikey" for r in mapping.values()),
        "graph_candidates_with_supported_routes": len(mapped_with_routes),
        "graph_seed_unmatched_compounds": len(unmatched_seed),
        "exactly_mapped_seeds_without_routes": len(exact_mapped_seed_without_routes),
        "supported_routes": len(route_rows),
        "routes_with_target_and_pathway_evidence": len(route_rows) - route_target_evidence_missing - route_pathway_evidence_missing,
        "unique_linked_evidence_records": len({evidence_id for row in output for evidence_id in row["kg_supporting_evidence_ids"].split(";") if evidence_id}),
        "project_s2_conditions": len(project_s2_rows),
        "project_s2_rows_exactly_matching_historical_scheme_b": matched_formal,
        "project_s2_candidates_with_conditions": len(project_s2_by_pert),
        "project_s2_exact_zero_wtcs_conditions_preserved": sum(float(row["WTCS_median"]) == 0.0 for row in project_s2_rows),
    }
    manifest = {
        "status": "PASS",
        "generated_at_utc": generated_at,
        "project_id": PROJECT_ID,
        "graph_build_id": GRAPH_BUILD_ID,
        "analysis_run_ids": {
            "exp006_exp011_matrix": "experiments/second_round_summary/results/candidate_evidence_integrated.csv",
            "graph_bundle": BUNDLE_RUN_ID,
            "s1": bundle_manifest["s1_analysis_run_id"],
            "s2": bundle_manifest["s2_analysis_run_id"],
            "enrichment": bundle_manifest["enrichment_analysis_run_id"],
        },
        "join_policy": "Exact LINCS pert_id; graph compound mappings only accepted from audited exact InChIKey; no display-name joins.",
        "interpretation_policy": "No combined efficacy score or weighted rank is computed. Missing graph seed coverage is distinguished from failed compound mapping.",
        "counts": counts,
        "input_sha256": {
            MATRIX.relative_to(ROOT).as_posix(): sha256(MATRIX),
            FORMAL_CONDITION_RANKING.relative_to(ROOT).as_posix(): sha256(FORMAL_CONDITION_RANKING),
            project_s2_key: sha256(project_s2_summary),
            SECOND_ROUND_MANIFEST.relative_to(ROOT).as_posix(): sha256(SECOND_ROUND_MANIFEST),
            bundle_manifest_path.relative_to(ROOT).as_posix(): sha256(bundle_manifest_path),
            **{(BUNDLE_DIR / filename).relative_to(ROOT).as_posix(): sha256(BUNDLE_DIR / filename) for filename in bundle_manifest["output_hashes"]},
        },
        "output_sha256": {OUTPUT_CSV.relative_to(ROOT).as_posix(): sha256(OUTPUT_CSV)},
    }
    report = [
        "# Phase F：Exp006–Exp011 与项目 GraphBuild 候选证据整合", "",
        f"生成时间（UTC）：{generated_at}", "",
        "## 整合规则", "",
        "以 LINCS perturbagen ID 精确联结第二轮综合证据矩阵与项目 GraphBundle。化合物只接受已审计的精确 InChIKey 映射；名称仅作展示，不参与匹配。当前图谱种子来自 Exp006 Top50，因此未进入该种子的候选标为‘未评估图谱’，不能误作映射失败。", "",
        "不将 S2 WTCS、Exp007–010 稳定性/外部 S1 和 Exp011 PRISM 合成加权分数，也不据此生成疗效 Top10。图谱交汇数只表示在所用 OptimusKG 版本和 S1 通路数据中存在可溯源关系。", "",
        "## 实际整合计数", "",
        f"- 第二轮候选行：{counts['integrated_candidates']:,}；LINCS perturbagen ID 唯一性校验通过。",
        f"- 纳入图谱候选种子：{counts['graph_seed_candidates']}；其中精确 InChIKey 映射 {counts['graph_seed_exact_inchikey_matches']}。",
        f"- 有支持路径的精确映射候选：{counts['graph_candidates_with_supported_routes']}；未映射种子 {counts['graph_seed_unmatched_compounds']}；映射成功但无交汇路径 {counts['exactly_mapped_seeds_without_routes']}。",
        f"- 候选—靶点—S1 通路交汇行：{counts['supported_routes']:,}。每行候选保留关联靶点、稳定通路 ID 和对应来源 evidence ID。", "",
        f"- 项目级 S2 剂量条件：{counts['project_s2_conditions']} 行，全部与历史正式 scheme B 条件表逐条件匹配；覆盖 {counts['project_s2_candidates_with_conditions']} 个 perturbagen。WTCS 恰为 0 的 {counts['project_s2_exact_zero_wtcs_conditions_preserved']} 行按原始数据保留，不做改写或插补。", "",
        "## 解释限制", "",
        "公共知识图谱路径是数据库来源断言与本项目差异表达/富集结果的交汇，不证明直接因果、药物作用方向、ER 阳性特异性或疗效。PRISM 是体外细胞存活终点，与 LINCS 表达逆转不是同一实验结果。Exp008 仍为 PARTIAL，保持原方法学限制。", "",
        "## 可复现文件", "",
        f"- 整合矩阵：`{OUTPUT_CSV.relative_to(ROOT).as_posix()}`",
        f"- 输入/输出哈希与运行清单：`{OUTPUT_JSON.relative_to(ROOT).as_posix()}`",
        "- 构建代码：`scripts/build_phase_f_candidate_evidence.py`", "",
    ]
    OUTPUT_MD.write_text("\n".join(report), encoding="utf-8")
    manifest["output_sha256"][OUTPUT_MD.relative_to(ROOT).as_posix()] = sha256(OUTPUT_MD)
    OUTPUT_JSON.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "counts": counts, "output": OUTPUT_CSV.relative_to(ROOT).as_posix()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
