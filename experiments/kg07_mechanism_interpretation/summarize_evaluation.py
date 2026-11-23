"""Summarize real KG07 model runs and prepare a blinded human-review worksheet."""
from __future__ import annotations

import csv
import hashlib
import json
import random
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app.kg07 import _compact_package

OUT = ROOT / "experiments" / "kg07_mechanism_interpretation"
EVAL = OUT / "evaluation"
PACKAGES = ROOT / "experiments" / "kg06_mechanism_evidence" / "results" / "evidence_packages_v2"
CASE_CSV = OUT / "kg07_evaluation_20_cases.csv"
CLAIM_SECTIONS = ("screening_basis", "known_targets", "associated_pathways", "independent_validation", "mechanism_hypotheses", "insufficient_evidence")
REVIEW_FIELDS = ("supported_claim_fraction", "citation_precision", "unsupported_assertion_count", "relation_direction_error_count", "uncertainty_accuracy", "review_notes")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def claims_from(output: dict) -> list[dict]:
    claims = []
    explanation = output.get("explanation", {})
    for section in CLAIM_SECTIONS:
        for claim in explanation.get(section, []):
            if isinstance(claim, dict) and isinstance(claim.get("text"), str):
                claims.append({"section": section, **claim})
    return claims


def reviewer_claims(output: dict) -> list[dict]:
    return [
        {key: claim.get(key) for key in ("section", "text", "evidence_ids", "path_ids", "relation") if key in claim}
        for claim in claims_from(output)
    ]


def citation_snapshots(package: dict, evidence_ids: list[str], path_ids: list[str]) -> tuple[list[dict], bool]:
    paths = package.get("paths", [])
    path_by_id = {str(path.get("path_id")): path for path in paths}
    snapshots: list[dict] = []
    found_all = True
    for path_id in path_ids:
        path = path_by_id.get(str(path_id))
        if path is None:
            found_all = False
            snapshots.append({"reference_type": "path", "reference_id": path_id, "found_in_package": False})
            continue
        snapshots.append({
            "reference_type": "path", "reference_id": path_id, "found_in_package": True,
            "route_type": path.get("route_type"), "target_gene_id": path.get("target_gene_id"),
            "pathway_id": path.get("pathway_id"), "pathway_label": path.get("pathway_label"),
            "relation_types": path.get("relation_types"), "reported_actions": path.get("reported_actions"),
            "relation_conflict": path.get("relation_conflict"), "evidence_complete": path.get("evidence_complete"),
            "disease_expression_assertions": path.get("disease_expression_assertions"),
            "pathway_adjusted_p_values": path.get("pathway_adjusted_p_values"),
            "edges": [{key: edge.get(key) for key in ("edge_id", "source_id", "target_id", "relation_type", "source_release", "source_record_id", "source_assertion", "analysis_assertions", "reported_actions", "action_interpretation", "relation_conflict", "evidence_ids", "sources")} for edge in path.get("edges", [])],
        })
    for evidence_id in evidence_ids:
        matches = []
        for path in paths:
            if str(evidence_id) in {str(value) for value in path.get("evidence_ids", [])}:
                matches.append({"reference_type": "path_evidence", "path_id": path.get("path_id"), "route_type": path.get("route_type"), "target_gene_id": path.get("target_gene_id"), "pathway_id": path.get("pathway_id"), "pathway_label": path.get("pathway_label"), "evidence_id": evidence_id})
            for edge in path.get("edges", []):
                for source in edge.get("sources", []):
                    if str(source.get("evidence_id")) == str(evidence_id):
                        matches.append({"reference_type": "edge_source", "path_id": path.get("path_id"), "edge_id": edge.get("edge_id"), "relation_type": edge.get("relation_type"), "source_assertion": edge.get("source_assertion"), "analysis_assertions": edge.get("analysis_assertions"), "reported_actions": edge.get("reported_actions"), "action_interpretation": edge.get("action_interpretation"), "source": source})
        for condition in package.get("screening_evidence", {}).get("s2_conditions", []):
            if str(evidence_id) in {str(value) for value in condition.get("evidence_ids", [])}:
                condition_props = condition.get("condition", {})
                matches.append({"reference_type": "s2_condition", "condition_key": condition.get("condition_key"), "condition": {key: condition_props.get(key) for key in ("cell_id", "pert_type", "dose", "time", "WTCS_median", "WTCS_mean", "n_signatures", "quality_cc_median", "TAS_median")}, "evidence_id": evidence_id, "sources": [source for source in condition.get("sources", []) if str(source.get("evidence_id")) == str(evidence_id)]})
        if not matches:
            found_all = False
        snapshots.extend(matches)
    return snapshots, found_all


def retained_reference_integrity(output: dict, package: dict, mode: str) -> tuple[int, int]:
    compact, allowed_evidence, allowed_paths = _compact_package(package)
    valid = total = 0
    for claim in claims_from(output):
        if claim.get("citation_reference_status") == "verified_coverage_gap_from_EvidencePackage":
            continue
        evidence_ids = [str(value) for value in claim.get("evidence_ids", [])]
        path_ids = [str(value) for value in claim.get("path_ids", [])]
        if not evidence_ids and not path_ids:
            if mode == "kg_rule" and claim.get("section") == "insufficient_evidence":
                continue
            continue
        total += 1
        if set(evidence_ids) <= allowed_evidence and set(path_ids) <= allowed_paths:
            valid += 1
    return valid, total


def main() -> None:
    run_manifest_path = EVAL / "kg07_evaluation_manifest.json"
    run_csv_path = EVAL / "kg07_evaluation_cases.csv"
    run_manifest = read_json(run_manifest_path)
    run_rows = list(csv.DictReader(run_csv_path.open(encoding="utf-8-sig", newline="")))
    if len(run_rows) != 20 or run_manifest.get("n_errors") != 0:
        raise SystemExit("The real 20-case run is incomplete or has API/runtime errors; do not summarize it as complete.")

    case_rows = list(csv.DictReader(CASE_CSV.open(encoding="utf-8-sig", newline="")))
    case_by_id = {row["pert_id"]: row for row in case_rows}
    method_names = ("direct_llm", "kg_rule", "kg_llm")
    review_path = OUT / "kg07_human_review_20_cases.csv"
    key_path = OUT / "kg07_human_review_blinding_key.csv"
    if review_path.is_file():
        existing_review = list(csv.DictReader(review_path.open(encoding="utf-8-sig", newline="")))
        if any((row.get(field) or "").strip() for row in existing_review for field in (*REVIEW_FIELDS, "reviewer", "review_date")):
            raise SystemExit("Refusing to overwrite a partially or fully completed human-review sheet.")
    existing_code_map = {}
    if key_path.is_file():
        for key_row in csv.DictReader(key_path.open(encoding="utf-8-sig", newline="")):
            existing_code_map.setdefault(key_row["case"], {})[key_row["method"]] = key_row["review_code"]
        if len(existing_code_map) != 20 or any(set(value) != set(method_names) for value in existing_code_map.values()):
            raise SystemExit("Existing blind-review key is incomplete; refusing to replace it.")
    summary = {mode: {"latencies": [], "claims": 0, "issues": {}, "references_valid": 0, "references_total": 0, "prompt_tokens": 0, "completion_tokens": 0, "reported_costs": 0, "cache_hits": 0} for mode in ("direct_llm", "kg_llm")}
    review_records = []
    evidence_detail_rows = []
    review_key = []
    rng = random.Random(20261115)
    aliases = ["A", "B", "C"]

    for run_row in run_rows:
        pert_id = run_row["pert_id"]
        case = case_by_id[pert_id]
        package = read_json(PACKAGES / f"{pert_id}.json")
        if package.get("provenance", {}).get("evidence_input_sha256") != case["evidence_input_sha256"]:
            raise SystemExit(f"Evidence input hash mismatch for {pert_id}")

        result_by_method = {}
        for mode in ("direct_llm", "kg_llm"):
            relative = run_row.get(f"{mode}_output", "")
            output_path = ROOT / relative
            if not output_path.is_file():
                raise SystemExit(f"Missing {mode} output for {pert_id}")
            output = read_json(output_path)
            if output.get("evidence_input_sha256") != case["evidence_input_sha256"]:
                raise SystemExit(f"Output EvidencePackage hash mismatch for {pert_id} ({mode})")
            result_by_method[mode] = (output, output_path)
            data = summary[mode]
            data["latencies"].append(float(output.get("latency_seconds", 0)))
            data["claims"] += len(claims_from(output))
            data["prompt_tokens"] += int(output.get("usage", {}).get("prompt_tokens", 0) or 0)
            data["completion_tokens"] += int(output.get("usage", {}).get("completion_tokens", 0) or 0)
            data["reported_costs"] += int(output.get("provider_cost") is not None)
            data["cache_hits"] += int(bool(output.get("cached")))
            data["references_valid"], data["references_total"] = (
                data["references_valid"] + retained_reference_integrity(output, package, mode)[0],
                data["references_total"] + retained_reference_integrity(output, package, mode)[1],
            )
            for issue in output.get("citation_validation_issues", []):
                issue_name = issue.get("issue", "unknown")
                data["issues"][issue_name] = data["issues"].get(issue_name, 0) + 1
            case[f"{mode}_status"] = output.get("status", "failed")
            case[f"{mode}_latency_seconds"] = output.get("latency_seconds", "")
            case[f"{mode}_cost"] = output.get("provider_cost") if output.get("provider_cost") is not None else "not reported"
            case[f"{mode}_output"] = relative
            case[f"{mode}_citation_reference_validation_pass"] = str(bool(output.get("citation_reference_validation_pass"))).lower()
            case[f"{mode}_validation_issue_count"] = len(output.get("citation_validation_issues", []))

        rule_path = ROOT / case["kg_rule_output"]
        rule_output = read_json(rule_path)
        if rule_output.get("evidence_input_sha256") != case["evidence_input_sha256"]:
            raise SystemExit(f"Rule template EvidencePackage hash mismatch for {pert_id}")
        result_by_method["kg_rule"] = (rule_output, rule_path)

        if existing_code_map:
            code_map = existing_code_map[case["case"]]
        else:
            code_order = aliases.copy()
            rng.shuffle(code_order)
            code_map = dict(zip(method_names, code_order))
        for method in method_names:
            output, output_path = result_by_method[method]
            review_key.append({"case": case["case"], "pert_id": pert_id, "review_code": code_map[method], "method": method})
            public_claims = reviewer_claims(output)
            review_records.append({
                "case": case["case"], "pert_id": pert_id, "drug_name": case["drug_name"],
                "review_code": code_map[method], "evidence_input_sha256": case["evidence_input_sha256"],
                "evidence_package_path": f"experiments/kg06_mechanism_evidence/results/evidence_packages_v2/{pert_id}.json",
                "evidence_detail_path": "experiments/kg07_mechanism_interpretation/kg07_human_review_evidence.csv",
                "claims_json": json.dumps(public_claims, ensure_ascii=False, separators=(",", ":")),
                **{field: "" for field in REVIEW_FIELDS},
            })
            for claim_index, claim in enumerate(public_claims, start=1):
                snapshots, refs_found = citation_snapshots(package, claim.get("evidence_ids", []), claim.get("path_ids", []))
                evidence_detail_rows.append({
                    "case": case["case"], "pert_id": pert_id, "drug_name": case["drug_name"],
                    "review_code": code_map[method], "claim_index": claim_index,
                    "claim_section": claim.get("section"), "claim_text": claim.get("text"),
                    "relation": claim.get("relation", ""),
                    "evidence_ids": json.dumps(claim.get("evidence_ids", []), ensure_ascii=False),
                    "path_ids": json.dumps(claim.get("path_ids", []), ensure_ascii=False),
                    "citation_found_in_package": str(bool(refs_found) if claim.get("evidence_ids") or claim.get("path_ids") else False).lower(),
                    "source_snapshots_json": json.dumps(snapshots, ensure_ascii=False, separators=(",", ":")),
                })

    with CASE_CSV.open("w", encoding="utf-8-sig", newline="") as stream:
        fields = list(dict.fromkeys(key for row in case_rows for key in row))
        fields += [key for key in ("direct_llm_output", "direct_llm_citation_reference_validation_pass", "direct_llm_validation_issue_count", "kg_llm_output", "kg_llm_citation_reference_validation_pass", "kg_llm_validation_issue_count") if key not in fields]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(case_rows)

    with review_path.open("w", encoding="utf-8-sig", newline="") as stream:
        fields = list(review_records[0])
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(review_records)
    evidence_detail_path = OUT / "kg07_human_review_evidence.csv"
    with evidence_detail_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(evidence_detail_rows[0]))
        writer.writeheader()
        writer.writerows(evidence_detail_rows)
    if not key_path.is_file():
        with key_path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(review_key[0]))
            writer.writeheader()
            writer.writerows(review_key)

    rubric_path = OUT / "kg07_human_review_instructions.md"
    rubric_path.write_text("""# KG07 20 案盲审说明

## 审阅顺序

1. 先只打开 `kg07_human_review_20_cases.csv` 与 `kg07_human_review_evidence.csv`，不要查看 `kg07_human_review_blinding_key.csv`，直到所有案例完成评分。
2. 每行是一名候选的一种解释方法。`claims_json` 仅含实际展示的保留声明；辅助表按 `case + review_code + claim_index` 给出声明引用的证据快照。审阅期间不要打开模型原始结果 JSON，以免从文件名或元数据得知方法。
3. 核对声明时沿 `evidence_ids` 查包中的 `evidence`/`edges.sources`，沿 `path_ids` 查包中的 `paths`。ID 存在不等于它支持文字；需核对来源陈述与关系方向。
4. 完成全部评分后再打开盲审映射表，揭盲并按方法汇总。

## 每个候选的评分口径

- `supported_claim_fraction`：被所引证据直接支持的事实性声明数 / 全部事实性声明数，填 0–1；没有事实性声明填 `NA`。
- `citation_precision`：确实支持对应声明的引用数 / 核查过的引用数，填 0–1；无引用填 `NA`。只核对 ID 是否存在不能算引用正确。
- `unsupported_assertion_count`：按 claim 对象计数；一个 claim 含一条或多条无依据事实时计 1。缺少证据、引用与句子无关、或把相关性说成因果都算无依据，填非负整数。
- `relation_direction_error_count`：按 claim 对象计数；一个 claim 即使同时有多个错误方向也计 1。把结合/抑制/激活/关联方向说错或来源未支持方向都计入，填非负整数。
- `uncertainty_accuracy`：对每一处证据不足/不确定性表述判断是否与实际证据覆盖一致；填“正确的表述数 / 可评估表述数” (0–1)，无可评估表述填 `NA`。
- `review_notes`：简要写出最关键的证据问题，可列 `Path ID` / `Evidence ID`。

延迟与 token 用量已在模型逐例 CSV/JSON 中记录。服务方未返回费用，费用不要估算。建议以案例为单位先算比例，再报告方法间宏平均；断言错误数另报总数。任何结果都不应被写成临床疗效证据。

盲审表中评分单元格为空表示未审阅，不代表 0 分。""", encoding="utf-8")

    old_manifest = read_json(OUT / "kg07_evaluation_manifest.json")
    old_manifest.update({
        "status": "MODEL_OUTPUTS_GENERATED_HUMAN_REVIEW_PENDING",
        "n_cases": 20,
        "methods": ["direct_llm generated", "kg_rule generated", "kg_llm generated"],
        "human_review_required": True,
        "external_data_sent_to_zhipu": True,
        "model_run_manifest": str(run_manifest_path.relative_to(ROOT)).replace("\\", "/"),
        "model_run_manifest_sha256": sha(run_manifest_path),
        "model_run_results_sha256": sha(run_csv_path),
        "review_sheet": str(review_path.relative_to(ROOT)).replace("\\", "/"),
        "review_sheet_sha256": sha(review_path),
        "review_evidence_detail": str(evidence_detail_path.relative_to(ROOT)).replace("\\", "/"),
        "review_evidence_detail_sha256": sha(evidence_detail_path),
        "review_instructions": str(rubric_path.relative_to(ROOT)).replace("\\", "/"),
        "review_instructions_sha256": sha(rubric_path),
        "blinding_key": str(key_path.relative_to(ROOT)).replace("\\", "/"),
        "human_review_scores_filled": False,
    })
    old_manifest["outputs"] = {**old_manifest.get("outputs", {}), CASE_CSV.name: sha(CASE_CSV), review_path.name: sha(review_path), evidence_detail_path.name: sha(evidence_detail_path), key_path.name: sha(key_path), rubric_path.name: sha(rubric_path)}
    (OUT / "kg07_evaluation_manifest.json").write_text(json.dumps(old_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    direct = summary["direct_llm"]
    kg = summary["kg_llm"]
    top50_dir = OUT / "top50_llm"
    top50_manifest = read_json(top50_dir / "kg07_top50_llm_manifest.json")
    top50_rows = list(csv.DictReader((top50_dir / "kg07_top50_llm_results.csv").open(encoding="utf-8-sig", newline="")))
    top50_reference_pass = sum(str(row.get("citation_reference_validation_pass", "")).lower() == "true" for row in top50_rows)
    top50_strict_pass = sum(str(row.get("citation_validation_pass", "")).lower() == "true" for row in top50_rows)
    top50_tokens = sum(int(row.get("total_tokens") or 0) for row in top50_rows)
    top50_latency = statistics.mean(float(row.get("latency_seconds") or 0) for row in top50_rows)
    resolved_detail_refs = sum(row.get("citation_found_in_package") == "true" for row in evidence_detail_rows)
    unresolved_detail_refs = sum(row.get("citation_found_in_package") == "false" and (row.get("evidence_ids") != "[]" or row.get("path_ids") != "[]") for row in evidence_detail_rows)
    uncited_detail_claims = sum(row.get("evidence_ids") == "[]" and row.get("path_ids") == "[]" for row in evidence_detail_rows)
    eval_report = f"""# KG07 20 案解释对照与 Top50 生成报告

## 实际运行

- 20 个真实候选均来自分层抽样集；每个案例使用同一 EvidencePackage 输入哈希。
- 智谱模型：`glm-5.3-flash`；KG+LLM 提示词版本：`kg07-evidence-interpretation-v1.5`。20 案 direct baseline 与 20 案 KG+LLM 均完成，API/解析错误为 0。
- Direct LLM：{len(run_rows)}/20 完成，平均响应 {statistics.mean(direct['latencies']):.2f} 秒，输出 {direct['claims']} 条声明；提示词输入/输出 token 共 {direct['prompt_tokens']}/{direct['completion_tokens']}。该基线不接收图谱路径；模型产生的无效引用会被移除，剩余文字标记未验证，不能视为证据引用通过。
- KG 规则模板：20/20 本地生成，20/20 的引用 ID/Path ID 可回到对应 EvidencePackage；它是按字段填充的模板，不是语义正确性证明。
- KG+LLM：20/20 完成，平均响应 {statistics.mean(kg['latencies']):.2f} 秒，保留 {kg['claims']} 条声明；提示词输入/输出 token 共 {kg['prompt_tokens']}/{kg['completion_tokens']}。校验共记录 {sum(kg['issues'].values())} 个问题：{kg['issues'].get('claim dropped: no verifiable citation', 0)} 条未引用模型声明被丢弃、{kg['issues'].get('relation direction not asserted by cited source; downgraded', 0)} 条方向表述被降级。保留的有引文声明中 {kg['references_valid']}/{kg['references_total']} 个 ID 属于该候选允许的 EvidencePackage 子集。
- 服务方没有返回费用字段；token 用量已记录。缓存命中：direct {direct['cache_hits']}/20，KG+LLM {kg['cache_hits']}/20。

## Top50 解释

- Top50 LLM 结果：{top50_manifest.get('n_generated', 0)}/50，调用错误 {top50_manifest.get('n_errors', 0)}，其中未缓存的真实 API 调用 {top50_manifest.get('n_uncached_calls', 0)} 次、缓存复用 {top50_manifest.get('n_candidates', 0)-top50_manifest.get('n_uncached_calls', 0)} 次。
- 累计 token {top50_tokens}，平均响应 {top50_latency:.2f} 秒；保留结论的引用 ID/Path ID 可核验：{top50_reference_pass}/50；原始模型输出无降级/丢弃问题：{top50_strict_pass}/50。引用 ID 命中只证明来源可定位，不证明语义蕴含。
- KG06 输入包的本轮审计：50/50 文件与哈希有效，28/50 有图谱路径，30/50 有精确化合物映射。对没有路径或映射的候选不补造关系。

## 人工审核状态与解释边界

- 20 案盲审表已生成，60 行；逐声明证据快照表有 {len(evidence_detail_rows)} 行，其中 {resolved_detail_refs} 行带有包内可定位的 Evidence/Path ID、{uncited_detail_claims} 行没有引用、带引用但包内无法定位为 {unresolved_detail_refs} 行。评分列仍为空，等待人工逐项判断句子是否真的受引用支持。评分规则见 `kg07_human_review_instructions.md`；盲审代码对应关系单独保存在 `kg07_human_review_blinding_key.csv`。
- 本次没有给出“模型更正确”或生物学正确率结论。自动程序只检查输出能否解析、引用 ID 是否属于当前 EvidencePackage、方向表述是否需要降级；语义支持、机制合理性及不确定性准确度必须由人工审阅。
- WTCS/PRISM、关联路径和数据库靶点记录均不等同于临床疗效证据。

## 可复现文件

- 逐案模型结果：`evaluation/kg07_evaluation_cases.csv`；原始运行记录：`evaluation/kg07_evaluation_manifest.json`。
- 20 案审阅表：`kg07_human_review_20_cases.csv`；引用快照：`kg07_human_review_evidence.csv`；盲审映射：`kg07_human_review_blinding_key.csv`。
- 审阅评分说明：`kg07_human_review_instructions.md`；填写完成后运行 `score_human_review.py`，脚本会先做完整性与范围校验，当前空表会被拒绝，不生成评分结果。
- Top50 结果：`top50_llm/kg07_top50_llm_results.csv` 与逐候选 JSON；覆盖审计：`kg07_top50_explanation_coverage_report.md`。
- 首次因长输出出现的 9 个 JSON 截断错误记录保存在 `evaluation/run_v1_3/`；压缩到 12 条摘要路径和 8 条精简 S2 条件后，后续 20 案及 Top50 均完成。
"""
    (OUT / "kg07_evaluation_report.md").write_text(eval_report, encoding="utf-8")
    print(json.dumps({"status": "MODEL_OUTPUTS_GENERATED_HUMAN_REVIEW_PENDING", "n_cases": 20, "review_rows": len(review_records), "evidence_detail_rows": len(evidence_detail_rows), "resolved_cited_claim_rows": resolved_detail_refs, "uncited_claim_rows": uncited_detail_claims, "unresolved_cited_claim_rows": unresolved_detail_refs, "direct_claims": direct["claims"], "kg_claims": kg["claims"], "kg_citation_issues": kg["issues"], "top50_generated": top50_manifest.get("n_generated")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
