from __future__ import annotations

import pytest

from kg.scripts.biocypher_adapter import normalize_graph_rows, translate_graph_rows


def test_biocypher_schema_normalizes_without_changing_identity_or_assertions():
    nodes = [
        {"id": "DRUG:X", "type": "Drug", "properties_json": '{"source":"fixture"}'},
        {"id": "ENSG000001", "type": "Gene", "properties_json": '{"symbol":"TP53"}'},
    ]
    edges = [{
        "from": "DRUG:X",
        "to": "ENSG000001",
        "label": "DRG-GEN",
        "source_release": "fixture-1",
        "properties_json": '{"source_assertions":[{"source":"fixture"}]}',
    }]

    report = normalize_graph_rows(nodes, edges)

    assert report["status"] == "PASS"
    assert report["translation_mode"].startswith("offline schema translation")
    assert report["stable_node_ids_preserved"] is True
    assert report["stable_edge_ids_and_endpoints_preserved"] is True
    assert report["source_properties_preserved_by_translator"] is True
    assert len(report["schema_config_sha256"]) == 64
    assert len(report["kg_lock_sha256"]) == 64
    assert len(report["adapter_code_sha256"]) == 64
    assert report["neo4j_driver_version"] == "6.4.1"
    assert report["normalized_edge_types"] == {"TARGETS": 1}

    bc_nodes, bc_edges, _ = translate_graph_rows(nodes, edges)
    assert [(item.node_id, item.node_label) for item in bc_nodes] == [
        ("DRUG:X", "Drug"), ("ENSG000001", "Gene")
    ]
    assert bc_edges[0].relationship_label == "TARGETS"
    assert bc_edges[0].properties["source_assertions"] == [{"source": "fixture"}]


def test_biocypher_adapter_rejects_missing_edge_endpoint():
    nodes = [{"id": "DRUG:X", "type": "Drug", "properties_json": "{}"}]
    edges = [{
        "from": "DRUG:X",
        "to": "GENE:MISSING",
        "label": "DRG-GEN",
        "source_release": "fixture-1",
        "properties_json": "{}",
    }]

    with pytest.raises(ValueError, match="endpoint missing"):
        normalize_graph_rows(nodes, edges)
