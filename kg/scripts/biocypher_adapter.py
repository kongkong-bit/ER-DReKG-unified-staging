"""Validate and normalize graph bundle tuples through BioCypher's schema translator.

This stage is deliberately offline. The live Neo4j import remains the custom,
GraphBuild-aware MERGE importer because it preserves per-build relationship
membership and source assertions without replacing the database.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from importlib.metadata import version
import os
import csv
import sys
import hashlib


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "kg" / "config"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def translate_graph_rows(
    node_rows: list[dict[str, Any]],
    edge_rows: list[dict[str, Any]],
) -> tuple[list[Any], list[Any], dict[str, Any]]:
    """Translate project node/edge rows with BioCypher and return its entities."""
    # BioCypher 0.17's module initializer reads its shipped UTF-8 YAML without
    # an encoding argument. On Windows installations configured for GBK that
    # fails before BioCypher can be imported. Apply a temporary UTF-8 default
    # only during its import, then restore normal file handling.
    import builtins
    original_open = builtins.open

    def utf8_text_open(file, mode="r", *args, **kwargs):
        if "b" not in mode and "encoding" not in kwargs:
            kwargs["encoding"] = "utf-8"
        return original_open(file, mode, *args, **kwargs)

    previous_cwd = Path.cwd()
    builtins.open = utf8_text_open
    try:
        os.chdir(CONFIG.parent)
        from biocypher import BioCypher
    finally:
        os.chdir(previous_cwd)
        builtins.open = original_open

    bc = BioCypher(
        dbms="neo4j",
        offline=True,
        strict_mode=False,
        biocypher_config_path=str(CONFIG / "biocypher_config.yaml"),
        schema_config_path=str(CONFIG / "biocypher_schema.yaml"),
        head_ontology=None,
    )
    translator = bc._get_translator()

    seen_ids: dict[str, str] = {}
    nodes = []
    for row in node_rows:
        node_id = str(row["id"])
        node_type = str(row["type"])
        previous = seen_ids.setdefault(node_id, node_type)
        if previous != node_type:
            raise ValueError(f"Node {node_id} has conflicting types: {previous}, {node_type}")
        props = json.loads(row.get("properties_json") or "{}")
        nodes.append((node_id, node_type, props))

    translated_nodes = list(translator.translate_nodes(nodes))
    if len(translated_nodes) != len(nodes):
        raise ValueError("BioCypher schema did not translate every graph node")
    for original, normalized in zip(nodes, translated_nodes):
        if normalized.node_id != original[0] or normalized.node_label != original[1]:
            raise ValueError(f"BioCypher changed stable node identity/type for {original[0]}: expected {original[1]}, got {normalized.node_label}")
        if any(normalized.properties.get(key) != value for key, value in original[2].items()):
            changed = {key: {"input": value, "translated": normalized.properties.get(key, "<missing>")}
                       for key, value in original[2].items() if normalized.properties.get(key) != value}
            raise ValueError(f"BioCypher filtered or changed source properties for node {original[0]}: {changed}")

    edge_ids = set()
    edges = []
    for row in edge_rows:
        source, target = str(row["from"]), str(row["to"])
        if source not in seen_ids or target not in seen_ids:
            raise ValueError(f"Edge endpoint missing from bundle nodes: {source} -> {target}")
        props = json.loads(row.get("properties_json") or "{}")
        source_assertion_id = (props.get("assertion_id") or props.get("source_record_id") or "") if row["label"] == "REGULATES" else ""
        rel_id = f"{source}|{row['label']}|{target}|{row['source_release']}|{source_assertion_id}"
        if rel_id in edge_ids:
            raise ValueError(f"Duplicate edge identity in bundle: {rel_id}")
        edge_ids.add(rel_id)
        edges.append((rel_id, source, target, str(row["label"]), props))

    translated_edges = list(translator.translate_edges(edges))
    if len(translated_edges) != len(edges):
        raise ValueError("BioCypher schema did not translate every graph edge")
    for original, normalized in zip(edges, translated_edges):
        if (normalized.relationship_id, normalized.source_id, normalized.target_id) != original[:3]:
            raise ValueError(f"BioCypher changed edge identity or endpoints: {original[0]}")
        if any(normalized.properties.get(key) != value for key, value in original[4].items()):
            raise ValueError(f"BioCypher filtered or changed source assertions for edge {original[0]}")

    missing_types = translator.get_missing_biolink_types()
    if missing_types:
        raise ValueError(f"BioCypher schema left graph entity types unmapped: {missing_types}")
    report = {
        "status": "PASS",
        "biocypher_version": version("biocypher"),
        "schema_config": "kg/config/biocypher_schema.yaml",
        "schema_config_sha256": sha256(CONFIG / "biocypher_schema.yaml"),
        "biocypher_config_sha256": sha256(CONFIG / "biocypher_config.yaml"),
        "kg_pyproject_sha256": sha256(ROOT / "kg" / "pyproject.toml"),
        "kg_lock_sha256": sha256(ROOT / "kg" / "uv.lock"),
        "adapter_code_sha256": sha256(Path(__file__).resolve()),
        "neo4j_driver_version": version("neo4j"),
        "translation_mode": "offline schema translation; no BioCypher database connection",
        "neo4j_persistence": "GraphBuild-scoped MERGE importer consumes BioCypher translated entities",
        "node_count": len(translated_nodes),
        "edge_count": len(translated_edges),
        "node_types": dict(sorted(_count(row[1] for row in nodes).items())),
        "input_edge_types": dict(sorted(_count(row[3] for row in edges).items())),
        "normalized_edge_types": dict(sorted(_count(edge.relationship_label for edge in translated_edges).items())),
        "stable_node_ids_preserved": True,
        "stable_edge_ids_and_endpoints_preserved": True,
        "source_properties_preserved_by_translator": True,
    }
    return translated_nodes, translated_edges, report


def normalize_graph_rows(
    node_rows: list[dict[str, Any]],
    edge_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Run BioCypher translation and return the JSON-safe audit summary."""
    return translate_graph_rows(node_rows, edge_rows)[2]


def _count(values):
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def validate_bundle_directory(bundle_dir: Path) -> dict[str, Any]:
    csv.field_size_limit(min(sys.maxsize, 2_147_483_647))

    def load(name: str) -> list[dict[str, str]]:
        with (bundle_dir / name).open(encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))

    report = normalize_graph_rows(load("subgraph_nodes.csv"), load("subgraph_edges.csv"))
    report_path = bundle_dir / "biocypher_validation.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
