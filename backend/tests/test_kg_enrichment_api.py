import os
os.environ["GRAPH_SOURCE"] = "csv"
import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.bootstrap import seed_historical_project
from app.db import Base
from app.main import top10_mechanism_report
from app.models import Project


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    seed_historical_project(session)
    yield session
    session.close(); Base.metadata.drop_all(engine); engine.dispose()


def test_enrichment_dossier_api_is_frozen_and_hash_verified(db):
    project = db.scalar(select(Project).where(Project.slug == "erpos-gse42568"))
    response = top10_mechanism_report(project.project_id, "BRD-K44227013", db)
    assert response["artifact_status"] == "validated_offline_report_artifacts"
    assert response["report"]["rank"] == 1
    assert response["report"]["pert_id"] == "BRD-K44227013"
    assert response["report"]["rule_based_dimensions"]["DirectionConsistency"]["value"] == "not_assessable_at_S1_transcript_vs_protein_activity_level"
    assert response["report"]["candidate_mechanism_paths"]
    assert response["report"]["candidate_mechanism_paths"][0]["evidence"]
    assert response["provenance"]["report_sha256"]


def test_enrichment_dossier_api_rejects_non_top10_candidate(db):
    project = db.scalar(select(Project).where(Project.slug == "erpos-gse42568"))
    with pytest.raises(HTTPException) as exc:
        top10_mechanism_report(project.project_id, "not-a-top10-drug", db)
    assert exc.value.status_code == 404


def test_enrichment_dossier_api_rejects_modified_report(db, monkeypatch):
    from app import main
    project = db.scalar(select(Project).where(Project.slug == "erpos-gse42568"))
    # Tampering with a report under the workspace is avoided; monkeypatch only
    # the hashing function to simulate a checksum mismatch at the read boundary.
    monkeypatch.setattr(main, "_hash_file", lambda path: "0" * 64)
    with pytest.raises(HTTPException) as exc:
        top10_mechanism_report(project.project_id, "BRD-K44227013", db)
    assert exc.value.status_code == 503
