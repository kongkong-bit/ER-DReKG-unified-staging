import csv

import pytest

from kg.scripts.kg_enrichment import detect_conflicts, download_source, enumerate_paths, evaluate_drugmechdb, normalize_mapped_tsv, normalize_omnipath, normalize_reactome_pathways, normalize_signor, normalize_tsv, propagate


def test_sign_propagation_and_unknown():
    assert propagate(["positive", "negative"]) == "negative"
    assert propagate(["negative", "negative"]) == "positive"
    assert propagate(["positive", "unknown"]) == "unknown"
    assert propagate(["positive", "conflicting"]) == "unknown"


def test_only_directed_regulation_paths_are_used():
    edges = [
        {"id": "a", "source": "P1", "target": "G1", "relation": "REGULATES", "sign": "negative", "directed": True},
        {"id": "b", "source": "G1", "target": "G2", "relation": "REGULATES", "sign": "positive", "directed": True},
        {"id": "ppi", "source": "P1", "target": "G2", "relation": "INTERACTS_WITH", "sign": "positive", "directed": True},
        {"id": "undirected", "source": "P1", "target": "G2", "relation": "REGULATES", "sign": "positive", "directed": False},
    ]
    result = enumerate_paths(edges, {"P1"}, {"G2"}, max_depth=3)
    assert result == [{"nodes": ["P1", "G1", "G2"], "edge_ids": ["a", "b"], "direction": "negative", "cell_context": "unknown", "context_compatible": True}]


def test_normalizer_requires_provenance_and_logs_rejects(tmp_path):
    source = tmp_path / "input.tsv"
    source.write_text("source_id\tsource\ttarget\trelation\tsign\torganism\nr1\tP1\tG1\tREGULATES\tnegative\t9606\nr2\tP1\tG2\tREGULATES\tup\t9606\n", encoding="utf-8")
    output = tmp_path / "normalized.csv"
    report = normalize_tsv(source, output, "Fixture")
    assert report["records_raw"] == 2 and report["records_valid"] == 1
    assert report["records_rejected"] == [{"line": 3, "reason": "invalid_sign"}]
    row = next(csv.DictReader(output.open(encoding="utf-8")))
    assert row["source_file_sha256"] == report["sha256"]
    with pytest.raises(ValueError):
        normalize_tsv(source, output, "")


def test_top10_audit_creates_frozen_snapshot():
    from kg.scripts.kg_enrichment import audit
    result = audit()
    assert len(result["top10"]) == 10
    assert [r["rank"] for r in result["top10"]] == list(range(1, 11))


def test_conflicting_signs_coexist_without_majority_vote():
    rows = [
        {"source": "P1", "target": "G1", "organism": "9606", "cell_context": "MCF7", "sign": "positive", "relation_id": "a", "source_database": "A"},
        {"source": "P1", "target": "G1", "organism": "9606", "cell_context": "MCF7", "sign": "negative", "relation_id": "b", "source_database": "B"},
        {"source": "P1", "target": "G1", "organism": "10090", "cell_context": "MCF7", "sign": "negative", "relation_id": "c", "source_database": "C"},
    ]
    conflicts = detect_conflicts(rows)
    assert len(conflicts) == 1
    assert conflicts[0]["status"] == "conflict"
    assert conflicts[0]["assertion_ids"] == ["a", "b"]
    assert conflicts[0]["sources"] == ["A", "B"]


def test_downloader_does_not_overwrite_existing_file(tmp_path):
    output = tmp_path / "source.dat"
    output.write_text("user data", encoding="utf-8")
    import pytest
    with pytest.raises(FileExistsError):
        download_source("https://invalid.example", output, "test", "v1", "unknown", "human", "v1")
    assert output.read_text(encoding="utf-8") == "user data"


def test_mapped_normalizer_preserves_raw_rows_and_rejects_nonhuman(tmp_path):
    source = tmp_path / "resource.tsv"
    source.write_text("src\ttgt\ttype\teffect\tspecies\nP1\tG1\tREGULATES\tnegative\t9606\nP2\tG2\tREGULATES\tpositive\t10090\nP3\tG3\tREGULATES\tactivate\t9606\n", encoding="utf-8")
    output = tmp_path / "normalized.csv"
    manifest = normalize_mapped_tsv(source, output, source_name="Fixture", release="v1", license_name="CC0", species="Homo sapiens",
        column_map={"source": "src", "target": "tgt", "relation": "type", "sign": "effect", "organism": "species"})
    rows = list(csv.DictReader(output.open(encoding="utf-8")))
    rejected = list(csv.DictReader(output.with_suffix(".csv.rejected.csv").open(encoding="utf-8")))
    assert manifest["records_raw"] == 3 and manifest["records_valid"] == 1
    assert rows[0]["sign"] == "negative" and rows[0]["raw_row_json"]
    assert {x["reason"] for x in rejected} == {"non_human_species", "invalid_sign"}


def test_mapped_normalizer_requires_explicit_source_columns(tmp_path):
    source = tmp_path / "data.tsv"
    source.write_text("src\ttgt\nA\tB\n", encoding="utf-8")
    with pytest.raises(ValueError, match="column_map"):
        normalize_mapped_tsv(source, tmp_path / "out.csv", source_name="X", release="v1", license_name="CC0", species="Homo sapiens", column_map={"source": "src"})


def test_explicit_stimulation_inhibition_mapping_preserves_conflict(tmp_path):
    source = tmp_path / "signed.tsv"
    source.write_text("source\ttarget\tis_stimulation\tis_inhibition\nP1\tG1\t1\t0\nP2\tG2\t1\t1\nP3\tG3\t0\t0\n", encoding="utf-8")
    output = tmp_path / "normalized.csv"
    normalize_mapped_tsv(source, output, source_name="OmniPath fixture", release="v1", license_name="source-specific", species="Homo sapiens",
        column_map={"source": "source", "target": "target", "relation": "constant:REGULATES", "sign": "sign_from:is_stimulation,is_inhibition"})
    rows = list(csv.DictReader(output.open(encoding="utf-8")))
    assert [x["sign"] for x in rows] == ["positive", "conflicting", "unknown"]


def test_reactome_headerless_layout_species_filter_and_parent_child_direction(tmp_path):
    pathways = tmp_path / "pathways.txt"
    hierarchy = tmp_path / "relation.txt"
    pathways.write_text("R-HSA-1\tParent\tHomo sapiens\nR-HSA-2\tChild\tHomo sapiens\nR-MMU-1\tMouse\tMus musculus\n", encoding="utf-8")
    hierarchy.write_text("R-HSA-1\tR-HSA-2\nR-HSA-1\tR-MMU-1\n", encoding="utf-8")
    manifest = normalize_reactome_pathways(pathways, hierarchy, tmp_path / "normalized")
    nodes = list(csv.DictReader((tmp_path / "normalized/reactome_pathway_nodes.csv").open(encoding="utf-8")))
    edges = list(csv.DictReader((tmp_path / "normalized/reactome_pathway_hierarchy.csv").open(encoding="utf-8")))
    assert manifest["human_pathways"] == 2
    assert len(nodes) == 2 and len(edges) == 1
    assert edges[0]["source"] == "REACT:R-HSA-2" and edges[0]["target"] == "REACT:R-HSA-1"
    assert edges[0]["relation"] == "SUBPATHWAY_OF" and edges[0]["sign"] == "unknown"


def test_materialized_top10_context_routes_are_source_linked_and_noncausal():
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    frozen = json.loads((root / "reports/top10_kg/02_top10_frozen_manifest.json").read_text(encoding="utf-8"))
    assert len(frozen["items"]) == 10
    for item in frozen["items"]:
        path = root / "artifacts/kg_enrichment/subgraphs" / f"{item['rank']:02d}_{item['pert_id']}.json"
        graph = json.loads(path.read_text(encoding="utf-8"))
        assert graph["pert_id"] == item["pert_id"]
        edge_ids = {edge["id"] for edge in graph["edges"] if edge.get("id")}
        evidence_ids = set(graph["evidence_ids"])
        for route in graph["candidate_context_paths"]:
            assert route["causal"] is False
            assert route["direction"] == "unknown"
            assert set(route["edge_ids"]).issubset(edge_ids)
            assert set(route["evidence_ids"]).issubset(evidence_ids)


def test_materialized_regulatory_paths_keep_edges_and_identifier_mapping_evidence():
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    graphs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((root / "artifacts/kg_enrichment/subgraphs").glob("*.json"))]
    assert len(graphs) == 10
    assert sum(bool(g["candidate_mechanism_paths"]) for g in graphs) > 0
    for graph in graphs:
        edge_ids = {e.get("id") for e in graph["edges"]}
        evidence_ids = set(graph["evidence_ids"])
        for path in graph["candidate_mechanism_paths"]:
            assert len(path["edge_ids"]) <= 4
            assert set(path["edge_ids"]).issubset(edge_ids)
            assert set(path["mapping_evidence_ids"]).issubset(evidence_ids)
            assert path["direction"] in {"positive", "negative", "unknown"}
            assert path["s1_directionality_interpretation"].startswith("descriptive transcript")


def test_signor_source_parser_uses_verified_schema_and_preserves_rejections(tmp_path):
    fields = "ENTITYA TYPEA IDA DATABASEA ENTITYB TYPEB IDB DATABASEB EFFECT MECHANISM RESIDUE SEQUENCE TAX_ID CELL_DATA TISSUE_DATA MODULATOR_COMPLEX TARGET_COMPLEX MODIFICATIONA MODASEQ MODIFICATIONB MODBSEQ PMID DIRECT NOTES ANNOTATOR SENTENCE SIGNOR_ID".split()
    rows = [
        dict(ENTITYA="A", TYPEA="protein", IDA="P1", DATABASEA="UNIPROT", ENTITYB="B", TYPEB="protein", IDB="P2", DATABASEB="UNIPROT", EFFECT="down-regulates activity", MECHANISM="phosphorylation", TAX_ID="9606", CELL_DATA="BTO:1", PMID="12345", DIRECT="t", ANNOTATOR="curator", SENTENCE="statement", SIGNOR_ID="SIGNOR-1"),
        dict(ENTITYA="A", TYPEA="protein", IDA="P1", DATABASEA="UNIPROT", ENTITYB="B", TYPEB="protein", IDB="P2", DATABASEB="UNIPROT", EFFECT="up-regulates activity", MECHANISM="phosphorylation", TAX_ID="10090", PMID="12345", DIRECT="t", ANNOTATOR="curator", SENTENCE="statement", SIGNOR_ID="SIGNOR-2"),
        dict(ENTITYA="A", TYPEA="protein", IDA="P1", DATABASEA="UNIPROT", ENTITYB="C", TYPEB="complex", IDB="SIGNOR-C1", DATABASEB="SIGNOR", EFFECT="form complex", MECHANISM="binding", TAX_ID="9606", PMID="12345", DIRECT="t", ANNOTATOR="curator", SENTENCE="statement", SIGNOR_ID="SIGNOR-3"),
    ]
    source = tmp_path / "signor.tsv"
    with source.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t"); writer.writeheader(); writer.writerows(rows)
    out = tmp_path / "normalized.csv"
    manifest = normalize_signor(source, out, release="fixture", license_name="CC BY 4.0")
    normalized = list(csv.DictReader(out.open(encoding="utf-8")))
    rejects = list(csv.DictReader(out.with_suffix(".csv.rejected.csv").open(encoding="utf-8")))
    assert manifest["records_valid"] == 1 and manifest["records_rejected"] == 2
    assert normalized[0]["sign"] == "negative" and normalized[0]["evidence_ids"] == "PMID:12345"
    assert {row["reason"] for row in rejects} == {"nonhuman_or_unspecified_taxon", "non_protein_endpoint"}


def test_omnipath_parser_splits_signed_core_evidence_and_records_resource_license(tmp_path):
    import json
    source = tmp_path / "omnipath.tsv"
    header = "source\ttarget\tis_directed\tevidences\n"
    evidence = {"positive": [{"dataset": "omnipath", "resource": "A", "references": ["12345"], "attrs": {"mechanism": ["phosphorylation"]}}, {"dataset": "pathwayextra", "resource": "X", "references": [], "attrs": {}}], "negative": [{"dataset": "omnipath", "resource": "B", "references": ["10.1/example"], "attrs": {}}]}
    source.write_text(header + "P1\tP2\tTrue\t" + json.dumps(evidence) + "\nP3\tP4\tFalse\t{}\n", encoding="utf-8")
    resource_file = tmp_path / "resources.json"
    resource_file.write_text(json.dumps({"A": {"license": {"name": "CC BY 4.0", "url": "https://example/a"}}, "B": {"license": {"name": "CC BY-NC 4.0", "url": "https://example/b"}}}), encoding="utf-8")
    output = tmp_path / "normalized.csv"
    manifest = normalize_omnipath(source, resource_file, output, release="fixture")
    rows = list(csv.DictReader(output.open(encoding="utf-8")))
    assert manifest["records_valid"] == 2
    assert {(r["sign"], r["evidence_resource"], r["license"]) for r in rows} == {("positive", "A", "CC BY 4.0"), ("negative", "B", "CC BY-NC 4.0")}


def test_conflicting_signs_with_unspecified_context_remain_unknown():
    rows = [
        {"source": "P1", "target": "P2", "organism": "9606", "cell_context": "unknown", "sign": "positive", "assertion_id": "a", "source_database": "OmniPath"},
        {"source": "P1", "target": "P2", "organism": "9606", "cell_context": "BTO:1", "sign": "negative", "assertion_id": "b", "source_database": "SIGNOR"},
    ]
    conflicts = detect_conflicts(rows)
    assert len(conflicts) == 1
    assert conflicts[0]["status"] == "potential_conflict_unknown_context"
    assert conflicts[0]["assertion_ids"] == ["a", "b"]


def test_drugmechdb_exact_breast_indication_and_target_overlap():
    result = evaluate_drugmechdb()
    assert result["raw_path_record_count"] == 4846
    assert result["top10_exact_breast_neoplasm_path_count"] == 1
    assert result["top10_coverage"] == "1/10"
    assert result["target_overlap_fraction"] == "1/1"
    assert "not ER+ subtype evidence" in result["disease_scope"]["interpretation"]
