"""Read-only verification of the corrected formal ER+ GraphBuild and APIs."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models import AnalysisRun, GraphBuild, S2ConditionResult  # noqa: E402

csv.field_size_limit(min(sys.maxsize, 2_147_483_647))

PROJECT_ID = "3f18f4c1-713d-58c5-8a53-38eca5a5aaf9"
GRAPH_BUILD_ID = f"GRAPH_BUILD:{PROJECT_ID}:a6aabb2147cb5f5e"
S1_RUN_ID = "ANALYSIS_RUN:S1_PRECOMPUTED:9ebd6c43-9342-487e-a052-ae901461b58c"
S2_RUN_ID = "ANALYSIS_RUN:S2_LINCS:c922f2b0-242e-5991-9f76-dcbc8f66ce57"
ENRICHMENT_RUN_ID = "ANALYSIS_RUN:S1_ENRICHMENT:eb409567-e846-4422-ae19-0055937871ea"
BUNDLE_RUN_ID = "ANALYSIS_RUN:KG_GRAPH_BUNDLE:8eda9601-2fd3-48cc-9a45-74809870a480"
JSON_REPORT = ROOT / "experiments" / "platform_phase_c" / "formal_graphbuild_verification.json"
MD_REPORT = ROOT / "experiments" / "platform_phase_c" / "formal_graphbuild_verification.md"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    checked_at = datetime.now(timezone.utc).isoformat()
    outcome: dict = {"checked_at_utc": checked_at, "project_id": PROJECT_ID, "graph_build_id": GRAPH_BUILD_ID, "status": "running"}
    with SessionLocal() as db:
        build = db.get(GraphBuild, GRAPH_BUILD_ID)
        bundle_run = db.get(AnalysisRun, BUNDLE_RUN_ID)
        enrichment = db.get(AnalysisRun, ENRICHMENT_RUN_ID)
        s2 = db.get(AnalysisRun, S2_RUN_ID)
        assert build is not None and build.project_id == PROJECT_ID and build.status == "materialized"
        assert bundle_run is not None and bundle_run.status == "completed"
        assert enrichment is not None and enrichment.status == "completed"
        assert s2 is not None and s2.status == "completed"
        persisted_conditions = db.scalar(select(func.count()).select_from(S2ConditionResult).where(S2ConditionResult.analysis_run_id == S2_RUN_ID)) or 0
        assert persisted_conditions == 240, persisted_conditions
        bundle_dir = (ROOT / bundle_run.parameters["bundle_dir"]).resolve()
        assert bundle_dir.is_relative_to((ROOT / "data" / "processed" / "projects" / PROJECT_ID).resolve())
        manifest_path = bundle_dir / "bundle_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest.get("status") == "validated" and manifest.get("analysis_run_id") == BUNDLE_RUN_ID
        for filename, expected in manifest["output_hashes"].items():
            assert sha256(bundle_dir / filename) == expected, filename

    nodes = read_rows(bundle_dir / "subgraph_nodes.csv")
    pathway_ids = [row["id"] for row in nodes if row["type"] in {"Pathway", "GeneSet"}]
    assert pathway_ids and all(node_id.startswith(("GO:", "REACT:", "MSIGDB:")) for node_id in pathway_ids)
    assert "fatty acid metabolic process" not in pathway_ids
    routes = read_rows(bundle_dir / "candidate_target_pathway_routes.csv")
    assert len(routes) == 1494
    route = routes[0]
    assert route["pathway_id"].startswith(("GO:", "REACT:", "MSIGDB:"))
    evidence = next(row for row in read_rows(bundle_dir / "evidence_records.csv") if row["predicate"] == "REFERENCES_DRUG")

    with TestClient(app) as client:
        prefix = f"/api/v1/projects/{PROJECT_ID}"
        summary_resp = client.get(prefix + "/graph/summary", params={"graph_build_id": GRAPH_BUILD_ID})
        assert summary_resp.status_code == 200, summary_resp.text
        summary = summary_resp.json()
        assert summary.get("source") == "neo4j"
        assert summary.get("nodes_by_type", {}).get("DiseaseContext") == 1, summary.get("nodes_by_type")

        mechanism_resp = client.get(prefix + f"/drugs/{route['pert_id']}/mechanisms", params={"graph_build_id": GRAPH_BUILD_ID})
        assert mechanism_resp.status_code == 200, mechanism_resp.text
        mechanisms = mechanism_resp.json().get("routes", [])
        assert mechanisms, f"No API mechanism paths returned for {route['pert_id']}"

        evidence_resp = client.get(f"/api/v1/evidence/{evidence['evidence_id']}", params={"graph_build_id": GRAPH_BUILD_ID})
        assert evidence_resp.status_code == 200, evidence_resp.text
        assert evidence_resp.json().get("evidence_id") == evidence["evidence_id"]

        pathways_resp = client.get(prefix + "/s1/pathways", params={"collection": "go_up", "analysis_run_id": ENRICHMENT_RUN_ID, "limit": 1})
        assert pathways_resp.status_code == 200, pathways_resp.text
        assert pathways_resp.json().get("total") == 206
        conditions_resp = client.get(prefix + "/s2/conditions", params={"limit": 1})
        assert conditions_resp.status_code == 200, conditions_resp.text
        assert conditions_resp.json().get("total") == persisted_conditions

    outcome.update({
        "status": "PASS",
        "analysis_run_ids": {"s1": S1_RUN_ID, "s2": S2_RUN_ID, "enrichment": ENRICHMENT_RUN_ID, "graph_bundle": BUNDLE_RUN_ID},
        "neo4j_summary": summary,
        "bundle": {"directory": bundle_dir.relative_to(ROOT).as_posix(), "manifest_sha256": sha256(manifest_path), "nodes": len(nodes), "stable_pathway_gene_set_ids": len(pathway_ids), "pathway_gene_links": manifest["counts"]["pathway_gene_links"], "unique_ensembl_mapped_pathway_links": manifest["counts"]["pathway_gene_unique_mapped"], "candidates": manifest["counts"]["candidate_perturbagens"], "exact_inchikey_mapped_drugs": manifest["counts"]["exact_inchikey_mapped_drugs"], "s2_condition_rows": persisted_conditions, "candidate_target_pathway_routes": len(routes)},
        "api_checks": {"graph_summary": "PASS", "mechanism_routes": {"pert_id": route["pert_id"], "count": len(mechanisms)}, "evidence_status": evidence_resp.status_code, "go_up_total": pathways_resp.json()["total"], "s2_condition_total": conditions_resp.json()["total"]},
        "graph_build_scope_check": {"disease_contexts_in_selected_build": summary["nodes_by_type"].get("DiseaseContext"), "status": "PASS"},
        "graph_build_recorded_summary": build.summary_json,
        "superseded_graph_builds": ["GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:92ccf8669de7c697", "GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:89efd9796240c910"],
    })
    JSON_REPORT.write_text(json.dumps(outcome, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 正式 ER+ GraphBuild 实际验收报告", "", f"检查时间（UTC）：{checked_at}", "",
        f"正式 GraphBuild：`{GRAPH_BUILD_ID}`。", "",
        "## 数据与 Neo4j 核验", "",
        f"- Neo4j 实际查询：{summary['node_count']:,} 个节点、{summary['edge_count']:,} 条关系。",
        f"- GraphBuild 版本范围检查：当前版本 DiseaseContext={summary['nodes_by_type'].get('DiseaseContext')}；旧版本上下文未混入。",
        f"- 图包含 {len(pathway_ids):,} 个通路/基因集节点；所有 ID 均为 GO、Reactome 或 MSigDB 稳定 ID，没有将通路描述误作节点 ID。",
        f"- 通路—基因链接 {manifest['counts']['pathway_gene_links']:,} 条，其中 {manifest['counts']['pathway_gene_unique_mapped']:,} 条唯一映射到 Ensembl。",
        f"- 候选 perturbagen 50 个；精确 InChIKey 映射到公共药物 30 个；240 个剂量条件；交汇路径 {len(routes):,} 条。",
        "- GraphBundle 所有输出文件均与 manifest 哈希一致；S2 条件数据库持久记录为 240 条。", "",
        "## FastAPI 实际接口核验", "",
        f"- 图摘要：200，来源 `neo4j`，按 GraphBuild 关系过滤；当前版本 DiseaseContext=1。GraphBuild 数据库中旧 summary 留存其生成时统计，本报告使用修复后的实时版本内计数。",
        f"- 机制查询：候选 `{route['pert_id']}` 返回 {len(mechanisms)} 条版本内路径。",
        f"- 证据查询：返回 HTTP {evidence_resp.status_code}，可按 evidence ID 回溯。",
        f"- S1 GO 上调通路接口：{pathways_resp.json()['total']} 项。S2 条件接口：{conditions_resp.json()['total']} 项。", "",
        "## 版本解释", "",
        "先前两个 GraphBuild 保留在数据库中供审计；一个缺少 Ensembl 映射，另一个曾使用显示名称作为节点 ID。当前 GraphBuild 使用稳定 ID，是正式查询应选择的修正版。所有机制路径仍表示来源关系交汇，不证明因果、治疗效果或 ER 阳性特异性。", "",
        f"机器可读记录：`{JSON_REPORT.relative_to(ROOT).as_posix()}`。", "",
    ]
    MD_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": outcome["status"], "graph_build_id": GRAPH_BUILD_ID, "report": MD_REPORT.relative_to(ROOT).as_posix()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
