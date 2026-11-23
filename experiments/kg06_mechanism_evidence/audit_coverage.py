"""Read-only audit of the live GraphBuild schema and ER+ Top50 evidence coverage."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from neo4j import GraphDatabase
from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import settings  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.models import AnalysisRun, DiseaseContext, EvidenceRecord, GraphBuild, Project  # noqa: E402

PROJECT_ID = "3f18f4c1-713d-58c5-8a53-38eca5a5aaf9"
OUT = ROOT / "experiments" / "kg06_mechanism_evidence"
TOP50 = ROOT / "experiments" / "exp006_ranking_reliability" / "results" / "candidate_drugs_top50.csv"
PHASE_F = ROOT / "experiments" / "phase_f_integrated_evidence" / "candidate_evidence_with_kg.csv"

SCHEMA_QUERY = """
CALL db.labels() YIELD label
RETURN collect(label) AS labels
"""
RELATIONSHIP_TYPES_QUERY = """
CALL db.relationshipTypes() YIELD relationshipType
RETURN collect(relationshipType) AS relationship_types
"""
CONSTRAINTS_QUERY = """
SHOW CONSTRAINTS YIELD name, type, entityType, labelsOrTypes, properties
RETURN name, type, entityType, labelsOrTypes, properties ORDER BY name
"""
BUILD_EDGE_PROFILE_QUERY = """
MATCH ()-[r]->()
WHERE $build_id IN coalesce(r.graph_build_ids, [])
RETURN type(r) AS relationship_type,
       count(r) AS relationship_count,
       sum(CASE WHEN size(coalesce(r.evidence_ids, [])) = 0 THEN 1 ELSE 0 END) AS missing_evidence_ids,
       sum(CASE WHEN coalesce(r.source_release, '') = '' THEN 1 ELSE 0 END) AS missing_source_release,
       sum(CASE WHEN coalesce(r.source_assertion_json, '') = '' THEN 1 ELSE 0 END) AS missing_source_assertion
ORDER BY relationship_type
"""
BUILD_NODE_PROFILE_QUERY = """
MATCH (ctx:DiseaseContext {project_slug: $project_slug})-[seed]-()
WHERE $build_id IN coalesce(seed.graph_build_ids, [])
WITH DISTINCT ctx
MATCH (ctx)-[r]-(n)
WHERE $build_id IN coalesce(r.graph_build_ids, [])
RETURN labels(n) AS labels, collect(DISTINCT keys(n)) AS property_sets,
       count(DISTINCT n) AS node_count
ORDER BY labels
"""

TARGET_PATHS_QUERY = """
UNWIND $pert_ids AS pert_id
MATCH (ctx:DiseaseContext {project_slug: $project_slug})-[has_candidate:HAS_CANDIDATE]->(c:Candidate {pert_id: pert_id})
      -[references_drug:REFERENCES_DRUG]->(d:Drug)-[target:TARGETS]->(g:Gene)
WHERE $build_id IN coalesce(has_candidate.graph_build_ids, [])
  AND $build_id IN coalesce(references_drug.graph_build_ids, [])
  AND $build_id IN coalesce(target.graph_build_ids, [])
RETURN pert_id, c.id AS candidate_id, c.mapping_status AS mapping_status,
       d.id AS drug_id, g.id AS gene_id,
       [properties(has_candidate), properties(references_drug), properties(target)] AS edge_properties,
       [type(has_candidate), type(references_drug), type(target)] AS relation_types
"""

PUBLIC_PATHS_QUERY = """
UNWIND $pert_ids AS pert_id
MATCH (ctx:DiseaseContext {project_slug: $project_slug})-[has_candidate:HAS_CANDIDATE]->(c:Candidate {pert_id: pert_id})
      -[references_drug:REFERENCES_DRUG]->(d:Drug)-[target:TARGETS]->(g:Gene)
MATCH (p)-[contains_gene:CONTAINS_GENE]->(g)
WHERE (p:Pathway OR p:GeneSet)
  AND $build_id IN coalesce(has_candidate.graph_build_ids, [])
  AND $build_id IN coalesce(references_drug.graph_build_ids, [])
  AND $build_id IN coalesce(target.graph_build_ids, [])
  AND $build_id IN coalesce(contains_gene.graph_build_ids, [])
RETURN pert_id, c.id AS candidate_id, d.id AS drug_id, g.id AS gene_id,
       p.id AS pathway_id, p.label AS pathway_label,
       [properties(has_candidate), properties(references_drug), properties(target), properties(contains_gene)] AS edge_properties,
       [type(has_candidate), type(references_drug), type(target), type(contains_gene)] AS relation_types
"""

S1_OVERLAP_PATHS_QUERY = """
UNWIND $pert_ids AS pert_id
MATCH (ctx:DiseaseContext {project_slug: $project_slug})-[has_candidate:HAS_CANDIDATE]->(c:Candidate {pert_id: pert_id})
      -[references_drug:REFERENCES_DRUG]->(d:Drug)-[target:TARGETS]->(g:Gene)
MATCH (p)-[enriched_gene:HAS_ENRICHED_GENE]->(g)
MATCH (ctx)-[enriched_pathway:HAS_ENRICHED_PATHWAY]->(p)
WHERE (p:Pathway OR p:GeneSet)
  AND $build_id IN coalesce(has_candidate.graph_build_ids, [])
  AND $build_id IN coalesce(references_drug.graph_build_ids, [])
  AND $build_id IN coalesce(target.graph_build_ids, [])
  AND $build_id IN coalesce(enriched_gene.graph_build_ids, [])
  AND $build_id IN coalesce(enriched_pathway.graph_build_ids, [])
RETURN pert_id, c.id AS candidate_id, d.id AS drug_id, g.id AS gene_id,
       p.id AS pathway_id, p.label AS pathway_label,
       [properties(has_candidate), properties(references_drug), properties(target), properties(enriched_gene), properties(enriched_pathway)] AS edge_properties,
       [type(has_candidate), type(references_drug), type(target), type(enriched_gene), type(enriched_pathway)] AS relation_types
"""

DEG_OVERLAP_PATHS_QUERY = """
UNWIND $pert_ids AS pert_id
MATCH (ctx:DiseaseContext {project_slug: $project_slug})-[has_candidate:HAS_CANDIDATE]->(c:Candidate {pert_id: pert_id})
      -[references_drug:REFERENCES_DRUG]->(d:Drug)-[target:TARGETS]->(g:Gene)
MATCH (ctx)-[deg:HAS_DEG]->(g)
WHERE $build_id IN coalesce(has_candidate.graph_build_ids, [])
  AND $build_id IN coalesce(references_drug.graph_build_ids, [])
  AND $build_id IN coalesce(target.graph_build_ids, [])
  AND $build_id IN coalesce(deg.graph_build_ids, [])
RETURN pert_id, c.id AS candidate_id, d.id AS drug_id, g.id AS gene_id,
       [properties(has_candidate), properties(references_drug), properties(target), properties(deg)] AS edge_properties,
       [type(has_candidate), type(references_drug), type(target), type(deg)] AS relation_types
"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def edge_record(props: dict, relation_type: str) -> dict:
    assertion_raw = props.get("source_assertion_json") or ""
    try:
        assertion = json.loads(assertion_raw) if assertion_raw else {}
    except json.JSONDecodeError:
        assertion = {"invalid_json": assertion_raw}
    relation_assertions = assertion.get("relation_assertions") or []
    actions = [item.get("relation") for item in relation_assertions if isinstance(item, dict) and item.get("relation")]
    analysis_assertions = assertion.get("analysis_assertions") or []
    return {
        "edge_id": props.get("id", ""),
        "relation_type": relation_type,
        "source_release": props.get("source_release", ""),
        "evidence_ids": props.get("evidence_ids") or [],
        "source_record_id": assertion.get("source_record_id", ""),
        "source_urls": assertion.get("source_urls") or assertion.get("source_url") or [],
        "relation_assertions": relation_assertions,
        "reported_actions": actions,
        "analysis_assertions": analysis_assertions,
        "relation_conflict": bool(assertion.get("relation_conflict", False)),
        "assertion": assertion,
        "assertion_json_valid": "invalid_json" not in assertion,
    }


def build_path(row: dict, route_type: str, build_id: str) -> dict:
    edges = [edge_record(props, rel) for props, rel in zip(row["edge_properties"], row["relation_types"])]
    identity = "|".join(edge["edge_id"] for edge in edges)
    path_id = hashlib.sha256(f"{build_id}|{route_type}|{identity}".encode()).hexdigest()
    return {
        "path_id": path_id,
        "route_type": route_type,
        "pert_id": row["pert_id"],
        "candidate_id": row["candidate_id"],
        "drug_id": row["drug_id"],
        "target_gene_id": row["gene_id"],
        "pathway_id": row.get("pathway_id", ""),
        "pathway_label": row.get("pathway_label", ""),
        "relation_types": row["relation_types"],
        "edges": edges,
        "evidence_ids": sorted({eid for edge in edges for eid in edge["evidence_ids"]}),
        "source_releases": sorted({edge["source_release"] for edge in edges if edge["source_release"]}),
        "relation_conflict": any(edge["relation_conflict"] for edge in edges),
    }


def main() -> None:
    started = datetime.now(timezone.utc)
    top50_rows = read_csv(TOP50)
    pert_ids = [row["pert_id"] for row in top50_rows]
    if len(pert_ids) != 50 or len(set(pert_ids)) != 50:
        raise ValueError(f"Expected 50 unique Top50 pert_id, got {len(pert_ids)} / {len(set(pert_ids))}")

    with SessionLocal() as db:
        project = db.get(Project, PROJECT_ID)
        if project is None:
            raise RuntimeError(f"Project not found: {PROJECT_ID}")
        build = db.scalar(
            select(GraphBuild)
            .where(GraphBuild.project_id == PROJECT_ID, GraphBuild.status == "materialized")
            .order_by(GraphBuild.created_at.desc())
            .limit(1)
        )
        if build is None:
            raise RuntimeError("No materialized GraphBuild for ER+ project")
        bundle_run = db.get(AnalysisRun, build.analysis_run_id)
        if bundle_run is None or bundle_run.status != "completed":
            raise RuntimeError("Latest materialized GraphBuild does not have a completed GraphBundle run")
        graph_build_id = build.graph_build_id
        bundle_dir = (ROOT / bundle_run.parameters["bundle_dir"]).resolve()
        if not bundle_dir.is_relative_to((ROOT / "data" / "processed" / "projects" / PROJECT_ID).resolve()):
            raise RuntimeError("GraphBundle path is outside the formal ER+ project")
        manifest_path = bundle_dir / "bundle_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("status") != "validated":
            raise RuntimeError("Current GraphBundle is not validated")
        evidence_db = {
            row.evidence_id: row
            for row in db.scalars(select(EvidenceRecord).where(EvidenceRecord.graph_build_id == graph_build_id))
        }

    driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    try:
        with driver.session(database=settings.neo4j_database) as session:
            labels = session.run("CALL db.labels() YIELD label RETURN collect(label) AS labels").single()["labels"]
            relationship_types = session.run(
                "CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) AS types"
            ).single()["types"]
            constraints = session.run(CONSTRAINTS_QUERY).data()
            edge_profile = session.run(BUILD_EDGE_PROFILE_QUERY, build_id=graph_build_id).data()
            node_profile = session.run(
                BUILD_NODE_PROFILE_QUERY, build_id=graph_build_id, project_slug=project.slug
            ).data()
            params = {"pert_ids": pert_ids, "project_slug": project.slug, "build_id": graph_build_id}
            target_rows = session.run(TARGET_PATHS_QUERY, **params).data()
            public_rows = session.run(PUBLIC_PATHS_QUERY, **params).data()
            s1_rows = session.run(S1_OVERLAP_PATHS_QUERY, **params).data()
            deg_rows = session.run(DEG_OVERLAP_PATHS_QUERY, **params).data()
    finally:
        driver.close()

    paths = []
    paths.extend(build_path(row, "direct_target", graph_build_id) for row in target_rows)
    paths.extend(build_path(row, "public_pathway", graph_build_id) for row in public_rows)
    paths.extend(build_path(row, "s1_enrichment_overlap", graph_build_id) for row in s1_rows)
    paths.extend(build_path(row, "s1_deg_overlap", graph_build_id) for row in deg_rows)
    for path in paths:
        all_ids = path["evidence_ids"]
        path["evidence_integrity"] = {
            "evidence_count": len(all_ids),
            "evidence_in_postgres_count": sum(eid in evidence_db for eid in all_ids),
            "missing_evidence_ids": len(all_ids) == 0,
            "missing_source_fields": any(not edge["source_release"] or not edge["source_record_id"] for edge in path["edges"]),
            "invalid_assertion_json": any(not edge["assertion_json_valid"] for edge in path["edges"]),
            "conflict": path["relation_conflict"],
        }
        for edge in path["edges"]:
            edge["evidence_records"] = [
                {
                    "evidence_id": eid,
                    "source_release": evidence_db[eid].source_release,
                    "source_record_id": evidence_db[eid].source_record_id,
                    "source_url": evidence_db[eid].source_url,
                    "assertion_sha256": evidence_db[eid].assertion_sha256,
                }
                for eid in edge["evidence_ids"]
                if eid in evidence_db
            ]

    target_pert = {row["pert_id"] for row in target_rows}
    public_pert = {row["pert_id"] for row in public_rows}
    s1_pert = {row["pert_id"] for row in s1_rows}
    deg_pert = {row["pert_id"] for row in deg_rows}
    # The live graph is authoritative for candidate and exact compound mapping.
    candidates = {}
    for row in target_rows:
        candidates[row["pert_id"]] = {"candidate_id": row["candidate_id"], "mapping_status": row["mapping_status"]}
    for route_rows in (public_rows, s1_rows, deg_rows):
        for row in route_rows:
            candidates.setdefault(row["pert_id"], {"candidate_id": row["candidate_id"], "mapping_status": "mapped"})

    # Query candidate/map-only rows so unmatched compounds and mapped compounds without targets remain visible.
    driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    try:
        with driver.session(database=settings.neo4j_database) as session:
            candidate_rows = session.run(
                """
                UNWIND $pert_ids AS pert_id
                OPTIONAL MATCH (ctx:DiseaseContext {project_slug: $project_slug})-[hc:HAS_CANDIDATE]->(c:Candidate {pert_id: pert_id})
                WHERE $build_id IN coalesce(hc.graph_build_ids, [])
                OPTIONAL MATCH (c)-[cr:REFERENCES_DRUG]->(d:Drug)
                WHERE $build_id IN coalesce(cr.graph_build_ids, [])
                RETURN pert_id, c.id AS candidate_id, c.mapping_status AS mapping_status,
                       d.id AS drug_id, size(coalesce(cr.evidence_ids, [])) AS mapping_evidence_count
                """,
                **params,
            ).data()
            all_evidence_ids = session.run(
                """
                MATCH ()-[r]->() WHERE $build_id IN coalesce(r.graph_build_ids, [])
                UNWIND coalesce(r.evidence_ids, []) AS evidence_id
                RETURN collect(DISTINCT evidence_id) AS evidence_ids
                """,
                build_id=graph_build_id,
            ).single()["evidence_ids"]
    finally:
        driver.close()

    coverage_rows = []
    for source in top50_rows:
        pert_id = source["pert_id"]
        c = next((row for row in candidate_rows if row["pert_id"] == pert_id), {})
        related_paths = [path for path in paths if path["pert_id"] == pert_id]
        unique_targets = {path["target_gene_id"] for path in related_paths if path["route_type"] == "direct_target"}
        public_path_count = sum(path["route_type"] == "public_pathway" for path in related_paths)
        s1_path_count = sum(path["route_type"] == "s1_enrichment_overlap" for path in related_paths)
        deg_path_count = sum(path["route_type"] == "s1_deg_overlap" for path in related_paths)
        route_evidence = {eid for path in related_paths for eid in path["evidence_ids"]}
        coverage_rows.append({
            "rank_exp006": source.get("rank", ""),
            "pert_id": pert_id,
            "drug_name": source.get("drug_name", ""),
            "candidate_id": c.get("candidate_id", ""),
            "mapping_status": c.get("mapping_status", "candidate_not_in_graphbuild"),
            "mapped_compound_id": c.get("drug_id", ""),
            "mapping_evidence_count": c.get("mapping_evidence_count", 0),
            "direct_target_gene_count": len(unique_targets),
            "public_pathway_route_count": public_path_count,
            "s1_enrichment_overlap_path_count": s1_path_count,
            "s1_deg_overlap_path_count": deg_path_count,
            "unique_path_evidence_count": len(route_evidence),
            "path_evidence_in_postgres_count": sum(eid in evidence_db for eid in route_evidence),
            "all_path_edges_have_evidence": all(not path["evidence_integrity"]["missing_evidence_ids"] for path in related_paths),
            "all_path_edges_have_source": all(not path["evidence_integrity"]["missing_source_fields"] for path in related_paths),
            "any_asserted_relation_conflict": any(path["relation_conflict"] for path in related_paths),
            "wtcs_B": source.get("wtcs_median_B", ""),
            "wtcs_A": source.get("wtcs_median_A", ""),
            "dose_stability": source.get("dose_stability", ""),
            "evidence_limitations": source.get("evidence_limitations", ""),
        })

    schema = {
        "audited_at_utc": started.isoformat(),
        "project_id": PROJECT_ID,
        "project_slug": project.slug,
        "graph_build_id": graph_build_id,
        "graph_bundle_run_id": build.analysis_run_id,
        "graph_bundle_manifest_sha256": sha256(manifest_path),
        "neo4j_database": settings.neo4j_database,
        "labels": sorted(labels),
        "relationship_types": sorted(relationship_types),
        "constraints": constraints,
        "build_node_profile": node_profile,
        "build_relationship_profile": edge_profile,
        "postgres_evidence_record_count": len(evidence_db),
        "neo4j_build_evidence_id_count": len(set(all_evidence_ids)),
        "neo4j_evidence_ids_missing_in_postgres": len(set(all_evidence_ids) - set(evidence_db)),
        "protein_target_label_present": "ProteinTarget" in labels,
        "evidence_record_node_label_present": "EvidenceRecord" in labels,
        "storage_note": "EvidenceRecord is persisted in PostgreSQL and also copied to Neo4j relationship properties; no EvidenceRecord node label is present.",
    }
    summary = {
        "top50_count": len(coverage_rows),
        "candidate_nodes_present": sum(bool(row["candidate_id"]) for row in coverage_rows),
        "exact_compound_mappings": sum(row["mapping_status"] == "matched_exact_inchikey" for row in coverage_rows),
        "candidates_with_direct_targets": sum(row["direct_target_gene_count"] > 0 for row in coverage_rows),
        "candidates_with_public_pathway_routes": len(public_pert),
        "candidates_with_s1_enrichment_overlap": len(s1_pert),
        "candidates_with_s1_deg_overlap": len(deg_pert),
        "direct_target_path_rows": sum(path["route_type"] == "direct_target" for path in paths),
        "public_pathway_path_rows": sum(path["route_type"] == "public_pathway" for path in paths),
        "s1_enrichment_overlap_path_rows": sum(path["route_type"] == "s1_enrichment_overlap" for path in paths),
        "s1_deg_overlap_path_rows": sum(path["route_type"] == "s1_deg_overlap" for path in paths),
        "all_neo4j_build_evidence_ids_found_in_postgres": schema["neo4j_evidence_ids_missing_in_postgres"] == 0,
        "paths_with_any_asserted_conflict": sum(path["relation_conflict"] for path in paths),
        "all_relation_rows_have_evidence_ids": all(item["missing_evidence_ids"] == 0 for item in edge_profile),
        "all_relation_rows_have_source_release": all(item["missing_source_release"] == 0 for item in edge_profile),
        "all_relation_rows_have_source_assertion": all(item["missing_source_assertion"] == 0 for item in edge_profile),
    }

    outputs = OUT / "results"
    outputs.mkdir(parents=True, exist_ok=True)
    with (outputs / "top50_mechanism_coverage.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(coverage_rows[0]))
        writer.writeheader()
        writer.writerows(coverage_rows)
    with (outputs / "kg06_mechanism_paths.jsonl").open("w", encoding="utf-8") as stream:
        for path in paths:
            stream.write(json.dumps(path, ensure_ascii=False, sort_keys=True) + "\n")
    (outputs / "neo4j_schema_audit.json").write_text(json.dumps(schema, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    audit = {
        "status": "PASS" if summary["all_neo4j_build_evidence_ids_found_in_postgres"] and summary["all_relation_rows_have_evidence_ids"] and summary["all_relation_rows_have_source_assertion"] else "FAIL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "top50_path": TOP50.relative_to(ROOT).as_posix(),
            "top50_sha256": sha256(TOP50),
            "phase_f_matrix_path": PHASE_F.relative_to(ROOT).as_posix(),
            "phase_f_matrix_sha256": sha256(PHASE_F),
            "graph_bundle_manifest_sha256": schema["graph_bundle_manifest_sha256"],
        },
        "schema": schema,
        "coverage": summary,
        "outputs": {
            "top50_mechanism_coverage.csv": sha256(outputs / "top50_mechanism_coverage.csv"),
            "kg06_mechanism_paths.jsonl": sha256(outputs / "kg06_mechanism_paths.jsonl"),
            "neo4j_schema_audit.json": sha256(outputs / "neo4j_schema_audit.json"),
        },
    }
    (outputs / "kg06_audit_manifest.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    ratio = lambda n: f"{n}/50 ({n / 50:.1%})"
    report = [
        "# KG06 机制证据覆盖审计", "", f"审计时间（UTC）：{audit['generated_at_utc']}",
        f"正式 GraphBuild：`{graph_build_id}`；GraphBundle：`{build.analysis_run_id}`。", "",
        "## Neo4j 实际 Schema", "",
        f"- 节点标签：{', '.join(schema['labels'])}。",
        f"- 关系类型：{', '.join(schema['relationship_types'])}。",
        f"- 当前 Schema 没有 `ProteinTarget` 或 `EvidenceRecord` 节点标签；靶点用 Drug→Gene 的 `TARGETS` 关系表示，EvidenceRecord 存在 PostgreSQL，并将 evidence IDs/source assertions 冗余写在关系属性中。",
        f"- GraphBuild 作用域内关系数：{sum(item['relationship_count'] for item in edge_profile):,}；没有 evidence IDs 的关系数：{sum(item['missing_evidence_ids'] for item in edge_profile):,}；缺 source release：{sum(item['missing_source_release'] for item in edge_profile):,}；缺 source assertion：{sum(item['missing_source_assertion'] for item in edge_profile):,}。",
        f"- PostgreSQL EvidenceRecord：{len(evidence_db):,}；Neo4j 当前 GraphBuild 去重 evidence ID：{len(set(all_evidence_ids)):,}；未能在 PostgreSQL 找到：{schema['neo4j_evidence_ids_missing_in_postgres']:,}。", "",
        "## Top50 覆盖", "",
        f"- Top50 候选节点：{ratio(summary['candidate_nodes_present'])}；精确化合物映射：{ratio(summary['exact_compound_mappings'])}。",
        f"- 有至少一个真实直接靶点：{ratio(summary['candidates_with_direct_targets'])}；有公共 KG pathway 路径：{ratio(summary['candidates_with_public_pathway_routes'])}。",
        f"- 有 S1 富集通路交汇：{ratio(summary['candidates_with_s1_enrichment_overlap'])}；有 S1 DEG 直接交汇：{ratio(summary['candidates_with_s1_deg_overlap'])}。",
        f"- 路径行数：直接靶点 {summary['direct_target_path_rows']:,}、公共 Pathway {summary['public_pathway_path_rows']:,}、S1 富集交汇 {summary['s1_enrichment_overlap_path_rows']:,}、S1 DEG 交汇 {summary['s1_deg_overlap_path_rows']:,}。", "",
        "## 判读边界", "",
        "Top50 来源于 Exp006，WTCS、剂量稳定性等保留为独立关联证据；本审计不把 WTCS 负值转换为疗效。OptimusKG 关系断言中的 `TARGET`、`INHIBITOR` 等仅记录来源描述；没有明确作用词的关系不推断抑制/激活。路径表示来源关系交汇，不证明因果或临床疗效。没有映射或路径的候选在 CSV 中保留为零覆盖，不补造机制。", "",
        "## 复现产物", "",
        "- `results/neo4j_schema_audit.json`：实时 Neo4j 标签、关系、约束和属性审计。",
        "- `results/top50_mechanism_coverage.csv`：逐候选覆盖率及 S2 稳定性字段。",
        "- `results/kg06_mechanism_paths.jsonl`：逐路径边属性、来源断言、作用词、冲突标记和 evidence ID。",
        "- `results/kg06_audit_manifest.json`：输入/输出 SHA-256 及验收状态。", "",
    ]
    (OUT / "reports" / "kg06_audit_report.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps({"status": audit["status"], "graph_build_id": graph_build_id, "coverage": summary, "report": "experiments/kg06_mechanism_evidence/reports/kg06_audit_report.md"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
