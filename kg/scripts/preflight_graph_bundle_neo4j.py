"""Read-only BioCypher and Neo4j shared-state preflight for one complete GraphBundle."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from import_phase_b_to_neo4j import (
    expected_node_map,
    expected_relationship_map,
    input_fingerprint,
    preflight_existing_graph,
    prepare_biocypher_import_rows,
    read_graph_inputs,
)
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-dir", type=Path, required=True)
    parser.add_argument("--graph-build-id", required=True)
    parser.add_argument("--uri", default=os.getenv("NEO4J_URI"))
    parser.add_argument("--database", default=os.getenv("NEO4J_DATABASE", "neo4j"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.uri or not os.getenv("NEO4J_USER") or not os.getenv("NEO4J_PASSWORD"):
        raise SystemExit("NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD must be set")
    bundle_dir = args.bundle_dir.resolve()
    if not bundle_dir.is_relative_to(ROOT / "data/processed/projects"):
        raise SystemExit("Read-only preflight only accepts project-scoped processed GraphBundles")

    node_rows, edge_rows, input_hashes = read_graph_inputs(bundle_dir, None)
    fingerprint = input_fingerprint(input_hashes)
    nodes_by_label, edges_by_relation, biocypher = prepare_biocypher_import_rows(
        node_rows, edge_rows, args.graph_build_id, fingerprint, fingerprint
    )
    expected_nodes = expected_node_map(nodes_by_label)
    expected_relationships = expected_relationship_map(edges_by_relation, args.graph_build_id)
    driver = GraphDatabase.driver(args.uri, auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
    try:
        driver.verify_connectivity()
        with driver.session(database=args.database, default_access_mode="READ") as session:
            preflight_existing_graph(session, args.graph_build_id, expected_nodes, expected_relationships)
    finally:
        driver.close()

    report = {
        "schema_version": 1,
        "status": "PASS",
        "mode": "read_only_preflight",
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "endpoint": args.uri,
        "database": args.database,
        "bundle_dir": bundle_dir.relative_to(ROOT).as_posix(),
        "graph_build_id": args.graph_build_id,
        "input_sha256": input_hashes,
        "biocypher": biocypher,
        "expected_unique_nodes": len(expected_nodes),
        "expected_relationships": len(expected_relationships),
        "checks": {
            "existing_shared_node_labels_and_properties_match": True,
            "no_relationship_identity_collision_in_build": True,
            "no_existing_membership_for_new_build": True,
            "write_queries_executed": False,
        },
    }
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(serialized, encoding="utf-8")
    print(serialized)


if __name__ == "__main__":
    main()
