"""Remove one GraphBuild's Neo4j relationships and PostgreSQL evidence snapshot."""
from __future__ import annotations

import argparse
import json
from urllib.parse import urlparse

from app.core.config import settings
from app.db import SessionLocal
from app.models import DiseaseContext, EvidenceRecord, GraphBuild
from tools.register_analysis_run import LOCAL_HOSTS, _assert_safe_apply_target


COUNT_QUERY = """
MATCH ()-[r]->()
WHERE $graph_build_id IN coalesce(r.graph_build_ids, [])
  AND r.id ENDS WITH $relationship_id_suffix
RETURN count(r) AS relationship_count
"""

DELETE_ONLY_MEMBER_QUERY = """
MATCH ()-[r]->()
WHERE $graph_build_id IN coalesce(r.graph_build_ids, [])
  AND r.id ENDS WITH $relationship_id_suffix
  AND size(coalesce(r.graph_build_ids, [])) <= 1
DELETE r
"""

DETACH_MEMBERSHIP_QUERY = """
MATCH ()-[r]->()
WHERE $graph_build_id IN coalesce(r.graph_build_ids, [])
  AND r.id ENDS WITH $relationship_id_suffix
  AND size(coalesce(r.graph_build_ids, [])) > 1
SET r.graph_build_ids = [member IN r.graph_build_ids WHERE member <> $graph_build_id]
RETURN count(r) AS updated_count
"""


def relationship_counts(session, graph_build_id: str) -> int:
    suffix = f"|{graph_build_id}"
    result = session.run(COUNT_QUERY, graph_build_id=graph_build_id, relationship_id_suffix=suffix).single()
    return int(result["relationship_count"])


def remove_build_relationships(session, graph_build_id: str) -> dict[str, int]:
    """Delete only relationships owned by this GraphBuild; keep shared nodes."""
    suffix = f"|{graph_build_id}"
    deleted_summary = session.run(
        DELETE_ONLY_MEMBER_QUERY, graph_build_id=graph_build_id, relationship_id_suffix=suffix,
    ).consume()
    updated = session.run(
        DETACH_MEMBERSHIP_QUERY, graph_build_id=graph_build_id, relationship_id_suffix=suffix,
    ).single()
    return {
        "deleted_relationships": int(deleted_summary.counters.relationships_deleted),
        "updated_shared_relationships": int(updated["updated_count"]),
    }


def delete_postgres_snapshot(session, graph_build_id: str) -> dict[str, int]:
    """Delete only the selected GraphBuild and its version-scoped SQL evidence."""
    current = session.get(GraphBuild, graph_build_id)
    if current is None:
        raise ValueError(f"PostgreSQL 中没有 GraphBuild：{graph_build_id}")
    evidence_count = session.query(EvidenceRecord).filter_by(graph_build_id=graph_build_id).delete(synchronize_session=False)
    context_count = session.query(DiseaseContext).filter_by(graph_build_id=graph_build_id).delete(synchronize_session=False)
    session.delete(current)
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {"deleted_evidence_records": int(evidence_count), "deleted_disease_contexts": int(context_count)}


def _assert_safe_neo4j_target(allow_nonlocal: bool = False) -> None:
    parsed = urlparse(settings.neo4j_uri)
    if parsed.hostname not in LOCAL_HOSTS and not allow_nonlocal:
        raise ValueError("目标 Neo4j 非本机；确认备份后需显式增加 --allow-nonlocal")


def _get_build_and_counts(graph_build_id: str) -> tuple[GraphBuild, dict[str, int]]:
    with SessionLocal() as session:
        build = session.get(GraphBuild, graph_build_id)
        if build is None:
            raise ValueError(f"PostgreSQL 中没有 GraphBuild：{graph_build_id}")
        if build.graph_source != "neo4j" or build.summary_json.get("neo4j_membership") != "registered":
            raise ValueError("只允许回滚已登记 Neo4j 关系的 GraphBuild")
        counts = {
            "evidence_records": session.query(EvidenceRecord).filter_by(graph_build_id=graph_build_id).count(),
            "disease_contexts": session.query(DiseaseContext).filter_by(graph_build_id=graph_build_id).count(),
        }
        return build, counts


def rollback_graph_build(graph_build_id: str, apply: bool = False) -> dict[str, object]:
    """Preview or apply the scoped Neo4j and PostgreSQL rollback."""
    build, sql_counts = _get_build_and_counts(graph_build_id)
    from neo4j import GraphDatabase

    with GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)) as driver:
        with driver.session(database=settings.neo4j_database) as neo_session:
            relationship_count = relationship_counts(neo_session, graph_build_id)
            if not apply:
                return {
                    "result": "dry_run",
                    "graph_build_id": graph_build_id,
                    "project_id": build.project_id,
                    "neo4j_relationships": relationship_count,
                    **sql_counts,
                    "shared_nodes_deleted": 0,
                }

            neo_result = neo_session.execute_write(remove_build_relationships, graph_build_id)

    with SessionLocal() as session:
        try:
            sql_deleted = delete_postgres_snapshot(session, graph_build_id)
        except ValueError as error:
            raise ValueError("Neo4j 关系已处理，但 PostgreSQL GraphBuild 在回滚期间消失；请审计并重试") from error
    return {
        "result": "rolled_back",
        "graph_build_id": graph_build_id,
        "project_id": build.project_id,
        "neo4j_relationships_before": relationship_count,
        **neo_result,
        **sql_deleted,
        "shared_nodes_deleted": 0,
        "analysis_run_preserved": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph-build-id", required=True)
    parser.add_argument("--apply", action="store_true", help="执行删除；默认仅预览")
    parser.add_argument("--confirm-graph-build-id", help="--apply 时必须再次精确提供同一 ID")
    parser.add_argument("--allow-nonlocal", action="store_true", help="允许非本机数据库，需先完成备份")
    args = parser.parse_args()
    if args.apply:
        if args.confirm_graph_build_id != args.graph_build_id:
            parser.error("--apply 必须提供与 --graph-build-id 完全相同的 --confirm-graph-build-id")
        _assert_safe_apply_target(args.allow_nonlocal)
        _assert_safe_neo4j_target(args.allow_nonlocal)
    result = rollback_graph_build(args.graph_build_id, apply=args.apply)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
