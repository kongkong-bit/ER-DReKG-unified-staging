"""Verified v4 candidate ranking context for evidence-grounded KG07 runs."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from app.core.config import PROJECT_ROOT

RESULTS_DIR = PROJECT_ROOT / "experiments" / "robust_candidate_prioritization" / "results"
MANIFEST_PATH = RESULTS_DIR / "v4_manifest.json"
MECHANISM_TOP10_PATH = RESULTS_DIR / "v4_mechanism_top10.csv"


class RobustV4ArtifactError(RuntimeError):
    """The v4 result files are missing or fail their manifest checks."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _required_number(row: dict[str, str], field: str, *, integer: bool = False) -> int | float:
    value = row.get(field)
    try:
        return int(value) if integer else float(value)
    except (TypeError, ValueError):
        raise RobustV4ArtifactError(f"v4 candidate has invalid {field}") from None


def load_mechanism_candidate(pert_id: str) -> dict[str, Any] | None:
    """Return one v4 mechanism Top10 row after validating PASS manifest hashes."""
    if not MANIFEST_PATH.is_file() or not MECHANISM_TOP10_PATH.is_file():
        raise RobustV4ArtifactError("v4 mechanism Top10 artifacts are unavailable")
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise RobustV4ArtifactError("v4 manifest is unreadable") from None
    expected = (manifest.get("outputs") or {}).get(MECHANISM_TOP10_PATH.name)
    if manifest.get("status") != "PASS" or not expected:
        raise RobustV4ArtifactError("v4 manifest is not PASS or omits the mechanism Top10 output")
    output_sha256 = _sha256(MECHANISM_TOP10_PATH)
    if output_sha256 != expected:
        raise RobustV4ArtifactError("v4 mechanism Top10 hash does not match its manifest")

    try:
        with MECHANISM_TOP10_PATH.open(encoding="utf-8-sig", newline="") as stream:
            row = next((item for item in csv.DictReader(stream) if item.get("pert_id") == pert_id), None)
    except OSError:
        raise RobustV4ArtifactError("v4 mechanism Top10 output is unreadable") from None
    if row is None:
        return None

    context = {
        "protocol": manifest.get("protocol"),
        "protocol_sha256": manifest.get("spec_sha256"),
        "pert_id": pert_id,
        "drug_name": row.get("drug_name"),
        "mechanism_rank": _required_number(row, "rank_mech", integer=True),
        "rank_v4": _required_number(row, "rank_v4", integer=True),
        "S_disc": _required_number(row, "S_disc"),
        "dose_condition_count": _required_number(row, "n_dose_conditions", integer=True),
        "WTCS_dose_median": _required_number(row, "WTCS_dose_median"),
        "WTCS_negative_fraction": _required_number(row, "WTCS_neg_frac"),
        "algorithm_consensus": row.get("algorithm_consensus", "").strip().lower() == "true",
        "stability_top20": _required_number(row, "stability_top20"),
        "graph_chain_count": _required_number(row, "n_chains", integer=True),
        "er_positive_chain_count": _required_number(row, "n_er_chains", integer=True),
        "target_symbols": [value.strip() for value in (row.get("chain_targets") or "").split(";") if value.strip()],
        "manifest_sha256": _sha256(MANIFEST_PATH),
        "result_sha256": output_sha256,
    }
    context["context_sha256"] = hashlib.sha256(
        json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return context
