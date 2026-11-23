"""Read-only audit of AnalysisRun dataset and upstream-run provenance."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import select

from app.db import SessionLocal
from app.models import AnalysisRun, Dataset, GraphBuild, Project


REQUIRED_RUN_TYPES = {"s1_precomputed_deg", "s1_limma_microarray", "s1_edger_voom", "s1_pathway_enrichment", "s2_lincs", "kg_graph_bundle"}
UPSTREAM_FIELDS = ("s1_analysis_run_id", "s2_analysis_run_id", "enrichment_analysis_run_id")
OUTPUT_DIR = ROOT / "experiments" / "platform_phase_e_provenance"


def audit(project_id: str) -> dict:
    with SessionLocal() as db:
        project = db.get(Project, project_id)
        if project is None:
            raise ValueError(f"project not found: {project_id}")
        datasets = {row.dataset_id: row for row in db.scalars(select(Dataset).where(Dataset.project_id == project_id))}
        runs = list(db.scalars(select(AnalysisRun).where(AnalysisRun.project_id == project_id).order_by(AnalysisRun.created_at, AnalysisRun.analysis_run_id)))
        run_map = {row.analysis_run_id: row for row in runs}
        run_results = []
        for run in runs:
            parameters = run.parameters or {}
            software = run.software_versions or {}
            inputs = run.input_hashes or {}
            issues = []
            exempt_legacy = run.run_type == "knowledge_graph_seed_subgraph"
            if run.run_type in REQUIRED_RUN_TYPES:
                if not parameters:
                    issues.append("missing_parameters")
                if not software:
                    issues.append("missing_software_versions")
                if not inputs:
                    issues.append("missing_input_hashes")
            direct_dataset_ids = [parameters.get("dataset_id"), parameters.get("sample_metadata_dataset_id")]
            direct_dataset_ids = [value for value in direct_dataset_ids if value]
            for dataset_id in direct_dataset_ids:
                dataset = datasets.get(dataset_id)
                if dataset is None:
                    issues.append(f"dataset_not_in_project:{dataset_id}")
                elif inputs.get(dataset_id) != dataset.sha256:
                    issues.append(f"dataset_hash_not_linked:{dataset_id}")
            dependencies = {field: parameters.get(field) for field in UPSTREAM_FIELDS if parameters.get(field)}
            for field, upstream_id in dependencies.items():
                upstream = run_map.get(upstream_id)
                if upstream is None:
                    issues.append(f"upstream_run_missing_or_cross_project:{field}")
                elif upstream.status != "completed":
                    issues.append(f"upstream_run_not_completed:{field}")
            if run.run_type == "kg_graph_bundle":
                for required_field in UPSTREAM_FIELDS:
                    if not parameters.get(required_field):
                        issues.append(f"missing_graph_bundle_dependency:{required_field}")
            run_results.append({
                "analysis_run_id": run.analysis_run_id,
                "run_type": run.run_type,
                "status": run.status,
                "created_at": run.created_at.isoformat() if run.created_at else None,
                "dataset_ids": direct_dataset_ids,
                "upstream_run_ids": list(dependencies.values()),
                "input_hash_count": len(inputs),
                "software_component_count": len(software),
                "legacy_exempt": exempt_legacy,
                "provenance_status": "PASS" if not issues else "FAIL",
                "issues": issues,
            })
        builds = list(db.scalars(select(GraphBuild).where(GraphBuild.project_id == project_id)))
        build_issues = []
        for build in builds:
            run = run_map.get(build.analysis_run_id)
            if run is None:
                build_issues.append({"graph_build_id": build.graph_build_id, "issue": "analysis_run_missing_or_cross_project"})
        required = [row for row in run_results if row["run_type"] in REQUIRED_RUN_TYPES]
        return {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "project_id": project_id,
            "project_slug": project.slug,
            "dataset_count": len(datasets),
            "analysis_run_count": len(runs),
            "required_pipeline_run_count": len(required),
            "required_pipeline_runs_provenance_passed": sum(row["provenance_status"] == "PASS" for row in required),
            "required_pipeline_completed_count": sum(row["status"] == "completed" for row in required),
            "required_pipeline_failed_count": sum(row["status"] == "failed" for row in required),
            "legacy_exempt_run_count": sum(row["legacy_exempt"] for row in run_results),
            "graph_build_count": len(builds),
            "graph_build_link_issues": build_issues,
            "status": "PASS" if all(row["provenance_status"] == "PASS" for row in required) and not build_issues else "FAIL",
            "runs": run_results,
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.project_id)
    out = args.output or OUTPUT_DIR / f"{args.project_id}_run_provenance.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"provenance_status": result["status"], "analysis_runs": result["analysis_run_count"], "pipeline_runs_with_valid_provenance": result["required_pipeline_runs_provenance_passed"], "pipeline_run_count": result["required_pipeline_run_count"], "completed_pipeline_runs": result["required_pipeline_completed_count"], "failed_pipeline_runs": result["required_pipeline_failed_count"], "legacy_exempt_runs": result["legacy_exempt_run_count"], "graph_builds": result["graph_build_count"], "graph_build_link_issues": len(result["graph_build_link_issues"]), "report": out.relative_to(ROOT).as_posix() if out.is_relative_to(ROOT) else str(out)}, ensure_ascii=False))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
