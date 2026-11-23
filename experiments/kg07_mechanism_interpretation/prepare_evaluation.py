"""Prepare a stratified 20-candidate KG07 evaluation set without external calls."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app.kg07 import rule_template  # noqa: E402

RESULTS = ROOT / "experiments" / "kg06_mechanism_evidence" / "results" / "evidence_packages_v2"
OUT = ROOT / "experiments" / "kg07_mechanism_interpretation"
INDEX = RESULTS / "top50_evidence_package_index.csv"


def main() -> None:
    records = list(csv.DictReader(INDEX.open(encoding="utf-8-sig", newline="")))
    strata: dict[tuple[bool, bool, bool, bool], list[dict[str, str]]] = defaultdict(list)
    for row in records:
        key = (
            row["candidate_mapping_status"] == "matched_exact_inchikey",
            int(row["direct_target_path_count"]) > 0,
            int(row["public_pathway_path_count"]) > 0,
            int(row["s1_enrichment_overlap_path_count"]) > 0,
        )
        strata[key].append(row)
    # Five cases per observed coverage stratum, preserving original Exp006 rank order.
    selected = []
    for key in sorted(strata, key=lambda value: (not any(value), value)):
        if len(selected) >= 20:
            break
        selected.extend((key, row) for row in strata[key][: min(5, 20 - len(selected))])
    if len(selected) < 20:
        used = {row["pert_id"] for _, row in selected}
        selected.extend((None, row) for row in records if row["pert_id"] not in used)
        selected = selected[:20]

    OUT.mkdir(parents=True, exist_ok=True)
    rule_dir = OUT / "rule_templates"
    rule_dir.mkdir(exist_ok=True)
    evaluation_rows = []
    file_hashes = {}
    for index, (stratum, row) in enumerate(selected, 1):
        package_path = ROOT / row["package_path"]
        package = json.loads(package_path.read_text(encoding="utf-8"))
        rule = rule_template(package)
        rule_path = rule_dir / f"{row['pert_id']}.json"
        rule_path.write_text(json.dumps(rule, ensure_ascii=False, indent=2), encoding="utf-8")
        file_hashes[str(rule_path.relative_to(ROOT)).replace("\\", "/")] = hashlib.sha256(rule_path.read_bytes()).hexdigest()
        evaluation_rows.append({
            "case": index,
            "exp006_rank": row["rank_exp006"],
            "pert_id": row["pert_id"],
            "drug_name": row["drug_name"],
            "coverage_stratum": "|".join("yes" if value else "no" for value in stratum) if stratum else "supplemental",
            "candidate_mapping_status": row["candidate_mapping_status"],
            "direct_target_paths": row["direct_target_path_count"],
            "public_pathway_paths": row["public_pathway_path_count"],
            "s1_enrichment_paths": row["s1_enrichment_overlap_path_count"],
            "verified_evidence_count": row["verified_evidence_count"],
            "evidence_input_sha256": row["evidence_input_sha256"],
            "direct_llm_status": "pending_external_data_authorization",
            "direct_llm_latency_seconds": "",
            "direct_llm_cost": "",
            "kg_rule_status": "generated",
            "kg_rule_output": str(rule_path.relative_to(ROOT)).replace("\\", "/"),
            "kg_llm_status": "pending_external_data_authorization",
            "kg_llm_latency_seconds": "",
            "kg_llm_cost": "",
            "human_review_blinded": "",
            "supported_claim_fraction": "",
            "citation_precision": "",
            "unsupported_assertion_count": "",
            "relation_direction_error_count": "",
            "uncertainty_accuracy": "",
            "review_notes": "",
        })

    csv_path = OUT / "kg07_evaluation_20_cases.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(evaluation_rows[0]))
        writer.writeheader()
        writer.writerows(evaluation_rows)
    manifest = {
        "status": "PREPARED_EXTERNAL_LLM_PENDING_AUTHORIZATION",
        "n_cases": len(evaluation_rows),
        "sampling": "Top50 Exp006 sorted rank; five per available coverage stratum (exact compound mapping, direct target, public pathway, S1 enrichment overlap); rule templates are locally generated from verified KG06 packages.",
        "methods": ["direct_llm pending", "kg_rule generated", "kg_llm pending"],
        "human_review_required": True,
        "evidence_package_index_sha256": hashlib.sha256(INDEX.read_bytes()).hexdigest(),
        "outputs": {"kg07_evaluation_20_cases.csv": hashlib.sha256(csv_path.read_bytes()).hexdigest(), **file_hashes},
    }
    (OUT / "kg07_evaluation_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    report = [
        "# KG07 解释质量对照实验（本地准备阶段）",
        "",
        f"- 候选案例：{len(evaluation_rows)} 个，来自真实 Top50 KG06 EvidencePackage。",
        "- 抽样：按化合物映射、直接靶点、公共通路、S1 富集路径覆盖分层；不根据模型输出挑样。",
        "- KG 规则模板：已由真实证据包生成并保留输入哈希。",
        "- Direct LLM 与 KG + LLM：尚未调用，等待用户明确授权将研究证据发送到智谱 API。",
        "- 人工审核：表格已留出盲审结果和审阅备注字段；空值不是零分。",
        "- 当前没有声称解释正确率或生物学正确性。程序引用校验仅检查 ID 是否属于当前 EvidencePackage。",
        "",
        "完整逐例字段见 `kg07_evaluation_20_cases.csv`；规则模板见 `rule_templates/`。",
    ]
    (OUT / "kg07_evaluation_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "n_cases": len(evaluation_rows), "rule_templates": len(file_hashes), "strata": {"|".join("yes" if value else "no" for value in key): len(value) for key, value in strata.items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
