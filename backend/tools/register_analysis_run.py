"""Validate and idempotently register a completed GraphBundle AnalysisRun."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import SessionLocal
from app.models import AnalysisRun, Project


REPO_ROOT = Path(__file__).resolve().parents[2]
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"无法读取 JSON 文件：{path}") from error
    if not isinstance(value, dict):
        raise ValueError(f"JSON 根对象必须是 object：{path}")
    return value


def load_and_validate_registration(path: Path, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    """Load a registration template and verify its project-scoped bundle files."""
    registration = _read_json(path)
    required = {"analysis_run_id", "project_id", "run_type", "status", "parameters", "software_versions", "input_hashes"}
    if not required.issubset(registration):
        raise ValueError(f"AnalysisRun registration 缺少字段：{sorted(required - registration.keys())}")
    if registration["run_type"] != "kg_graph_bundle" or registration["status"] != "completed":
        raise ValueError("只允许登记已完成的 kg_graph_bundle AnalysisRun")
    project_id = registration["project_id"]
    parameters = registration["parameters"]
    if not isinstance(project_id, str) or not isinstance(parameters, dict):
        raise ValueError("project_id 或 parameters 类型错误")
    bundle_rel = parameters.get("bundle_dir")
    if not isinstance(bundle_rel, str):
        raise ValueError("registration 缺少 parameters.bundle_dir")
    bundle_dir = (repo_root / bundle_rel).resolve()
    expected_root = (repo_root / "data" / "processed" / "projects" / project_id).resolve()
    if not bundle_dir.is_relative_to(expected_root):
        raise ValueError("bundle_dir 越出对应 project 的 processed 数据目录")

    bundle_manifest_path = bundle_dir / "bundle_manifest.json"
    bundle_manifest = _read_json(bundle_manifest_path)
    if (_sha256(bundle_manifest_path) != parameters.get("manifest_sha256")
            or bundle_manifest.get("status") != "validated"
            or bundle_manifest.get("project_id") != project_id
            or bundle_manifest.get("analysis_run_id") != registration["analysis_run_id"]):
        raise ValueError("bundle manifest 状态、身份或 SHA-256 与 registration 不一致")

    output_hashes = parameters.get("output_hashes")
    if not isinstance(output_hashes, dict) or not output_hashes:
        raise ValueError("registration 缺少 output_hashes")
    for relative_name, expected_hash in output_hashes.items():
        output_path = (bundle_dir / relative_name).resolve()
        if not output_path.is_relative_to(bundle_dir) or not output_path.is_file() or _sha256(output_path) != expected_hash:
            raise ValueError(f"GraphBundle 输出文件缺失或 SHA-256 不匹配：{relative_name}")

    run_manifest_path = bundle_dir / "analysis_run_manifest.json"
    run_manifest = _read_json(run_manifest_path)
    if (_sha256(run_manifest_path) != parameters.get("analysis_run_manifest_sha256")
            or run_manifest.get("analysis_run_id") != registration["analysis_run_id"]
            or run_manifest.get("project_id") != project_id
            or run_manifest.get("status") != "completed"):
        raise ValueError("analysis_run_manifest 与 registration 不一致")

    checksums_path = bundle_dir / "bundle_checksums.json"
    checksums = _read_json(checksums_path)
    for relative_name, expected_hash in checksums.items():
        output_path = (bundle_dir / relative_name).resolve()
        if not output_path.is_relative_to(bundle_dir) or not output_path.is_file() or _sha256(output_path) != expected_hash:
            raise ValueError(f"bundle_checksums 校验失败：{relative_name}")
    if checksums.get("analysis_run_manifest.json") != parameters.get("analysis_run_manifest_sha256"):
        raise ValueError("bundle_checksums 未绑定 analysis_run_manifest")
    return registration


def _run_values(registration: dict[str, Any]) -> dict[str, Any]:
    return {key: registration[key] for key in (
        "analysis_run_id", "project_id", "run_type", "status", "parameters", "software_versions", "input_hashes"
    )}


def _existing_matches(run: AnalysisRun, values: dict[str, Any]) -> bool:
    return all(getattr(run, key) == value for key, value in values.items())


def register_analysis_run(session: Session, registration: dict[str, Any], apply: bool = False) -> str:
    """Check project/run conflicts and optionally persist one AnalysisRun."""
    values = _run_values(registration)
    if session.get(Project, values["project_id"]) is None:
        raise ValueError(f"目标 PostgreSQL 中没有 project_id={values['project_id']} 的项目")
    existing = session.get(AnalysisRun, values["analysis_run_id"])
    if existing is not None:
        if not _existing_matches(existing, values):
            raise ValueError("相同 analysis_run_id 已存在但内容不同；拒绝覆盖")
        return "already_registered"
    if not apply:
        return "validated_dry_run"

    session.add(AnalysisRun(**values))
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = session.get(AnalysisRun, values["analysis_run_id"])
        if existing is None or not _existing_matches(existing, values):
            raise
        return "already_registered"
    return "registered"


def _assert_safe_apply_target(allow_nonlocal: bool = False) -> None:
    parsed = urlparse(settings.database_url)
    if not parsed.scheme.startswith("postgresql"):
        raise ValueError("--apply 仅允许 PostgreSQL；SQLite 只用于自动化测试")
    if parsed.hostname not in LOCAL_HOSTS and not allow_nonlocal:
        raise ValueError("目标 PostgreSQL 非本机；确认备份后需显式增加 --allow-nonlocal")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registration", type=Path, required=True, help="analysis_run_registration.json")
    parser.add_argument("--apply", action="store_true", help="实际写入 PostgreSQL；默认只验证")
    parser.add_argument("--allow-nonlocal", action="store_true", help="允许写入非本机 PostgreSQL，需先完成备份")
    args = parser.parse_args()
    registration_path = args.registration if args.registration.is_absolute() else REPO_ROOT / args.registration
    registration = load_and_validate_registration(registration_path.resolve())
    if args.apply:
        _assert_safe_apply_target(args.allow_nonlocal)
    with SessionLocal() as session:
        result = register_analysis_run(session, registration, apply=args.apply)
    print(json.dumps({
        "result": result,
        "analysis_run_id": registration["analysis_run_id"],
        "project_id": registration["project_id"],
        "database_host": urlparse(settings.database_url).hostname,
        "written": result == "registered",
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
