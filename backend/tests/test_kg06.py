import hashlib
import json
from types import SimpleNamespace

from app import kg06


def make_evidence(evidence_id: str, predicate: str = "TARGETS"):
    return SimpleNamespace(
        evidence_id=evidence_id,
        source_release="OptimusKG test release",
        source_record_id=f"source:{evidence_id}",
        subject_id="CHEMBL1",
        predicate=predicate,
        object_id="ENSG000001",
        source_url=None,
        assertion_sha256="a" * 64,
    )


def test_edge_evidence_preserves_actions_without_inventing_direction():
    evidence = make_evidence("e-target")
    edge = kg06._edge_evidence(
        {
            "id": "CHEMBL1|TARGETS|ENSG000001|source",
            "from": "CHEMBL1",
            "to": "ENSG000001",
            "source_release": "OptimusKG 3.2",
            "evidence_ids": ["e-target"],
            "source_assertion_json": json.dumps({"relation_assertions": [{"relation": "TARGET", "source": "DB"}]}),
        },
        "TARGETS",
        {"e-target": evidence},
    )
    assert edge["reported_actions"] == ["TARGET"]
    assert "no direction inferred" in edge["action_interpretation"]
    assert edge["evidence_complete"] is True
    assert edge["sources"][0]["source_record_id"] == "source:e-target"


def test_path_id_is_stable_and_degrees_are_kept_as_analysis_evidence():
    evidence = {f"e{i}": make_evidence(f"e{i}") for i in range(5)}
    properties = [
        {"id": "ctx|HAS_CANDIDATE|candidate|run", "from": "ctx", "to": "candidate", "evidence_ids": ["e0"], "source_release": "S2", "source_assertion_json": json.dumps({"source_record_id": "run:candidate"})},
        {"id": "candidate|REFERENCES_DRUG|CHEMBL1|run", "from": "candidate", "to": "CHEMBL1", "evidence_ids": ["e1"], "source_release": "LINCS", "source_assertion_json": json.dumps({"source_record_id": "LINCS:pert"})},
        {"id": "CHEMBL1|TARGETS|ENSG000001|kg", "from": "CHEMBL1", "to": "ENSG000001", "evidence_ids": ["e2"], "source_release": "OptimusKG", "source_assertion_json": json.dumps({"relation_assertions": [{"relation": "INHIBITOR"}]})},
        {"id": "GO:1|HAS_ENRICHED_GENE|ENSG000001|s1", "from": "GO:1", "to": "ENSG000001", "evidence_ids": ["e3"], "source_release": "S1 enrichment", "source_assertion_json": json.dumps({"analysis_assertions": [{"adjusted_p": 0.01}]})},
        {"id": "ctx|HAS_ENRICHED_PATHWAY|GO:1|s1", "from": "ctx", "to": "GO:1", "evidence_ids": ["e4"], "source_release": "S1 enrichment", "source_assertion_json": json.dumps({"analysis_assertions": [{"adjusted_p": 0.02}]})},
    ]
    row = {
        "candidate_id": "candidate", "drug_id": "CHEMBL1", "drug_label": "Drug A",
        "gene_id": "ENSG000001", "gene_label": "GENE1", "pathway_id": "GO:1", "pathway_label": "Pathway",
        "edge_properties": properties,
        "relation_types": ["HAS_CANDIDATE", "REFERENCES_DRUG", "TARGETS", "HAS_ENRICHED_GENE", "HAS_ENRICHED_PATHWAY"],
    }
    path_a = kg06._make_path(row, "s1_enrichment_overlap", "GRAPH_BUILD:test", evidence)
    path_b = kg06._make_path(row, "s1_enrichment_overlap", "GRAPH_BUILD:test", evidence)
    expected = hashlib.sha256(
        ("GRAPH_BUILD:test|s1_enrichment_overlap|" + "|".join(item["id"] for item in properties)).encode()
    ).hexdigest()
    assert path_a["path_id"] == path_b["path_id"] == expected
    assert [node["id"] for node in path_a["nodes"]] == ["candidate", "CHEMBL1", "ENSG000001", "GO:1", "ctx"]
    assert path_a["pathway_adjusted_p_values"] == [0.01, 0.02]
    assert path_a["reported_actions"] == ["INHIBITOR"]
    assert path_a["evidence_complete"] is True


def test_kg06_cypher_is_fixed_and_graphbuild_scoped():
    for query in [kg06.TARGET_QUERY, kg06.PUBLIC_PATHWAY_QUERY, kg06.S1_ENRICHMENT_QUERY, kg06.S1_DEG_QUERY]:
        assert "$project_slug" in query
        assert "$pert_id" in query
        assert "$graph_build_id" in query
        assert "LIMIT " in query
    assert "ProteinTarget" not in kg06.TARGET_QUERY
