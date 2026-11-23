"""Recompute saved KG07 citation-status flags without any API call."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app.kg07 import _retained_citations_verified, _compact_package  # noqa: E402

OUT = ROOT / "experiments" / "kg07_mechanism_interpretation"
PKG = ROOT / "experiments" / "kg06_mechanism_evidence" / "results" / "evidence_packages_v2"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def update_output(path: Path, package: dict) -> dict:
    result = json.loads(path.read_text(encoding="utf-8"))
    _, evidence_ids, path_ids = _compact_package(package)
    mode = result.get("mode", "")
    result["citation_reference_validation_pass"] = _retained_citations_verified(result.get("explanation", {}), evidence_ids, path_ids, mode)
    result["citation_reference_status"] = "retained_claims_cited_ids_verified" if result["citation_reference_validation_pass"] else "no_or_invalid_retained_claim_citations"
    result["citation_validation_pass"] = not result.get("citation_validation_issues") and mode == "kg_llm"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def rewrite_csv(path: Path, rows: list[dict]) -> None:
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    eval_dir = OUT / "evaluation"
    eval_csv = eval_dir / "kg07_evaluation_cases.csv"
    eval_rows = list(csv.DictReader(eval_csv.open(encoding="utf-8-sig", newline="")))
    for row in eval_rows:
        package = json.loads((PKG / f"{row['pert_id']}.json").read_text(encoding="utf-8"))
        for mode in ("direct_llm", "kg_llm"):
            output_path = ROOT / row[f"{mode}_output"]
            result = update_output(output_path, package)
            row[f"{mode}_citation_reference_validation_pass"] = str(bool(result["citation_reference_validation_pass"])).lower()
            row[f"{mode}_citation_validation_pass"] = str(bool(result["citation_validation_pass"])).lower()
            row[f"{mode}_citation_issues"] = len(result.get("citation_validation_issues", []))
            row[f"{mode}_output_sha256"] = sha(output_path)
    rewrite_csv(eval_csv, eval_rows)
    eval_manifest_path = eval_dir / "kg07_evaluation_manifest.json"
    eval_manifest = json.loads(eval_manifest_path.read_text(encoding="utf-8"))
    eval_manifest["output_csv_sha256"] = sha(eval_csv)
    eval_manifest["citation_flags_recomputed_locally"] = True
    eval_manifest_path.write_text(json.dumps(eval_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    top_dir = OUT / "top50_llm"
    top_csv = top_dir / "kg07_top50_llm_results.csv"
    top_rows = list(csv.DictReader(top_csv.open(encoding="utf-8-sig", newline="")))
    for row in top_rows:
        package = json.loads((PKG / f"{row['pert_id']}.json").read_text(encoding="utf-8"))
        output_path = top_dir / f"{row['pert_id']}.json"
        result = update_output(output_path, package)
        row["citation_reference_validation_pass"] = str(bool(result["citation_reference_validation_pass"])).lower()
        row["citation_validation_pass"] = str(bool(result["citation_validation_pass"])).lower()
        row["citation_validation_issues"] = len(result.get("citation_validation_issues", []))
        row["output_sha256"] = sha(output_path)
    rewrite_csv(top_csv, top_rows)
    top_manifest_path = top_dir / "kg07_top50_llm_manifest.json"
    top_manifest = json.loads(top_manifest_path.read_text(encoding="utf-8"))
    top_manifest["results_csv_sha256"] = sha(top_csv)
    top_manifest["citation_flags_recomputed_locally"] = True
    top_manifest_path.write_text(json.dumps(top_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "status": "REVALIDATED_WITHOUT_API_CALLS",
        "evaluation_cases": len(eval_rows),
        "top50_cases": len(top_rows),
        "top50_retained_reference_pass": sum(row.get("citation_reference_validation_pass") == "true" for row in top_rows),
        "top50_strict_validation_pass": sum(row.get("citation_validation_pass") == "true" for row in top_rows),
        "top50_original_uncached_calls_preserved": top_manifest.get("n_uncached_calls"),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
