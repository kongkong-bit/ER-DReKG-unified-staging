from kg.scripts.import_phase_b_to_neo4j import prepare_biocypher_import_rows


def test_biocypher_preserves_protein_target_and_reactome_semantics():
    nodes = [
        {"id": "CHEMBL272980", "type": "Drug", "label": "Mocetinostat", "properties_json": "{}"},
        {"id": "CHEMBL_TARGET:CHEMBL1829", "type": "ChEMBLTarget", "label": "Histone deacetylase 3", "properties_json": "{}"},
        {"id": "UNIPROT:O15379", "type": "Protein", "label": "HDAC3", "properties_json": '{"organism":"Homo sapiens"}'},
        {"id": "ENSG00000171720", "type": "Gene", "label": "HDAC3", "properties_json": "{}"},
        {"id": "REACT:R-HSA-9006925", "type": "Pathway", "label": "Intracellular signaling by second messengers", "properties_json": "{}"},
        {"id": "DISEASE_EVIDENCE:claim-1", "type": "DiseaseEvidence", "label": "ER-positive preclinical", "properties_json": '{"evidence_scope":"ER_positive_preclinical","review_status":"reviewed"}'},
        {"id": "MONDO:0007254", "type": "Disease", "label": "ER-positive breast cancer", "properties_json": "{}"},
    ]
    edges = [
        {"from": "CHEMBL272980", "label": "DRG-TARGET", "to": "CHEMBL_TARGET:CHEMBL1829", "source_release": "ChEMBL", "undirected": "false", "properties_json": '{"direct_interaction":true}'},
        {"from": "CHEMBL_TARGET:CHEMBL1829", "label": "TARGET-COMPONENT", "to": "UNIPROT:O15379", "source_release": "ChEMBL target component", "undirected": "false", "properties_json": "{}"},
        {"from": "UNIPROT:O15379", "label": "PROTEIN-GENE", "to": "ENSG00000171720", "source_release": "ChEMBL UniProt component synonym", "undirected": "false", "properties_json": "{}"},
        {"from": "UNIPROT:O15379", "label": "PROTEIN-PATHWAY", "to": "REACT:R-HSA-9006925", "source_release": "Reactome 98", "undirected": "false", "properties_json": "{}"},
        {"from": "REACT:R-HSA-9006925", "label": "PATHWAY-PARENT", "to": "REACT:R-HSA-162582", "source_release": "Reactome 98", "undirected": "false", "properties_json": "{}"},
        {"from": "CHEMBL272980", "label": "DRG-DISEASE-EVIDENCE", "to": "DISEASE_EVIDENCE:claim-1", "source_release": "Curated disease evidence review", "undirected": "false", "properties_json": "{\"claim_type\":\"drug_disease_context\"}"},
        {"from": "DISEASE_EVIDENCE:claim-1", "label": "DISEASE-EVIDENCE-ABOUT", "to": "MONDO:0007254", "source_release": "Curated disease evidence review", "undirected": "false", "properties_json": "{\"evidence_scope\":\"ER_positive_preclinical\"}"},
    ]
    nodes.append({"id": "REACT:R-HSA-162582", "type": "Pathway", "label": "Signal Transduction", "properties_json": "{}"})
    nodes_by_label, edges_by_relation, report = prepare_biocypher_import_rows(
        nodes, edges, "GRAPH_BUILD:staging:test", "a" * 64, "b" * 64,
    )
    assert report["status"] == "PASS"
    assert {"Protein", "ChEMBLTarget", "Gene", "Pathway", "DiseaseEvidence", "Disease"}.issubset(nodes_by_label)
    assert {relation for relation, _, _ in edges_by_relation} >= {
        "HAS_DIRECT_TARGET", "HAS_COMPONENT", "ENCODED_BY", "PARTICIPATES_IN", "SUBPATHWAY_OF",
        "HAS_DISEASE_CONTEXT_EVIDENCE", "CONCERNS_DISEASE",
    }
