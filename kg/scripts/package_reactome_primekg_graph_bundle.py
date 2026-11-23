"""Create an immutable GraphBundle overlay for current Reactome and PrimeKG.

Reactome gene membership/hierarchy remains unsigned annotation. PrimeKG native
associations remain unsigned and are excluded from regulatory path search.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = "3f18f4c1-713d-58c5-8a53-38eca5a5aaf9"
BASE = ROOT / "data/processed/projects" / PROJECT / "graph_bundle/runs/634be378-67ba-4b0c-b649-d61761b5b4dc"
TOP10 = ROOT / "artifacts/kg_enrichment/baseline/top10_snapshot.json"
IDENTITY = ROOT / "data/top10_kg/identity/top10_identity_mapping.csv"
REACT = ROOT / "data/kg_enrichment/normalized/reactome/2026-10"
PRIME = ROOT / "data/kg_enrichment/normalized/primekg/2022-05"
RUNS = ROOT / "data/processed/projects" / PROJECT / "graph_bundle/runs"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    csv.field_size_limit(min(sys.maxsize, 2_147_483_647))
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def put_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="raise", lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def compact(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum())


def ev_id(source: str, relation: str, target: str, release: str) -> str:
    return hashlib.sha256(f"{source}|{relation}|{target}|{release}".encode()).hexdigest()


def package(run_uuid: str) -> dict:
    uuid.UUID(run_uuid)
    output = RUNS / run_uuid
    if output.exists():
        raise FileExistsError(output)
    base_manifest = json.loads((BASE / "bundle_manifest.json").read_text(encoding="utf-8"))
    if base_manifest.get("status") != "validated" or base_manifest.get("project_id") != PROJECT:
        raise ValueError("Base GraphBundle is not a validated ER+ project bundle")
    for name, expected in base_manifest.get("output_hashes", {}).items():
        if not (BASE / name).is_file() or sha(BASE / name) != expected:
            raise ValueError(f"Base bundle output hash mismatch: {name}")
    shutil.copytree(BASE, output)
    node_fields, nodes = csv_rows(output / "subgraph_nodes.csv")
    edge_fields, edges = csv_rows(output / "subgraph_edges.csv")
    evidence_fields, evidence = csv_rows(output / "evidence_records.csv")
    node_by_id = {n["id"]: n for n in nodes}
    if len(node_by_id) != len(nodes):
        raise ValueError("Duplicate base node IDs")
    evidence_by_id = {e["evidence_id"]: e for e in evidence}
    added_nodes: dict[str, dict] = {}
    added_edges: dict[tuple[str, str, str, str], dict] = {}
    added_evidence: dict[str, dict] = {}
    mapping_rejects: list[dict[str, str]] = []

    # Add canonical gene nodes needed by current Reactome membership only.
    crosswalk = {r["gene_id"]: r for r in csv_rows(ROOT / "data/kg_enrichment/normalized/optimuskg/3.2/uniprot_gene_crosswalk.csv")[1]}
    for row in csv_rows(REACT / "reactome_gene_pathways.csv")[1]:
        gene_id = row["gene_id"]
        if gene_id in node_by_id or gene_id in added_nodes:
            continue
        mapping = crosswalk.get(gene_id)
        if not mapping:
            mapping_rejects.append({"source": "Reactome", "source_record_id": row["source_record_id"], "reason": "gene_id_missing_from_crosswalk"})
            continue
        added_nodes[gene_id] = {"id": gene_id, "type": "Gene", "label": mapping["gene_symbol"], "properties_json": json.dumps({"symbol": mapping["gene_symbol"], "source_database": "OptimusKG", "source_release": "3.2", "source_file_sha256": mapping["source_file_sha256"]}, ensure_ascii=False, sort_keys=True)}

    # Add current human Reactome pathways, preserving existing canonical nodes.
    reactome_nodes = csv_rows(REACT / "reactome_pathway_nodes.csv")[1]
    for row in reactome_nodes:
        if row["id"] in node_by_id or row["id"] in added_nodes:
            continue
        props = {key: row[key] for key in ("stable_id", "species", "source_database", "source_release", "license", "source_file_sha256")}
        added_nodes[row["id"]] = {"id": row["id"], "type": "Pathway", "label": row["label"], "properties_json": json.dumps(props, ensure_ascii=False, sort_keys=True)}

    # Aggregate multiple exact UniProt mapping rows for one gene-pathway edge;
    # preserve each original mapping record in the associated evidence record.
    membership_groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in csv_rows(REACT / "reactome_gene_pathways.csv")[1]:
        if row["gene_id"] in node_by_id | added_nodes:
            membership_groups[(row["pathway_id"], row["gene_id"])].append(row)
    current_release = "Reactome-current-2026-10"
    for (pathway_id, gene_id), records in sorted(membership_groups.items()):
        record_ids = sorted({r["source_record_id"] for r in records})
        properties = {"source_database": "Reactome", "source_record_ids_json": json.dumps(record_ids, separators=(",", ":")), "evidence_record_count": len(record_ids), "source_release": current_release, "license": "CC0 1.0 Universal", "source_file_sha256": records[0]["source_file_sha256"], "organism": "Homo sapiens", "sign": "unknown"}
        key = (pathway_id, "REACTOME-CURRENT-PWY-GEN", gene_id, current_release)
        added_edges[key] = {"from": pathway_id, "label": "REACTOME-CURRENT-PWY-GEN", "to": gene_id, "relation": "CONTAINS_GENE", "undirected": "false", "source_release": current_release, "properties_json": json.dumps(properties, ensure_ascii=False, sort_keys=True)}
        evidence_id = ev_id(pathway_id, "REACTOME-CURRENT-PWY-GEN", gene_id, current_release)
        added_evidence[evidence_id] = {"evidence_id": evidence_id, "source_release": current_release, "source_record_id": json.dumps(record_ids, separators=(",", ":")), "subject_id": pathway_id, "predicate": "CONTAINS_GENE", "object_id": gene_id, "source_assertion_json": json.dumps({**properties, "source_records": records}, ensure_ascii=False, sort_keys=True)}

    # Current pathway hierarchy, with source row identity retained.
    for row in csv_rows(REACT / "reactome_pathway_hierarchy.csv")[1]:
        if row["source"] not in node_by_id | added_nodes or row["target"] not in node_by_id | added_nodes:
            mapping_rejects.append({"source": "Reactome", "source_record_id": row["source_record_id"], "reason": "hierarchy_endpoint_missing"}); continue
        key = (row["source"], "PATHWAY-PARENT", row["target"], current_release)
        props = {"source_database": "Reactome", "source_record_id": row["source_record_id"], "source_file_sha256": row["source_file_sha256"], "sign": "unknown", "license": "CC0 1.0 Universal"}
        added_edges[key] = {"from": row["source"], "label": "PATHWAY-PARENT", "to": row["target"], "relation": "SUBPATHWAY_OF", "undirected": "false", "source_release": current_release, "properties_json": json.dumps(props, ensure_ascii=False, sort_keys=True)}
        evidence_id = ev_id(row["source"], "PATHWAY-PARENT", row["target"], current_release)
        added_evidence[evidence_id] = {"evidence_id": evidence_id, "source_release": current_release, "source_record_id": row["source_record_id"], "subject_id": row["source"], "predicate": "SUBPATHWAY_OF", "object_id": row["target"], "source_assertion_json": json.dumps(props, ensure_ascii=False, sort_keys=True)}

    # PrimeKG nodes: drug names map only through frozen exact aliases; gene
    # symbols map only to a unique canonical project Gene. Disease IDs are
    # namespaced and are never merged by label similarity.
    frozen = json.loads(TOP10.read_text(encoding="utf-8"))
    top_rows = {r["pert_id"]: r for r in frozen["top10"]}
    aliases: dict[str, set[str]] = defaultdict(set)
    for r in csv_rows(IDENTITY)[1]:
        pert = r["lincs_pert_id"]
        for name in [r.get("canonical_name", ""), r.get("lincs_name", ""), *r.get("aliases", "").split("|")]:
            if compact(name): aliases[compact(name)].add(pert)
    project_drugs = {n["id"] for n in nodes if n["type"] == "Drug"}
    gene_by_symbol: dict[str, set[str]] = defaultdict(set)
    for n in [*nodes, *added_nodes.values()]:
        if n["type"] == "Gene":
            props = json.loads(n["properties_json"] or "{}")
            for name in {n.get("label", ""), props.get("symbol", "")}:
                if name: gene_by_symbol[compact(name)].add(n["id"])
    prime_nodes = csv_rows(PRIME / "primekg_top10_nodes.csv")[1]
    prime_to_graph: dict[str, str] = {}
    for n in prime_nodes:
        idx, kind, native, name = n["node_index"], n["node_type"].casefold(), n["node_id"], n["node_name"]
        if kind == "drug":
            hits = aliases.get(compact(name), set())
            if len(hits) != 1:
                mapping_rejects.append({"source": "PrimeKG", "source_record_id": f"node:{idx}", "reason": "drug_identity_unmapped_or_ambiguous"}); continue
            chembl = top_rows[next(iter(hits))].get("standard_drug_id")
            if chembl not in project_drugs:
                mapping_rejects.append({"source": "PrimeKG", "source_record_id": f"node:{idx}", "reason": "canonical_drug_node_missing"}); continue
            prime_to_graph[idx] = chembl
        elif kind in {"gene/protein", "gene", "protein"}:
            hits = gene_by_symbol.get(compact(name), set())
            if len(hits) != 1:
                mapping_rejects.append({"source": "PrimeKG", "source_record_id": f"node:{idx}", "reason": "gene_symbol_unmapped_or_ambiguous"}); continue
            prime_to_graph[idx] = next(iter(hits))
        elif kind == "disease":
            disease_id = f"PRIMEKG_DISEASE:{native}"
            prime_to_graph[idx] = disease_id
            if disease_id not in node_by_id:
                added_nodes[disease_id] = {"id": disease_id, "type": "Disease", "label": name, "properties_json": "{}"}
        else:
            mapping_rejects.append({"source": "PrimeKG", "source_record_id": f"node:{idx}", "reason": "unsupported_node_type"})

    prime_edge_rows = csv_rows(PRIME / "primekg_top10_edges.csv")[1]
    for row in prime_edge_rows:
        source_id, target_id = prime_to_graph.get(row["x_index"]), prime_to_graph.get(row["y_index"])
        if not source_id or not target_id:
            mapping_rejects.append({"source": "PrimeKG", "source_record_id": row["source_record_id"], "reason": "unmapped_endpoint"}); continue
        rel = row["relation"]
        direction = "drug_to_protein" if rel == "drug_protein" else "unknown"
        undirected = rel != "drug_protein"
        release = "PrimeKG-Dataverse-v2-2022-05"
        props = {"source_database": "PrimeKG", "source_record_id": row["source_record_id"], "primekg_relation": rel, "native_x_id": row["x_id"], "native_y_id": row["y_id"], "source_release": release, "license": "CC0-1.0", "source_file_sha256": row["source_file_sha256"], "sign": "unknown", "direction": direction}
        key = (source_id, "PRIMEKG-ASSOCIATION", target_id, release)
        added_edges[key] = {"from": source_id, "label": "PRIMEKG-ASSOCIATION", "to": target_id, "relation": "ASSOCIATED_WITH", "undirected": str(undirected).lower(), "source_release": release, "properties_json": json.dumps(props, ensure_ascii=False, sort_keys=True)}
        evidence_id = ev_id(source_id, "PRIMEKG-ASSOCIATION", target_id, release)
        added_evidence[evidence_id] = {"evidence_id": evidence_id, "source_release": release, "source_record_id": row["source_record_id"], "subject_id": source_id, "predicate": "ASSOCIATED_WITH", "object_id": target_id, "source_assertion_json": json.dumps(props, ensure_ascii=False, sort_keys=True)}

    duplicate_ids = set(added_evidence) & set(evidence_by_id)
    if duplicate_ids:
        raise ValueError(f"Evidence ID collisions with base bundle: {len(duplicate_ids)}")
    nodes.extend(added_nodes.values())
    edges.extend(added_edges.values())
    evidence.extend(added_evidence.values())
    put_csv(output / "subgraph_nodes.csv", node_fields, nodes)
    put_csv(output / "subgraph_edges.csv", edge_fields, edges)
    put_csv(output / "evidence_records.csv", evidence_fields, evidence)
    put_csv(output / "external_mapping_rejects.csv", ["source", "source_record_id", "reason"], mapping_rejects)

    import sys
    sys.path.insert(0, str(ROOT / "kg/scripts"))
    from biocypher_adapter import translate_graph_rows
    _, _, validation = translate_graph_rows(nodes, edges)
    (output / "biocypher_validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    run_key = f"ANALYSIS_RUN:KG_GRAPH_BUNDLE:{run_uuid}"
    input_paths = [ROOT / "kg/scripts/package_reactome_primekg_graph_bundle.py", ROOT / "kg/config/biocypher_schema.yaml", ROOT / "kg/scripts/import_phase_b_to_neo4j.py", REACT / "reactome_gene_pathways.csv", REACT / "reactome_pathway_hierarchy.csv", REACT / "reactome_pathway_nodes.csv", PRIME / "primekg_top10_nodes.csv", PRIME / "primekg_top10_edges.csv", PRIME / "primekg_top10_manifest.json"]
    inputs = {p.relative_to(ROOT).as_posix(): sha(p) for p in input_paths}
    manifest = base_manifest
    manifest.update({"status": "validated", "analysis_run_id": run_key, "bundle_version": str(int(manifest.get("bundle_version", "1")) + 1), "created_at": datetime.now(timezone.utc).isoformat(), "input_hashes": {**manifest.get("input_hashes", {}), **inputs}, "counts": {**manifest.get("counts", {}), "nodes": len(nodes), "edges": len(edges), "evidence_records": len(evidence), "reactome_current_gene_pathway_edges": len([e for e in added_edges.values() if e["label"] == "REACTOME-CURRENT-PWY-GEN"]), "reactome_current_hierarchy_edges": len([e for e in added_edges.values() if e["label"] == "PATHWAY-PARENT"]), "primekg_association_edges": len([e for e in added_edges.values() if e["label"] == "PRIMEKG-ASSOCIATION"]), "external_mapping_rejects": len(mapping_rejects)}, "external_layers": {"Reactome_current": "unsigned pathway membership and hierarchy", "PrimeKG": "unsigned native associations; exact candidate name/alias only"}})
    outputs = ["subgraph_nodes.csv", "subgraph_edges.csv", "evidence_records.csv", "disease_contexts.csv", "biocypher_validation.json", "external_mapping_rejects.csv"]
    manifest["output_hashes"] = {name: sha(output / name) for name in outputs if (output / name).is_file()}
    manifest_path = output / "bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    parameters = {"bundle_dir": output.relative_to(ROOT).as_posix(), "manifest_sha256": sha(manifest_path), "output_hashes": manifest["output_hashes"], "counts": manifest["counts"], "test_only": False}
    analysis_manifest = {"analysis_run_id": run_key, "project_id": PROJECT, "run_type": "kg_graph_bundle", "status": "completed", "parameters": parameters, "software_versions": manifest.get("software_versions", {}), "input_hashes": inputs}
    run_manifest_path = output / "analysis_run_manifest.json"
    run_manifest_path.write_text(json.dumps(analysis_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    registration = {**analysis_manifest, "parameters": {**parameters, "analysis_run_manifest_sha256": sha(run_manifest_path)}}
    (output / "analysis_run_registration.json").write_text(json.dumps(registration, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    checksums = {**manifest["output_hashes"], "bundle_manifest.json": sha(manifest_path), "analysis_run_manifest.json": sha(run_manifest_path)}
    (output / "bundle_checksums.json").write_text(json.dumps(checksums, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"status": "PACKAGED_VALIDATED_FOR_REGISTRATION", "analysis_run_id": run_key, "bundle_dir": output.relative_to(ROOT).as_posix(), "counts": manifest["counts"], "new_nodes": len(added_nodes), "new_edges": len(added_edges), "new_evidence_records": len(added_evidence), "mapping_rejects": len(mapping_rejects), "registration": str((output / "analysis_run_registration.json").relative_to(ROOT))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    print(json.dumps(package(args.run_id), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
