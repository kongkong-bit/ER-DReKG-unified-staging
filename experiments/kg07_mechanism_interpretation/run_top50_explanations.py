"""Generate KG+LLM explanations for the Top50 after pilot/evaluation gates."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app.kg07 import interpret  # noqa: E402

PKG_DIR = ROOT / "experiments" / "kg06_mechanism_evidence" / "results" / "evidence_packages_v2"
OUT = ROOT / "experiments" / "kg07_mechanism_interpretation" / "top50_llm"
INDEX = PKG_DIR / "top50_evidence_package_index.csv"
PACKAGE_MANIFEST = PKG_DIR / "top50_evidence_package_manifest.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-external-data-transfer", action="store_true", help="confirm Top50 project EvidencePackages may be sent to the configured LLM")
    args = parser.parse_args()
    if not args.allow_external_data_transfer:
        raise SystemExit("Refusing external requests: require explicit external-data approval.")
    package_manifest = json.loads(PACKAGE_MANIFEST.read_text(encoding="utf-8"))
    index_rows = list(csv.DictReader(INDEX.open(encoding="utf-8-sig", newline="")))
    if package_manifest.get("status") != "PASS" or package_manifest.get("package_count") != 50 or len(index_rows) != 50:
        raise SystemExit("Top50 KG06 package gate is not PASS")
    if package_manifest.get("index_sha256") != sha(INDEX):
        raise SystemExit("Top50 KG06 package index hash mismatch")
    pilot_manifest_path = ROOT / "experiments" / "kg07_mechanism_interpretation" / "pilot" / "kg07_pilot_manifest.json"
    evaluation_manifest_path = ROOT / "experiments" / "kg07_mechanism_interpretation" / "evaluation" / "kg07_evaluation_manifest.json"
    for label, manifest_path, expected_cases in (("5-case LLM pilot", pilot_manifest_path, 5), ("20-case comparison", evaluation_manifest_path, 20)):
        if not manifest_path.is_file():
            raise SystemExit(f"{label} gate is missing")
        gate = json.loads(manifest_path.read_text(encoding="utf-8"))
        if gate.get("n_cases") != expected_cases or gate.get("n_errors") != 0 or gate.get("status") != "LLM_CALLS_COMPLETED_HUMAN_REVIEW_PENDING":
            raise SystemExit(f"{label} gate has not passed cleanly")
    OUT.mkdir(parents=True, exist_ok=True)
    results, errors = [], []
    started = time.perf_counter()
    for row in index_rows:
        pert_id = row["pert_id"]
        package_path = PKG_DIR / f"{pert_id}.json"
        if sha(package_path) != package_manifest["package_sha256"].get(pert_id):
            errors.append({"pert_id": pert_id, "error": "package_file_hash_mismatch"})
            continue
        package = json.loads(package_path.read_text(encoding="utf-8"))
        if package.get("provenance", {}).get("evidence_input_sha256") != row["evidence_input_sha256"]:
            errors.append({"pert_id": pert_id, "error": "evidence_input_hash_mismatch"})
            continue
        try:
            result = interpret(package, "kg_llm")
            target = OUT / f"{pert_id}.json"
            target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            results.append({"pert_id": pert_id, "drug_name": row["drug_name"], "status": result["status"], "cached": result.get("cached", False), "citation_reference_validation_pass": result.get("citation_reference_validation_pass", False), "citation_validation_pass": result.get("citation_validation_pass", False), "citation_validation_issues": len(result.get("citation_validation_issues", [])), "semantic_entailment_status": result.get("semantic_entailment_status"), "prompt_version": result["prompt_version"], "model": result["model"], "evidence_input_sha256": result["evidence_input_sha256"], "latency_seconds": result["latency_seconds"], "total_tokens": result.get("usage", {}).get("total_tokens"), "provider_cost": result.get("provider_cost"), "provider_cost_status": result.get("provider_cost_status"), "output_sha256": sha(target)})
        except Exception as error:  # preserve per-candidate failures without stopping the rest
            errors.append({"pert_id": pert_id, "error_type": type(error).__name__, "message": str(error)[:500]})
    elapsed = round(time.perf_counter() - started, 3)
    report_rows = results
    csv_path = OUT / "kg07_top50_llm_results.csv"
    if report_rows:
        with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(report_rows[0]))
            writer.writeheader()
            writer.writerows(report_rows)
    manifest = {"status": "PASS" if len(results) == 50 and not errors else "PARTIAL_OR_FAILED", "created_at_utc": datetime.now(timezone.utc).isoformat(), "project_id": package_manifest.get("project_id"), "graph_build_id": package_manifest.get("graph_build_id"), "n_candidates": 50, "n_generated": len(results), "n_errors": len(errors), "errors": errors, "external_data_sent": bool(results), "model_calls_including_cache_hits": len(results), "n_uncached_calls": sum(not row["cached"] for row in results), "elapsed_seconds": elapsed, "package_manifest_sha256": sha(PACKAGE_MANIFEST), "index_sha256": sha(INDEX), "results_csv_sha256": sha(csv_path) if csv_path.exists() else None}
    (OUT / "kg07_top50_llm_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "n_generated": len(results), "n_errors": len(errors), "n_uncached_calls": manifest["n_uncached_calls"], "api_key_recorded": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
