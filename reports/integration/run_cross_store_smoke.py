"""Exercise the staging graph-build API against isolated PostgreSQL/Neo4j."""
from __future__ import annotations

import hashlib
import json
import csv
from pathlib import Path

from fastapi.testclient import TestClient

from app.bootstrap import seed_historical_project
from app.db import SessionLocal
from app.main import app
from app.models import AnalysisRun


ROOT = Path(__file__).resolve().parents[2]
PROJECT_ID = "3f18f4c1-713d-58c5-8a53-38eca5a5aaf9"
BUNDLE_RUN_ID = "ANALYSIS_RUN:KG_GRAPH_BUNDLE:e0421796-2aff-47e2-9228-d683eab05fa9"
S1_RUN_ID = "ANALYSIS_RUN:S1_PRECOMPUTED:9ebd6c43-9342-487e-a052-ae901461b58c"
S2_RUN_ID = "ANALYSIS_RUN:S2_LINCS:eab2f02a-2bdf-53c8-833b-fedab03070c5"
ENRICHMENT_RUN_ID = "ANALYSIS_RUN:S1_ENRICHMENT:eb409567-e846-4422-ae19-0055937871ea"
BUNDLE_DIR = ROOT / "data/processed/projects" / PROJECT_ID / "graph_bundle/runs/e0421796-2aff-47e2-9228-d683eab05fa9"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    analysis_manifest_path = BUNDLE_DIR / "analysis_run_manifest.json"
    analysis_manifest = json.loads(analysis_manifest_path.read_text(encoding="utf-8"))
    with SessionLocal() as db:
        seed_historical_project(db)
        for relative, expected_id in [
            ("data/processed/projects/" + PROJECT_ID + "/s1/9ebd6c43-9342-487e-a052-ae901461b58c/run_manifest.json", S1_RUN_ID),
            ("data/processed/projects/" + PROJECT_ID + "/s1_enrichment/eb409567-e846-4422-ae19-0055937871ea/run_manifest.json", ENRICHMENT_RUN_ID),
        ]:
            manifest = json.loads((ROOT / relative).read_text(encoding="utf-8"))
            if manifest["analysis_run_id"] != expected_id:
                raise ValueError(f"unexpected run identity in {relative}")
            if db.get(AnalysisRun, expected_id) is None:
                db.add(AnalysisRun(
                    analysis_run_id=expected_id,
                    project_id=PROJECT_ID,
                    run_type=manifest["run_type"],
                    status=manifest["status"],
                    parameters=manifest["parameters"],
                    software_versions=manifest["software_versions"],
                    input_hashes=manifest["input_hashes"],
                ))
        db.flush()
        if db.get(AnalysisRun, BUNDLE_RUN_ID) is None:
            registered = dict(analysis_manifest["parameters"])
            registered["analysis_run_manifest_sha256"] = sha256(analysis_manifest_path)
            db.add(AnalysisRun(
                analysis_run_id=BUNDLE_RUN_ID,
                project_id=PROJECT_ID,
                run_type="kg_graph_bundle",
                status="completed",
                parameters=registered,
                software_versions=analysis_manifest["software_versions"],
                input_hashes=analysis_manifest["input_hashes"],
            ))
        db.commit()

    with TestClient(app) as client:
        imported = client.post(
            f"/api/v1/projects/{PROJECT_ID}/s2/import",
            json={"analysis_run_id": S2_RUN_ID},
        )
        if imported.status_code != 200:
            raise AssertionError(f"S2 import failed: {imported.status_code} {imported.text}")
        imported_body = imported.json()
        built = client.post(
            f"/api/v1/projects/{PROJECT_ID}/graph-builds",
            params={"bundle_run_id": BUNDLE_RUN_ID},
        )
        built.raise_for_status()
        graph_build_id = built.json()["graph_build_id"]
        summary = client.get(
            f"/api/v1/projects/{PROJECT_ID}/graph/summary",
            params={"graph_build_id": graph_build_id},
        )
        summary.raise_for_status()
        counts = summary.json()
        # This acceptance run explicitly targets Neo4j. The API summary is a
        # DiseaseContext two-hop projection, not the full imported bundle.
        if counts.get("source") != "neo4j":
            raise AssertionError(f"expected Neo4j graph source; got {counts.get('source')!r}")
        if counts.get("node_count") != 12171 or counts.get("edge_count") != 44932:
            raise AssertionError(f"unexpected Neo4j two-hop graph summary counts: {counts}")
        top10 = client.get(f"/api/v1/projects/{PROJECT_ID}/top10/mechanisms")
        top10.raise_for_status()
        top10_body = top10.json()
        items = top10_body.get("items", [])
        if len(items) != 10:
            raise AssertionError(f"expected 10 Top10 rows, got {len(items)}")
        pert_id = items[0]["pert_id"]
        package_response = client.get(
            f"/api/v1/projects/{PROJECT_ID}/kg06/evidence-package/{pert_id}",
            params={"graph_build_id": graph_build_id},
        )
        if package_response.status_code != 200:
            raise AssertionError(f"KG06 Evidence Package failed: {package_response.status_code} {package_response.text}")
        evidence_package = package_response.json()
        explanation_response = client.post(
            f"/api/v1/projects/{PROJECT_ID}/kg07/interpret/{pert_id}",
            params={"graph_build_id": graph_build_id, "mode": "kg_rule"},
        )
        if explanation_response.status_code != 200:
            raise AssertionError(f"KG07 rule explanation failed: {explanation_response.status_code} {explanation_response.text}")
        explanation = explanation_response.json()
        missing_key_response = client.post(
            f"/api/v1/projects/{PROJECT_ID}/kg07/interpret/{pert_id}",
            params={"graph_build_id": graph_build_id, "mode": "kg_llm"},
        )
        if missing_key_response.status_code != 503 or "not configured" not in missing_key_response.text.lower():
            raise AssertionError(f"missing GLM key was not reported explicitly: {missing_key_response.status_code} {missing_key_response.text}")
        explanation_candidate_id = explanation.get("candidate", {}).get("candidate_id", "")
        if evidence_package.get("pert_id") != pert_id or not explanation_candidate_id.endswith(f":{pert_id}"):
            raise AssertionError(f"Top10 ID mismatch: package={evidence_package.get('pert_id')!r}, explanation_candidate={explanation.get('candidate')!r}")
        evidence_coverage = evidence_package.get("coverage", {})
        if evidence_coverage.get("candidate_present") is not True or evidence_coverage.get("s2_condition_count", 0) < 1:
            raise AssertionError(f"EvidencePackage lacks candidate/S2 provenance: {evidence_coverage}")
        acceptance_rows = []
        for item in items:
            item_pert_id = item["pert_id"]
            if item_pert_id == pert_id:
                current_package = evidence_package
                current_explanation = explanation
            else:
                current_response = client.get(
                    f"/api/v1/projects/{PROJECT_ID}/kg06/evidence-package/{item_pert_id}",
                    params={"graph_build_id": graph_build_id},
                )
                if current_response.status_code == 404:
                    acceptance_rows.append({"rank": item["rank"], "pert_id": item_pert_id, "kg06_status": "no_graph_evidence", "path_count": 0, "unique_evidence_count": 0, "s2_condition_count": 0, "kg_rule_status": "not_run", "citation_reference_validation": "not_applicable", "evidence_gaps": current_response.json().get("detail", "")})
                    continue
                if current_response.status_code != 200:
                    raise AssertionError(f"KG06 failed for {item_pert_id}: {current_response.status_code} {current_response.text}")
                current_package = current_response.json()
                current_explanation_response = client.post(
                    f"/api/v1/projects/{PROJECT_ID}/kg07/interpret/{item_pert_id}",
                    params={"graph_build_id": graph_build_id, "mode": "kg_rule"},
                )
                if current_explanation_response.status_code != 200:
                    raise AssertionError(f"KG07 rule failed for {item_pert_id}: {current_explanation_response.status_code} {current_explanation_response.text}")
                current_explanation = current_explanation_response.json()
            coverage = current_package.get("coverage", {})
            if current_package.get("pert_id") != item_pert_id or not current_explanation.get("citation_reference_validation_pass"):
                raise AssertionError(f"Top10 evidence identity/citation validation failed for {item_pert_id}")
            acceptance_rows.append({
                "rank": item["rank"], "pert_id": item_pert_id, "kg06_status": "available",
                "path_count": len(current_package.get("paths", [])),
                "unique_evidence_count": coverage.get("unique_evidence_count", 0),
                "s2_condition_count": coverage.get("s2_condition_count", 0),
                "kg_rule_status": current_explanation.get("status", "unknown"),
                "citation_reference_validation": current_explanation.get("citation_reference_validation_pass"),
                "evidence_gaps": "; ".join(current_package.get("evidence_gaps", [])),
            })
        with (ROOT / "reports/integration/08_top10_acceptance.csv").open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["rank", "pert_id", "kg06_status", "path_count", "unique_evidence_count", "s2_condition_count", "kg_rule_status", "citation_reference_validation", "evidence_gaps"])
            writer.writeheader()
            writer.writerows(acceptance_rows)
        result = {
            "status": "PASS",
            "project_id": PROJECT_ID,
            "bundle_run_id": BUNDLE_RUN_ID,
            "s2_import": imported_body,
            "graph_build_id": graph_build_id,
            "graph_summary": counts,
            "top10_count": len(items),
            "top10_kg06_available": sum(row["kg06_status"] == "available" for row in acceptance_rows),
            "top10_first_pert_id": pert_id,
            "top10_artifact_status": top10_body.get("artifact_status"),
            "evidence_package_id": evidence_package.get("package_id"),
            "path_count": len(evidence_package.get("paths", [])),
            "unique_evidence_count": evidence_coverage.get("unique_evidence_count"),
            "s2_condition_count": evidence_coverage.get("s2_condition_count"),
            "explanation_candidate_id": explanation_candidate_id,
            "explanation_status": explanation.get("status"),
            "explanation_citation_validation": explanation.get("citation_reference_validation_pass"),
            "glm_without_key_status": missing_key_response.status_code,
            "glm_without_key_message": missing_key_response.json().get("detail"),
        }
        serialized = json.dumps(result, ensure_ascii=False, indent=2)
        (ROOT / "reports/integration/cross_store_e2e.json").write_text(serialized + "\n", encoding="utf-8")
        print(serialized)


if __name__ == "__main__":
    main()
