"""Create an immutable project GraphBundle containing the validated Top10 regulatory overlay."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT_ID = "3f18f4c1-713d-58c5-8a53-38eca5a5aaf9"
BASE_RUN = "7e70628f-7c76-4a2e-9dd5-56004e9c8c21"
BASE = ROOT / "data/processed/projects" / PROJECT_ID / "graph_bundle/runs" / BASE_RUN
EXTENSION = ROOT / "artifacts/kg_enrichment/regulatory_extension"
RUN_ROOT = ROOT / "data/processed/projects" / PROJECT_ID / "graph_bundle/runs"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    csv.field_size_limit(min(sys.maxsize, 100_000_000))
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def package(run_id: str | None = None) -> dict[str, object]:
    if not BASE.is_dir() or not EXTENSION.is_dir():
        raise FileNotFoundError("Frozen project GraphBundle or validated regulatory extension is missing")
    extension_manifest = json.loads((EXTENSION / "bundle_manifest.json").read_text(encoding="utf-8"))
    if extension_manifest.get("status") != "offline_biocypher_validated_not_imported":
        raise ValueError("Regulatory extension is not in the expected offline-validated state")
    run_uuid = run_id or str(uuid.uuid4())
    uuid.UUID(run_uuid)
    run_key = f"ANALYSIS_RUN:KG_GRAPH_BUNDLE:{run_uuid}"
    output = RUN_ROOT / run_uuid
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing GraphBundle run: {output}")
    shutil.copytree(BASE, output)

    node_fields, base_nodes = read_csv(output / "subgraph_nodes.csv")
    _, extension_nodes = read_csv(EXTENSION / "subgraph_nodes.csv")
    base_node_by_id = {row["id"]: row for row in base_nodes}
    if len(base_node_by_id) != len(base_nodes):
        raise ValueError("Base GraphBundle has duplicate node IDs")
    new_nodes: list[dict[str, str]] = []
    reused_nodes = 0
    for row in extension_nodes:
        prior = base_node_by_id.get(row["id"])
        if prior is None:
            new_nodes.append(row)
            continue
        if prior["type"] != row["type"]:
            raise ValueError(f"Node type conflict for shared entity {row['id']}")
        # Preserve the registered bundle's canonical shared-node properties.
        reused_nodes += 1
    all_nodes = base_nodes + new_nodes
    write_csv(output / "subgraph_nodes.csv", node_fields, all_nodes)

    edge_fields, base_edges = read_csv(output / "subgraph_edges.csv")
    _, extension_edges = read_csv(EXTENSION / "subgraph_edges.csv")
    if edge_fields != ["from", "label", "to", "relation", "undirected", "source_release", "properties_json"]:
        raise ValueError(f"Unexpected base edge schema: {edge_fields}")
    if edge_fields != ["from", "label", "to", "relation", "undirected", "source_release", "properties_json"]:
        raise ValueError("Unexpected extension edge schema")
    if any(row["relation"] != "REGULATES" for row in extension_edges if json.loads(row["properties_json"]).get("source_database") in {"SIGNOR", "OmniPath"}):
        raise ValueError("A SIGNOR/OmniPath assertion is not represented by REGULATES")
    all_edges = base_edges + extension_edges
    write_csv(output / "subgraph_edges.csv", edge_fields, all_edges)

    sys.path.insert(0, str(ROOT / "kg" / "scripts"))
    from biocypher_adapter import translate_graph_rows

    _, _, biocypher_report = translate_graph_rows(all_nodes, all_edges)
    write_json(output / "biocypher_validation.json", biocypher_report)

    evidence_fields, evidence_rows = read_csv(output / "evidence_records.csv")
    existing_evidence = {row["evidence_id"] for row in evidence_rows}
    new_evidence = []
    for row in extension_edges:
        if row["relation"] != "REGULATES":
            continue
        assertion = json.loads(row["properties_json"])
        evidence_id = str(assertion.get("assertion_id") or "")
        if len(evidence_id) != 64:
            raise ValueError(f"Signed assertion lacks stable SHA-256 ID: {row['from']} -> {row['to']}")
        if evidence_id in existing_evidence:
            raise ValueError(f"Evidence ID collision with base bundle: {evidence_id}")
        existing_evidence.add(evidence_id)
        new_evidence.append({
            "evidence_id": evidence_id,
            "source_release": row["source_release"],
            "source_record_id": str(assertion.get("source_record_id") or ""),
            "subject_id": row["from"],
            "predicate": row["relation"],
            "object_id": row["to"],
            "source_assertion_json": json.dumps(assertion, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        })
    evidence_rows.extend(new_evidence)
    write_csv(output / "evidence_records.csv", evidence_fields, evidence_rows)

    shutil.copy2(EXTENSION / "biocypher_validation.json", output / "regulatory_extension_biocypher_validation.json")
    shutil.copy2(EXTENSION / "bundle_manifest.json", output / "regulatory_extension_manifest.json")
    manifest_path = output / "bundle_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["analysis_run_id"] = run_key
    manifest["status"] = "validated"
    manifest["parent_bundle_manifest_sha256"] = sha256(BASE / "bundle_manifest.json")
    manifest["regulatory_extension_manifest_sha256"] = sha256(EXTENSION / "bundle_manifest.json")
    manifest["counts"]["nodes"] = len(all_nodes)
    manifest["counts"]["edges"] = len(all_edges)
    manifest["counts"]["evidence_records"] = len(evidence_rows)
    manifest["counts"]["regulatory_assertions"] = len(new_evidence)
    manifest["counts"]["regulatory_extension_new_nodes"] = len(new_nodes)
    manifest["counts"]["regulatory_shared_nodes_reused"] = reused_nodes
    manifest["input_hashes"]["artifacts/kg_enrichment/regulatory_extension/bundle_manifest.json"] = sha256(EXTENSION / "bundle_manifest.json")
    manifest["input_hashes"]["artifacts/kg_enrichment/regulatory_extension/subgraph_nodes.csv"] = sha256(EXTENSION / "subgraph_nodes.csv")
    manifest["input_hashes"]["artifacts/kg_enrichment/regulatory_extension/subgraph_edges.csv"] = sha256(EXTENSION / "subgraph_edges.csv")

    output_names = set(manifest.get("output_hashes", {}))
    output_names.update({"regulatory_extension_biocypher_validation.json", "regulatory_extension_manifest.json"})
    manifest["output_hashes"] = {
        name: sha256(output / name)
        for name in sorted(output_names)
        if name not in {"bundle_manifest.json", "bundle_checksums.json", "analysis_run_manifest.json", "analysis_run_registration.json"}
    }
    write_json(manifest_path, manifest)

    software_versions = dict(manifest.get("software_versions", {}))
    input_hashes = dict(manifest.get("input_hashes", {}))
    input_hashes["kg/scripts/package_top10_regulatory_graph_bundle.py"] = sha256(Path(__file__).resolve())
    parameters = {
        "bundle_dir": output.relative_to(ROOT).as_posix(),
        "manifest_sha256": sha256(manifest_path),
        "output_hashes": manifest["output_hashes"],
        "counts": manifest["counts"],
        "mapping_policy": manifest.get("mapping_policy"),
        "cross_dose_policy": manifest.get("cross_dose_policy"),
    }
    analysis_manifest = {
        "analysis_run_id": run_key,
        "project_id": PROJECT_ID,
        "run_type": "kg_graph_bundle",
        "status": "completed",
        "parameters": parameters,
        "software_versions": software_versions,
        "input_hashes": input_hashes,
    }
    analysis_manifest_path = output / "analysis_run_manifest.json"
    write_json(analysis_manifest_path, analysis_manifest)
    parameters["analysis_run_manifest_sha256"] = sha256(analysis_manifest_path)
    registration = {**analysis_manifest, "parameters": parameters}
    registration_path = output / "analysis_run_registration.json"
    write_json(registration_path, registration)
    checksums = dict(manifest["output_hashes"])
    checksums.update({
        "bundle_manifest.json": sha256(manifest_path),
        "analysis_run_manifest.json": sha256(analysis_manifest_path),
    })
    write_json(output / "bundle_checksums.json", checksums)
    return {
        "status": "PACKAGED_VALIDATED_FOR_REGISTRATION",
        "analysis_run_id": run_key,
        "bundle_dir": output.relative_to(ROOT).as_posix(),
        "nodes": len(all_nodes),
        "new_nodes": len(new_nodes),
        "shared_nodes_reused": reused_nodes,
        "edges": len(all_edges),
        "regulatory_assertions": len(new_evidence),
        "evidence_records": len(evidence_rows),
        "registration": registration_path.relative_to(ROOT).as_posix(),
        "bundle_manifest_sha256": sha256(manifest_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", help="New UUID directory/AnalysisRun suffix; defaults to a new UUID")
    args = parser.parse_args()
    print(json.dumps(package(args.run_id), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
