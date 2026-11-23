"""Create a new project GraphBundle with auditable ChEMBL/Reactome relations.

The source Top 10 bundle is copied, never modified. A ChEMBL protein-family
target remains a ChEMBLTarget node; its UniProt components are not re-labelled
as direct drug targets. Reactome records add component participation only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
PROJECT_ID = "3f18f4c1-713d-58c5-8a53-38eca5a5aaf9"
BASE = ROOT / "reports" / "top10_kg" / "top10_graph_bundle" / "3928c54d_external_v1"
EVIDENCE = ROOT / "data" / "top10_kg" / "evidence"
IDENTITY = ROOT / "data" / "top10_kg" / "identity" / "top10_identity_mapping.csv"
DISEASE_EVIDENCE = ROOT / "reports" / "top10_kg" / "external_disease_evidence.csv"
DISEASE_EVIDENCE_MANIFEST = ROOT / "reports" / "top10_kg" / "external_disease_evidence_manifest.json"
GENES = ROOT / "data" / "optimuskg" / "3.2" / "nodes" / "gene.parquet"
RUN_ROOT = ROOT / "data" / "processed" / "projects" / PROJECT_ID / "graph_bundle" / "runs"
csv.field_size_limit(min(sys.maxsize, 2_147_483_647))


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def json_compact(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def parse_json(value: str | None, fallback):
    try:
        return json.loads(value or "")
    except (TypeError, json.JSONDecodeError):
        return fallback


def validate_manifest_files(bundle: Path, manifest: dict) -> None:
    for name, expected in manifest.get("output_hashes", {}).items():
        path = (bundle / name).resolve()
        if not path.is_relative_to(bundle.resolve()) or not path.is_file() or sha(path) != expected:
            raise ValueError(f"Base Top 10 bundle output hash mismatch: {name}")


def edge_evidence_id(edge: dict) -> str:
    raw = f"{edge['from']}|{edge['label']}|{edge['to']}|{edge['source_release']}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-id", help="Optional run UUID for reproducible staging directory selection")
    args = parser.parse_args()
    run_id = args.output_id or str(uuid.uuid4())
    run_dir = RUN_ROOT / run_id
    if run_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing project GraphBundle run: {run_dir}")

    base_manifest_path = BASE / "bundle_manifest.json"
    base_manifest = json.loads(base_manifest_path.read_text(encoding="utf-8"))
    if base_manifest.get("project_id") != PROJECT_ID or base_manifest.get("status") != "validated_with_external_evidence_overlay":
        raise ValueError("Expected the validated Top 10 external overlay for the ER+ project")
    validate_manifest_files(BASE, base_manifest)

    source_manifest_path = EVIDENCE / "top10_source_evidence_manifest.json"
    reactome_manifest_path = EVIDENCE / "top10_reactome_manifest.json"
    identity_manifest_path = ROOT / "data" / "top10_kg" / "identity" / "identity_mapping_manifest.json"
    disease_manifest = json.loads(DISEASE_EVIDENCE_MANIFEST.read_text(encoding="utf-8"))
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    reactome_manifest = json.loads(reactome_manifest_path.read_text(encoding="utf-8"))
    identity_manifest = json.loads(identity_manifest_path.read_text(encoding="utf-8"))
    frozen_manifest_path = ROOT / "reports" / "top10_kg" / "02_top10_frozen_manifest.json"
    frozen_manifest = json.loads(frozen_manifest_path.read_text(encoding="utf-8"))
    frozen_hash = frozen_manifest.get("source_sha256")
    if source_manifest.get("frozen_top10_sha256") != frozen_hash or reactome_manifest.get("frozen_top10_sha256") != frozen_hash:
        raise ValueError("Source evidence is not tied to the base bundle's frozen Top 10")
    source_output_hashes = {Path(name).as_posix(): value for name, value in source_manifest.get("outputs_sha256", {}).items()}
    if reactome_manifest.get("chembl_target_components_sha256") != source_output_hashes.get("data/top10_kg/evidence/chembl_mechanism_targets.csv"):
        raise ValueError("Reactome UniProt mappings were not built from this ChEMBL component snapshot")
    if source_manifest.get("api_error_count") != 0 or reactome_manifest.get("api_error_count") != 0:
        raise ValueError("Source API errors must be reviewed before adding source records to a bundle")
    if identity_manifest.get("frozen_top10_sha256") != frozen_hash:
        raise ValueError("Identity mapping manifest is not tied to the frozen Top 10")
    if disease_manifest.get("frozen_top10_sha256") != frozen_hash:
        raise ValueError("Disease evidence is not tied to the frozen Top 10")
    if disease_manifest.get("source_file") != DISEASE_EVIDENCE.relative_to(ROOT).as_posix() or sha(DISEASE_EVIDENCE) != disease_manifest.get("source_sha256"):
        raise ValueError("Disease evidence source hash mismatch")
    for filename, expected in identity_manifest.get("outputs", {}).items():
        identity_file = IDENTITY.parent / filename
        if not identity_file.is_file() or sha(identity_file) != expected:
            raise ValueError(f"Identity mapping output hash mismatch: {filename}")
    for relative, expected in source_manifest.get("outputs_sha256", {}).items():
        source_file = ROOT / relative
        if not source_file.is_file() or sha(source_file) != expected:
            raise ValueError(f"ChEMBL/DGIdb source output hash mismatch: {relative}")
    for filename, expected in reactome_manifest.get("output_sha256", {}).items():
        reactome_file = EVIDENCE / filename
        if not reactome_file.is_file() or sha(reactome_file) != expected:
            raise ValueError(f"Reactome output hash mismatch: {filename}")

    inputs: dict[str, str] = {
        str(base_manifest_path.relative_to(ROOT).as_posix()): sha(base_manifest_path),
        str(frozen_manifest_path.relative_to(ROOT).as_posix()): sha(frozen_manifest_path),
        str(source_manifest_path.relative_to(ROOT).as_posix()): sha(source_manifest_path),
        str(reactome_manifest_path.relative_to(ROOT).as_posix()): sha(reactome_manifest_path),
        str(identity_manifest_path.relative_to(ROOT).as_posix()): sha(identity_manifest_path),
        str(DISEASE_EVIDENCE_MANIFEST.relative_to(ROOT).as_posix()): sha(DISEASE_EVIDENCE_MANIFEST),
        str(DISEASE_EVIDENCE.relative_to(ROOT).as_posix()): sha(DISEASE_EVIDENCE),
    }
    for path in (IDENTITY, EVIDENCE / "chembl_mechanisms.csv", EVIDENCE / "chembl_mechanism_targets.csv",
                 EVIDENCE / "dgidb_interactions.csv", EVIDENCE / "top10_source_evidence_summary.csv",
                 EVIDENCE / "reactome_protein_pathways.csv", EVIDENCE / "reactome_pathway_hierarchy.csv",
                 EVIDENCE / "top10_reactome_api_calls.json", EVIDENCE / "top10_source_api_calls.json", GENES):
        inputs[path.relative_to(ROOT).as_posix()] = sha(path)
    for name, expected in reactome_manifest.get("raw_snapshot_sha256", {}).items():
        raw = ROOT / "data" / "top10_kg" / "raw" / "reactome" / name
        if not raw.is_file() or sha(raw) != expected:
            raise ValueError(f"Reactome raw snapshot hash mismatch: {name}")

    temp_parent = run_dir.parent
    temp_parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(BASE, run_dir)
    nodes, node_fields = read_csv(run_dir / "subgraph_nodes.csv")
    edges, edge_fields = read_csv(run_dir / "subgraph_edges.csv")
    evidence_rows, evidence_fields = read_csv(run_dir / "evidence_records.csv")
    mappings, _ = read_csv(run_dir / "candidate_mapping_audit.csv")
    identities = {row["lincs_pert_id"]: row for row in read_csv(IDENTITY)[0]}
    mechanisms = read_csv(EVIDENCE / "chembl_mechanisms.csv")[0]
    components = read_csv(EVIDENCE / "chembl_mechanism_targets.csv")[0]
    pathway_rows = read_csv(EVIDENCE / "reactome_protein_pathways.csv")[0]
    hierarchy_rows = read_csv(EVIDENCE / "reactome_pathway_hierarchy.csv")[0]
    disease_evidence_rows = read_csv(DISEASE_EVIDENCE)[0]

    node_by_id = {row["id"]: row for row in nodes}
    edge_by_key = {(row["from"], row["label"], row["to"], row["source_release"]): row for row in edges}
    evidence_by_id = {row["evidence_id"]: row for row in evidence_rows}
    mapping_by_pert = {row["pert_id"]: row for row in mappings}
    snapshot_date = source_manifest.get("retrieved_at_utc", "unknown")[:10]
    chembl_release = f"ChEMBL mechanism snapshot {snapshot_date}"
    target_release = f"ChEMBL target components {snapshot_date}"
    reactome_release = f"Reactome {reactome_manifest.get('reactome_release', 'unknown')}"

    def upsert_node(node_id: str, node_type: str, label: str, properties: dict) -> None:
        prior = node_by_id.get(node_id)
        if prior:
            if prior["type"] != node_type:
                raise ValueError(f"Conflicting node type for {node_id}: {prior['type']} vs {node_type}")
            old_props = parse_json(prior.get("properties_json"), {})
            old_props.update({key: value for key, value in properties.items() if value is not None})
            prior["properties_json"] = json_compact(old_props)
            if not prior["label"] or prior["label"] == node_id:
                prior["label"] = label
            return
        row = {"id": node_id, "type": node_type, "label": label or node_id, "properties_json": json_compact(properties)}
        node_by_id[node_id] = row
        nodes.append(row)

    def upsert_edge(from_id: str, label: str, to_id: str, relation: str, release: str, properties: dict) -> None:
        key = (from_id, label, to_id, release)
        prior = edge_by_key.get(key)
        if prior:
            previous = parse_json(prior.get("properties_json"), {})
            assertions = previous.setdefault("source_assertions", [previous.copy()])
            assertion = {key: value for key, value in properties.items() if key != "source_assertions"}
            if assertion not in assertions:
                assertions.append(assertion)
            prior["properties_json"] = json_compact(previous)
            return
        row = {"from": from_id, "label": label, "to": to_id, "relation": relation,
               "undirected": "false", "source_release": release, "properties_json": json_compact(properties)}
        edge_by_key[key] = row
        edges.append(row)
        evidence_id = edge_evidence_id(row)
        assertion = dict(properties)
        source_url = assertion.get("source_url") or assertion.get("source_urls")
        evidence_by_id[evidence_id] = {
            "evidence_id": evidence_id, "source_release": release,
            "source_record_id": assertion.get("source_record_id") or json_compact(assertion.get("source_record_ids", [])),
            "subject_id": from_id, "predicate": label, "object_id": to_id,
            "source_assertion_json": json_compact(assertion),
        }

    # Ensure every frozen candidate is connected to its exact Drug entity.
    candidate_by_pert = {}
    for node in nodes:
        if node["type"] == "Candidate":
            properties = parse_json(node.get("properties_json"), {})
            if properties.get("pert_id"):
                candidate_by_pert[properties["pert_id"]] = node["id"]
    for pert_id, identity in identities.items():
        mapping = mapping_by_pert.get(pert_id, {})
        drug_id = mapping.get("graph_drug_id") or identity.get("chembl_id")
        if not drug_id or drug_id not in node_by_id or node_by_id[drug_id]["type"] != "Drug":
            raise ValueError(f"Missing exact Drug node for {pert_id}: {drug_id}")
        candidate_id = candidate_by_pert.get(pert_id)
        if not candidate_id:
            raise ValueError(f"Missing frozen Candidate node for {pert_id}")
        if identity.get("chembl_id") != drug_id and identity.get("identity_status") != "matched_exact_inchikey":
            # The two external identity nodes are still exact InChIKey-resolved.
            raise ValueError(f"Drug node ID differs from exact identity mapping for {pert_id}")
        upsert_edge(candidate_id, "PROJECT-REFERENCES_DRUG", drug_id, "REFERENCES_DRUG",
                    "LINCS exact InChIKey + standardized identity",
                    {"pert_id": pert_id, "inchi_key": identity.get("inchikey"), "mapping_method": "exact InChIKey", "source_record_id": f"LINCS pert_info:{pert_id}"})

    mechanisms_by_key: dict[tuple[str, str], list[dict]] = {}
    for mechanism in mechanisms:
        target_id = mechanism.get("target_chembl_id")
        if not target_id:
            continue
        mechanisms_by_key.setdefault((mechanism["pert_id"], target_id), []).append(mechanism)

    target_rows_by_id: dict[str, list[dict]] = {}
    for row in components:
        target_rows_by_id.setdefault(row["target_chembl_id"], []).append(row)
    for (pert_id, target_id), claims in mechanisms_by_key.items():
        identity = identities[pert_id]
        drug_id = mapping_by_pert[pert_id].get("graph_drug_id") or identity["chembl_id"]
        target_rows = target_rows_by_id.get(target_id, [])
        if not target_rows:
            raise ValueError(f"ChEMBL mechanism target endpoint did not resolve {target_id}")
        target = target_rows[0]
        if target["molecule_chembl_id"] != identity["chembl_id"]:
            raise ValueError(f"Mechanism molecule does not match exact drug identity for {pert_id}")
        mechanism_records = [parse_json(row.get("record"), {}) for row in claims]
        source_ids = [f"CHEMBL_MECHANISM:{record.get('mec_id') or target_id}" for record in mechanism_records]
        target_node_id = f"CHEMBL_TARGET:{target_id}"
        upsert_node(target_node_id, "ChEMBLTarget", target.get("target_name") or target_id, {
            "chembl_target_id": target_id, "target_type": target.get("target_type"),
            "organism": target.get("target_organism"), "direct_interaction": any(row.get("direct_interaction") == "1" for row in claims),
            "mechanism_of_action": [row.get("mechanism_of_action") for row in claims if row.get("mechanism_of_action")],
            "action_types": sorted({row.get("action_type") for row in claims if row.get("action_type")}),
            "component_accessions": sorted({row["component_accession"] for row in target_rows if row.get("component_accession")}),
            "source_database": "ChEMBL", "source_record_ids": source_ids,
        })
        for claim, record, source_record_id in zip(claims, mechanism_records, source_ids):
            if claim.get("direct_interaction") != "1":
                continue
            references = parse_json(claim.get("mechanism_refs"), [])
            upsert_edge(drug_id, "DRG-TARGET", target_node_id, "HAS_DIRECT_TARGET", chembl_release, {
                "pert_id": pert_id, "molecule_chembl_id": identity["chembl_id"],
                "mechanism_of_action": claim.get("mechanism_of_action"), "action_type": claim.get("action_type"),
                "selectivity": claim.get("selectivity"), "direct_interaction": True,
                "source_database": "ChEMBL", "source_record_id": source_record_id,
                "source_record_ids": [source_record_id], "source_urls": [f"https://www.ebi.ac.uk/chembl/compound_report_card/{identity['chembl_id']}/"],
                "references": references, "interpretation_limit": "ChEMBL curated mechanism; target type and missing action direction remain as sourced.",
            })

    # Map the exact ChEMBL component GENE_SYMBOL synonym to unique graph Gene IDs.
    missing_symbols = set()
    component_symbols: dict[str, set[str]] = {}
    for component in components:
        synonyms = parse_json(component.get("component_synonyms"), [])
        symbols = {item.get("component_synonym") for item in synonyms
                   if item.get("syn_type") == "GENE_SYMBOL" and item.get("component_synonym")}
        if symbols:
            component_symbols.setdefault(component["component_accession"], set()).update(symbols)
        else:
            missing_symbols.add(component["component_accession"])
    gene_by_symbol: dict[str, list[dict]] = {}
    for node in nodes:
        if node["type"] == "Gene":
            symbol = parse_json(node.get("properties_json"), {}).get("symbol")
            if symbol:
                gene_by_symbol.setdefault(str(symbol).upper(), []).append(node)
    needed_symbols = {symbol.upper() for symbols in component_symbols.values() for symbol in symbols}
    absent_symbols = needed_symbols - set(gene_by_symbol)
    if absent_symbols:
        table = pq.read_table(GENES, columns=["id", "label", "properties"]).to_pylist()
        for row in table:
            props = row.get("properties") or {}
            symbol = str(props.get("symbol") or "").upper()
            if symbol in absent_symbols:
                gene = {"id": row["id"], "type": "Gene", "label": row["label"], "properties_json": json_compact(props)}
                node_by_id[gene["id"]] = gene
                nodes.append(gene)
                gene_by_symbol.setdefault(symbol, []).append(gene)

    component_audit = []
    components_by_accession: dict[str, list[dict]] = {}
    for component in components:
        components_by_accession.setdefault(component["component_accession"], []).append(component)
    for accession, accession_components in components_by_accession.items():
        component = accession_components[0]
        protein_id = f"UNIPROT:{accession}"
        symbols = sorted(component_symbols.get(accession, set()))
        upsert_node(protein_id, "Protein", symbols[0] if len(symbols) == 1 else component.get("component_type") or accession, {
            "uniprot_accession": accession, "organism": component.get("target_organism"),
            "gene_symbols": symbols, "component_type": component.get("component_type"),
            "component_synonyms_json": json_compact(parse_json(component.get("component_synonyms"), [])),
            "source_database": "ChEMBL", "source_record_id": f"UniProt:{accession}",
            "source_url": f"https://www.uniprot.org/uniprotkb/{accession}/entry",
        })
        for target_id in sorted({row["target_chembl_id"] for row in accession_components}):
            target_node_id = f"CHEMBL_TARGET:{target_id}"
            if target_node_id not in node_by_id:
                # Some target components may be returned for a target whose mechanism row is absent; preserve it as an association.
                target_rows = target_rows_by_id.get(target_id, [])
                if not target_rows:
                    continue
                target = target_rows[0]
                upsert_node(target_node_id, "ChEMBLTarget", target.get("target_name") or target_id, {
                    "chembl_target_id": target_id, "target_type": target.get("target_type"),
                    "organism": target.get("target_organism"), "direct_interaction": False,
                    "component_accessions": sorted({row["component_accession"] for row in target_rows}),
                    "source_database": "ChEMBL target endpoint", "source_record_ids": [target_id],
                })
            upsert_edge(target_node_id, "TARGET-COMPONENT", protein_id, "HAS_COMPONENT", target_release, {
                "chembl_target_id": target_id, "target_type": component.get("target_type"),
                "component_relationship": component.get("component_relationship"),
                "component_type": component.get("component_type"), "component_accession": accession,
                "source_database": "ChEMBL", "source_record_id": f"{target_id}:{accession}",
                "source_url": component.get("source_url"),
            })
        mapped_gene_ids = set()
        if len(symbols) == 1:
            hits = gene_by_symbol.get(symbols[0].upper(), [])
            if len(hits) == 1:
                gene = hits[0]
                mapped_gene_ids.add(gene["id"])
                upsert_edge(protein_id, "PROTEIN-GENE", gene["id"], "ENCODED_BY", target_release, {
                    "uniprot_accession": accession, "gene_symbol": symbols[0],
                    "source_database": "ChEMBL UniProt component synonym", "source_record_id": f"{accession}:GENE_SYMBOL:{symbols[0]}",
                    "source_url": f"https://www.uniprot.org/uniprotkb/{accession}/entry",
                })
            else:
                component_audit.append({"uniprot_accession": accession, "target_chembl_ids": "|".join(sorted({r["target_chembl_id"] for r in accession_components})),
                                        "gene_symbols": "|".join(symbols), "status": "gene_symbol_unmatched" if not hits else "gene_symbol_ambiguous", "candidate_gene_ids": "|".join(g["id"] for g in hits)})
        else:
            component_audit.append({"uniprot_accession": accession, "target_chembl_ids": "|".join(sorted({r["target_chembl_id"] for r in accession_components})),
                                    "gene_symbols": "|".join(symbols), "status": "missing_or_multiple_canonical_symbols", "candidate_gene_ids": ""})

    pathway_by_id: dict[str, dict] = {}
    for row in pathway_rows:
        pathway_by_id.setdefault(row["pathway_id"], row)
    for row in hierarchy_rows:
        for pid, name in ((row["child_pathway_id"], row["child_pathway_name"]), (row["parent_pathway_id"], row["parent_pathway_name"])):
            pathway_by_id.setdefault(pid, {"pathway_id": pid, "pathway_name": name, "organism": row.get("organism"), "pathway_version": "", "is_disease_pathway": "", "is_inferred": "", "source_database": "Reactome", "source_version": reactome_manifest.get("reactome_release"), "source_record_id": pid, "source_url": f"https://reactome.org/content/detail/{pid}"})
    for pathway_id, pathway in pathway_by_id.items():
        node_id = f"REACT:{pathway_id}"
        upsert_node(node_id, "Pathway", pathway.get("pathway_name") or pathway_id, {
            "source_ids": [pathway_id], "source_database": "Reactome", "source_version": pathway.get("source_version") or reactome_manifest.get("reactome_release"),
            "organism": pathway.get("organism"), "st_id_version": pathway.get("pathway_version"),
            "is_disease_pathway": pathway.get("is_disease_pathway"), "is_inferred": pathway.get("is_inferred"),
            "source_url": pathway.get("source_url") or f"https://reactome.org/content/detail/{pathway_id}",
        })
    for row in pathway_rows:
        protein_id = f"UNIPROT:{row['uniprot_accession']}"
        pathway_id = f"REACT:{row['pathway_id']}"
        upsert_edge(protein_id, "PROTEIN-PATHWAY", pathway_id, "PARTICIPATES_IN", reactome_release, {
            "uniprot_accession": row["uniprot_accession"], "pathway_id": row["pathway_id"],
            "pathway_name": row["pathway_name"], "organism": row["organism"],
            "is_disease_pathway": row["is_disease_pathway"], "is_inferred": row["is_inferred"],
            "source_database": "Reactome", "source_record_id": row["source_record_id"],
            "source_url": row["source_url"],
            "interpretation_limit": "Protein component pathway mapping; does not imply drug-induced pathway direction or disease specificity.",
        })
    for row in hierarchy_rows:
        child, parent = f"REACT:{row['child_pathway_id']}", f"REACT:{row['parent_pathway_id']}"
        upsert_edge(child, "PATHWAY-PARENT", parent, "SUBPATHWAY_OF", reactome_release, {
            "child_pathway_id": row["child_pathway_id"], "parent_pathway_id": row["parent_pathway_id"],
            "source_database": "Reactome", "source_record_id": row["source_record_id"], "source_url": row["source_url"],
        })

    # Keep each manually reviewed disease-context record as a qualified claim
    # node. A Drug -> DiseaseEvidence -> Disease path records what was studied;
    # it does not assert that the drug treats ER-positive breast cancer.
    disease_id = "MONDO:0007254"
    if disease_id not in node_by_id or node_by_id[disease_id]["type"] != "Disease":
        raise ValueError(f"Missing ER-positive breast-cancer Disease node: {disease_id}")
    seen_disease_candidates: set[str] = set()
    for row in disease_evidence_rows:
        pert_id = row.get("pert_id", "")
        if pert_id not in identities or not row.get("review_status", "").startswith("reviewed"):
            raise ValueError(f"Disease evidence must be reviewed and belong to the frozen Top 10: {pert_id}")
        drug_id = mapping_by_pert[pert_id].get("graph_drug_id") or identities[pert_id]["chembl_id"]
        if drug_id not in node_by_id or node_by_id[drug_id]["type"] != "Drug":
            raise ValueError(f"Disease evidence has no exact standardized Drug node for {pert_id}")
        identity_payload = "|".join(row.get(field, "") for field in (
            "pert_id", "evidence_scope", "claim_type", "context", "source_id",
        ))
        evidence_node_id = "DISEASE_EVIDENCE:" + hashlib.sha256(identity_payload.encode("utf-8")).hexdigest()
        upsert_node(evidence_node_id, "DiseaseEvidence", row.get("evidence_scope") or row.get("claim_type") or evidence_node_id, {
            "pert_id": pert_id, "evidence_scope": row.get("evidence_scope"),
            "claim_type": row.get("claim_type"), "context": row.get("context"),
            "curated_finding": row.get("curated_finding"), "direction": row.get("direction"),
            "source_type": row.get("source_type"), "source_id": row.get("source_id"),
            "source_url": row.get("source_url"), "limitations": row.get("limitations"),
            "review_status": row.get("review_status"),
        })
        evidence_release = f"Curated disease evidence review {disease_manifest.get('review_date', 'unknown')}"
        source_record_id = f"external_disease_evidence.csv:{pert_id}:{row.get('source_id', '')}"
        upsert_edge(drug_id, "DRG-DISEASE-EVIDENCE", evidence_node_id,
                    "HAS_DISEASE_CONTEXT_EVIDENCE", evidence_release, {
                        "pert_id": pert_id, "claim_type": row.get("claim_type"),
                        "evidence_scope": row.get("evidence_scope"), "source_record_id": source_record_id,
                        "interpretation_limit": "A reviewed disease-context record; not a treatment-effect or efficacy assertion.",
                    })
        upsert_edge(evidence_node_id, "DISEASE-EVIDENCE-ABOUT", disease_id,
                    "CONCERNS_DISEASE", evidence_release, {
                        "pert_id": pert_id, "evidence_scope": row.get("evidence_scope"),
                        "source_record_id": source_record_id,
                        "interpretation_limit": "Disease subtype and model context are stored on the linked evidence node; do not infer clinical efficacy.",
                    })
        seen_disease_candidates.add(pert_id)
    expected_disease_candidates = set(identities)
    if seen_disease_candidates != expected_disease_candidates:
        raise ValueError("Reviewed disease evidence must cover every frozen Top 10 candidate")

    # Audit every edge, including two historical external-identity reference edges
    # that the parent overlay had omitted from evidence_records.csv.
    for edge in edges:
        evidence_id = edge_evidence_id(edge)
        if evidence_id in evidence_by_id:
            continue
        assertion = parse_json(edge.get("properties_json"), {})
        evidence_by_id[evidence_id] = {
            "evidence_id": evidence_id, "source_release": edge["source_release"],
            "source_record_id": assertion.get("source_record_id") or json_compact(assertion.get("source_record_ids", [])),
            "subject_id": edge["from"], "predicate": edge["label"], "object_id": edge["to"],
            "source_assertion_json": json_compact(assertion),
        }
    if len(evidence_by_id) != len(edges):
        raise ValueError(f"Expected one evidence identity per relation; got {len(evidence_by_id)} for {len(edges)}")

    write_csv(run_dir / "subgraph_nodes.csv", nodes, node_fields)
    write_csv(run_dir / "subgraph_edges.csv", edges, edge_fields)
    write_csv(run_dir / "evidence_records.csv", list(evidence_by_id.values()), evidence_fields)
    audit_fields = ["uniprot_accession", "target_chembl_ids", "gene_symbols", "status", "candidate_gene_ids"]
    write_csv(run_dir / "unmatched_target_components.csv", component_audit, audit_fields)

    try:
        from kg.scripts.biocypher_adapter import validate_bundle_directory
    except ImportError:
        from biocypher_adapter import validate_bundle_directory
    bc_report = validate_bundle_directory(run_dir)
    if bc_report.get("status") != "PASS":
        raise ValueError("BioCypher validation did not pass")

    manifest = dict(base_manifest)
    manifest.update({
        "status": "validated", "analysis_run_id": f"ANALYSIS_RUN:KG_GRAPH_BUNDLE:{run_id}",
        "project_slug": "erpos-gse42568", "build_scope": "frozen Top 10 plus source-supported ChEMBL mechanism targets and Reactome human pathway components",
        "input_hashes": inputs, "parent_bundle_manifest_sha256": sha(base_manifest_path),
        "source_evidence_manifest_sha256": sha(source_manifest_path), "reactome_manifest_sha256": sha(reactome_manifest_path),
        "chembl_reactome_integration": {
            "direct_target_relation": "Drug -> ChEMBLTarget only when ChEMBL direct_interaction=1 and a target ID is present",
            "family_policy": "Protein-family mechanism targets remain ChEMBLTarget nodes; member proteins are linked as components, not as direct drug targets",
            "pathway_policy": "Protein component -> Reactome Pathway PARTICIPATES_IN; no direction or ER+ specificity inferred",
            "unmatched_target_components": len(component_audit),
        },
    })
    manifest["counts"] = dict(base_manifest.get("counts", {}))
    manifest["counts"].update({
        "nodes": len(nodes), "edges": len(edges), "evidence_records": len(evidence_by_id),
        "proteins": sum(node["type"] == "Protein" for node in nodes),
        "chembl_target_entities": sum(node["type"] == "ChEMBLTarget" for node in nodes),
        "chembl_direct_target_edges": sum(edge["label"] == "DRG-TARGET" for edge in edges),
        "protein_gene_edges": sum(edge["label"] == "PROTEIN-GENE" for edge in edges),
        "reactome_protein_pathway_edges": sum(edge["label"] == "PROTEIN-PATHWAY" for edge in edges),
        "reactome_pathway_hierarchy_edges": sum(edge["label"] == "PATHWAY-PARENT" for edge in edges),
        "disease_evidence_nodes": sum(node["type"] == "DiseaseEvidence" for node in nodes),
        "drug_disease_evidence_edges": sum(edge["label"] == "DRG-DISEASE-EVIDENCE" for edge in edges),
        "disease_evidence_disease_edges": sum(edge["label"] == "DISEASE-EVIDENCE-ABOUT" for edge in edges),
        "reactome_unique_pathways": len(pathway_by_id), "unmatched_target_components": len(component_audit),
    })
    manifest["output_hashes"] = {
        path.name: sha(path) for path in sorted(run_dir.iterdir())
        if path.is_file() and path.name not in {"bundle_manifest.json", "bundle_checksums.json", "analysis_run_manifest.json"}
    }
    manifest_path = run_dir / "bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    parameters = {
        "bundle_dir": run_dir.relative_to(ROOT).as_posix(), "manifest_sha256": sha(manifest_path),
        "output_hashes": manifest["output_hashes"], "counts": manifest["counts"], "test_only": False,
    }
    analysis_run = {
        "analysis_run_id": manifest["analysis_run_id"], "project_id": PROJECT_ID,
        "run_type": "kg_graph_bundle", "status": "completed", "parameters": parameters,
        "software_versions": manifest.get("software_versions", {}), "input_hashes": inputs,
    }
    analysis_manifest_path = run_dir / "analysis_run_manifest.json"
    analysis_manifest_path.write_text(json.dumps(analysis_run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    registration_record = {**analysis_run, "parameters": {**parameters,
                              "analysis_run_manifest_sha256": sha(analysis_manifest_path)}}
    (run_dir / "analysis_run_registration.json").write_text(json.dumps(registration_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # The database can register the emitted AnalysisRun manifest without rewriting the immutable bundle.
    checksums = {**manifest["output_hashes"], "bundle_manifest.json": sha(manifest_path),
                 "analysis_run_manifest.json": sha(analysis_manifest_path)}
    (run_dir / "bundle_checksums.json").write_text(json.dumps(checksums, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "project_id": PROJECT_ID,
                      "analysis_run_id": manifest["analysis_run_id"], "bundle_dir": str(run_dir.relative_to(ROOT)),
                      "counts": manifest["counts"], "registration_record": registration_record}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
