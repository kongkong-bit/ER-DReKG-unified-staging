"""Read-only inventory for the dedicated Top10 KG Neo4j staging endpoint."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))


def collect_audit(uri: str, database: str = "neo4j") -> dict:
    parsed = urlparse(uri)
    if parsed.hostname not in {"127.0.0.1", "localhost"} or parsed.port != 17687:
        raise ValueError("Read-only task audit is restricted to the isolated localhost:17687 staging endpoint")
    from app.core.config import settings
    if not settings.neo4j_password:
        raise RuntimeError("NEO4J_PASSWORD is not configured in the project environment")
    driver = GraphDatabase.driver(uri, auth=(settings.neo4j_user, settings.neo4j_password))
    try:
        driver.verify_connectivity()
        with driver.session(database=database, default_access_mode="READ") as session:
            components = session.run("CALL dbms.components() YIELD name, versions, edition RETURN name, versions, edition").data()
            dbs = session.run("SHOW DATABASES YIELD name, currentStatus RETURN name, currentStatus").data()
            node_counts = session.run("MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS count ORDER BY label").data()
            unlabeled_nodes = session.run("MATCH (n) WHERE size(labels(n)) = 0 RETURN count(n) AS count").single()["count"]
            relationship_counts = session.run("MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS count ORDER BY type").data()
            graph_build_inventory = session.run("MATCH ()-[r]->() UNWIND coalesce(r.graph_build_ids, []) AS graph_build_id RETURN graph_build_id, count(DISTINCT r.id) AS unique_relationships ORDER BY graph_build_id").data()
            candidate_inventory = session.run("MATCH (c:Candidate) RETURN c.id AS id, c.pert_id AS pert_id, c.label AS label ORDER BY c.pert_id").data()
            node_duplicate_ids = session.run("MATCH (n) WHERE n.id IS NOT NULL WITH n.id AS id, count(*) AS count WHERE count > 1 RETURN id, count ORDER BY count DESC LIMIT 20").data()
            relationship_duplicate_ids = session.run("MATCH ()-[r]->() WHERE r.id IS NOT NULL WITH r.id AS id, count(*) AS count WHERE count > 1 RETURN id, count ORDER BY count DESC LIMIT 20").data()
            constraints = session.run("SHOW CONSTRAINTS YIELD name, type, entityType, labelsOrTypes, properties, ownedIndex RETURN name, type, entityType, labelsOrTypes, properties, ownedIndex ORDER BY name").data()
            indexes = session.run("SHOW INDEXES YIELD name, type, entityType, labelsOrTypes, properties, state RETURN name, type, entityType, labelsOrTypes, properties, state ORDER BY name").data()
            relationship_inventory = session.run("MATCH ()-[r]->() RETURN count(r) AS relationships, count(CASE WHEN r.id IS NULL THEN 1 END) AS missing_id, count(CASE WHEN r.source_release IS NULL THEN 1 END) AS missing_source_release, count(CASE WHEN r.source_assertion_json IS NULL AND r.evidence_ids IS NULL THEN 1 END) AS missing_source_assertion_and_evidence, count(CASE WHEN r.graph_build_ids IS NOT NULL THEN 1 END) AS graphbuild_scoped").single().data()
        return {
            "schema_version": 1,
            "status": "read_only_staging_audit_complete",
            "audited_at": datetime.now(timezone.utc).isoformat(),
            "endpoint": "bolt://127.0.0.1:17687",
            "database": database,
            "write_queries_executed": False,
            "components": components,
            "databases": dbs,
            "node_counts_by_label": node_counts,
            "unlabeled_node_count": unlabeled_nodes,
            "relationship_counts_by_type": relationship_counts,
            "graph_build_inventory": graph_build_inventory,
            "candidate_inventory": candidate_inventory,
            "node_duplicate_id_sample": node_duplicate_ids,
            "relationship_duplicate_id_sample": relationship_duplicate_ids,
            "constraints": constraints,
            "indexes": indexes,
            "relationship_provenance_inventory": relationship_inventory,
            "safe_for_import_preflight": not node_duplicate_ids and not relationship_duplicate_ids,
            "not_performed": ["backup", "restore rehearsal", "import", "rollback rehearsal"],
        }
    finally:
        driver.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uri", default="bolt://127.0.0.1:17687")
    parser.add_argument("--database", default="neo4j")
    parser.add_argument("--output", type=Path, default=ROOT / "reports/kg_enrichment/02_live_neo4j_audit.json")
    args = parser.parse_args()
    result = collect_audit(args.uri, args.database)
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        output_label = output.relative_to(ROOT).as_posix()
    except ValueError:
        output_label = str(output)
    print(json.dumps({"status": result["status"], "node_labels": len(result["node_counts_by_label"]), "relationship_types": len(result["relationship_counts_by_type"]), "duplicate_node_ids": len(result["node_duplicate_id_sample"]), "duplicate_relationship_ids": len(result["relationship_duplicate_id_sample"]), "output": output_label}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
