import pytest

from tools.rollback_graph_build import (
    COUNT_QUERY,
    DELETE_ONLY_MEMBER_QUERY,
    DETACH_MEMBERSHIP_QUERY,
    _assert_safe_neo4j_target,
    delete_postgres_snapshot,
    relationship_counts,
    remove_build_relationships,
)


class _Result:
    def __init__(self, value):
        self.value = value

    def single(self):
        return self.value

    def consume(self):
        return self.value


class _Summary:
    def __init__(self, relationships_deleted):
        self.counters = type("Counters", (), {"relationships_deleted": relationships_deleted})()


class _FakeNeo4jSession:
    def __init__(self):
        self.calls = []

    def run(self, query, **params):
        self.calls.append((query, params))
        if query == COUNT_QUERY:
            return _Result({"relationship_count": 12})
        if query == DELETE_ONLY_MEMBER_QUERY:
            return _Result(_Summary(10))
        if query == DETACH_MEMBERSHIP_QUERY:
            return _Result({"updated_count": 2})
        raise AssertionError("unexpected query")


def test_rollback_queries_are_scoped_to_graph_build_membership():
    session = _FakeNeo4jSession()
    graph_build_id = "GRAPH_BUILD:project:abc123"

    assert relationship_counts(session, graph_build_id) == 12
    result = remove_build_relationships(session, graph_build_id)

    assert result == {"deleted_relationships": 10, "updated_shared_relationships": 2}
    assert len(session.calls) == 3
    for query, params in session.calls:
        assert "graph_build_ids" in query
        assert params["graph_build_id"] == graph_build_id
        assert params["relationship_id_suffix"] == f"|{graph_build_id}"
    assert all("DELETE r" not in query or "graph_build_ids" in query for query, _ in session.calls)


def test_nonlocal_neo4j_apply_requires_override(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "neo4j_uri", "bolt://neo4j.example:7687")
    with pytest.raises(ValueError, match="非本机"):
        _assert_safe_neo4j_target()
    _assert_safe_neo4j_target(allow_nonlocal=True)


def test_postgres_rollback_deletes_only_selected_graph_build_snapshot():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.db import Base
    from app.models import AnalysisRun, DiseaseContext, EvidenceRecord, GraphBuild, Project

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    project_id = "project-rollback-test"
    with Session(engine) as session:
        session.add(Project(project_id=project_id, slug="rollback-test", name="rollback test", disease_id="MONDO:0007254"))
        for suffix in ("one", "two"):
            run_id = f"ANALYSIS_RUN:{suffix}"
            build_id = f"GRAPH_BUILD:{suffix}"
            session.add(AnalysisRun(
                analysis_run_id=run_id, project_id=project_id, run_type="kg_graph_bundle", status="completed",
                parameters={}, software_versions={}, input_hashes={},
            ))
            session.add(GraphBuild(
                graph_build_id=build_id, project_id=project_id, analysis_run_id=run_id, build_key=suffix.ljust(64, "0"),
                status="materialized", graph_source="neo4j", input_hashes={}, summary_json={},
            ))
            session.add(EvidenceRecord(
                record_id=f"record-{suffix}", graph_build_id=build_id, project_id=project_id,
                evidence_id=f"evidence-{suffix}", source_release="test", source_record_id=suffix,
                subject_id="drug:1", predicate="TARGET", object_id="gene:1", source_assertion={},
                source_url=None, assertion_sha256=suffix.ljust(64, "0"),
            ))
            session.add(DiseaseContext(
                record_id=f"context-{suffix}", graph_build_id=build_id, project_id=project_id,
                context_id=f"context:{suffix}", disease_id="MONDO:0007254", context_label=suffix,
                context_json={}, context_sha256=suffix.ljust(64, "0"),
            ))
        session.commit()

        assert delete_postgres_snapshot(session, "GRAPH_BUILD:one") == {
            "deleted_evidence_records": 1,
            "deleted_disease_contexts": 1,
        }
        assert session.get(GraphBuild, "GRAPH_BUILD:one") is None
        assert session.get(EvidenceRecord, "record-one") is None
        assert session.get(DiseaseContext, "context-one") is None
        assert session.get(GraphBuild, "GRAPH_BUILD:two") is not None
        assert session.get(EvidenceRecord, "record-two") is not None
        assert session.get(DiseaseContext, "context-two") is not None
        assert session.get(AnalysisRun, "ANALYSIS_RUN:one") is not None
    Base.metadata.drop_all(engine)
    engine.dispose()
