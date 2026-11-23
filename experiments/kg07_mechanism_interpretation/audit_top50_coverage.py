"""Report the real Top50 evidence-input coverage for KG07; never imply LLM runs."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "experiments" / "kg06_mechanism_evidence" / "results" / "evidence_packages_v2"
OUT = ROOT / "experiments" / "kg07_mechanism_interpretation"
INDEX = PKG / "top50_evidence_package_index.csv"
PACKAGE_MANIFEST = PKG / "top50_evidence_package_manifest.json"
PROJECT_ID = "3f18f4c1-713d-58c5-8a53-38eca5a5aaf9"
GRAPH_BUILD_ID = "GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:a08001496a447f7f"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def internal_package_sha256(package: dict) -> str:
    payload = {key: value for key, value in package.items() if key != "package_sha256"}
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    index_rows = list(csv.DictReader(INDEX.open(encoding="utf-8-sig", newline="")))
    package_manifest = json.loads(PACKAGE_MANIFEST.read_text(encoding="utf-8"))
    if package_manifest.get("status") != "PASS" or package_manifest.get("package_count") != 50 or package_manifest.get("failed_count") != 0:
        raise RuntimeError("Top50 EvidencePackage manifest is not a complete PASS")
    if package_manifest.get("index_sha256") != file_sha256(INDEX):
        raise RuntimeError("Top50 EvidencePackage index hash does not match package manifest")
    if len(index_rows) != 50:
        raise RuntimeError(f"expected 50 package index rows, found {len(index_rows)}")
    llm_manifest_path = OUT / "top50_llm" / "kg07_top50_llm_manifest.json"
    llm_manifest = json.loads(llm_manifest_path.read_text(encoding="utf-8")) if llm_manifest_path.is_file() else None
    llm_rows = {}
    if llm_manifest:
        llm_results_path = OUT / "top50_llm" / "kg07_top50_llm_results.csv"
        if not llm_results_path.is_file() or file_sha256(llm_results_path) != llm_manifest.get("results_csv_sha256"):
            raise RuntimeError("Top50 LLM results CSV is missing or its hash does not match the manifest")
        for llm_row in csv.DictReader(llm_results_path.open(encoding="utf-8-sig", newline="")):
            output_path = OUT / "top50_llm" / f"{llm_row['pert_id']}.json"
            if not output_path.is_file() or file_sha256(output_path) != llm_row.get("output_sha256"):
                raise RuntimeError(f"Top50 LLM output hash mismatch for {llm_row['pert_id']}")
            llm_rows[llm_row["pert_id"]] = llm_row
    rows = []
    for source in index_rows:
        package_path = ROOT / source["package_path"]
        actual_file_hash = file_sha256(package_path)
        if actual_file_hash != package_manifest.get("package_sha256", {}).get(source["pert_id"]):
            raise RuntimeError(f"package file hash mismatch for {source['pert_id']}")
        package = json.loads(package_path.read_text(encoding="utf-8"))
        if package.get("project_id") != PROJECT_ID or package.get("graph_build_id") != GRAPH_BUILD_ID or package.get("pert_id") != source["pert_id"]:
            raise RuntimeError(f"project/build/candidate mismatch for {source['pert_id']}")
        if package.get("package_sha256") != internal_package_sha256(package):
            raise RuntimeError(f"internal EvidencePackage hash mismatch for {source['pert_id']}")
        if package.get("provenance", {}).get("evidence_input_sha256") != source["evidence_input_sha256"]:
            raise RuntimeError(f"evidence input hash mismatch for {source['pert_id']}")
        paths = package.get("paths", [])
        path_evidence = {eid for path in paths for eid in path.get("evidence_ids", [])}
        verified_path_evidence = {src["evidence_id"] for path in paths for edge in path.get("edges", []) for src in edge.get("sources", []) if src.get("verified_in_postgres") and src.get("evidence_id")}
        s2_conditions = package.get("screening_evidence", {}).get("s2_conditions", [])
        s2_evidence = {eid for condition in s2_conditions for eid in condition.get("evidence_ids", [])}
        all_paths_complete = bool(paths) and all(path.get("evidence_complete") for path in paths)
        rows.append({
            "exp006_rank": source["rank_exp006"],
            "pert_id": source["pert_id"],
            "drug_name": source["drug_name"],
            "evidence_input_sha256": source["evidence_input_sha256"],
            "package_file_sha256": actual_file_hash,
            "internal_package_sha256_valid": True,
            "exact_compound_mapping": source["candidate_mapping_status"] == "matched_exact_inchikey",
            "path_count": len(paths),
            "direct_target_path_count": sum(path.get("route_type") == "direct_target" for path in paths),
            "public_pathway_path_count": sum(path.get("route_type") == "public_pathway" for path in paths),
            "s1_enrichment_path_count": sum(path.get("route_type") == "s1_enrichment_overlap" for path in paths),
            "s1_deg_overlap_path_count": sum(path.get("route_type") == "s1_deg_overlap" for path in paths),
            "path_evidence_id_count": len(path_evidence),
            "postgres_verified_path_evidence_id_count": len(verified_path_evidence),
            "s2_condition_count": len(s2_conditions),
            "s2_condition_evidence_id_count": len(s2_evidence),
            "all_path_evidence_complete": all_paths_complete,
            "evidence_gaps": " | ".join(package.get("evidence_gaps", [])),
            "llm_interpretation_status": (
                "not_generated_external_authorization_pending" if source["pert_id"] not in llm_rows else
                "generated_reference_ids_pass_semantics_review_required" if llm_rows[source["pert_id"]].get("citation_reference_validation_pass", "").lower() == "true" else
                "generated_reference_validation_failed_or_issues_present"
            ),
        })
    csv_path = OUT / "kg07_top50_explanation_coverage.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    n = len(rows)
    with_paths = sum(row["path_count"] > 0 for row in rows)
    complete_paths = sum(row["all_path_evidence_complete"] for row in rows)
    mapped = sum(row["exact_compound_mapping"] for row in rows)
    s2 = sum(row["s2_condition_count"] > 0 for row in rows)
    llm_generated = sum(row.get("status") == "generated" for row in llm_rows.values())
    llm_reference_pass = sum(row.get("citation_reference_validation_pass", "").lower() == "true" for row in llm_rows.values())
    report = f"""# KG07 Top50 解释输入覆盖审计

审计范围：当前正式 GraphBuild 下、Exp006 Top50 的 50 个 KG06 EvidencePackage。报告统计的是解释输入可用性，不代表模型解释已生成或机制结论正确。

## 真实覆盖

- EvidencePackage：{n}/{n}。
- EvidencePackage 文件哈希、内部 package 哈希、项目/GraphBuild/候选 ID 与 evidence input hash：{sum(row['internal_package_sha256_valid'] for row in rows)}/{n} 全部核对通过。
- 精确 InChIKey 化合物映射：{mapped}/{n}。
- 至少一条真实路径（直接靶点、公共通路或 S1 交汇）：{with_paths}/{n}。
- 至少一条路径且路径证据在 PostgreSQL 可验证：{complete_paths}/{n}。
- S2 条件及其 Evidence ID：{s2}/{n} 有条件记录；逐例数量见 CSV。
- 当前 KG+LLM 解释：{llm_generated}/{n}；以逐候选输出文件及 manifest hash 核验后的结果计数，不把未生成或失败案例算作覆盖。其间 {llm_reference_pass}/{n} 个候选的保留声明通过引用 ID 核验，语义仍需人工审核。

## 边界

没有路径的候选保留为证据不足；没有精确化合物映射的候选不补造映射。Evidence ID 可验证只证明该 ID 属于本项目 GraphBuild 的证据记录，不证明它语义上支持某个具体句子。路径也不构成因果或临床疗效证据。

## 复现

- 输入索引 SHA-256：`{hashlib.sha256(INDEX.read_bytes()).hexdigest()}`。
- 逐候选明细：`kg07_top50_explanation_coverage.csv`。
- LLM 调用状态：`{llm_manifest.get('status', 'NOT RUN') if llm_manifest else 'NOT RUN'}`；模型输出数量为 {llm_generated}/{n}，实际未缓存 API 调用 {llm_manifest.get('n_uncached_calls', 0) if llm_manifest else 0} 次。费用以服务方回传为准；未回传的项目记为未报告。
"""
    (OUT / "kg07_top50_explanation_coverage_report.md").write_text(report, encoding="utf-8")
    llm_status = "EVIDENCE_INPUT_AUDITED_LLM_NOT_RUN" if llm_manifest is None else ("LLM_TOP50_GENERATED_PENDING_HUMAN_REVIEW" if llm_generated == n else "LLM_TOP50_PARTIAL")
    manifest = {"status": llm_status, "n_candidates": n, "n_package_hashes_validated": sum(row["internal_package_sha256_valid"] for row in rows), "n_with_paths": with_paths, "n_with_complete_path_evidence": complete_paths, "n_exact_compound_mapped": mapped, "n_llm_interpretations_generated": llm_generated, "llm_manifest_sha256": file_sha256(llm_manifest_path) if llm_manifest else None, "package_manifest_sha256": file_sha256(PACKAGE_MANIFEST), "input_index_sha256": file_sha256(INDEX), "output_sha256": file_sha256(csv_path)}
    (OUT / "kg07_top50_explanation_coverage_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
