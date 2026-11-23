"""Run the KG07 20-case LLM comparison after explicit external-data approval."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app.kg07 import interpret  # noqa: E402

OUT = ROOT / "experiments" / "kg07_mechanism_interpretation"
PKG_ROOT = ROOT / "experiments" / "kg06_mechanism_evidence" / "results" / "evidence_packages_v2"


def claim_count(output: dict) -> int:
    explanation = output.get("explanation", {})
    return sum(len(explanation.get(key, [])) for key in ("known_targets", "associated_pathways", "independent_validation", "mechanism_hypotheses", "insufficient_evidence"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-external-data-transfer", action="store_true", help="confirm project evidence packages may be sent to Zhipu")
    parser.add_argument("--phase", choices=("pilot", "evaluation"), default="pilot", help="pilot runs 5 real candidates; evaluation runs all 20")
    args = parser.parse_args()
    if not args.allow_external_data_transfer:
        raise SystemExit("Refusing external requests: rerun with --allow-external-data-transfer only after explicit authorization.")
    manifest = json.loads((OUT / "kg07_evaluation_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "PREPARED_EXTERNAL_LLM_PENDING_AUTHORIZATION":
        raise SystemExit("Unexpected evaluation manifest status; inspect before running.")
    cases = list(csv.DictReader((OUT / "kg07_evaluation_20_cases.csv").open(encoding="utf-8-sig", newline="")))
    if args.phase == "pilot":
        cases = cases[:5]
        run_dir = OUT / "pilot"
    else:
        run_dir = OUT / "evaluation"
    run_dir.mkdir(exist_ok=True)
    predictions = run_dir / "predictions"
    predictions.mkdir(exist_ok=True)
    rows = []
    errors = []
    for case in cases:
        package = json.loads((PKG_ROOT / f"{case['pert_id']}.json").read_text(encoding="utf-8"))
        row = {**case}
        for mode in ("direct_llm", "kg_llm"):
            try:
                result = interpret(package, mode)
                raw = json.dumps(result, ensure_ascii=False, indent=2)
                path = predictions / f"{case['case']}_{case['pert_id']}_{mode}.json"
                path.write_text(raw, encoding="utf-8")
                row[f"{mode}_status"] = result["status"]
                row[f"{mode}_latency_seconds"] = result["latency_seconds"]
                row[f"{mode}_cost"] = result.get("provider_cost") if result.get("provider_cost") is not None else "not reported"
                row[f"{mode}_prompt_tokens"] = result.get("usage", {}).get("prompt_tokens", "")
                row[f"{mode}_completion_tokens"] = result.get("usage", {}).get("completion_tokens", "")
                row[f"{mode}_total_tokens"] = result.get("usage", {}).get("total_tokens", "")
                row[f"{mode}_output"] = str(path.relative_to(ROOT)).replace("\\", "/")
                row[f"{mode}_output_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
                row[f"{mode}_claim_count"] = claim_count(result)
                row[f"{mode}_citation_issues"] = len(result.get("citation_validation_issues", []))
                row[f"{mode}_citation_validation_pass"] = result.get("citation_validation_pass", False)
            except Exception as error:  # failures remain explicit in the case table
                row[f"{mode}_status"] = "failed"
                row[f"{mode}_latency_seconds"] = ""
                row[f"{mode}_cost"] = ""
                row[f"{mode}_prompt_tokens"] = ""
                row[f"{mode}_completion_tokens"] = ""
                row[f"{mode}_total_tokens"] = ""
                row[f"{mode}_output"] = ""
                row[f"{mode}_citation_issues"] = ""
                row[f"{mode}_citation_validation_pass"] = False
                errors.append({"case": case["case"], "pert_id": case["pert_id"], "mode": mode, "error_type": type(error).__name__, "message": str(error)[:500]})
        rows.append(row)
    csv_path = run_dir / f"kg07_{args.phase}_cases.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(dict.fromkeys(key for row in rows for key in row)))
        writer.writeheader()
        writer.writerows(rows)
    result_manifest = {"status": "COMPLETED_WITH_ERRORS" if errors else "LLM_CALLS_COMPLETED_HUMAN_REVIEW_PENDING", "phase": args.phase, "created_at_utc": datetime.now(timezone.utc).isoformat(), "n_cases": len(rows), "n_model_calls_expected": len(rows)*2, "n_errors": len(errors), "model": "configured Zhipu model", "api_key_recorded": False, "errors": errors, "output_csv_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest()}
    (run_dir / f"kg07_{args.phase}_manifest.json").write_text(json.dumps(result_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": result_manifest["status"], "cases": len(rows), "errors": len(errors), "api_key_recorded": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
