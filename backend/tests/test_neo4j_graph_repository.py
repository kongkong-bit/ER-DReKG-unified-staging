import json
import csv
import hashlib

from app import graph_repository


class FakeSession:
    def __init__(self):
        self.queries = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def run(self, query, **params):
        self.queries.append((query, params))
        if "HAS_ENRICHED_GENE" in query:
            return iter([{
                "candidate_id": "CANDIDATE:BRD-TEST",
                "drug_id": "CHEMBL1",
                "target_gene_id": "ENSG000001",
                "pathway_id": "GO:0000001",
                "pathway_label": "test pathway",
                "disease_context_id": "DISEASE_CONTEXT:TEST",
                "candidate_evidence_ids": ["e-candidate"],
                "candidate_assertion": json.dumps({"mapping_method": "exact InChIKey"}),
                "target_evidence_ids": ["e-target"],
                "target_assertion": json.dumps({"sources": {"direct": ["DB"]}}),
                "pathway_gene_evidence_ids": ["e-gene"],
                "pathway_gene_assertion": json.dumps({"analysis_assertions": [{"gene_symbol": "TEST"}]}),
                "context_evidence_ids": ["e-context"],
                "context_assertion": json.dumps({"analysis_assertions": [{"analysis": "GO_UP"}]}),
            }])
        if "CONTAINS_GENE" in query:
            return iter([{
                "candidate_id": "CANDIDATE:BRD-TEST",
                "drug_id": "CHEMBL1",
                "target_gene_id": "ENSG000001",
                "pathway_id": "REACTOME:TEST",
                "pathway_label": "test Reactome pathway",
                "target_evidence_ids": ["e-target"],
                "target_assertion": json.dumps({"target": "direct"}),
                "pathway_evidence_ids": ["e-pathway"],
                "pathway_assertion": json.dumps({"source": "public KG"}),
            }])
        if "source_release AS source_release" in query:
            return FakeSingle({"source_release": "GSE test release", "assertion": json.dumps({"analysis": "GO_UP"})})
        raise AssertionError(f"Unexpected query: {query}")


class FakeSingle(dict):
    def single(self):
        return self


class FakeDriver:
    def __init__(self):
        self.session_instance = FakeSession()
        self.closed = False

    def session(self, **_):
        return self.session_instance

    def close(self):
        self.closed = True


def test_neo4j_mechanisms_return_both_route_types_and_source_evidence(monkeypatch):
    driver = FakeDriver()
    monkeypatch.setattr(graph_repository.settings, "graph_source", "neo4j")
    monkeypatch.setattr(graph_repository.GraphDatabase, "driver", lambda *args, **kwargs: driver)

    routes = graph_repository.mechanism_for_pert_id("BRD-TEST", "erpos-gse42568", "GRAPH_BUILD:test")

    assert {route["route_type"] for route in routes} == {"public_kg_pathway", "s1_enrichment_overlap"}
    enriched = next(route for route in routes if route["route_type"] == "s1_enrichment_overlap")
    assert enriched["evidence_ids"] == ["e-candidate", "e-target", "e-gene", "e-context"]
    assert enriched["analysis_assertions"] == [{"gene_symbol": "TEST"}]
    assert len(enriched["source_assertions"]) == 4
    assert all(params == {"project_slug": "erpos-gse42568", "pert_id": "BRD-TEST", "build_id": "GRAPH_BUILD:test"} for _, params in driver.session_instance.queries)
    assert all("graph_build_ids" in query for query, _ in driver.session_instance.queries)
    assert driver.closed


def test_neo4j_evidence_lookup_returns_source_release_and_assertion(monkeypatch):
    driver = FakeDriver()
    monkeypatch.setattr(graph_repository.settings, "graph_source", "neo4j")
    monkeypatch.setattr(graph_repository.GraphDatabase, "driver", lambda *args, **kwargs: driver)

    evidence = graph_repository.get_evidence("e-context")

    assert evidence == {
        "evidence_id": "e-context",
        "source_release": "GSE test release",
        "source_assertion": {"analysis": "GO_UP"},
        "source_url": None,
    }
    assert driver.session_instance.queries[0][1] == {"evidence_id": "e-context", "build_id": None}
    assert driver.closed


def test_neo4j_evidence_lookup_is_scoped_to_graph_build(monkeypatch):
    driver = FakeDriver()
    monkeypatch.setattr(graph_repository.settings, "graph_source", "neo4j")
    monkeypatch.setattr(graph_repository.GraphDatabase, "driver", lambda *args, **kwargs: driver)

    graph_repository.get_evidence("e-context", "GRAPH_BUILD:test")

    query, params = driver.session_instance.queries[0]
    assert "graph_build_ids" in query
    assert params == {"evidence_id": "e-context", "build_id": "GRAPH_BUILD:test"}


def test_graph_queries_require_context_relationship_in_selected_build(monkeypatch):
    class Result:
        def data(self):
            return []

        def single(self):
            return {"count": 0, "total": 0, "nodes": []}

    class QuerySession(FakeSession):
        def run(self, query, **params):
            self.queries.append((query, params))
            return Result()

    driver = FakeDriver()
    driver.session_instance = QuerySession()
    monkeypatch.setattr(graph_repository.settings, "graph_source", "neo4j")
    monkeypatch.setattr(graph_repository.GraphDatabase, "driver", lambda *args, **kwargs: driver)

    graph_repository.graph_counts("erpos-gse42568", "GRAPH_BUILD:test")
    graph_repository.search_nodes("erpos-gse42568", "TP53", graph_build_id="GRAPH_BUILD:test")
    graph_repository.get_subgraph("project-test", "erpos-gse42568", None, 2, 100, graph_build_id="GRAPH_BUILD:test")

    scoped_queries = [query for query, _ in driver.session_instance.queries if "MATCH (ctx:DiseaseContext" in query]
    all_queries = [query for query, _ in driver.session_instance.queries]
    assert len(scoped_queries) == 3
    assert all("graph_build_ids" in query for query in scoped_queries)
    assert any("$build_id IN coalesce(r.graph_build_ids" in query for query in all_queries)
    assert any("RETURN startNode(r).id AS source" in query for query in all_queries)
    assert not any("MATCH (a {id: $node_id})" in query for query, _ in driver.session_instance.queries)


def test_neo4j_subgraph_returns_centered_paged_neighbors_and_real_edges(monkeypatch):
    class Node(dict):
        labels = frozenset({"Drug"})

    class GeneNode(dict):
        labels = frozenset({"Gene"})

    center = Node(id="CHEMBL1", label="Drug A")
    gene_a = GeneNode(id="ENSG1", label="GENE1")
    gene_b = GeneNode(id="ENSG2", label="GENE2")

    class Result:
        def __init__(self, single=None, data=None):
            self.record = single
            self.rows = data or []

        def single(self):
            return self.record

        def data(self):
            return self.rows

    class SubgraphSession(FakeSession):
        def run(self, query, **params):
            self.queries.append((query, params))
            if "RETURN count(neighbor) AS total" in query:
                return Result({"total": 3})
            if "RETURN center, neighbors" in query:
                return Result({"center": center, "neighbors": [
                    {"node": gene_a, "type": "Gene", "depth": 1},
                    {"node": gene_b, "type": "Gene", "depth": 1},
                ]})
            return Result(data=[
                {"id": "edge:1", "source": "CHEMBL1", "target": "ENSG1", "relation": "TARGETS", "evidence_ids": ["e1"]},
                {"id": "edge:2", "source": "CHEMBL1", "target": "ENSG2", "relation": "TARGETS", "evidence_ids": ["e2"]},
            ])

    driver = FakeDriver()
    driver.session_instance = SubgraphSession()
    monkeypatch.setattr(graph_repository.settings, "graph_source", "neo4j")
    monkeypatch.setattr(graph_repository.GraphDatabase, "driver", lambda *args, **kwargs: driver)

    result = graph_repository.get_subgraph("p", "test", "CHEMBL1", 1, 3, 0, "GRAPH_BUILD:test", "RUN:test")

    assert [node["id"] for node in result["nodes"]] == ["CHEMBL1", "ENSG1", "ENSG2"]
    assert len(result["edges"]) == 2 and all(edge["directed"] for edge in result["edges"])
    assert result["truncated"] is True and result["next_cursor"] == "2"
    assert all(edge["source"] in {node["id"] for node in result["nodes"]} and edge["target"] in {node["id"] for node in result["nodes"]} for edge in result["edges"])
    assert driver.session_instance.queries[0][1] == {"node_id": "CHEMBL1", "build_id": "GRAPH_BUILD:test"}
    assert driver.session_instance.queries[1][1] == {"node_id": "CHEMBL1", "build_id": "GRAPH_BUILD:test", "cursor": 0, "page_size": 2}
    assert driver.closed


def test_csv_project_bundle_supports_summary_search_subgraph_mechanism_and_evidence(tmp_path, monkeypatch):
    from pathlib import Path

    bundle = Path(tmp_path)
    nodes = [
        {"id": "CTX:test", "type": "DiseaseContext", "label": "测试疾病上下文", "properties_json": json.dumps({"project_id": "project-test", "project_slug": "test-disease", "analysis_run_id": "RUN:KG:test", "s1_analysis_run_id": "RUN:S1:test"})},
        {"id": "CANDIDATE:project-test:BRD-TEST", "type": "Candidate", "label": "Drug A", "properties_json": json.dumps({"project_id": "project-test", "project_slug": "test-disease", "pert_id": "BRD-TEST", "analysis_run_id": "RUN:S2:test"})},
        {"id": "CHEMBL1", "type": "Drug", "label": "Drug A", "properties_json": json.dumps({"inchi_key": "TEST-INCHI"})},
        {"id": "ENSG000001", "type": "Gene", "label": "TP53", "properties_json": json.dumps({"symbol": "TP53"})},
        {"id": "GO:0000001", "type": "Pathway", "label": "Test pathway", "properties_json": json.dumps({"name": "Test pathway"})},
        {"id": "S2_CONDITION:project-test:1", "type": "S2Condition", "label": "Drug A · 1 uM · 24 h", "properties_json": json.dumps({"project_id": "project-test", "analysis_run_id": "RUN:S2:test", "dose": "1 uM", "time": "24 h", "WTCS_median": -0.4})},
    ]
    edges = [
        {"from": "CTX:test", "label": "PROJECT-HAS_CANDIDATE", "to": "CANDIDATE:project-test:BRD-TEST", "relation": "HAS_CANDIDATE", "source_release": "S2 test", "undirected": "false", "properties_json": json.dumps({"analysis_run_id": "RUN:S2:test"})},
        {"from": "CANDIDATE:project-test:BRD-TEST", "label": "PROJECT-REFERENCES_DRUG", "to": "CHEMBL1", "relation": "REFERENCES_DRUG", "source_release": "LINCS test", "undirected": "false", "properties_json": json.dumps({"analysis_run_id": "RUN:S2:test", "mapping_method": "exact InChIKey"})},
        {"from": "CHEMBL1", "label": "DRG-GEN", "to": "ENSG000001", "relation": "TARGETS", "source_release": "Public KG test", "undirected": "false", "properties_json": json.dumps({"relation_assertions": [{"source": "test"}]})},
        {"from": "GO:0000001", "label": "PWY-GEN", "to": "ENSG000001", "relation": "CONTAINS_GENE", "source_release": "Public KG test", "undirected": "false", "properties_json": json.dumps({"source": "test"})},
        {"from": "CTX:test", "label": "S1-ENRICHED-PATHWAY", "to": "GO:0000001", "relation": "HAS_ENRICHED_PATHWAY", "source_release": "S1 test", "undirected": "false", "properties_json": json.dumps({"analysis_assertions": [{"analysis_run_id": "RUN:ENRICH:test", "adjusted_p": 0.01}]})},
        {"from": "GO:0000001", "label": "S1-ENRICHED-GENE", "to": "ENSG000001", "relation": "HAS_ENRICHED_GENE", "source_release": "S1 test", "undirected": "false", "properties_json": json.dumps({"analysis_assertions": [{"analysis_run_id": "RUN:ENRICH:test", "gene_symbol": "TP53"}]})},
        {"from": "CANDIDATE:project-test:BRD-TEST", "label": "PROJECT-HAS_S2_CONDITION", "to": "S2_CONDITION:project-test:1", "relation": "HAS_S2_CONDITION", "source_release": "S2 test", "undirected": "false", "properties_json": json.dumps({"analysis_run_id": "RUN:S2:test"})},
    ]
    edges.append(edges[2].copy())  # Repeated source row must not become a second visual edge.
    for filename, rows, fields in [
        ("subgraph_nodes.csv", nodes, ["id", "type", "label", "properties_json"]),
        ("subgraph_edges.csv", edges, ["from", "label", "to", "relation", "source_release", "undirected", "properties_json"]),
    ]:
        with (bundle / filename).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    monkeypatch.setattr(graph_repository.settings, "graph_source", "csv")
    graph_dir = str(bundle)

    counts = graph_repository.graph_counts("test-disease", "GRAPH_BUILD:test", graph_dir)
    search = graph_repository.search_nodes("test-disease", "TP53", graph_dir=graph_dir)
    unanchored = graph_repository.get_subgraph("project-test", "test-disease", None, 2, 100, graph_build_id="GRAPH_BUILD:test", analysis_run_id="RUN:KG:test", graph_dir=graph_dir)
    subgraph = graph_repository.get_subgraph("project-test", "test-disease", "CHEMBL1", 1, 100, graph_build_id="GRAPH_BUILD:test", analysis_run_id="RUN:KG:test", graph_dir=graph_dir)
    routes = graph_repository.mechanism_for_pert_id("BRD-TEST", "test-disease", "GRAPH_BUILD:test", graph_dir)
    target_edge_id = hashlib.sha256("CHEMBL1|DRG-GEN|ENSG000001|Public KG test".encode()).hexdigest()
    evidence = graph_repository.get_evidence(target_edge_id, "GRAPH_BUILD:test", graph_dir)

    assert counts["node_count"] == 6 and counts["edge_count"] == 7
    assert search == [{"id": "ENSG000001", "type": "Gene", "label": "TP53"}]
    assert len(unanchored["edges"]) == 7 and len(unanchored["nodes"]) == 6
    assert unanchored["analysis_run_id"] == "RUN:KG:test"
    assert subgraph["analysis_run_id"] == "RUN:KG:test"
    assert {node["id"] for node in subgraph["nodes"]} == {"CHEMBL1", "ENSG000001", "CANDIDATE:project-test:BRD-TEST"}
    assert len(subgraph["edges"]) == 2 and all(edge["source"] in {node["id"] for node in subgraph["nodes"]} and edge["target"] in {node["id"] for node in subgraph["nodes"]} for edge in subgraph["edges"])
    assert {route["route_type"] for route in routes} == {"public_kg_pathway", "s1_enrichment_overlap"}
    assert evidence["source_release"] == "Public KG test" and evidence["source_assertion"]["relation_assertions"][0]["source"] == "test"


def test_csv_subgraph_centers_paginates_without_dangling_or_fake_edges():
    nodes = {"DRUG:single": {"id": "DRUG:single", "type": "Drug", "label": "Single", "properties": {}}}
    edges = []
    for index in range(250):
        gene_id = f"GENE:{index:03d}"
        nodes[gene_id] = {"id": gene_id, "type": "Gene", "label": gene_id, "properties": {}}
        edges.append({"id": f"edge:{index}", "source": "DRUG:single", "target": gene_id, "relation": "TARGETS", "evidence_ids": [f"edge:{index}"]})

    first = graph_repository._csv_subgraph("p", "DRUG:single", 1, 100, 0, nodes, edges)
    second = graph_repository._csv_subgraph("p", "DRUG:single", 1, 100, int(first["next_cursor"]), nodes, edges)
    missing = graph_repository._csv_subgraph("p", "DRUG:missing", 1, 100, 0, nodes, edges)
    unanchored = graph_repository._csv_subgraph("p", None, 1, 100, 0, nodes, edges)

    assert first["nodes"][0]["id"] == "DRUG:single"
    assert len(first["nodes"]) == 100 and len(first["edges"]) == 99 and first["truncated"]
    assert second["nodes"][0]["id"] == "DRUG:single"
    assert len(second["nodes"]) == 100 and len(second["edges"]) == 99 and second["truncated"]
    for page in (first, second):
        page_ids = {node["id"] for node in page["nodes"]}
        assert all(edge["source"] in page_ids and edge["target"] in page_ids for edge in page["edges"])
    assert missing["nodes"] == [] and missing["edges"] == []
    assert len(unanchored["edges"]) == 250 and len(unanchored["nodes"]) == 251 and not unanchored["truncated"]



def test_csv_subgraph_supports_single_and_multiple_real_relationships_in_fixture():
    nodes = {
        "DRUG:one": {"id": "DRUG:one", "type": "Drug", "label": "Drug one", "properties": {}},
        "GENE:a": {"id": "GENE:a", "type": "Gene", "label": "A", "properties": {}},
        "GENE:b": {"id": "GENE:b", "type": "Gene", "label": "B", "properties": {}},
    }
    edges = [
        {"id": "real:a", "source": "DRUG:one", "target": "GENE:a", "relation": "TARGETS", "evidence_ids": ["real:a"]},
        {"id": "real:b", "source": "DRUG:one", "target": "GENE:b", "relation": "INHIBITOR", "evidence_ids": ["real:b"]},
        {"id": "gene-link", "source": "GENE:a", "target": "GENE:b", "relation": "INTERACTS_WITH", "evidence_ids": ["gene-link"]},
    ]
    result = graph_repository._csv_subgraph("p", "DRUG:one", 1, 100, 0, nodes, edges)
    assert {node["id"] for node in result["nodes"]} == {"DRUG:one", "GENE:a", "GENE:b"}
    assert {edge["id"] for edge in result["edges"]} == {"real:a", "real:b"}
