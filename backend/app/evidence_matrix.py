import csv
import hashlib
import json
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = PROJECT_ROOT / "experiments" / "second_round_summary" / "results"
MATRIX_PATH = RESULT_DIR / "candidate_evidence_integrated.csv"
MANIFEST_PATH = RESULT_DIR / "second_round_manifest.json"


@lru_cache(maxsize=1)
def _load_matrix() -> tuple[tuple[dict[str, str], ...], dict]:
    if not MATRIX_PATH.is_file() or not MANIFEST_PATH.is_file():
        return (), {"available": False, "reason": "integrated evidence matrix or manifest is missing"}
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    expected_sha = manifest.get("outputs", {}).get("candidate_evidence_integrated.csv")
    digest = hashlib.sha256(MATRIX_PATH.read_bytes()).hexdigest()
    if not expected_sha or digest != expected_sha:
        return (), {"available": False, "reason": "integrated evidence matrix does not match its manifest hash"}
    with MATRIX_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = tuple(dict(row) for row in csv.DictReader(handle))
    return rows, {"available": True, "built_utc": manifest.get("built_utc"), "sha256": digest, "source_experiments": [x["experiment"] for x in manifest.get("experiment_status", [])]}


def evidence_matrix(limit: int = 50, offset: int = 0) -> dict:
    rows, provenance = _load_matrix()
    page = rows[offset:offset + limit]
    return {**provenance, "total": len(rows), "offset": offset, "limit": limit, "items": list(page)}
