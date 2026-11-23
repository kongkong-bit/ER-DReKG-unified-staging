import copy
import hashlib
import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.models import AnalysisRun, Project
from tools.register_analysis_run import (
    load_and_validate_registration,
    register_analysis_run,
    _assert_safe_apply_target,
)


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _registration_fixture(tmp_path):
    project_id = "3f18f4c1-713d-58c5-8a53-38eca5a5aaf9"
    run_id = "ANALYSIS_RUN:KG_GRAPH_BUNDLE:test-registration"
    bundle_dir = tmp_path / "data" / "processed" / "projects" / project_id / "graph_bundle" / "runs" / "test"
    bundle_dir.mkdir(parents=True)
    output = bundle_dir / "evidence_records.csv"
    output.write_text("evidence_id\nE1\n", encoding="utf-8")
    output_hashes = {output.name: _sha256(output)}
    bundle_manifest = {"status": "validated", "project_id": project_id, "analysis_run_id": run_id}
    bundle_manifest_path = bundle_dir / "bundle_manifest.json"
    bundle_manifest_path.write_text(json.dumps(bundle_manifest), encoding="utf-8")
    run_manifest = {
        "analysis_run_id": run_id, "project_id": project_id, "run_type": "kg_graph_bundle", "status": "completed",
    }
    run_manifest_path = bundle_dir / "analysis_run_manifest.json"
    run_manifest_path.write_text(json.dumps(run_manifest), encoding="utf-8")
    manifest_hash = _sha256(bundle_manifest_path)
    run_manifest_hash = _sha256(run_manifest_path)
    checksums = {
        output.name: output_hashes[output.name],
        "bundle_manifest.json": manifest_hash,
        "analysis_run_manifest.json": run_manifest_hash,
    }
    (bundle_dir / "bundle_checksums.json").write_text(json.dumps(checksums), encoding="utf-8")
    registration = {
        "analysis_run_id": run_id,
        "project_id": project_id,
        "run_type": "kg_graph_bundle",
        "status": "completed",
        "parameters": {
            "bundle_dir": bundle_dir.relative_to(tmp_path).as_posix(),
            "manifest_sha256": manifest_hash,
            "analysis_run_manifest_sha256": run_manifest_hash,
            "output_hashes": output_hashes,
        },
        "software_versions": {"pipeline": "test"},
        "input_hashes": {"source": "a" * 64},
    }
    registration_path = tmp_path / "analysis_run_registration.json"
    registration_path.write_text(json.dumps(registration), encoding="utf-8")
    return registration_path, registration


def test_registration_validates_bundle_hashes_and_project_scope(tmp_path):
    registration_path, _ = _registration_fixture(tmp_path)
    registration = load_and_validate_registration(registration_path, tmp_path)
    assert registration["run_type"] == "kg_graph_bundle"

    output = tmp_path / registration["parameters"]["bundle_dir"] / "evidence_records.csv"
    output.write_text("modified", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256"):
        load_and_validate_registration(registration_path, tmp_path)


def test_analysis_run_registration_is_dry_by_default_and_idempotent(tmp_path):
    _, registration = _registration_fixture(tmp_path)
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(Project(
            project_id=registration["project_id"], slug="register-test", name="registration test", disease_id="MONDO:0007254",
        ))
        session.commit()
        assert register_analysis_run(session, registration) == "validated_dry_run"
        assert session.get(AnalysisRun, registration["analysis_run_id"]) is None
        assert register_analysis_run(session, registration, apply=True) == "registered"
        assert register_analysis_run(session, registration, apply=True) == "already_registered"
        conflict = copy.deepcopy(registration)
        conflict["software_versions"]["pipeline"] = "different"
        with pytest.raises(ValueError, match="内容不同"):
            register_analysis_run(session, conflict, apply=True)
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_apply_requires_postgres_and_explicit_nonlocal_override(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "database_url", "sqlite:///./test.db")
    with pytest.raises(ValueError, match="仅允许 PostgreSQL"):
        _assert_safe_apply_target()
    monkeypatch.setattr(settings, "database_url", "postgresql+psycopg://user:secret@db.example/diseasegraph")
    with pytest.raises(ValueError, match="非本机"):
        _assert_safe_apply_target()
    _assert_safe_apply_target(allow_nonlocal=True)
