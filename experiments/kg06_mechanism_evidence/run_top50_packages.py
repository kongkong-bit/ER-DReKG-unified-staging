"""Fetch and persist the 50 live KG06 EvidencePackages from FastAPI."""
from __future__ import annotations

import concurrent.futures
import csv
import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT_ID = "3f18f4c1-713d-58c5-8a53-38eca5a5aaf9"
BASE_URL = os.environ.get("KG06_BASE_URL", "http://127.0.0.1:8000")
AUDIT_MANIFEST = ROOT / "experiments" / "kg06_mechanism_evidence" / "results" / "kg06_audit_manifest.json"
TOP50 = ROOT / "experiments" / "exp006_ranking_reliability" / "results" / "candidate_drugs_top50.csv"
OUT = Path(os.environ.get("KG06_PACKAGE_OUT", ROOT / "experiments" / "kg06_mechanism_evidence" / "results" / "evidence_packages"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fetch(pert_id: str, graph_build_id: str) -> dict:
    query = urllib.parse.urlencode({"graph_build_id": graph_build_id})
    path = f"/api/v1/projects/{PROJECT_ID}/kg06/evidence-package/{urllib.parse.quote(pert_id, safe='')}?{query}"
    request = urllib.request.Request(BASE_URL + path, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            if response.status != 200:
                raise RuntimeError(f"{pert_id}: API returned HTTP {response.status}")
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{pert_id}: HTTP {error.code}: {detail}") from error


def main() -> None:
    audit = json.loads(AUDIT_MANIFEST.read_text(encoding="utf-8"))
    if audit.get("status") != "PASS":
        raise RuntimeError("KG06 audit manifest is not PASS")
    graph_build_id = audit["schema"]["graph_build_id"]
    coverage_path = ROOT / "experiments" / "kg06_mechanism_evidence" / "results" / "top50_mechanism_coverage.csv"
    if sha256(coverage_path) != audit["outputs"]["top50_mechanism_coverage.csv"]:
        raise RuntimeError("KG06 coverage CSV hash no longer matches its audit manifest")
    OUT.mkdir(parents=True, exist_ok=True)
    source_rows = {row["pert_id"]: row for row in csv.DictReader(TOP50.open(encoding="utf-8-sig", newline=""))}
    coverage_rows = list(csv.DictReader(coverage_path.open(encoding="utf-8-sig", newline="")))
    pert_ids = [row["pert_id"] for row in coverage_rows]
    if len(pert_ids) != 50 or set(pert_ids) != set(source_rows):
        raise RuntimeError("Top50 input does not align exactly with KG06 coverage results")

    results: dict[str, dict] = {}
    failures: dict[str, str] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fetch, pert_id, graph_build_id): pert_id for pert_id in pert_ids}
        for future in concurrent.futures.as_completed(futures):
            pert_id = futures[future]
            try:
                package = future.result()
                if package.get("pert_id") != pert_id or package.get("graph_build_id") != graph_build_id:
                    raise RuntimeError("API package project/candidate/build did not match the request")
                if not package.get("coverage", {}).get("evidence_integrity_pass"):
                    raise RuntimeError("Package contains unverified evidence references")
                package_path = OUT / f"{pert_id}.json"
                package_path.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
                results[pert_id] = {
                    "pert_id": pert_id,
                    "rank_exp006": source_rows[pert_id].get("rank", ""),
                    "drug_name": source_rows[pert_id].get("drug_name", ""),
                    "package_id": package["package_id"],
                    "package_sha256": sha256(package_path),
                    "evidence_input_sha256": package["provenance"]["evidence_input_sha256"],
                    "candidate_mapping_status": package["candidate"]["mapping_status"],
                    "compound_id": package["candidate"]["compound_id"] or "",
                    "direct_target_path_count": package["coverage"]["direct_target_path_count"],
                    "public_pathway_path_count": package["coverage"]["public_pathway_path_count"],
                    "s1_enrichment_overlap_path_count": package["coverage"]["s1_enrichment_overlap_path_count"],
                    "s1_deg_overlap_path_count": package["coverage"]["s1_deg_overlap_path_count"],
                    "unique_evidence_count": package["coverage"]["unique_evidence_count"],
                    "verified_evidence_count": package["coverage"]["verified_evidence_count"],
                    "conflicted_path_count": package["coverage"]["conflicted_path_count"],
                    "evidence_gaps": " | ".join(package["evidence_gaps"]),
                    "package_path": package_path.relative_to(ROOT).as_posix(),
                }
            except Exception as error:  # noqa: BLE001 - preserve per-candidate failure detail
                failures[pert_id] = str(error)
            if (len(results) + len(failures)) % 5 == 0:
                print(f"completed={len(results) + len(failures)}/50 passed={len(results)} failed={len(failures)}", flush=True)

    fields = list(next(iter(results.values())).keys()) if results else ["pert_id", "error"]
    with (OUT / "top50_evidence_package_index.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for pert_id in pert_ids:
            if pert_id in results:
                writer.writerow(results[pert_id])
            else:
                writer.writerow({"pert_id": pert_id, "error": failures.get(pert_id, "missing result")})

    package_manifest = {
        "status": "PASS" if len(results) == 50 and not failures else "FAIL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_id": PROJECT_ID,
        "graph_build_id": graph_build_id,
        "kg06_audit_manifest_sha256": sha256(AUDIT_MANIFEST),
        "top50_input_sha256": sha256(TOP50),
        "package_count": len(results),
        "failed_count": len(failures),
        "failures": failures,
        "index_sha256": sha256(OUT / "top50_evidence_package_index.csv"),
        "package_sha256": {pert_id: results[pert_id]["package_sha256"] for pert_id in sorted(results)},
    }
    (OUT / "top50_evidence_package_manifest.json").write_text(json.dumps(package_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": package_manifest["status"], "package_count": len(results), "failed_count": len(failures), "output_dir": OUT.relative_to(ROOT).as_posix(), "failures": failures}, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
