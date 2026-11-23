"""Persist already materialized GraphBundle evidence into PostgreSQL by GraphBuild.

This script does not touch Neo4j. Every source file is revalidated through the
same manifest/hash gate used by the GraphBuild API before any database insert.
Run with --apply to commit the version-scoped EvidenceRecord rows.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import select

from app.db import SessionLocal
from app.main import _graph_build_inputs, _persist_graph_evidence_records, _persist_disease_contexts
from app.models import AnalysisRun, DiseaseContext, GraphBuild, Project


REPORT_DIR = ROOT / "experiments" / "platform_phase_e_evidence"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--apply", action="store_true", help="Commit evidence and disease-context rows and GraphBuild summary metadata")
    args = parser.parse_args()

    report: dict = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_id": args.project_id,
        "mode": "apply" if args.apply else "dry-run",
        "graph_builds": [],
    }
    repo_root = ROOT
    with SessionLocal() as db:
        project = db.get(Project, args.project_id)
        if project is None:
            raise SystemExit(f"Project not found: {args.project_id}")
        builds = list(db.scalars(select(GraphBuild).where(
            GraphBuild.project_id == project.project_id,
            GraphBuild.status == "materialized",
            GraphBuild.graph_source == "neo4j",
        ).order_by(GraphBuild.created_at, GraphBuild.graph_build_id)))

        for build in builds:
            run = db.get(AnalysisRun, build.analysis_run_id)
            if run is None or run.run_type != "kg_graph_bundle" or run.status != "completed":
                report["graph_builds"].append({"graph_build_id": build.graph_build_id, "status": "SKIP", "reason": "no completed GraphBundle AnalysisRun"})
                continue
            try:
                _, bundle_dir, _, input_hashes, _ = _graph_build_inputs(project, repo_root, db, run.analysis_run_id)
                evidence_sha256 = input_hashes.get("evidence_records.csv")
                if not evidence_sha256 or evidence_sha256 != build.input_hashes.get("evidence_records.csv"):
                    raise ValueError("validated evidence_records.csv hash differs from the original GraphBuild input hash")
                before = build.summary_json.get("evidence_record_count")
                if args.apply:
                    count = _persist_graph_evidence_records(db, build, Path(bundle_dir))
                    context_count = _persist_disease_contexts(db, build, Path(bundle_dir))
                    build.summary_json = {
                        **build.summary_json,
                        "evidence_record_count": count,
                        "evidence_records_sha256": evidence_sha256,
                        "evidence_records_status": "persisted",
                        "disease_context_count": context_count,
                        "disease_contexts_sha256": input_hashes.get("subgraph_nodes.csv"),
                        "disease_contexts_status": "persisted",
                    }
                    db.commit()
                else:
                    previous_limit = csv.field_size_limit()
                    csv.field_size_limit(min(sys.maxsize, 2_147_483_647))
                    try:
                        with (Path(bundle_dir) / "evidence_records.csv").open(encoding="utf-8-sig", newline="") as stream:
                            count = sum(1 for _ in csv.DictReader(stream))
                    finally:
                        csv.field_size_limit(previous_limit)
                    with (Path(bundle_dir) / "subgraph_nodes.csv").open(encoding="utf-8-sig", newline="") as stream:
                        context_count = sum(1 for row in csv.DictReader(stream) if row.get("type") == "DiseaseContext")
                report["graph_builds"].append({
                    "graph_build_id": build.graph_build_id,
                    "analysis_run_id": run.analysis_run_id,
                    "status": "PASS" if args.apply else "READY",
                    "evidence_record_count": count,
                    "previous_summary_count": before,
                    "evidence_records_sha256": evidence_sha256,
                    "disease_context_count": context_count,
                    "disease_contexts_sha256": input_hashes.get("subgraph_nodes.csv"),
                })
            except Exception as error:
                db.rollback()
                report["graph_builds"].append({"graph_build_id": build.graph_build_id, "status": "BLOCKED", "reason": str(error)})

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / "evidence_record_backfill.json"
    report["summary"] = {
        "eligible_versions": len(report["graph_builds"]),
        "passed_or_ready": sum(row["status"] in {"PASS", "READY"} for row in report["graph_builds"]),
        "blocked": sum(row["status"] == "BLOCKED" for row in report["graph_builds"]),
        "skipped": sum(row["status"] == "SKIP" for row in report["graph_builds"]),
        "total_evidence_records": sum(row.get("evidence_record_count", 0) for row in report["graph_builds"]),
        "total_disease_contexts": sum(row.get("disease_context_count", 0) for row in report["graph_builds"]),
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"report": report_path.relative_to(ROOT).as_posix(), **report["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
