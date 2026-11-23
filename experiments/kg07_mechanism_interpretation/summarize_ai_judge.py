"""Unblind and summarize the completed AI-as-judge KG07 evaluation."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments" / "kg07_mechanism_interpretation"
AI = OUT / "ai_judge"
SCORES = AI / "kg07_ai_judge_scores.csv"
REVIEW = OUT / "kg07_human_review_20_cases.csv"
KEY = OUT / "kg07_human_review_blinding_key.csv"
EVALUATION = OUT / "evaluation" / "kg07_evaluation_cases.csv"
MANIFEST = AI / "kg07_ai_judge_manifest.json"
FACTUAL_SECTIONS = {"screening_basis", "known_targets", "associated_pathways", "independent_validation", "mechanism_hypotheses"}
DIRECTIONAL_RELATIONS = {"binding", "inhibition", "activation", "causal"}
DIRECTION_WORDS = re.compile(r"结合|抑制|激活|激动|拮抗|阻断|bind(?:ing)?|inhibit(?:ion)?|activat(?:e|ion)|agonist|antagonist|causal|因果", re.I)
METHOD_LABELS = {"direct_llm": "Direct LLM", "kg_rule": "KG 规则模板", "kg_llm": "KG + LLM"}
RATIO_FIELDS = ("supported_claim_fraction", "citation_precision", "uncertainty_accuracy")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def number(value: str, field: str, row: str) -> float | None:
    raw = (value or "").strip()
    if raw.upper() == "NA":
        if field not in RATIO_FIELDS:
            raise ValueError(f"{row}: {field} cannot be NA")
        return None
    n = float(raw)
    if not math.isfinite(n):
        raise ValueError(f"{row}: {field} must be finite")
    if field in RATIO_FIELDS and not 0 <= n <= 1:
        raise ValueError(f"{row}: {field} outside [0,1]")
    if field not in RATIO_FIELDS and (n < 0 or not n.is_integer()):
        raise ValueError(f"{row}: {field} must be a nonnegative integer")
    return n


def mean(values: list[float | None]) -> float | None:
    nums = [value for value in values if value is not None]
    return statistics.mean(nums) if nums else None


def fmt(value: float | None, percent: bool = False) -> str:
    if value is None:
        return "NA"
    return f"{value * 100:.1f}%" if percent else f"{value:.3f}"


def main() -> None:
    score_rows = read_csv(SCORES)
    review_rows = read_csv(REVIEW)
    key_rows = read_csv(KEY)
    eval_rows = read_csv(EVALUATION)
    run_manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if run_manifest.get("status") != "AI_JUDGE_COMPLETE" or run_manifest.get("n_scores") != 60:
        raise SystemExit("AI judge manifest is not complete; refusing to unblind")
    if len(score_rows) != 60 or len(review_rows) != 60 or len(key_rows) != 60:
        raise SystemExit("Expected 60 score, source-review, and blind-key rows")
    if run_manifest.get("source_review_csv_sha256") != sha(REVIEW):
        raise SystemExit("Blinded source review CSV hash mismatch")
    if run_manifest.get("source_evidence_csv_sha256") != sha(OUT / "kg07_human_review_evidence.csv"):
        raise SystemExit("Blinded source evidence CSV hash mismatch")

    key_map = {(row["case"], row["review_code"]): row["method"] for row in key_rows}
    review_map = {(row["case"], row["review_code"]): row for row in review_rows}
    if len(key_map) != 60 or set(key_map) != set(review_map):
        raise SystemExit("Blind key does not exactly match the 60 reviewed records")
    if set(key_map.values()) != set(METHOD_LABELS):
        raise SystemExit("Blind key does not contain exactly the three expected methods")
    eval_by_id = {row["pert_id"]: row for row in eval_rows}

    per_method: dict[str, list[dict[str, Any]]] = defaultdict(list)
    case_method: dict[tuple[str, str], dict[str, Any]] = {}
    for score in score_rows:
        identity = (score["case"], score["review_code"])
        source = review_map.get(identity)
        if source is None or identity not in key_map:
            raise SystemExit(f"Score row not found in source/key: {identity}")
        if score["pert_id"] != source["pert_id"] or score["drug_name"] != source["drug_name"] or score["evidence_input_sha256"] != source["evidence_input_sha256"]:
            raise SystemExit(f"Identity or EvidencePackage hash mismatch: {identity}")
        if score["review_type"] != "AI-as-judge; not human review":
            raise SystemExit(f"Unexpected review type: {identity}")
        method = key_map[identity]
        eval_row = eval_by_id.get(score["pert_id"])
        if eval_row is None:
            raise SystemExit(f"Missing original method run row: {score['pert_id']}")
        method_output_path = ROOT / eval_row[f"{method}_output"]
        method_output = json.loads(method_output_path.read_text(encoding="utf-8"))
        method_usage = method_output.get("usage", {}) or {}
        method_data: dict[str, Any] = {
            "case": score["case"], "review_code": score["review_code"],
            "method": method, "pert_id": score["pert_id"], "drug_name": score["drug_name"],
            "factual_claim_count": sum(claim.get("section") in FACTUAL_SECTIONS for claim in json.loads(source["claims_json"])),
            "directional_claim_count": sum(
                1 for claim in json.loads(source["claims_json"])
                if claim.get("section") in FACTUAL_SECTIONS and
                (claim.get("relation", "").lower() in DIRECTIONAL_RELATIONS or bool(DIRECTION_WORDS.search(claim.get("text", ""))))
            ),
            "method_latency_seconds": float(method_output.get("latency_seconds", 0) or 0),
            "method_prompt_tokens": int(method_usage.get("prompt_tokens", 0) or 0),
            "method_completion_tokens": int(method_usage.get("completion_tokens", 0) or 0),
            "method_total_tokens": int(method_usage.get("total_tokens", 0) or 0),
            "method_provider_cost": method_output.get("provider_cost"),
            "ai_judge_latency_seconds": float(score["latency_seconds"]),
            "ai_judge_prompt_tokens": int(score["prompt_tokens"] or 0),
            "ai_judge_completion_tokens": int(score["completion_tokens"] or 0),
            "ai_judge_request_count": int(score.get("request_count", "1") or 1),
            "prompt_version": score["prompt_version"],
            "model": score["model"],
        }
        for field in RATIO_FIELDS:
            method_data[field] = number(score[field], field, str(identity))
        for field in ("unsupported_assertion_count", "relation_direction_error_count"):
            method_data[field] = int(number(score[field], field, str(identity)) or 0)
        if method_data["unsupported_assertion_count"] > method_data["factual_claim_count"]:
            raise SystemExit(f"Unsupported assertions exceed factual claims: {identity}")
        if method_data["relation_direction_error_count"] > method_data["directional_claim_count"]:
            raise SystemExit(f"Direction errors exceed directional claims: {identity}")
        per_method[method].append(method_data)
        case_method[(score["case"], method)] = method_data

    if any(len(per_method.get(method, [])) != 20 for method in METHOD_LABELS):
        raise SystemExit("Each method must have 20 paired cases")

    method_fields = [
        "method", "display_name", "n_cases", "n_supported_claim_fraction_cases",
        "supported_claim_fraction_macro_mean", "n_citation_precision_cases", "citation_precision_macro_mean", "unsupported_assertion_count_total",
        "unsupported_assertion_rate", "relation_direction_error_count_total",
        "relation_direction_error_rate", "n_uncertainty_accuracy_cases", "uncertainty_accuracy_macro_mean",
        "mean_method_output_latency_seconds", "total_method_output_tokens",
        "method_provider_cost_reported_cases", "mean_ai_judge_latency_seconds",
        "ai_judge_prompt_tokens_reported", "ai_judge_completion_tokens_reported",
        "ai_judge_provider_cost_reported_cases",
    ]
    method_summary = []
    report_lines = [
        "# KG07 20 案 AI 自动盲审结果",
        "",
        "> **这是智谱 GLM-5.3-Flash 的 AI-as-judge 结果，不是人工审阅结果。它不能满足原方案要求的独立人工证据审核，也不能作为临床疗效证据。**",
        "",
        f"评审样本：20 个候选 × 3 种解释，共 60 条；模型：`{run_manifest['model']}`；评分 Prompt：`{run_manifest['prompt_version']}`。",
        f"评分 CSV SHA-256：`{sha(SCORES)}`。人工盲审仍为待完成；原人工评分表没有被修改。",
        "",
        "## 方法汇总",
        "",
        "比例指标先按每条解释计算，再对每种方法的 20 条解释取宏平均；错误计数按声明对象汇总。",
        "",
        "| 方法 | 案例数 | 有依据声明比例（可评分数） | 引用支持准确率（可评分数） | 无依据断言数 / 率 | 方向错误数 / 率 | 不确定性准确率（可评分数） | 方法平均耗时（秒） | 方法输出 tokens | 方法费用 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for method in ("direct_llm", "kg_rule", "kg_llm"):
        rows = per_method[method]
        factual_total = sum(row["factual_claim_count"] for row in rows)
        direction_total = sum(row["directional_claim_count"] for row in rows)
        unsupported_total = sum(row["unsupported_assertion_count"] for row in rows)
        direction_errors = sum(row["relation_direction_error_count"] for row in rows)
        method_cost_count = sum(row["method_provider_cost"] not in (None, "", "not reported by provider") for row in rows)
        judge_cost_count = 0
        result = {
            "method": method,
            "display_name": METHOD_LABELS[method],
            "n_cases": len(rows),
            "n_supported_claim_fraction_cases": sum(r["supported_claim_fraction"] is not None for r in rows),
            "supported_claim_fraction_macro_mean": mean([r["supported_claim_fraction"] for r in rows]),
            "n_citation_precision_cases": sum(r["citation_precision"] is not None for r in rows),
            "citation_precision_macro_mean": mean([r["citation_precision"] for r in rows]),
            "unsupported_assertion_count_total": unsupported_total,
            "unsupported_assertion_rate": unsupported_total / factual_total if factual_total else None,
            "relation_direction_error_count_total": direction_errors,
            "relation_direction_error_rate": direction_errors / direction_total if direction_total else None,
            "n_uncertainty_accuracy_cases": sum(r["uncertainty_accuracy"] is not None for r in rows),
            "uncertainty_accuracy_macro_mean": mean([r["uncertainty_accuracy"] for r in rows]),
            "mean_method_output_latency_seconds": statistics.mean(r["method_latency_seconds"] for r in rows),
            "total_method_output_tokens": sum(r["method_total_tokens"] for r in rows),
            "method_provider_cost_reported_cases": method_cost_count,
            "mean_ai_judge_latency_seconds": statistics.mean(r["ai_judge_latency_seconds"] for r in rows),
            "ai_judge_prompt_tokens_reported": sum(r["ai_judge_prompt_tokens"] for r in rows),
            "ai_judge_completion_tokens_reported": sum(r["ai_judge_completion_tokens"] for r in rows),
            "ai_judge_provider_cost_reported_cases": judge_cost_count,
        }
        method_summary.append(result)
        report_lines.append(
            f"| {METHOD_LABELS[method]} | 20 | {fmt(result['supported_claim_fraction_macro_mean'], True)} ({result['n_supported_claim_fraction_cases']}/20) | {fmt(result['citation_precision_macro_mean'], True)} ({result['n_citation_precision_cases']}/20) | {unsupported_total} / {fmt(result['unsupported_assertion_rate'], True)} | {direction_errors} / {fmt(result['relation_direction_error_rate'], True)} | {fmt(result['uncertainty_accuracy_macro_mean'], True)} ({result['n_uncertainty_accuracy_cases']}/20) | {result['mean_method_output_latency_seconds']:.1f} | {result['total_method_output_tokens']} | 未返回 |"
        )

    deltas = []
    for left, right in (("kg_rule", "direct_llm"), ("kg_llm", "direct_llm"), ("kg_llm", "kg_rule")):
        for field in RATIO_FIELDS:
            pairs = [(case_method[(case, left)][field], case_method[(case, right)][field]) for case in sorted({key[0] for key in case_method})]
            diffs = [a - b for a, b in pairs if a is not None and b is not None]
            deltas.append({"contrast": f"{METHOD_LABELS[left]} minus {METHOD_LABELS[right]}", "metric": field, "n_paired": len(diffs), "mean_paired_difference": statistics.mean(diffs) if diffs else None})

    report_lines += [
        "",
        "## 配对分数差异",
        "",
        "正值表示左侧方法的比例分数较高；该比较是描述性汇总，不是显著性检验。",
        "",
        "| 对比 | 指标 | 配对数 | 平均差值 |",
        "|---|---|---:|---:|",
    ]
    for row in deltas:
        report_lines.append(f"| {row['contrast']} | {row['metric']} | {row['n_paired']} | {fmt(row['mean_paired_difference'])} |")
    report_lines += [
        "",
        "## 解释边界与审计限制",
        "",
        "- 评审模型只依据盲化输出、引用快照和 EvidencePackage 覆盖摘要打分；A/B/C 在评分结束后才通过独立映射表揭盲。",
        "- 这是单一模型的自动评审，且生成器与评审器都使用同一智谱模型系列，存在自我偏好和系统性误差风险。结果不能替代专业人员逐条核对原始来源。",
        "- `supported_claim_fraction` 的分母为事实性 claim 数；`citation_precision` 按每个被引用的 Evidence ID / Path ID 逐个计；无可评估项为 NA。无依据断言率以事实性 claim 总数为分母；方向错误率以含方向性表述的事实 claim 总数为分母。",
        "- 方法耗时与生成 tokens 来自原始 Direct LLM / KG 规则 / KG+LLM 运行输出；它们与下面 AI 评审自身的 API 耗时/token 分开统计。",
        "- 评审使用外部 API，证据与解释文本已按授权发送给智谱。服务方没有返回费用，不做估算。已保留成功评分记录报告的 AI 评审 token 用量为 {judge_prompt:,} prompt / {judge_completion:,} completion，平均评审延迟 {judge_latency:.1f} 秒；此前 10 次失败/重试请求没有完整记录逐次 token，故 token 数不是总账单用量。".format(
            judge_prompt=sum(int(row["ai_judge_prompt_tokens"]) for method_rows in per_method.values() for row in method_rows),
            judge_completion=sum(int(row["ai_judge_completion_tokens"]) for method_rows in per_method.values() for row in method_rows),
            judge_latency=statistics.mean(row["ai_judge_latency_seconds"] for method_rows in per_method.values() for row in method_rows),
        ),
        "- 所有分数只描述这 20 个案例的自动审阅结果，不证明药物机制正确性或临床疗效，也不能据此声称某方案被人工验证为优越。",
        "",
    ]

    case_path = AI / "kg07_ai_judge_case_scores.csv"
    case_fields = ["case", "method", "review_code", "pert_id", "drug_name", *RATIO_FIELDS,
                   "unsupported_assertion_count", "relation_direction_error_count", "factual_claim_count",
                   "directional_claim_count", "method_latency_seconds", "method_total_tokens",
                   "method_provider_cost", "ai_judge_latency_seconds", "ai_judge_prompt_tokens",
                   "ai_judge_completion_tokens", "ai_judge_request_count", "prompt_version"]
    with case_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=case_fields)
        writer.writeheader()
        for method in ("direct_llm", "kg_rule", "kg_llm"):
            for row in sorted(per_method[method], key=lambda item: int(item["case"])):
                writer.writerow({field: row.get(field) for field in case_fields})

    summary_path = AI / "kg07_ai_judge_method_summary.csv"
    with summary_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=method_fields)
        writer.writeheader()
        writer.writerows(method_summary)
    delta_path = AI / "kg07_ai_judge_paired_differences.csv"
    with delta_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["contrast", "metric", "n_paired", "mean_paired_difference"])
        writer.writeheader()
        writer.writerows(deltas)
    report_path = AI / "kg07_ai_judge_report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest.update({
        "ai_summary_status": "COMPLETE",
        "human_review_status": "HUMAN_REVIEW_PENDING; AI scores do not satisfy human-review requirement",
        "summary_csv_sha256": sha(summary_path),
        "case_scores_csv_sha256": sha(case_path),
        "paired_differences_csv_sha256": sha(delta_path),
        "report_sha256": sha(report_path),
        "usage_scope": "retained successful results only; prior failed attempts were not fully token-logged; these totals are not total billable usage",
        "attempt_ledger_completeness": "incomplete; only final retry requests were written to the current ledger",
        "previous_failed_attempts_known_from_run_output": 10,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    })
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "AI_JUDGE_SUMMARY_COMPLETE", "n_cases": 20, "n_scores": 60,
                      "methods": method_summary, "report": str(report_path.relative_to(ROOT))}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
