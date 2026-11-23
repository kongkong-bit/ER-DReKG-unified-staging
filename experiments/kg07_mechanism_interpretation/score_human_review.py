"""Validate completed blinded scores, then unblind and summarize the 20-case review."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments" / "kg07_mechanism_interpretation"
sys.path.insert(0, str(ROOT / "backend"))

if len(sys.argv) > 2:
    raise SystemExit("Usage: python score_human_review.py [path/to/completed_blind_review.csv]")
REVIEW = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else OUT / "kg07_human_review_20_cases.csv"
KEY = OUT / "kg07_human_review_blinding_key.csv"
EVAL = OUT / "evaluation" / "kg07_evaluation_cases.csv"
MANIFEST = OUT / "kg07_evaluation_manifest.json"
PKG_DIR = ROOT / "experiments" / "kg06_mechanism_evidence" / "results" / "evidence_packages_v2"
SCORE_COLUMNS = ("supported_claim_fraction", "citation_precision", "unsupported_assertion_count", "relation_direction_error_count", "uncertainty_accuracy")
FRACTION_COLUMNS = {"supported_claim_fraction", "citation_precision", "uncertainty_accuracy"}
METHODS = ("direct_llm", "kg_rule", "kg_llm")
FACTUAL_SECTIONS = {"screening_basis", "known_targets", "associated_pathways", "independent_validation", "mechanism_hypotheses"}
DIRECTIONAL_RELATIONS = {"binding", "inhibition", "activation", "causal"}
DIRECTION_WORDS = re.compile(r"结合|抑制|激活|激动|拮抗|阻断|bind(?:ing)?|inhibit(?:ion)?|activat(?:e|ion)|agonist|antagonist|causal", re.IGNORECASE)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))


def parse_score(row: dict[str, str], column: str, row_index: int) -> float | None:
    raw = (row.get(column) or "").strip()
    if raw.upper() == "NA":
        if column in {"unsupported_assertion_count", "relation_direction_error_count"}:
            raise ValueError(f"row {row_index}: {column} must be a nonnegative integer, not NA")
        return None
    if not raw:
        raise ValueError(f"row {row_index}: {column} is blank; human review is still pending")
    try:
        value = float(raw)
    except ValueError as error:
        raise ValueError(f"row {row_index}: {column} must be numeric or NA") from error
    if not math.isfinite(value):
        raise ValueError(f"row {row_index}: {column} must be finite")
    if column in FRACTION_COLUMNS and not 0 <= value <= 1:
        raise ValueError(f"row {row_index}: {column} must be between 0 and 1")
    if column not in FRACTION_COLUMNS and (value < 0 or not value.is_integer()):
        raise ValueError(f"row {row_index}: {column} must be a nonnegative integer")
    return value


def validate_rows(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, float | None]]:
    if len(rows) != 60:
        raise ValueError(f"expected 60 review rows, found {len(rows)}")
    parsed: dict[tuple[str, str], dict[str, float | None]] = {}
    per_case: dict[str, set[str]] = defaultdict(set)
    for index, row in enumerate(rows, start=2):
        case = row.get("case", "")
        code = row.get("review_code", "")
        if not case or not code:
            raise ValueError(f"row {index}: case and review_code are required")
        key = (case, code)
        if key in parsed:
            raise ValueError(f"row {index}: duplicate case/review_code {key}")
        if not row.get("claims_json"):
            raise ValueError(f"row {index}: claims_json is missing")
        json.loads(row["claims_json"])
        parsed[key] = {column: parse_score(row, column, index) for column in SCORE_COLUMNS}
        per_case[case].add(code)
        package_path = ROOT / row["evidence_package_path"]
        package = json.loads(package_path.read_text(encoding="utf-8"))
        if package.get("provenance", {}).get("evidence_input_sha256") != row.get("evidence_input_sha256"):
            raise ValueError(f"row {index}: EvidencePackage hash mismatch for {row.get('pert_id')}")
    if len(per_case) != 20 or any(len(codes) != 3 for codes in per_case.values()):
        raise ValueError("each of 20 cases must have exactly three distinct blinded method codes")
    return parsed


def main() -> None:
    rows = read_csv(REVIEW)
    try:
        scores = validate_rows(rows)
    except (ValueError, json.JSONDecodeError, OSError) as error:
        raise SystemExit(f"HUMAN_REVIEW_PENDING: {error}") from error

    mapping_rows = read_csv(KEY)
    code_to_method: dict[tuple[str, str], str] = {}
    methods_by_case: dict[str, set[str]] = defaultdict(set)
    for row in mapping_rows:
        key = (row["case"], row["review_code"])
        method = row["method"]
        if key in code_to_method or method not in METHODS:
            raise SystemExit(f"Invalid or duplicate blinded mapping: {key}")
        code_to_method[key] = method
        methods_by_case[row["case"]].add(method)
    if set(code_to_method) != set(scores) or {method for _, method in code_to_method.items()} != set(METHODS):
        raise SystemExit("Blinding key does not exactly match the reviewed rows and three expected methods")
    if len(methods_by_case) != 20 or any(methods != set(METHODS) for methods in methods_by_case.values()):
        raise SystemExit("Every reviewed case must map once to each of Direct LLM, KG rule, and KG+LLM")

    by_case_method: dict[tuple[str, str], dict[str, Any]] = {}
    eval_rows = read_csv(EVAL)
    eval_by_id = {row["pert_id"]: row for row in eval_rows}
    for row in rows:
        method = code_to_method[(row["case"], row["review_code"])]
        claims = json.loads(row["claims_json"])
        factual = [claim for claim in claims if claim.get("section") in FACTUAL_SECTIONS]
        directional = [claim for claim in factual if str(claim.get("relation", "")).lower() in DIRECTIONAL_RELATIONS or DIRECTION_WORDS.search(str(claim.get("text", "")))]
        value = scores[(row["case"], row["review_code"])]
        source = eval_by_id[row["pert_id"]]
        if method == "kg_rule":
            output = json.loads((ROOT / source["kg_rule_output"]).read_text(encoding="utf-8"))
            latency = float(output.get("latency_seconds", 0) or 0)
            cost = output.get("provider_cost")
            tokens = 0
        else:
            output = json.loads((ROOT / source[f"{method}_output"]).read_text(encoding="utf-8"))
            latency = float(output.get("latency_seconds", 0) or 0)
            cost = output.get("provider_cost")
            tokens = int(output.get("usage", {}).get("total_tokens", 0) or 0)
        by_case_method[(row["case"], method)] = {
            **value,
            "pert_id": row["pert_id"],
            "drug_name": row["drug_name"],
            "factual_claim_count": len(factual),
            "directional_claim_count": len(directional),
            "latency_seconds": latency,
            "provider_cost": cost,
            "total_tokens": tokens,
        }
        if value["unsupported_assertion_count"] is not None and value["unsupported_assertion_count"] > len(factual):
            raise SystemExit(f"Unsupported-assertion count exceeds factual claims for {row['pert_id']} ({method})")

    summary_rows = []
    report_lines = [
        "# KG07 20 案人工盲审结果",
        "",
        f"评分表 SHA-256：`{sha(REVIEW)}`；盲审映射 SHA-256：`{sha(KEY)}`。",
        "人工评分已完整通过范围、完整性和 EvidencePackage 哈希校验；以下方法标签是在校验后才揭盲得到。",
        "",
        "| 方法 | 案例数 | 有依据声明比例（宏平均） | 引用精确率（宏平均） | 无依据断言数 | 无依据断言率 | 关系方向错误数 | 方向错误率 | 不确定性准确度（宏平均） | 平均延迟（秒） | 总 token | 服务方回报费用数 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for method in METHODS:
        case_data = [value for (_, method_name), value in by_case_method.items() if method_name == method]
        mean = lambda name: statistics.mean([value[name] for value in case_data if value[name] is not None]) if any(value[name] is not None for value in case_data) else None
        unsupported = sum(int(value["unsupported_assertion_count"] or 0) for value in case_data)
        factual_total = sum(value["factual_claim_count"] for value in case_data)
        direction_errors = sum(int(value["relation_direction_error_count"] or 0) for value in case_data)
        directional_total = sum(value["directional_claim_count"] for value in case_data)
        cost_count = sum(value["provider_cost"] is not None for value in case_data)
        row = {
            "method": method,
            "n_cases": len(case_data),
            "supported_claim_fraction_macro_mean": mean("supported_claim_fraction"),
            "citation_precision_macro_mean": mean("citation_precision"),
            "unsupported_assertion_count_total": unsupported,
            "unsupported_assertion_rate": unsupported / factual_total if factual_total else "NA",
            "relation_direction_error_count_total": direction_errors,
            "relation_direction_error_rate": direction_errors / directional_total if directional_total else "NA",
            "uncertainty_accuracy_macro_mean": mean("uncertainty_accuracy"),
            "mean_latency_seconds": statistics.mean(value["latency_seconds"] for value in case_data),
            "total_tokens": sum(value["total_tokens"] for value in case_data),
            "provider_cost_reported_cases": cost_count,
            "provider_cost_status": "not reported" if cost_count == 0 else "reported for some cases",
        }
        summary_rows.append(row)
        def fmt(value: Any) -> str:
            return "NA" if value is None or value == "NA" else f"{float(value):.3f}"
        report_lines.append(
            f"| {method} | {len(case_data)} | {fmt(row['supported_claim_fraction_macro_mean'])} | {fmt(row['citation_precision_macro_mean'])} | {unsupported} | {fmt(row['unsupported_assertion_rate'])} | {direction_errors} | {fmt(row['relation_direction_error_rate'])} | {fmt(row['uncertainty_accuracy_macro_mean'])} | {row['mean_latency_seconds']:.2f} | {row['total_tokens']} | {cost_count} |"
        )
    report_lines += [
        "",
        "比例指标先按候选计算，再报告 20 案宏平均；断言错误数和 token 数报告总量。无可评估分母时记为 NA。服务方未提供费用时不估算。",
        "该表描述本次人工审阅样本，不代表临床疗效或总体候选药物的普遍结论。",
        "",
    ]
    csv_path = OUT / "kg07_human_review_summary.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary_rows[0]))
        writer.writeheader()
        writer.writerows(summary_rows)
    report_path = OUT / "kg07_human_review_results.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    result_manifest = {
        "status": "HUMAN_REVIEW_COMPLETE",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "n_cases": 20,
        "n_methods": 3,
        "n_scores": len(rows),
        "review_sheet_sha256": sha(REVIEW),
        "blinding_key_sha256": sha(KEY),
        "summary_csv_sha256": sha(csv_path),
        "report_sha256": sha(report_path),
        "study_manifest": str(MANIFEST.relative_to(ROOT)),
    }
    manifest_path = OUT / "kg07_human_review_results_manifest.json"
    manifest_path.write_text(json.dumps(result_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    study_manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    study_manifest.update({
        "status": "HUMAN_REVIEW_COMPLETE",
        "human_review_scores_filled": True,
        "human_review_results_manifest": str(manifest_path.relative_to(ROOT)).replace("\\", "/"),
        "human_review_results_manifest_sha256": sha(manifest_path),
    })
    MANIFEST.write_text(json.dumps(study_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path = OUT / "kg07_evaluation_report.md"
    current_report = report_path.read_text(encoding="utf-8")
    current_report = current_report.replace(
        "20 案盲审表已生成，60 行（每个候选的 Direct LLM、KG 规则、KG+LLM 三种输出各一行）；评分列保持空白，等待人工逐项核对主张与引用证据。评分规则见 `kg07_human_review_instructions.md`；盲审代码对应关系单独保存在 `kg07_human_review_blinding_key.csv`。",
        "20 案盲审表已由审阅者填写，60 行（每个候选的 Direct LLM、KG 规则、KG+LLM 三种输出各一行）；逐方法评分及审阅结论已汇总到 `kg07_human_review_results.md`。",
    )
    current_report += "\n## 人工盲审结果\n\n人工评分已经完整校验并汇总。逐方法数值见 `kg07_human_review_results.md` 和 `kg07_human_review_summary.csv`；审阅评分清单与揭盲映射哈希记录在 `kg07_human_review_results_manifest.json`。\n"
    report_path.write_text(current_report, encoding="utf-8")
    study_manifest["outputs"] = {
        **study_manifest.get("outputs", {}),
        "kg07_human_review_summary.csv": sha(csv_path),
        "kg07_human_review_results.md": sha(report_path),
        "kg07_evaluation_report.md": sha(OUT / "kg07_evaluation_report.md"),
    }
    MANIFEST.write_text(json.dumps(study_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": result_manifest["status"], "cases": 20, "methods": 3, "scores": len(rows), "report": str(report_path.relative_to(ROOT))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
