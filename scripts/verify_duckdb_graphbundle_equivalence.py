"""Rebuild the current formal bundle in a disposable folder and compare outputs."""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kg.scripts.build_project_graph_bundle import build_bundle  # noqa: E402

SOURCE_RUN = ROOT / "data/processed/projects/3f18f4c1-713d-58c5-8a53-38eca5a5aaf9/graph_bundle/runs/8eda9601-2fd3-48cc-9a45-74809870a480"
REPORT = ROOT / "experiments/platform_phase_c/duckdb_graphbundle_equivalence.json"
CSV_OUTPUTS = [
    "subgraph_nodes.csv",
    "subgraph_edges.csv",
    "candidate_mapping_audit.csv",
    "s1_gene_mapping_audit.csv",
    "pathway_gene_mapping_audit.csv",
    "unmatched_entities.csv",
    "relation_conflicts.csv",
    "evidence_records.csv",
    "candidate_target_pathway_routes.csv",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    started = datetime.now(timezone.utc).isoformat()
    reference_manifest = json.loads((SOURCE_RUN / "bundle_manifest.json").read_text(encoding="utf-8"))
    source_config = json.loads((SOURCE_RUN / "build_config.json").read_text(encoding="utf-8"))
    scratch_parent = ROOT / "experiments/platform_phase_c/.tmp"
    scratch_parent.mkdir(parents=True, exist_ok=True)
    scratch = scratch_parent / f"duckdb-projection-{uuid.uuid4()}"
    scratch.mkdir()
    try:
        config = {**source_config, "output_dir": str(scratch / "bundle"), "config_path": str(scratch / "build_config.json")}
        (scratch / "build_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
        rebuilt = build_bundle(config)
        hashes = {name: sha256(scratch / "bundle" / name) for name in CSV_OUTPUTS}
        matches = {
            name: hashes[name] == reference_manifest["output_hashes"].get(name)
            for name in CSV_OUTPUTS
        }
        runtime_versions = rebuilt.get("software_versions", {})
        required_versions = {"python", "duckdb", "polars", "pyarrow", "biocypher"}
        versions_complete = required_versions.issubset(runtime_versions)
        result = {
            "started_at_utc": started,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "PASS" if all(matches.values()) and rebuilt["counts"] == reference_manifest["counts"] and versions_complete else "FAIL",
            "reference_graphbundle_run_id": reference_manifest["analysis_run_id"],
            "duckdb_version": __import__("duckdb").__version__,
            "software_versions": runtime_versions,
            "software_versions_complete": versions_complete,
            "projected_node_fields": {
                "Drug": ["name", "inchi_key", "canonical_smiles", "source_ids", "synonyms", "sources"],
                "Gene": ["symbol", "name", "biotype", "xrefs", "symbol_synonyms", "obsolete_symbols", "sources"],
                "Pathway": ["name", "sources"],
            },
            "counts_equal": rebuilt["counts"] == reference_manifest["counts"],
            "counts": rebuilt["counts"],
            "csv_outputs_byte_identical": matches,
            "output_sha256": hashes,
            "temporary_output_removed": True,
        }
        REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result["status"] != "PASS":
            raise SystemExit(1)
    finally:
        resolved_scratch = scratch.resolve()
        if resolved_scratch.parent != scratch_parent.resolve() or not resolved_scratch.name.startswith("duckdb-projection-"):
            raise RuntimeError(f"Refusing to remove unexpected scratch directory: {resolved_scratch}")
        shutil.rmtree(resolved_scratch)


if __name__ == "__main__":
    main()
