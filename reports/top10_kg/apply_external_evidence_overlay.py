"""Create a new Top10 bundle variant with explicitly sourced external claims.

The input bundle is never modified. This is an offline curation overlay, not a
Neo4j importer. Claims are limited to the two exact-InChIKey-resolved drugs.
"""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "reports/top10_kg/top10_graph_bundle/3928c54d"
OUT = ROOT / "reports/top10_kg/top10_graph_bundle/3928c54d_external_v1"
GENES = ROOT / "data/optimuskg/3.2/nodes/gene.parquet"
csv.field_size_limit(min(sys.maxsize, 2_147_483_647))

CLAIMS = [
    {
        "pert_id": "BRD-K50000283", "drug_id": "CHEMBL225519", "name": "PHA-767491",
        "inchi_key": "DKXHSOUZPMHNIZ-UHFFFAOYSA-N", "gene_symbol": "CDC7",
        "relation": "INHIBITOR", "source": "PUBMED", "source_release": "PubMed:18469809",
        "source_record_id": "PUBMED:18469809:PHA-767491:CDC7",
        "source_url": "https://pubmed.ncbi.nlm.nih.gov/18469809/",
        "study_context": "Original biochemical and cell-based characterization; preclinical models.",
        "assay_context": "Cdc7 kinase inhibition and Cdc7-dependent helicase phosphorylation.",
        "limitation": "General pharmacology; not ER-positive breast cancer evidence.",
        "source_ids": ["18469809"],
    },
    {
        "pert_id": "BRD-K50000283", "drug_id": "CHEMBL225519", "name": "PHA-767491",
        "inchi_key": "DKXHSOUZPMHNIZ-UHFFFAOYSA-N", "gene_symbol": "CDK9",
        "relation": "INHIBITOR", "source": "PUBMED", "source_release": "PubMed:31262335",
        "source_record_id": "PUBMED:31262335:PHA-767491:CDK9",
        "source_url": "https://pubmed.ncbi.nlm.nih.gov/31262335/",
        "study_context": "TNBC cell lines; sensitization to EGFR-targeted therapy.",
        "assay_context": "Cdc7/CDK9 inhibitor in a triple-negative breast cancer study.",
        "limitation": "Different subtype and experimental context; not ER-positive efficacy evidence.",
        "source_ids": ["31262335"],
    },
    {
        "pert_id": "BRD-K13094524", "drug_id": "CHEMBL2179387", "name": "PFI-1",
        "inchi_key": "TXZPMHLMPKIUGK-UHFFFAOYSA-N", "gene_symbol": "BRD2",
        "relation": "INHIBITOR", "source": "SGC", "source_release": "SGC PFI-1 chemical probe page",
        "source_record_id": "SGC:PFI-1:BRD2-bromodomain",
        "source_url": "https://www.thesgc.org/chemical-probes/pfi-1",
        "study_context": "In-vitro BET bromodomain chemical-probe characterization.",
        "assay_context": "BRD2 second bromodomain AlphaScreen IC50 0.098 uM.",
        "limitation": "In-vitro probe data; not ER-positive disease evidence or candidate-dose target engagement.",
        "source_ids": [],
    },
    {
        "pert_id": "BRD-K13094524", "drug_id": "CHEMBL2179387", "name": "PFI-1",
        "inchi_key": "TXZPMHLMPKIUGK-UHFFFAOYSA-N", "gene_symbol": "BRD4",
        "relation": "INHIBITOR", "source": "SGC", "source_release": "SGC PFI-1 chemical probe page",
        "source_record_id": "SGC:PFI-1:BRD4-bromodomain",
        "source_url": "https://www.thesgc.org/chemical-probes/pfi-1",
        "study_context": "In-vitro BET bromodomain chemical-probe characterization.",
        "assay_context": "BRD4 first bromodomain AlphaScreen IC50 0.22 uM; ITC KD 0.136 uM.",
        "limitation": "In-vitro probe data; not ER-positive disease evidence or candidate-dose target engagement.",
        "source_ids": [],
    },
]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    if OUT.exists():
        raise FileExistsError(f"Refusing to overwrite existing overlay: {OUT}")
    shutil.copytree(BASE, OUT)

    node_rows, node_fields = read_csv(OUT / "subgraph_nodes.csv")
    edge_rows, edge_fields = read_csv(OUT / "subgraph_edges.csv")
    evidence_rows, evidence_fields = read_csv(OUT / "evidence_records.csv")
    mapping_rows, mapping_fields = read_csv(OUT / "candidate_mapping_audit.csv")
    route_rows, route_fields = read_csv(OUT / "candidate_target_pathway_routes.csv")
    nodes = {row["id"]: row for row in node_rows}
    edges = {(row["from"], row["label"], row["to"], row["source_release"]): row for row in edge_rows}
    mappings = {row["pert_id"]: row for row in mapping_rows}

    gene_table = pq.read_table(GENES, columns=["id", "label", "properties"]).to_pylist()
    gene_by_symbol: dict[str, list[dict]] = {}
    for row in gene_table:
        properties = row.get("properties") or {}
        symbol = properties.get("symbol")
        if symbol:
            gene_by_symbol.setdefault(str(symbol).upper(), []).append(row)

    for drug_id, name, inchi in [
        ("CHEMBL225519", "PHA-767491", "DKXHSOUZPMHNIZ-UHFFFAOYSA-N"),
        ("CHEMBL2179387", "PFI-1", "TXZPMHLMPKIUGK-UHFFFAOYSA-N"),
    ]:
        if drug_id not in nodes:
            props = {"name": name, "inchi_key": inchi, "source_ids": [drug_id],
                     "sources": ["PubChem", "ChEMBL"] if name == "PHA-767491" else ["ChEMBL", "SGC"],
                     "identity_status": "external exact InChIKey; local OptimusKG 3.2 node absent"}
            nodes[drug_id] = {"id": drug_id, "type": "Drug", "label": name,
                              "properties_json": json.dumps(props, ensure_ascii=False, sort_keys=True, separators=(",", ":"))}

    new_evidence = []
    for claim in CLAIMS:
        mapping = mappings[claim["pert_id"]]
        if mapping.get("inchi_key") != claim["inchi_key"]:
            raise ValueError(f"LINCS InChIKey mismatch for {claim['pert_id']}")
        hits = gene_by_symbol.get(claim["gene_symbol"], [])
        if len(hits) != 1:
            raise ValueError(f"Expected unique public gene for {claim['gene_symbol']}, got {len(hits)}")
        gene_id = hits[0]["id"]
        gene_props = hits[0].get("properties") or {}
        if gene_id not in nodes:
            props = {k: gene_props.get(k) for k in ["symbol", "name", "biotype", "xrefs", "sources"] if gene_props.get(k) is not None}
            nodes[gene_id] = {"id": gene_id, "type": "Gene", "label": gene_props.get("symbol") or gene_id,
                              "properties_json": json.dumps(props, ensure_ascii=False, sort_keys=True, separators=(",", ":"))}

        candidate_id = next((node_id for node_id, row in nodes.items()
                             if row["type"] == "Candidate"
                             and json.loads(row["properties_json"]).get("pert_id") == claim["pert_id"]), None)
        if candidate_id is None:
            raise ValueError(f"Missing candidate node {claim['pert_id']}")

        ref_props = {"pert_id": claim["pert_id"], "mapping_method": "external exact InChIKey",
                     "inchi_key": claim["inchi_key"], "source_record_id": f"LINCS pert_info:{claim['pert_id']}",
                     "identity_source": claim["source_url"]}
        ref_key = (candidate_id, "PROJECT-REFERENCES_DRUG", claim["drug_id"], "LINCS pert_info + external identity")
        if ref_key not in edges:
            edges[ref_key] = {"from": candidate_id, "label": "PROJECT-REFERENCES_DRUG", "to": claim["drug_id"],
                              "relation": "REFERENCES_DRUG", "undirected": "false",
                              "source_release": "LINCS pert_info + external identity",
                              "properties_json": json.dumps(ref_props, ensure_ascii=False, sort_keys=True, separators=(",", ":"))}
        edge_props = {
            "mechanisms_of_action": [claim["assay_context"]],
            "relation_assertions": [{"relation": claim["relation"], "source": claim["source"]}],
            "relation_conflict": False, "source_ids": claim["source_ids"],
            "source_record_id": claim["source_record_id"], "source_urls": [claim["source_url"]],
            "sources": {"direct": [claim["source"]], "indirect": []},
            "study_context": claim["study_context"], "assay_context": claim["assay_context"],
            "interpretation_limit": claim["limitation"], "evidence_tier": "primary_or_curated_source",
        }
        edge_key = (claim["drug_id"], "DRG-GEN", gene_id, claim["source_release"])
        edges[edge_key] = {"from": claim["drug_id"], "label": "DRG-GEN", "to": gene_id,
                           "relation": claim["relation"], "undirected": "false",
                           "source_release": claim["source_release"],
                           "properties_json": json.dumps(edge_props, ensure_ascii=False, sort_keys=True, separators=(",", ":"))}
        evidence_id = hashlib.sha256(f"{claim['drug_id']}|DRG-GEN|{gene_id}|{claim['source_release']}".encode()).hexdigest()
        evidence = {"evidence_id": evidence_id, "source_release": claim["source_release"],
                    "source_record_id": claim["source_record_id"], "subject_id": claim["drug_id"],
                    "predicate": claim["relation"], "object_id": gene_id,
                    "source_assertion_json": json.dumps(edge_props, ensure_ascii=False, sort_keys=True, separators=(",", ":"))}
        if not any(x["evidence_id"] == evidence_id for x in evidence_rows):
            evidence_rows.append(evidence)
        new_evidence.append({**claim, "gene_id": gene_id, "evidence_id": evidence_id})

        # A route is recorded only if the target gene is already in an S1-enriched pathway.
        pathway_ids = set()
        for edge in edges.values():
            if edge["label"] == "S1-ENRICHED-GENE" and edge["to"] == gene_id:
                pathway_ids.add(edge["from"])
        for pathway_id in sorted(pathway_ids):
            route = {"pert_id": claim["pert_id"], "drug_id": claim["drug_id"],
                     "target_gene_id": gene_id, "pathway_id": pathway_id,
                     "disease_context_id": next((n["id"] for n in nodes.values() if n["type"] == "DiseaseContext"), ""),
                     "interpretation": "external sourced target claim intersects project S1 pathway; not causal or efficacy evidence"}
            if route not in route_rows:
                route_rows.append(route)

    write_csv(OUT / "subgraph_nodes.csv", list(nodes.values()), node_fields)
    write_csv(OUT / "subgraph_edges.csv", list(edges.values()), edge_fields)
    write_csv(OUT / "evidence_records.csv", evidence_rows, evidence_fields)
    write_csv(OUT / "candidate_target_pathway_routes.csv", route_rows, route_fields)
    for row in mapping_rows:
        match = next((c for c in CLAIMS if c["pert_id"] == row["pert_id"]), None)
        if match:
            row["graph_drug_id"] = match["drug_id"]
            row["mapping_status"] = "matched_external_exact_inchikey"
            row["mapping_method"] = "external exact InChIKey; overlay only"
    write_csv(OUT / "candidate_mapping_audit.csv", mapping_rows, mapping_fields)

    claim_path = OUT / "external_evidence_overlay.csv"
    claim_fields = list(new_evidence[0])
    write_csv(claim_path, new_evidence, claim_fields)
    validation = {
        "status": "PASS", "mode": "offline external evidence overlay; no database writes",
        "parent_bundle_manifest_sha256": digest((BASE / "bundle_manifest.json").read_bytes()),
        "claims_added": len(new_evidence), "drugs_resolved": 2,
        "claim_source_urls": sorted({x["source_url"] for x in new_evidence}),
        "unmodified_parent_bundle": True,
    }
    (OUT / "external_overlay_validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8")

    try:
        from kg.scripts.biocypher_adapter import validate_bundle_directory
    except ImportError:
        sys.path.insert(0, str(ROOT / "kg/scripts"))
        from biocypher_adapter import validate_bundle_directory
    biocypher_result = validate_bundle_directory(OUT)
    if biocypher_result.get("status") != "PASS":
        raise RuntimeError("BioCypher validation failed")

    manifest = json.loads((OUT / "bundle_manifest.json").read_text(encoding="utf-8"))
    manifest["analysis_run_id"] += ":EXTERNAL_EVIDENCE_V1"
    manifest["status"] = "validated_with_external_evidence_overlay"
    manifest["parent_bundle_manifest_sha256"] = validation["parent_bundle_manifest_sha256"]
    manifest["external_evidence_overlay"] = "external_evidence_overlay.csv"
    manifest["external_evidence_overlay_sha256"] = digest(claim_path.read_bytes())
    manifest["counts"]["candidate_perturbagens"] = 10
    manifest["counts"]["exact_inchikey_mapped_drugs"] = 10
    manifest["counts"]["candidate_target_pathway_routes"] = len(route_rows)
    manifest["counts"]["relation_conflicts"] = 0
    output_files = [p for p in OUT.iterdir() if p.is_file() and p.name not in {"bundle_manifest.json", "bundle_checksums.json"}]
    manifest["output_hashes"] = {p.name: digest(p.read_bytes()) for p in output_files}
    (OUT / "bundle_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    checksums = {p.name: digest(p.read_bytes()) for p in output_files}
    checksums["bundle_manifest.json"] = digest((OUT / "bundle_manifest.json").read_bytes())
    (OUT / "bundle_checksums.json").write_text(json.dumps(checksums, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "output": str(OUT), "claims_added": len(new_evidence),
                      "nodes": len(nodes), "edges": len(edges), "routes": len(route_rows),
                      "biocypher": biocypher_result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
