"""Run an end-to-end GraphBundle/API check in the isolated test_only project.

The script copies the immutable full GSE42568 limma table into the existing
software-test project, creates or reuses linked S1/enrichment/S2/GraphBundle
runs, imports only that test project version to Neo4j, and checks its API.
It never changes source S1/S2 experiment files or starts an all-signature run.
"""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

csv.field_size_limit(min(sys.maxsize, 2_147_483_647))


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.ingestion import inspect_expression_file  # noqa: E402
from app.main import (  # noqa: E402
    app,
    build_project_graph_bundle,
    graph_build,
    run_precomputed_s1,
    run_project_pathway_enrichment,
    run_project_s2,
)
from app.models import AnalysisRun, Dataset, Project  # noqa: E402
from app.schemas import GraphBundleRequest, PrecomputedS1Request, S1EnrichmentRequest, S2RunRequest  # noqa: E402


SOURCE = ROOT / "experiments" / "s1_pathway_enrichment" / "input" / "limma_all_genes.csv"
REPORT_JSON = ROOT / "experiments" / "platform_phase_c" / "phase_e_graphbundle_e2e.json"
REPORT_MD = ROOT / "experiments" / "platform_phase_c" / "phase_e_graphbundle_e2e_report.md"
PROJECT_SLUG = "software-test-graph-isolation"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def get_or_create_s1_dataset(db, project_id: str) -> Dataset:
    source_hash = sha256(SOURCE)
    for row in db.scalars(select(Dataset).where(Dataset.project_id == project_id)):
        if row.sha256 == source_hash and row.metadata_json.get("dataset_type") == "precomputed_deg" and row.metadata_json.get("phase_e_source") == "GSE42568 full limma table":
            return row
    dataset_id = str(uuid4())
    project_upload = ROOT / "data" / "raw" / "uploads" / project_id / dataset_id
    project_upload.mkdir(parents=True, exist_ok=False)
    destination = project_upload / "data.csv"
    shutil.copy2(SOURCE, destination)
    validation = inspect_expression_file(destination, "precomputed_deg")
    relative_path = destination.relative_to(ROOT).as_posix()
    metadata = {
        **validation,
        "dataset_type": "precomputed_deg",
        "original_filename": SOURCE.name,
        "storage_path": relative_path,
        "file_bytes": destination.stat().st_size,
        "upload_validated": True,
        "phase_e_source": "GSE42568 full limma table",
        "source_sha256": source_hash,
        "test_only": True,
    }
    row = Dataset(
        dataset_id=dataset_id,
        project_id=project_id,
        source="GSE42568 derived limma result (test-only copy)",
        release="existing project S1 output; test-only workflow input",
        source_url="https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE42568",
        sha256=source_hash,
        license_status="internal_test_only; source citation retained",
        state="validation_pending",
        metadata_json=metadata,
    )
    db.add(row)
    db.commit()
    return row


def completed_run(db, project_id: str, run_type: str, predicate) -> AnalysisRun | None:
    runs = db.scalars(select(AnalysisRun).where(AnalysisRun.project_id == project_id, AnalysisRun.run_type == run_type, AnalysisRun.status == "completed").order_by(AnalysisRun.created_at.desc()))
    return next((run for run in runs if predicate(run)), None)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    if not SOURCE.is_file():
        raise FileNotFoundError(f"GSE42568 limma input missing: {SOURCE}")
    if settings.graph_source != "neo4j":
        raise RuntimeError("本端到端步骤需要 GRAPH_SOURCE=neo4j，以验证真实 Neo4j 导入")
    outcome: dict = {
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_path": SOURCE.relative_to(ROOT).as_posix(),
        "source_sha256": sha256(SOURCE),
        "test_only": True,
        "status": "running",
        "steps": {},
    }

    with SessionLocal() as db:
        project = db.scalar(select(Project).where(Project.slug == PROJECT_SLUG))
        if project is None or project.status != "test_only":
            raise RuntimeError("缺少隔离的 test_only 项目；拒绝向普通研究项目写入 smoke 运行")
        project_id = project.project_id
        dataset = get_or_create_s1_dataset(db, project_id)
        s1_run = completed_run(db, project_id, "s1_precomputed_deg", lambda run: run.parameters.get("dataset_id") == dataset.dataset_id)
        if s1_run is None:
            s1_result = run_precomputed_s1(project_id, dataset.dataset_id, PrecomputedS1Request(positive_group="Tumor", negative_group="Normal", fdr_threshold=0.05), db)
            s1_run = db.get(AnalysisRun, s1_result["analysis_run_id"])
        outcome["steps"]["s1"] = {"status": s1_run.status, "analysis_run_id": s1_run.analysis_run_id, "dataset_id": dataset.dataset_id, "tested_genes": s1_run.parameters.get("unique_genes"), "significant_genes": s1_run.parameters.get("significant_genes"), "test_only": s1_run.parameters.get("test_only"), "output_sha256": s1_run.parameters.get("output_sha256")}

        enrichment = completed_run(db, project_id, "s1_pathway_enrichment", lambda run: run.parameters.get("s1_analysis_run_id") == s1_run.analysis_run_id)
        if enrichment is None:
            result = run_project_pathway_enrichment(project_id, S1EnrichmentRequest(s1_analysis_run_id=s1_run.analysis_run_id, identifier_type="symbol", fdr_threshold=0.05), db)
            enrichment = db.get(AnalysisRun, result["analysis_run_id"])
        outcome["steps"]["enrichment"] = {"status": enrichment.status, "analysis_run_id": enrichment.analysis_run_id, "s1_analysis_run_id": enrichment.parameters.get("s1_analysis_run_id"), "mapped_universe": enrichment.parameters.get("mapped_universe"), "significant_pathway_counts": enrichment.parameters.get("significant_pathway_counts"), "test_only": enrichment.parameters.get("test_only")}

        s2 = completed_run(db, project_id, "s2_lincs", lambda run: run.parameters.get("s1_analysis_run_id") == s1_run.analysis_run_id and run.parameters.get("test_only") is True and run.parameters.get("requested_parameters", {}).get("max_signatures") == 30)
        if s2 is None:
            result = run_project_s2(project_id, S2RunRequest(s1_analysis_run_id=s1_run.analysis_run_id, identifier_type="symbol", fdr_threshold=0.05, top_n=100, cell_id="MCF7", perturbation_type="trt_cp", time="24 h", min_distil_cc_q75=0.2, max_signatures=30), db)
            s2 = db.get(AnalysisRun, result["analysis_run_id"])
        outcome["steps"]["s2"] = {"status": s2.status, "analysis_run_id": s2.analysis_run_id, "s1_analysis_run_id": s2.parameters.get("s1_analysis_run_id"), "test_only": s2.parameters.get("test_only"), "condition_count": s2.parameters.get("condition_count"), "qc_summary": s2.parameters.get("qc_summary")}

        bundle = completed_run(db, project_id, "kg_graph_bundle", lambda run: run.parameters.get("s1_analysis_run_id") == s1_run.analysis_run_id and run.parameters.get("s2_analysis_run_id") == s2.analysis_run_id and run.parameters.get("enrichment_analysis_run_id") == enrichment.analysis_run_id)
        if bundle is None:
            result = build_project_graph_bundle(project_id, GraphBundleRequest(s1_analysis_run_id=s1_run.analysis_run_id, s2_analysis_run_id=s2.analysis_run_id, enrichment_analysis_run_id=enrichment.analysis_run_id), db)
            bundle = db.get(AnalysisRun, result["analysis_run_id"])
        outcome["steps"]["graph_bundle"] = {"status": bundle.status, "analysis_run_id": bundle.analysis_run_id, "bundle_dir": bundle.parameters.get("bundle_dir"), "counts": bundle.parameters.get("counts"), "test_only": bundle.parameters.get("test_only"), "mapping_policy": bundle.parameters.get("mapping_policy")}

        build = graph_build(project_id, db, bundle.analysis_run_id)
        outcome["steps"]["neo4j_graph_build"] = {"status": build.get("status"), "graph_build_id": build.get("graph_build_id"), "summary": build.get("summary"), "idempotent": build.get("idempotent")}
        bundle_dir = ROOT / bundle.parameters["bundle_dir"]
        candidate_rows = read_csv(bundle_dir / "candidate_mapping_audit.csv")
        exact_pert_ids = [row["pert_id"] for row in candidate_rows if row.get("mapping_status") == "matched_exact_inchikey"]

        api_results: dict[str, dict] = {}
        with TestClient(app) as client:
            prefix = f"/api/v1/projects/{project_id}"
            build_id = build["graph_build_id"]
            summary_response = client.get(f"{prefix}/graph/summary", params={"graph_build_id": build_id})
            assert summary_response.status_code == 200, summary_response.text
            summary_body = summary_response.json()
            assert summary_body["graph_build_id"] == build_id
            api_results["summary"] = {"status_code": summary_response.status_code, "node_count": summary_body.get("node_count"), "edge_count": summary_body.get("edge_count")}

            search_response = client.get(f"{prefix}/graph/search", params={"q": "TP53", "graph_build_id": build_id, "limit": 10})
            assert search_response.status_code == 200, search_response.text
            api_results["search"] = {"status_code": search_response.status_code, "items": search_response.json().get("items", [])}

            graph_response = client.get(f"{prefix}/graph/subgraph", params={"graph_build_id": build_id, "limit": 100, "max_depth": 2})
            assert graph_response.status_code == 200, graph_response.text
            graph_body = graph_response.json()
            assert graph_body.get("graph_build_id") == build_id and len(graph_body.get("nodes", [])) <= 100
            api_results["subgraph"] = {"status_code": graph_response.status_code, "node_count": len(graph_body.get("nodes", [])), "edge_count": len(graph_body.get("edges", [])), "truncated": graph_body.get("truncated")}

            mechanism_body = None
            mechanism_pert_id = None
            for pert_id in exact_pert_ids:
                response = client.get(f"{prefix}/drugs/{pert_id}/mechanisms", params={"graph_build_id": build_id})
                assert response.status_code == 200, response.text
                if response.json().get("routes"):
                    mechanism_pert_id, mechanism_body = pert_id, response.json()
                    break
            api_results["mechanism"] = {"status_code": 200, "exact_inchikey_candidate_count": len(exact_pert_ids), "queried_pert_id": mechanism_pert_id, "route_count": len(mechanism_body.get("routes", [])) if mechanism_body else 0, "route_types": sorted({route["route_type"] for route in mechanism_body.get("routes", [])}) if mechanism_body else []}

            edge_rows = read_csv(bundle_dir / "subgraph_edges.csv")
            edge = next((row for row in edge_rows if row.get("label") == "PROJECT-REFERENCES_DRUG"), None)
            if edge:
                evidence_id = hashlib.sha256(f"{edge['from']}|{edge['label']}|{edge['to']}|{edge['source_release']}".encode()).hexdigest()
                evidence_response = client.get(f"/api/v1/evidence/{evidence_id}", params={"graph_build_id": build_id})
                assert evidence_response.status_code == 200, evidence_response.text
                api_results["evidence"] = {"status_code": evidence_response.status_code, "source_release": evidence_response.json().get("source_release"), "evidence_id": evidence_id}
            else:
                api_results["evidence"] = {"status": "no_candidate_reference_edge"}

            cross_project = client.get(f"/api/v1/projects/3f18f4c1-713d-58c5-8a53-38eca5a5aaf9/graph/summary", params={"graph_build_id": build_id})
            assert cross_project.status_code == 404
            api_results["cross_project_graph_build_filter"] = {"status_code": cross_project.status_code}
        outcome["steps"]["fastapi_queries"] = api_results

    outcome["status"] = "completed"
    outcome["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    REPORT_JSON.write_text(json.dumps(outcome, ensure_ascii=False, indent=2), encoding="utf-8")
    report = [
        "# Phase E GraphBundle 真实数据端到端验收报告",
        "",
        f"运行时间：{outcome['finished_at_utc']}",
        "",
        "本报告来自 PostgreSQL、GSE42568 全量 limma 结果、真实 LINCS MCF7 Level 5 子集、OptimusKG 3.2、Neo4j 及 FastAPI 的实际运行。所有本次新增 AnalysisRun 均位于 `test_only` 项目；S2 仅限 30 条 Signature，不构成正式药物排名。原始 S1/S2 输入文件保持只读。",
        "",
        "## 各阶段运行 ID 与结果",
        "",
    ]
    for step, detail in outcome["steps"].items():
        report.extend([f"### {step}", "", "```json", json.dumps(detail, ensure_ascii=False, indent=2), "```", ""])
    report.extend(["## 解释边界", "", "GraphBundle 和 API 路径只表示有来源记录的数据库关系与项目表达/富集证据交集，不证明因果、治疗效果或 ER 阳性特异性机制。Neo4j 中公共实体按稳定 ID 复用，项目关系按 GraphBuild ID 隔离。", ""])
    REPORT_MD.write_text("\n".join(report), encoding="utf-8")
    print(json.dumps({"status": outcome["status"], "project_id": project_id, "source_sha256": outcome["source_sha256"], "steps": {key: value.get("status", "completed") for key, value in outcome["steps"].items()}, "report": REPORT_MD.relative_to(ROOT).as_posix()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
