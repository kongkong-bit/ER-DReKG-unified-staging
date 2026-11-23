import csv
import hashlib
import json
from functools import lru_cache
from pathlib import Path

from neo4j import GraphDatabase

from app.core.config import settings

CONTEXT_NODE_ID = "DISEASE_CONTEXT:GSE42568_ERPOS_TUMOR_VS_NORMAL"
# Project GraphBundle assertions can contain large provenance payloads.
csv.field_size_limit(16 * 1024 * 1024)


@lru_cache(maxsize=8)
def load_csv_graph(graph_dir: str | None = None) -> tuple[dict[str, dict], list[dict]]:
    if graph_dir is not None:
        root = Path(graph_dir).resolve()
    else:
        root = Path(settings.graph_data_dir)
        if not root.is_absolute():
            root = (Path(__file__).resolve().parents[2] / root).resolve()
    nodes = {}
    with (root / "subgraph_nodes.csv").open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            nodes[row["id"]] = {"id": row["id"], "type": row["type"], "label": row["label"], "properties": json.loads(row["properties_json"] or "{}")}
    edges_by_id = {}
    with (root / "subgraph_edges.csv").open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            props = json.loads(row["properties_json"] or "{}")
            edge_id = hashlib.sha256(f"{row['from']}|{row['label']}|{row['to']}|{row['source_release']}".encode()).hexdigest()
            # The source bundle may repeat an identical assertion several times.
            # Its stable ID is derived from the assertion key, so retain it once.
            edges_by_id.setdefault(edge_id, {"id": edge_id, "source": row["from"], "target": row["to"], "relation": row["relation"], "label": row["label"], "source_release": row["source_release"], "directed": row.get("undirected", "false").strip().lower() != "true", "properties": props, "evidence_ids": [edge_id]})
    extension = root.parent / "platform_phase_b_pathways" if graph_dir is None else None
    if extension and extension.exists():
        for filename in ["pathway_nodes.csv", "gene_nodes.csv"]:
            path = extension / filename
            if not path.exists():
                continue
            with path.open(encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    node_id = row["id"]
                    node = {"id": node_id, "type": row["type"], "label": row["label"], "properties": json.loads(row["properties_json"] or "{}")}
                    if node_id in nodes:
                        nodes[node_id]["properties"].update(node["properties"])
                        provenance = nodes[node_id]["properties"].setdefault("provenance_sources", [])
                        if isinstance(provenance, list) and "S1 pathway enrichment" not in provenance:
                            provenance.append("S1 pathway enrichment")
                    else:
                        nodes[node_id] = node
        path = extension / "pathway_edges.csv"
        if path.exists():
            with path.open(encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    props = json.loads(row["properties_json"] or "{}")
                    edge_id = hashlib.sha256(f"{row['from']}|{row['label']}|{row['to']}|{row['source_release']}".encode()).hexdigest()
                    edges_by_id.setdefault(edge_id, {"id": edge_id, "source": row["from"], "target": row["to"], "relation": row["relation"], "label": row["label"], "source_release": row["source_release"], "directed": row.get("undirected", "false").strip().lower() != "true", "properties": props, "evidence_ids": [edge_id]})
    return nodes, list(edges_by_id.values())


def graph_counts(project_slug: str, graph_build_id: str | None = None, graph_dir: str | None = None, project_id: str | None = None) -> dict:
    if settings.graph_source != "neo4j" and project_slug != "erpos-gse42568" and graph_dir is None:
        return {"node_count": 0, "edge_count": 0, "nodes_by_type": {}, "source": settings.graph_source}
    if settings.graph_source == "neo4j":
        driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
        try:
            with driver.session(database=settings.neo4j_database) as session:
                node_rows = session.run(
                    "MATCH (ctx:DiseaseContext) WHERE (ctx.project_slug = $slug OR ($project_id IS NOT NULL AND ctx.project_id = $project_id)) "
                    "WITH ctx WHERE $build_id IS NULL OR EXISTS { MATCH (ctx)-[seed]-() WHERE $build_id IN coalesce(seed.graph_build_ids, []) } "
                    "MATCH p=(ctx)-[*0..2]-(n) "
                    "WHERE $build_id IS NULL OR all(r IN relationships(p) WHERE $build_id IN coalesce(r.graph_build_ids, [])) "
                    "RETURN labels(n) AS labels, count(DISTINCT n) AS count",
                    slug=project_slug, project_id=project_id, build_id=graph_build_id,
                ).data()
                edge_record = session.run(
                    "MATCH (ctx:DiseaseContext) WHERE (ctx.project_slug = $slug OR ($project_id IS NOT NULL AND ctx.project_id = $project_id)) "
                    "WITH ctx WHERE $build_id IS NULL OR EXISTS { MATCH (ctx)-[seed]-() WHERE $build_id IN coalesce(seed.graph_build_ids, []) } "
                    "MATCH p=(ctx)-[*0..2]-(n) "
                    "WHERE $build_id IS NULL OR all(r IN relationships(p) WHERE $build_id IN coalesce(r.graph_build_ids, [])) "
                    "WITH collect(DISTINCT n) AS nodes "
                    "UNWIND nodes AS n "
                    "MATCH (n)-[r]-(m) WHERE m IN nodes AND ($build_id IS NULL OR $build_id IN coalesce(r.graph_build_ids, [])) "
                    "RETURN count(DISTINCT r) AS count",
                    slug=project_slug, project_id=project_id, build_id=graph_build_id,
                ).single()
            by_type = {row["labels"][0] if row["labels"] else "Unknown": row["count"] for row in node_rows}
            return {"node_count": sum(by_type.values()), "edge_count": edge_record["count"] if edge_record else 0, "nodes_by_type": by_type, "source": settings.graph_source}
        finally:
            driver.close()
    nodes, edges = load_csv_graph(graph_dir)
    by_type = {}
    for node in nodes.values():
        by_type[node["type"]] = by_type.get(node["type"], 0) + 1
    return {"node_count": len(nodes), "edge_count": len(edges), "nodes_by_type": by_type, "source": settings.graph_source}


def search_nodes(project_slug: str, query_text: str, limit: int = 20, graph_build_id: str | None = None, graph_dir: str | None = None, project_id: str | None = None) -> list[dict]:
    query_text = query_text.strip().casefold()
    if len(query_text) < 2:
        return []
    if settings.graph_source == "neo4j":
        driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
        query = """
        MATCH (ctx:DiseaseContext)
        WHERE (ctx.project_slug = $project_slug OR ($project_id IS NOT NULL AND ctx.project_id = $project_id))
        WITH ctx WHERE $build_id IS NULL OR EXISTS { MATCH (ctx)-[seed]-() WHERE $build_id IN coalesce(seed.graph_build_ids, []) }
        MATCH p=(ctx)-[*0..2]-(n)
        WHERE $build_id IS NULL OR all(r IN relationships(p) WHERE $build_id IN coalesce(r.graph_build_ids, []))
        WITH DISTINCT n
        WHERE toLower(coalesce(n.label, n.id, '')) CONTAINS $query_text
           OR toLower(coalesce(n.id, '')) CONTAINS $query_text
        RETURN n.id AS id,
               coalesce(head(labels(n)), 'Unknown') AS type,
               coalesce(n.label, n.id, '') AS label
        ORDER BY label LIMIT $limit
        """
        try:
            with driver.session(database=settings.neo4j_database) as session:
                return session.run(query, project_slug=project_slug, project_id=project_id, query_text=query_text, limit=limit, build_id=graph_build_id).data()
        finally:
            driver.close()
    if project_slug != "erpos-gse42568" and graph_dir is None:
        return []
    nodes, _ = load_csv_graph(graph_dir)
    hits = [n for n in nodes.values() if query_text in n["id"].casefold() or query_text in n["label"].casefold()]
    hits.sort(key=lambda n: (n["label"].casefold(), n["id"]))
    return [{"id": n["id"], "type": n["type"], "label": n["label"]} for n in hits[:limit]]


def get_subgraph(project_id: str, project_slug: str, node_id: str | None, max_depth: int, limit: int, cursor: int = 0, graph_build_id: str | None = None, analysis_run_id: str | None = None, graph_dir: str | None = None) -> dict:
    if settings.graph_source != "neo4j" and project_slug != "erpos-gse42568" and graph_dir is None:
        return {"project_id": project_id, "analysis_run_id": None, "nodes": [], "edges": [], "truncated": False, "next_cursor": None}
    if settings.graph_source == "neo4j":
        return _neo4j_subgraph(project_id, project_slug, node_id, max_depth, limit, cursor, graph_build_id, analysis_run_id)
    nodes, edges = load_csv_graph(graph_dir)
    return _csv_subgraph(project_id, node_id, max_depth, limit, cursor, nodes, edges, analysis_run_id)


def _csv_subgraph(project_id: str, node_id: str | None, max_depth: int, limit: int, cursor: int, nodes: dict[str, dict], edges: list[dict], analysis_run_id: str | None = None) -> dict:
    if not node_id:
        # The unfiltered graph view is paged by stable edge order. Include both
        # endpoints so the frontend can progressively assemble the full graph.
        ordered_edges = sorted(edges, key=lambda edge: edge["id"])
        page_edges = ordered_edges
        page_ids = {node_id for edge in page_edges for node_id in (edge["source"], edge["target"])}
        return {
            "project_id": project_id,
            "analysis_run_id": analysis_run_id or "PHASEB_OPTIMUSKG32_20261113",
            "nodes": [nodes[key] for key in sorted(page_ids) if key in nodes],
            "edges": [{**{key: edge[key] for key in ["id", "source", "target", "relation", "evidence_ids"]}, "directed": edge.get("directed", True)} for edge in page_edges],
            "truncated": False,
            "next_cursor": None,
        }
    if node_id not in nodes:
        return {"project_id": project_id, "analysis_run_id": None, "nodes": [], "edges": [], "truncated": False, "next_cursor": None}
    distances = {node_id: 0}
    frontier = {node_id}
    for depth in range(1, max_depth + 1):
        next_frontier = set()
        for edge in edges:
            if edge["source"] in frontier and edge["target"] not in distances:
                next_frontier.add(edge["target"])
            if edge["target"] in frontier and edge["source"] not in distances:
                next_frontier.add(edge["source"])
        for neighbor in next_frontier:
            distances[neighbor] = depth
        frontier = next_frontier
        if not frontier:
            break

    ordered_neighbors = sorted((key for key in distances if key != node_id), key=lambda key: (distances[key], key))
    page_size = max(1, limit - 1)  # Keep the anchor on every page.
    page_neighbors = ordered_neighbors[cursor:cursor + page_size]
    page_ids = {node_id, *page_neighbors}
    page_edges = [e for e in edges if e["source"] in page_ids and e["target"] in page_ids and (max_depth != 1 or node_id in {e["source"], e["target"]})]
    next_offset = cursor + len(page_neighbors)
    truncated = next_offset < len(ordered_neighbors)
    ordered_page_ids = [node_id, *page_neighbors]
    return {"project_id": project_id, "analysis_run_id": analysis_run_id or "PHASEB_OPTIMUSKG32_20261113", "nodes": [nodes[k] for k in ordered_page_ids], "edges": [{**{k: e[k] for k in ["id", "source", "target", "relation", "evidence_ids"]}, "directed": e.get("directed", True)} for e in page_edges], "truncated": truncated, "next_cursor": str(next_offset) if truncated else None}


def _neo4j_subgraph(project_id: str, project_slug: str, node_id: str | None, max_depth: int, limit: int, cursor: int, graph_build_id: str | None = None, analysis_run_id: str | None = None) -> dict:
    limit = max(2, min(limit, 200))
    page_size = limit - 1  # One slot is reserved for the center node on every page.
    driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    if not node_id:
        # A registered GraphBuild is already project-scoped by its relationship
        # provenance tags. Query those relationships directly instead of
        # repeating a two-hop path expansion over the complete graph.
        if graph_build_id:
            full_graph_query = """
            MATCH (a)-[r]-(b)
            WHERE $build_id IN coalesce(r.graph_build_ids, [])
            WITH DISTINCT r
            RETURN startNode(r).id AS source, endNode(r).id AS target,
                   coalesce(r.id, elementId(r)) AS id, type(r) AS relation,
                   coalesce(r.evidence_ids, []) AS evidence_ids
            """
            full_nodes_query = """
            MATCH (n)
            WHERE n.id IN $node_ids
            RETURN properties(n) AS node, labels(n) AS node_labels
            """
        else:
            full_graph_query = None
        context_match = "MATCH (ctx:DiseaseContext) WHERE ctx.project_slug = $project_slug OR ctx.project_id = $project_id"
        scoped_nodes = f"""
        {context_match}
        WITH collect(DISTINCT ctx) AS contexts
        UNWIND contexts AS ctx
        MATCH p=(ctx)-[*0..2]-(n)
        WHERE $build_id IS NULL OR all(rel IN relationships(p) WHERE $build_id IN coalesce(rel.graph_build_ids, []))
        WITH collect(DISTINCT n) AS nodes
        """
        scoped_graph_query = scoped_nodes + """
        UNWIND nodes AS a
        MATCH (a)-[r]-(b) WHERE b IN nodes AND ($build_id IS NULL OR $build_id IN coalesce(r.graph_build_ids, []))
        WITH DISTINCT r
        WITH r, startNode(r) AS a, endNode(r) AS b
        ORDER BY coalesce(r.id, elementId(r))
        RETURN properties(a) AS a, labels(a) AS a_labels, properties(r) AS edge,
               type(r) AS relation, properties(b) AS b, labels(b) AS b_labels
        """
        try:
            with driver.session(database=settings.neo4j_database) as session:
                query = full_graph_query or scoped_graph_query
                records = session.run(query, project_slug=project_slug, project_id=project_id, build_id=graph_build_id).data()
                if full_graph_query:
                    node_ids = sorted({node_id for record in records for node_id in (record["source"], record["target"]) if node_id})
                    node_records = session.run(full_nodes_query, node_ids=node_ids).data() if node_ids else []
                else:
                    node_records = None
            if node_records is None:
                page_nodes = {}
                page_edges = []
                for record in records:
                    for key, labels_key in (("a", "a_labels"), ("b", "b_labels")):
                        raw = record[key]
                        node_id_value = raw.get("id")
                        if node_id_value:
                            page_nodes[node_id_value] = {"id": node_id_value, "type": next(iter(record[labels_key]), "Unknown"), "label": raw.get("label", node_id_value), "properties": dict(raw)}
                    source = record["a"].get("id")
                    target = record["b"].get("id")
                    edge = record["edge"]
                    relation = record["relation"]
                    edge_id = edge.get("id") or f"{source}|{relation}|{target}"
                    page_edges.append({"id": edge_id, "source": source, "target": target, "relation": relation, "evidence_ids": edge.get("evidence_ids", []), "directed": True})
                nodes_result = list(page_nodes.values())
            else:
                page_edges = [{"id": record["id"], "source": record["source"], "target": record["target"], "relation": record["relation"], "evidence_ids": record["evidence_ids"], "directed": True} for record in records]
                nodes_result = [{"id": raw["node"]["id"], "type": next(iter(raw["node_labels"]), "Unknown"), "label": raw["node"].get("label", raw["node"]["id"]), "properties": raw["node"]} for raw in node_records if raw["node"].get("id")]
            return {"project_id": project_id, "analysis_run_id": analysis_run_id, "nodes": nodes_result, "edges": page_edges, "truncated": False, "next_cursor": None}
        finally:
            driver.close()
    page_size = limit - 1  # One slot is reserved for the center node on every page.
    if max_depth == 0:
        query = "MATCH (center {id: $node_id}) RETURN center, [] AS neighbors, 0 AS total"
    else:
        count_query = f"""
    MATCH (center {{id: $node_id}})
    OPTIONAL MATCH p=(center)-[*1..{max_depth}]-(neighbor)
    WHERE $build_id IS NULL OR all(r IN relationships(p) WHERE $build_id IN coalesce(r.graph_build_ids, []))
    WITH neighbor, min(length(p)) AS depth
    WHERE neighbor IS NOT NULL
    RETURN count(neighbor) AS total
    """
        query = f"""
    MATCH (center {{id: $node_id}})
    CALL (center) {{
      OPTIONAL MATCH p=(center)-[*1..{max_depth}]-(neighbor)
      WHERE $build_id IS NULL OR all(r IN relationships(p) WHERE $build_id IN coalesce(r.graph_build_ids, []))
      WITH neighbor, min(length(p)) AS depth
      WHERE neighbor IS NOT NULL
      ORDER BY depth, neighbor.id
      SKIP $cursor LIMIT $page_size
      RETURN collect({{node: neighbor, type: coalesce(head(labels(neighbor)), 'Unknown'), depth: depth}}) AS neighbors
    }}
    RETURN center, neighbors
    """
    try:
        with driver.session(database=settings.neo4j_database) as session:
            total = 0
            if max_depth > 0:
                count_record = session.run(count_query, node_id=node_id, build_id=graph_build_id).single()
                total = int(count_record["total"] if count_record else 0)
            record = session.run(query, node_id=node_id, build_id=graph_build_id, cursor=cursor, page_size=page_size).single()
            if not record:
                return {"project_id": project_id, "analysis_run_id": analysis_run_id, "nodes": [], "edges": [], "truncated": False, "next_cursor": None}
            center = record["center"]
            raw_neighbors = list(record["neighbors"] or [])
            page = list(record["neighbors"] or [])
            raw_nodes = [{"node": center, "type": next(iter(center.labels), "Unknown")}, *page]
            result_nodes = [{"id": item["node"].get("id"), "type": item["type"], "label": item["node"].get("label", item["node"].get("id", "")), "properties": dict(item["node"])} for item in raw_nodes]
            ids = {n["id"] for n in result_nodes}
            relationships = session.run("MATCH (a)-[r]-(b) WHERE a.id IN $ids AND b.id IN $ids AND ($max_depth <> 1 OR a.id = $node_id OR b.id = $node_id) AND ($build_id IS NULL OR $build_id IN coalesce(r.graph_build_ids, [])) RETURN DISTINCT startNode(r).id AS source,endNode(r).id AS target,type(r) AS relation,coalesce(r.evidence_ids,[]) AS evidence_ids,coalesce(r.id,startNode(r).id+'|'+type(r)+'|'+endNode(r).id) AS id", ids=list(ids), node_id=node_id, max_depth=max_depth, build_id=graph_build_id).data()
            edge_rows = [{"id": e["id"], "source": e["source"], "target": e["target"], "relation": e["relation"], "evidence_ids": e["evidence_ids"], "directed": True} for e in relationships]
            next_offset = cursor + len(page)
            truncated = next_offset < total
            return {"project_id": project_id, "analysis_run_id": analysis_run_id, "nodes": result_nodes, "edges": edge_rows, "truncated": truncated, "next_cursor": str(next_offset) if truncated else None}
    finally:
        driver.close()


def mechanism_for_pert_id(pert_id: str, project_slug: str, graph_build_id: str | None = None, graph_dir: str | None = None) -> list[dict]:
    if settings.graph_source == "neo4j":
        return _neo4j_mechanism_for_pert_id(pert_id, project_slug, graph_build_id)
    if project_slug != "erpos-gse42568" and graph_dir is None:
        return []
    return _csv_mechanism_for_pert_id(pert_id, project_slug, graph_dir)


def _json_relationship_assertion(relationship: dict) -> dict:
    raw = relationship.get("source_assertion_json")
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return {"raw": raw}


def _neo4j_mechanism_for_pert_id(pert_id: str, project_slug: str, graph_build_id: str | None = None) -> list[dict]:
    driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    public_query = """
    MATCH (c:Candidate {project_slug: $project_slug, pert_id: $pert_id})
          -[candidate_ref:REFERENCES_DRUG]->(d:Drug)-[target:TARGETS]->(g:Gene)
    MATCH (p)-[contains:CONTAINS_GENE]->(g)
    WHERE (p:Pathway OR p:GeneSet)
      AND ($build_id IS NULL OR ($build_id IN coalesce(candidate_ref.graph_build_ids, []) AND $build_id IN coalesce(target.graph_build_ids, []) AND $build_id IN coalesce(contains.graph_build_ids, [])))
    RETURN c.id AS candidate_id, d.id AS drug_id, g.id AS target_gene_id,
           p.id AS pathway_id, p.label AS pathway_label,
           target.evidence_ids AS target_evidence_ids,
           target.source_assertion_json AS target_assertion,
           contains.evidence_ids AS pathway_evidence_ids,
           contains.source_assertion_json AS pathway_assertion
    """
    enriched_query = """
    MATCH (c:Candidate {project_slug: $project_slug, pert_id: $pert_id})
          -[candidate_ref:REFERENCES_DRUG]->(d:Drug)-[target:TARGETS]->(g:Gene)
    MATCH (p)-[pathway_gene:HAS_ENRICHED_GENE]->(g)
    MATCH (ctx:DiseaseContext {project_slug: $project_slug})-[context_pathway:HAS_ENRICHED_PATHWAY]->(p)
    WHERE $build_id IS NULL OR ($build_id IN coalesce(candidate_ref.graph_build_ids, []) AND $build_id IN coalesce(target.graph_build_ids, []) AND $build_id IN coalesce(pathway_gene.graph_build_ids, []) AND $build_id IN coalesce(context_pathway.graph_build_ids, []))
    RETURN c.id AS candidate_id, d.id AS drug_id, g.id AS target_gene_id,
           p.id AS pathway_id, p.label AS pathway_label, ctx.id AS disease_context_id,
           candidate_ref.evidence_ids AS candidate_evidence_ids,
           candidate_ref.source_assertion_json AS candidate_assertion,
           target.evidence_ids AS target_evidence_ids,
           target.source_assertion_json AS target_assertion,
           pathway_gene.evidence_ids AS pathway_gene_evidence_ids,
           pathway_gene.source_assertion_json AS pathway_gene_assertion,
           context_pathway.evidence_ids AS context_evidence_ids,
           context_pathway.source_assertion_json AS context_assertion
    """
    routes = []
    try:
        with driver.session(database=settings.neo4j_database) as session:
            for row in session.run(public_query, project_slug=project_slug, pert_id=pert_id, build_id=graph_build_id):
                routes.append({
                    "route_type": "public_kg_pathway",
                    "drug_id": row["drug_id"],
                    "target_gene_id": row["target_gene_id"],
                    "pathway_id": row["pathway_id"],
                    "pathway_label": row["pathway_label"],
                    "evidence_ids": (row["target_evidence_ids"] or []) + (row["pathway_evidence_ids"] or []),
                    "source_assertions": [
                        _json_relationship_assertion({"source_assertion_json": row["target_assertion"]}),
                        _json_relationship_assertion({"source_assertion_json": row["pathway_assertion"]}),
                    ],
                })
            for row in session.run(enriched_query, project_slug=project_slug, pert_id=pert_id, build_id=graph_build_id):
                routes.append({
                    "route_type": "s1_enrichment_overlap",
                    "candidate_id": row["candidate_id"],
                    "drug_id": row["drug_id"],
                    "target_gene_id": row["target_gene_id"],
                    "pathway_id": row["pathway_id"],
                    "pathway_label": row["pathway_label"],
                    "disease_context_id": row["disease_context_id"],
                    "analysis_assertions": _json_relationship_assertion({"source_assertion_json": row["pathway_gene_assertion"]}).get("analysis_assertions", []),
                    "context_assertions": _json_relationship_assertion({"source_assertion_json": row["context_assertion"]}).get("analysis_assertions", []),
                    "evidence_ids": (
                        (row["candidate_evidence_ids"] or [])
                        + (row["target_evidence_ids"] or [])
                        + (row["pathway_gene_evidence_ids"] or [])
                        + (row["context_evidence_ids"] or [])
                    ),
                    "source_assertions": [
                        _json_relationship_assertion({"source_assertion_json": row["candidate_assertion"]}),
                        _json_relationship_assertion({"source_assertion_json": row["target_assertion"]}),
                        _json_relationship_assertion({"source_assertion_json": row["pathway_gene_assertion"]}),
                        _json_relationship_assertion({"source_assertion_json": row["context_assertion"]}),
                    ],
                })
        return routes
    finally:
        driver.close()


def _csv_mechanism_for_pert_id(pert_id: str, project_slug: str, graph_dir: str | None = None) -> list[dict]:
    nodes, edges = load_csv_graph(graph_dir)
    candidate_id = next((k for k, v in nodes.items() if v["type"] == "Candidate" and v["properties"].get("pert_id") == pert_id), None)
    if not candidate_id:
        return []
    reference_edges = [e for e in edges if e["source"] == candidate_id and e["relation"] == "REFERENCES_DRUG"]
    drug_ids = {e["target"] for e in reference_edges}
    target_edges = [e for e in edges if e["source"] in drug_ids and e["label"] == "DRG-GEN"]
    routes = []
    for target in target_edges:
        for pathway in edges:
            if pathway["label"] == "PWY-GEN" and pathway["target"] == target["target"]:
                routes.append({"route_type": "public_kg_pathway", "drug_id": target["source"], "target_gene_id": target["target"], "pathway_id": pathway["source"], "evidence_ids": target["evidence_ids"] + pathway["evidence_ids"], "source_assertions": [target["properties"], pathway["properties"]]})

    # Join the drug-side target edges to this project's independently sourced S1 enrichment.
    # This is an evidence intersection, not a causal or efficacy claim.
    enriched_gene_edges = [e for e in edges if e["label"] == "S1-ENRICHED-GENE"]
    enriched_context_ids = {node_id for node_id, node in nodes.items() if node["type"] == "DiseaseContext" and node["properties"].get("project_slug") == project_slug}
    enriched_context_edges = [e for e in edges if e["label"] == "S1-ENRICHED-PATHWAY" and e["source"] in enriched_context_ids]
    gene_to_pathway: dict[str, list[dict]] = {}
    for edge in enriched_gene_edges:
        gene_to_pathway.setdefault(edge["target"], []).append(edge)
    context_by_pathway = {edge["target"]: edge for edge in enriched_context_edges}
    reference_by_drug = {edge["target"]: edge for edge in reference_edges}
    for target in target_edges:
        candidate_reference = reference_by_drug.get(target["source"])
        if candidate_reference is None:
            continue
        for pathway_gene in gene_to_pathway.get(target["target"], []):
            context_edge = context_by_pathway.get(pathway_gene["source"])
            if context_edge is None:
                continue
            pathway_node = nodes.get(pathway_gene["source"], {})
            routes.append({
                "route_type": "s1_enrichment_overlap",
                "candidate_id": candidate_id,
                "drug_id": target["source"],
                "target_gene_id": target["target"],
                "pathway_id": pathway_gene["source"],
                "pathway_label": pathway_node.get("label", pathway_gene["source"]),
                "disease_context_id": context_edge["source"],
                "analysis_assertions": pathway_gene["properties"].get("analysis_assertions", []),
                "context_assertions": context_edge["properties"].get("analysis_assertions", []),
                "evidence_ids": candidate_reference["evidence_ids"] + target["evidence_ids"] + pathway_gene["evidence_ids"] + context_edge["evidence_ids"],
                "source_assertions": [candidate_reference["properties"], target["properties"], pathway_gene["properties"], context_edge["properties"]],
            })
    return routes


def get_evidence(evidence_id: str, graph_build_id: str | None = None, graph_dir: str | None = None) -> dict | None:
    if settings.graph_source == "neo4j":
        driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
        try:
            with driver.session(database=settings.neo4j_database) as session:
                row = session.run(
                    "MATCH ()-[r]->() WHERE $evidence_id IN coalesce(r.evidence_ids, []) "
                    "AND ($build_id IS NULL OR $build_id IN coalesce(r.graph_build_ids, [])) "
                    "RETURN r.source_release AS source_release, r.source_assertion_json AS assertion LIMIT 1",
                    evidence_id=evidence_id, build_id=graph_build_id,
                ).single()
            if not row:
                return None
            try:
                assertion = json.loads(row["assertion"] or "{}")
            except json.JSONDecodeError:
                assertion = {"raw": row["assertion"]}
            return {"evidence_id": evidence_id, "source_release": row["source_release"], "source_assertion": assertion, "source_url": assertion.get("source_urls")}
        finally:
            driver.close()
    _, edges = load_csv_graph(graph_dir)
    edge = next((e for e in edges if e["id"] == evidence_id), None)
    if edge is None:
        return None
    return {"evidence_id": edge["id"], "source_release": edge.get("source_release", "OptimusKG 3.2"), "source_assertion": edge["properties"], "source_url": edge["properties"].get("source_urls")}
