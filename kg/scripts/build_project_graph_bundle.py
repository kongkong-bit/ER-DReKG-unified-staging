"""Build a versioned, provenance-preserving per-project graph bundle.

This extractor only uses exact public-entity mappings. Ambiguous and missing
identifiers are retained in audit tables and never guessed into graph edges.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import platform
from pathlib import Path
from typing import Any
from importlib.metadata import version

import duckdb
import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[2]
PUBLIC_RELEASE = "OptimusKG 3.2"
PUBLIC_LICENSE = "CC BY-NC-SA 4.0"
LINCS_RELEASE = "GSE70138 Broad LINCS Level 5; perturbagen metadata 2017-03-06"
ALLOWED_TYPES = {"Drug", "Gene", "Pathway", "GeneSet", "Candidate", "DiseaseContext", "Disease", "DiseaseEvidence", "S2Condition"}
ALLOWED_RELATIONS = {
    "DRG-GEN", "PWY-GEN", "PROJECT-HAS_CANDIDATE", "PROJECT-REFERENCES_DRUG",
    "PROJECT-HAS_DEG", "S1-ENRICHED-PATHWAY", "S1-ENRICHED-GENE",
    "PROJECT-ABOUT_DISEASE", "PROJECT-HAS_S2_CONDITION", "DRG-DISEASE-EVIDENCE", "DISEASE-EVIDENCE-ABOUT",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def read_projected_parquet_nodes(path: Path, property_fields: list[str]) -> list[dict[str, Any]]:
    """Read only the node columns used by this extractor via DuckDB projection pushdown."""
    if any(not field.replace("_", "").isalnum() for field in property_fields):
        raise ValueError("Parquet property names must be simple schema identifiers")
    schema = pq.read_schema(path)
    available_fields = {field.name for field in schema.field("properties").type}
    selected_fields = [field for field in property_fields if field in available_fields]
    projections = ["id", "label"]
    projections.extend(f'properties."{field}" AS "__prop_{field}"' for field in selected_fields)
    query = f"SELECT {', '.join(projections)} FROM read_parquet(?)"
    with duckdb.connect(database=":memory:") as connection:
        rows = connection.execute(query, [str(path)]).to_arrow_table().to_pylist()
    result = []
    for row in rows:
        properties = {field: row.pop(f"__prop_{field}") if field in available_fields else None for field in property_fields}
        result.append({"id": row["id"], "label": row["label"], "properties": properties})
    return result


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def jdump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def norm(value: Any) -> str:
    return str(value or "").strip().upper()


def finite_number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def pathway_node(analysis: str, source_id: str, name: str) -> tuple[str, str, str]:
    analysis = analysis.upper()
    source_id = source_id.strip()
    if analysis.startswith("HALLMARK"):
        return "GeneSet", f"MSIGDB:{source_id.removeprefix('MSIGDB:')}", name or source_id
    if analysis.startswith("REACTOME"):
        stable = source_id.removeprefix("REACT:")
        return "Pathway", f"REACT:{stable}", name or stable
    return "Pathway", source_id, name or source_id


def _node(nodes: dict[str, dict], node_id: str, node_type: str, label: str, properties: dict) -> None:
    if node_type not in ALLOWED_TYPES:
        raise ValueError(f"未允许的节点类型：{node_type}")
    if not node_id:
        raise ValueError("图谱节点 ID 不能为空")
    existing = nodes.get(node_id)
    if existing and existing["type"] != node_type:
        raise ValueError(f"同一节点 ID 出现不同类型：{node_id}")
    if existing:
        merged = dict(existing["properties"])
        merged.update({key: value for key, value in properties.items() if value is not None})
        existing["properties"] = merged
        if label and (not existing["label"] or existing["label"] == node_id):
            existing["label"] = label
    else:
        nodes[node_id] = {"id": node_id, "type": node_type, "label": label or node_id, "properties": properties}


def _edge(edges: dict[tuple[str, str, str, str], dict], source: str, relation_label: str, target: str,
          relation: str, properties: dict, source_release: str, *, undirected: bool = False) -> None:
    if relation_label not in ALLOWED_RELATIONS:
        raise ValueError(f"未允许的图谱关系：{relation_label}")
    key = (source, relation_label, target, source_release)
    row = {"from": source, "label": relation_label, "to": target, "relation": relation,
           "undirected": bool(undirected), "source_release": source_release, "properties": properties}
    previous = edges.get(key)
    if previous:
        prior = previous["properties"].get("source_assertions")
        prior = list(prior) if prior is not None else [dict(previous["properties"])]
        current = properties.get("source_assertions")
        current = list(current) if current is not None else [dict(properties)]
        previous["properties"]["source_assertions"] = prior + current
        previous["properties"]["relation_conflict"] = bool(previous["properties"].get("relation_conflict") or properties.get("relation_conflict"))
        previous["properties"]["source_assertion_count"] = len(prior) + len(current)
        if "analysis_assertions" in previous["properties"] or "analysis_assertions" in properties:
            previous["properties"]["analysis_assertions"] = list(previous["properties"].get("analysis_assertions") or []) + list(properties.get("analysis_assertions") or [])
    else:
        edges[key] = row


def build_bundle(config: dict[str, Any]) -> dict[str, Any]:
    """Transform audited S1/S2/enrichment tables and public KG parquet into a bundle."""
    project_id = str(config["project_id"])
    project_slug = str(config["project_slug"])
    project_name = str(config["project_name"])
    disease_id = str(config.get("disease_id") or "")
    analysis_run_id = str(config["analysis_run_id"])
    s1_run_id = str(config["s1_analysis_run_id"])
    s2_run_id = str(config["s2_analysis_run_id"])
    enrichment_run_id = str(config["enrichment_analysis_run_id"])
    output = Path(config["output_dir"]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    public_dir = Path(config["public_kg_dir"]).resolve()
    s2_pert_info = Path(config["pert_info_path"]).resolve()
    s1_path = Path(config["s1_table"]).resolve()
    s1_mapping_path = Path(config["s1_mapping_audit"]).resolve()
    enrichment_dir = Path(config["enrichment_dir"]).resolve()
    s2_conditions_path = Path(config["s2_conditions"]).resolve()
    if not all(path.is_file() for path in [s1_path, s1_mapping_path, s2_conditions_path, s2_pert_info]):
        raise FileNotFoundError("S1、S2、富集映射或 LINCS pert_info 输入文件缺失")
    for path in [enrichment_dir / "pathway_gene_links.csv", enrichment_dir / "go_up.csv", enrichment_dir / "go_down.csv", enrichment_dir / "reactome_up.csv", enrichment_dir / "reactome_down.csv", enrichment_dir / "hallmark_gsea.csv"]:
        if not path.is_file():
            raise FileNotFoundError(f"富集运行缺少必需文件：{path.name}")

    source_manifest_path = public_dir / "source_manifest.json"
    if not source_manifest_path.is_file():
        raise FileNotFoundError("OptimusKG source_manifest.json 缺失")
    public_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    if public_manifest.get("license") and "CC BY-NC-SA" not in str(public_manifest["license"]):
        raise ValueError("OptimusKG 数据许可与本项目许可审计不匹配")

    # Read only the bounded local public KG tables required for seed expansion.
    # These OptimusKG node files contain large unused fields (for example drug
    # molfile/image payloads and gene literature arrays). DuckDB projection
    # pushdown keeps only the IDs and properties used by this bounded extractor.
    public_drugs = read_projected_parquet_nodes(
        public_dir / "nodes" / "drug.parquet",
        ["name", "inchi_key", "canonical_smiles", "source_ids", "synonyms", "sources"],
    )
    public_genes = read_projected_parquet_nodes(
        public_dir / "nodes" / "gene.parquet",
        ["symbol", "name", "biotype", "xrefs", "symbol_synonyms", "obsolete_symbols", "sources"],
    )
    public_pathways = read_projected_parquet_nodes(
        public_dir / "nodes" / "pathway.parquet", ["name", "sources"]
    )
    drug_gene_edges = pl.read_parquet(public_dir / "edges" / "drug_gene.parquet").to_dicts()
    pathway_gene_edges = pl.read_parquet(public_dir / "edges" / "pathway_gene.parquet").to_dicts()
    drug_by_id = {row["id"]: row for row in public_drugs}
    gene_by_id = {row["id"]: row for row in public_genes}
    pathway_by_id = {row["id"]: row for row in public_pathways}
    drugs_by_inchi: dict[str, list[dict]] = {}
    for row in public_drugs:
        inchi = norm((row.get("properties") or {}).get("inchi_key"))
        if inchi:
            drugs_by_inchi.setdefault(inchi, []).append(row)
    symbol_to_gene_ids: dict[str, set[str]] = {}
    entrez_to_gene_ids: dict[str, set[str]] = {}
    for row in public_genes:
        props = row.get("properties") or {}
        aliases = [props.get("symbol"), *(props.get("symbol_synonyms") or []), *(props.get("obsolete_symbols") or [])]
        for alias in aliases:
            label = alias.get("label") if isinstance(alias, dict) else alias
            if label:
                symbol_to_gene_ids.setdefault(norm(label), set()).add(row["id"])
        for xref in props.get("xrefs") or []:
            if str(xref.get("source", "")).casefold() in {"entrez", "entrezgene", "ncbigene"}:
                entrez_to_gene_ids.setdefault(str(xref.get("id", "")).strip(), set()).add(row["id"])

    nodes: dict[str, dict] = {}
    edges: dict[tuple[str, str, str, str], dict] = {}
    context_id = f"DISEASE_CONTEXT:{project_id}:{analysis_run_id.rsplit(':', 1)[-1]}"
    context_props = {"project_id": project_id, "project_slug": project_slug, "project_name": project_name,
                     "disease_id": disease_id, "analysis_run_id": analysis_run_id, "s1_analysis_run_id": s1_run_id,
                     "s2_analysis_run_id": s2_run_id, "enrichment_analysis_run_id": enrichment_run_id,
                     "test_only": bool(config.get("test_only")), "source": "project-scoped analysis context"}
    _node(nodes, context_id, "DiseaseContext", project_name, context_props)
    if disease_id and (disease_id.startswith(("MONDO:", "EFO:", "DOID:"))):
        _node(nodes, disease_id, "Disease", disease_id, {"id_namespace": disease_id.split(":", 1)[0], "source": "project metadata", "test_only": bool(config.get("test_only"))})
        _edge(edges, context_id, "PROJECT-ABOUT_DISEASE", disease_id, "ABOUT_DISEASE", {"analysis_run_id": analysis_run_id, "assertion_type": "project context annotation"}, "DiseaseGraph project metadata")

    mapping_rows = read_csv(s1_mapping_path)
    mapping_by_source: dict[str, set[str]] = {}
    for row in mapping_rows:
        raw_id = str(row.get("gene_id") or "").strip()
        ensembl = {item.strip().split(".", 1)[0] for item in str(row.get("ensembl_gene_ids") or "").split("|") if item.strip()}
        if raw_id:
            mapping_by_source.setdefault(raw_id, set()).update(ensembl)
    s1_rows = read_csv(s1_path)
    s1_audit: list[dict] = []
    selected_s1_genes: set[str] = set()
    s1_fdr = float(config.get("s1_fdr_threshold", 0.05))
    for row in s1_rows:
        raw_id = str(row.get("gene_id") or row.get("gene_symbol") or "").strip()
        fdr = finite_number(row.get("adj.P.Val"))
        logfc = finite_number(row.get("logFC"))
        if not raw_id or fdr is None or logfc is None or fdr >= s1_fdr or logfc == 0:
            continue
        hits = set(mapping_by_source.get(raw_id, set()))
        if not hits:
            hits = set(symbol_to_gene_ids.get(norm(row.get("gene_symbol") or raw_id), set()))
        status = "mapped_unique_ensembl" if len(hits) == 1 else "ambiguous_ensembl" if len(hits) > 1 else "unmatched_public_gene"
        mapped_id = next(iter(hits)) if len(hits) == 1 else ""
        s1_audit.append({"gene_id": raw_id, "gene_symbol": row.get("gene_symbol", raw_id), "logFC": row.get("logFC", ""), "adj.P.Val": row.get("adj.P.Val", ""), "t": row.get("t", ""), "direction": "UP" if logfc > 0 else "DOWN", "ensembl_gene_id": mapped_id, "mapping_status": status})
        if not mapped_id:
            continue
        selected_s1_genes.add(mapped_id)
        public_gene = gene_by_id.get(mapped_id)
        if public_gene:
            props = public_gene.get("properties") or {}
            _node(nodes, mapped_id, "Gene", props.get("symbol") or mapped_id, {key: props.get(key) for key in ["symbol", "name", "biotype", "xrefs", "sources"] if props.get(key) is not None})
        else:
            _node(nodes, mapped_id, "Gene", row.get("gene_symbol") or mapped_id, {"ensembl_gene_id": mapped_id, "source": "org.Hs.eg.db mapping; public KG entity absent"})
        _edge(edges, context_id, "PROJECT-HAS_DEG", mapped_id, "HAS_DEG", {"analysis_run_id": s1_run_id, "gene_id": raw_id, "gene_symbol": row.get("gene_symbol") or raw_id, "logFC": logfc, "adj.P.Val": fdr, "t": finite_number(row.get("t")), "direction": "UP" if logfc > 0 else "DOWN", "source_record_id": f"{s1_run_id}:{raw_id}"}, str(config.get("s1_source_release") or "Project S1 differential expression"))

    significant_pathways: dict[str, dict] = {}
    for filename, analysis, id_column, name_column, p_column in [
        ("go_up.csv", "GO_UP", "ID", "Description", "p.adjust"),
        ("go_down.csv", "GO_DOWN", "ID", "Description", "p.adjust"),
        ("reactome_up.csv", "REACTOME_UP", "ID", "Description", "p.adjust"),
        ("reactome_down.csv", "REACTOME_DOWN", "ID", "Description", "p.adjust"),
        ("hallmark_gsea.csv", "HALLMARK_GSEA", "pathway", "pathway", "padj"),
    ]:
        for row in read_csv(enrichment_dir / filename):
            source_id = str(row.get(id_column) or "").strip()
            adjusted_p = finite_number(row.get(p_column))
            if not source_id or adjusted_p is None or adjusted_p >= 0.05:
                continue
            name = str(row.get(name_column) or source_id).strip()
            node_type, path_id, label = pathway_node(analysis, source_id, name)
            details = significant_pathways.setdefault(path_id, {"type": node_type, "label": label, "source_pathway_id": source_id, "analysis_assertions": []})
            details["analysis_assertions"].append({"analysis_run_id": enrichment_run_id, "s1_analysis_run_id": s1_run_id, "analysis": analysis, "pathway_id": source_id, "adjusted_p": adjusted_p, "NES": finite_number(row.get("NES")), "source_record_id": f"{enrichment_run_id}:{analysis}:{source_id}"})

    pathway_links = read_csv(enrichment_dir / "pathway_gene_links.csv")
    pathway_mapping_audit: list[dict] = []
    pathway_to_gene_ids: dict[str, set[str]] = {}
    for row in pathway_links:
        raw_analysis = str(row.get("analysis") or "").strip()
        name = str(row.get("pathway") or "").strip()
        source_pathway_id = str(row.get("pathway_id") or "").strip()
        if not source_pathway_id and raw_analysis.startswith("GO:"):
            # project_s1_enrichment.R stores the GO stable ID in `analysis`
            # and the display label in `pathway`.
            analysis, source_pathway_id = "GO", raw_analysis
        elif not source_pathway_id and raw_analysis.startswith("R-HSA-"):
            analysis, source_pathway_id = "REACTOME", raw_analysis
        elif not source_pathway_id and raw_analysis == "HALLMARK_GSEA":
            analysis, source_pathway_id = "HALLMARK_GSEA", name
        elif not source_pathway_id and raw_analysis.startswith("HALLMARK_"):
            analysis, source_pathway_id = "HALLMARK_GSEA", raw_analysis
        else:
            analysis = raw_analysis
            source_pathway_id = source_pathway_id or name
        name = name or source_pathway_id
        adjusted_p = finite_number(row.get("adjusted_p"))
        if not analysis or not source_pathway_id or adjusted_p is None or adjusted_p >= 0.05:
            continue
        node_type, path_id, label = pathway_node(analysis, source_pathway_id, name)
        details = significant_pathways.setdefault(path_id, {"type": node_type, "label": label, "source_pathway_id": source_pathway_id, "analysis_assertions": []})
        if not details["analysis_assertions"]:
            details["analysis_assertions"].append({"analysis_run_id": enrichment_run_id, "s1_analysis_run_id": s1_run_id, "analysis": analysis, "pathway_id": source_pathway_id, "adjusted_p": adjusted_p, "NES": finite_number(row.get("NES")), "source_record_id": f"{enrichment_run_id}:{analysis}:{source_pathway_id}"})
        raw_ensembl = {item.strip().split(".", 1)[0] for item in str(row.get("ensembl_gene_ids") or "").split("|") if item.strip()}
        if not raw_ensembl:
            entrez = str(row.get("ENTREZID") or "").strip()
            raw_ensembl = set(entrez_to_gene_ids.get(entrez, set()))
        status = "mapped_unique_ensembl" if len(raw_ensembl) == 1 else "ambiguous_ensembl" if len(raw_ensembl) > 1 else "unmatched_public_gene"
        mapped_gene = next(iter(raw_ensembl)) if len(raw_ensembl) == 1 else ""
        pathway_mapping_audit.append({"analysis": analysis, "pathway_id": source_pathway_id, "entrez_id": row.get("ENTREZID", ""), "gene_symbol": row.get("gene_symbol", ""), "ensembl_gene_ids": "|".join(sorted(raw_ensembl)), "mapping_status": status})
        if not mapped_gene:
            continue
        pathway_to_gene_ids.setdefault(path_id, set()).add(mapped_gene)
        if mapped_gene not in nodes:
            public_gene = gene_by_id.get(mapped_gene)
            props = (public_gene or {}).get("properties") or {}
            _node(nodes, mapped_gene, "Gene", props.get("symbol") or row.get("gene_symbol") or mapped_gene, {key: props.get(key) for key in ["symbol", "name", "biotype", "xrefs", "sources"] if props.get(key) is not None})
        assertion = {"analysis_run_id": enrichment_run_id, "s1_analysis_run_id": s1_run_id, "analysis": analysis,
                        "pathway_id": source_pathway_id, "adjusted_p": adjusted_p, "entrez_id": row.get("ENTREZID"),
                        "gene_symbol": row.get("gene_symbol"), "ensembl_gene_id": mapped_gene,
                        "source_record_id": f"{enrichment_run_id}:{analysis}:{source_pathway_id}:{row.get('ENTREZID', '')}"}
        _edge(edges, path_id, "S1-ENRICHED-GENE", mapped_gene, "HAS_ENRICHED_GENE", {"analysis_assertions": [assertion], "source_record_id": assertion["source_record_id"]}, "Project S1 pathway enrichment")

    mapped_pathway_link_count = sum(row["mapping_status"] == "mapped_unique_ensembl" for row in pathway_mapping_audit)
    if pathway_mapping_audit and mapped_pathway_link_count == 0:
        raise ValueError(
            "通路富集输入包含通路—基因链接，但没有任何一条唯一映射到 Ensembl；"
            "拒绝生成状态为 validated 的 GraphBundle。请补齐 Entrez/Symbol 到 Ensembl 的映射列并重试。"
        )

    for path_id, details in significant_pathways.items():
        public_path = pathway_by_id.get(path_id)
        public_props = (public_path or {}).get("properties") or {}
        _node(nodes, path_id, details["type"], details["label"], {"name": public_props.get("name") or details["label"], "source_pathway_id": details["source_pathway_id"], "sources": public_props.get("sources"), "source_release": PUBLIC_RELEASE})
        pathway_assertions = details["analysis_assertions"]
        _edge(edges, context_id, "S1-ENRICHED-PATHWAY", path_id, "HAS_ENRICHED_PATHWAY", {"analysis_assertions": pathway_assertions, "source_record_id": pathway_assertions[0]["source_record_id"] if pathway_assertions else ""}, "Project S1 pathway enrichment")

    # The LINCS mapping is structure-exact. Perturbagen names are retained for display only.
    opener = gzip.open if s2_pert_info.suffix.lower() == ".gz" else open
    with opener(s2_pert_info, "rt", encoding="utf-8-sig", newline="") as stream:
        pert_reader = csv.DictReader(stream, delimiter="\t")
        pert_info = {row["pert_id"]: row for row in pert_reader if row.get("pert_id") and row.get("pert_type") == "trt_cp"}
    inchi_to_public = {}
    for row in public_drugs:
        key = norm((row.get("properties") or {}).get("inchi_key"))
        if key:
            inchi_to_public.setdefault(key, []).append(row)
    conditions = read_csv(s2_conditions_path)
    by_pert: dict[str, list[dict]] = {}
    for row_num, row in enumerate(conditions, start=2):
        pert_id = str(row.get("pert_id") or "").strip()
        if not pert_id:
            continue
        by_pert.setdefault(pert_id, []).append(row)
    candidate_mapping_audit: list[dict] = []
    candidates: dict[str, dict] = {}
    selected_drug_ids: set[str] = set()
    condition_nodes: dict[str, dict] = {}
    for pert_id, rows in sorted(by_pert.items()):
        pert = pert_info.get(pert_id, {})
        inchi = norm(pert.get("inchi_key"))
        hits = inchi_to_public.get(inchi, []) if inchi else []
        mapping_status = "matched_exact_inchikey" if len(hits) == 1 else "ambiguous_inchikey" if len(hits) > 1 else "unmatched_no_exact_inchikey"
        drug = hits[0] if len(hits) == 1 else None
        candidate_id = f"CANDIDATE:{project_id}:{s2_run_id.rsplit(':', 1)[-1]}:{pert_id}"
        score_rows = [{key: row.get(key) for key in ["cell_id", "pert_type", "dose", "time", "n_signatures", "WTCS_median", "WTCS_mean", "WTCS_sd", "WTCS_mad", "quality_cc_median", "TAS_median", "replicates_median", "rank_within_condition"]} for row in rows]
        candidates[pert_id] = {"id": candidate_id, "drug_id": drug["id"] if drug else "", "name": pert.get("pert_iname") or rows[0].get("drug_name") or pert_id, "mapping_status": mapping_status, "conditions": score_rows}
        _node(nodes, candidate_id, "Candidate", candidates[pert_id]["name"], {"project_id": project_id, "project_slug": project_slug, "analysis_run_id": s2_run_id, "pert_id": pert_id, "mapping_status": mapping_status, "inchi_key": inchi or None, "condition_count": len(rows), "condition_scores": score_rows, "test_only": bool(config.get("test_only")), "score_interpretation": "condition-specific WTCS association; no cross-dose efficacy ranking"})
        _edge(edges, context_id, "PROJECT-HAS_CANDIDATE", candidate_id, "HAS_CANDIDATE", {"analysis_run_id": s2_run_id, "pert_id": pert_id, "condition_count": len(rows), "source_record_id": f"{s2_run_id}:{pert_id}"}, "Project S2 LINCS results")
        if drug:
            selected_drug_ids.add(drug["id"])
            drug_props = drug.get("properties") or {}
            _node(nodes, drug["id"], "Drug", drug_props.get("name") or drug["id"], {key: drug_props.get(key) for key in ["name", "inchi_key", "canonical_smiles", "source_ids", "synonyms", "sources"] if drug_props.get(key) is not None})
            _edge(edges, candidate_id, "PROJECT-REFERENCES_DRUG", drug["id"], "REFERENCES_DRUG", {"analysis_run_id": s2_run_id, "pert_id": pert_id, "mapping_method": "exact InChIKey", "inchi_key": inchi, "source_record_id": f"LINCS pert_info:{pert_id}"}, LINCS_RELEASE)
        candidate_mapping_audit.append({"pert_id": pert_id, "pert_iname": candidates[pert_id]["name"], "inchi_key": inchi, "graph_drug_id": drug["id"] if drug else "", "mapping_status": mapping_status, "mapping_method": "exact InChIKey" if drug else "none", "condition_rows": len(rows)})
        for index, row in enumerate(rows):
            condition_key = "|".join(str(row.get(key) or "") for key in ["cell_id", "pert_type", "dose", "time"])
            condition_hash = hashlib.sha256(f"{pert_id}|{condition_key}".encode()).hexdigest()[:16]
            condition_id = f"S2_CONDITION:{project_id}:{s2_run_id.rsplit(':', 1)[-1]}:{pert_id}:{condition_hash}"
            condition_nodes[condition_id] = row
            condition_properties = {"project_id": project_id, "analysis_run_id": s2_run_id, "pert_id": pert_id,
                                    "condition_key": condition_key, "cell_id": row.get("cell_id"), "pert_type": row.get("pert_type"),
                                    "dose": row.get("dose"), "time": row.get("time"), "n_signatures": finite_number(row.get("n_signatures")),
                                    "WTCS_median": finite_number(row.get("WTCS_median")), "WTCS_mean": finite_number(row.get("WTCS_mean")),
                                    "WTCS_sd": finite_number(row.get("WTCS_sd")), "WTCS_mad": finite_number(row.get("WTCS_mad")),
                                    "quality_cc_median": finite_number(row.get("quality_cc_median")), "TAS_median": finite_number(row.get("TAS_median")),
                                    "rank_within_condition": finite_number(row.get("rank_within_condition")),
                                    "source_record_id": f"{s2_run_id}:condition:{pert_id}:{condition_key}", "test_only": bool(config.get("test_only"))}
            _node(nodes, condition_id, "S2Condition", f"{candidates[pert_id]['name']} · {condition_key}", condition_properties)
            _edge(edges, candidate_id, "PROJECT-HAS_S2_CONDITION", condition_id, "HAS_S2_CONDITION", {"analysis_run_id": s2_run_id, "source_record_id": condition_properties["source_record_id"]}, "Project S2 LINCS results")

    # Preserve all public target assertions for mapped candidate drugs, while keeping
    # only their direct, bounded target relationships; no unrestricted graph expansion.
    selected_targets: set[str] = set()
    public_target_edges = []
    for edge in drug_gene_edges:
        if edge.get("from") not in selected_drug_ids:
            continue
        gene_id = edge.get("to")
        if gene_id not in gene_by_id:
            continue
        selected_targets.add(gene_id)
        public_target_edges.append(edge)
    for gene_id in selected_targets:
        if gene_id not in nodes:
            props = gene_by_id[gene_id].get("properties") or {}
            _node(nodes, gene_id, "Gene", props.get("symbol") or gene_id, {key: props.get(key) for key in ["symbol", "name", "biotype", "xrefs", "sources"] if props.get(key) is not None})
    for edge in public_target_edges:
        props = edge.get("properties") or {}
        _edge(edges, edge["from"], edge["label"], edge["to"], edge["relation"], {**props, "source_record_id": f"{PUBLIC_RELEASE}:drug_gene:{edge['from']}:{edge['to']}"}, PUBLIC_RELEASE, undirected=bool(edge.get("undirected")))

    # Add the exact public pathway-gene assertions for project-significant pathway genes.
    selected_pathway_gene_ids = {(path_id, gene_id) for path_id, gene_ids in pathway_to_gene_ids.items() for gene_id in gene_ids}
    for edge in pathway_gene_edges:
        if (edge.get("from"), edge.get("to")) not in selected_pathway_gene_ids:
            continue
        public_path_id = edge["from"]
        if public_path_id not in nodes:
            continue
        props = edge.get("properties") or {}
        _edge(edges, public_path_id, edge["label"], edge["to"], edge["relation"], {**props, "source_record_id": f"{PUBLIC_RELEASE}:pathway_gene:{edge['from']}:{edge['to']}"}, PUBLIC_RELEASE, undirected=bool(edge.get("undirected")))

    routes = []
    drug_target_by_drug: dict[str, set[str]] = {}
    for edge in public_target_edges:
        drug_target_by_drug.setdefault(edge["from"], set()).add(edge["to"])
    for pert_id, candidate in candidates.items():
        drug_id = candidate["drug_id"]
        if not drug_id:
            continue
        for gene_id in sorted(drug_target_by_drug.get(drug_id, set())):
            for path_id, gene_ids in pathway_to_gene_ids.items():
                if gene_id not in gene_ids:
                    continue
                routes.append({"pert_id": pert_id, "drug_id": drug_id, "target_gene_id": gene_id, "pathway_id": path_id,
                               "disease_context_id": context_id, "interpretation": "证据关系交汇；不是因果或疗效证据"})

    # Validate endpoints and preserve source assertion conflicts before writing.
    node_ids = set(nodes)
    if any(edge["from"] not in node_ids or edge["to"] not in node_ids for edge in edges.values()):
        raise ValueError("bundle 中发现端点不存在的关系")
    edge_rows = []
    evidence_rows = []
    conflicts = []
    for edge in sorted(edges.values(), key=lambda row: (row["from"], row["label"], row["to"], row["source_release"])):
        assertion = edge["properties"]
        properties_json = jdump(assertion)
        edge_rows.append({"from": edge["from"], "label": edge["label"], "to": edge["to"], "relation": edge["relation"], "undirected": str(edge["undirected"]).lower(), "source_release": edge["source_release"], "properties_json": properties_json})
        evidence_id = hashlib.sha256(f"{edge['from']}|{edge['label']}|{edge['to']}|{edge['source_release']}".encode()).hexdigest()
        evidence_rows.append({"evidence_id": evidence_id, "source_release": edge["source_release"], "source_record_id": assertion.get("source_record_id", ""), "subject_id": edge["from"], "predicate": edge["relation"], "object_id": edge["to"], "source_assertion_json": properties_json})
        if assertion.get("relation_conflict") is True:
            conflicts.append({"subject_id": edge["from"], "predicate": edge["relation"], "object_id": edge["to"], "source_release": edge["source_release"], "source_assertion_json": properties_json, "relation_conflict": True})
    node_rows = [{"id": row["id"], "type": row["type"], "label": row["label"], "properties_json": jdump(row["properties"])} for row in sorted(nodes.values(), key=lambda row: row["id"])]

    write_csv(output / "subgraph_nodes.csv", node_rows, ["id", "type", "label", "properties_json"])
    write_csv(output / "subgraph_edges.csv", edge_rows, ["from", "label", "to", "relation", "undirected", "source_release", "properties_json"])
    write_csv(output / "candidate_mapping_audit.csv", candidate_mapping_audit, ["pert_id", "pert_iname", "inchi_key", "graph_drug_id", "mapping_status", "mapping_method", "condition_rows"])
    write_csv(output / "s1_gene_mapping_audit.csv", s1_audit, ["gene_id", "gene_symbol", "logFC", "adj.P.Val", "t", "direction", "ensembl_gene_id", "mapping_status"])
    write_csv(output / "pathway_gene_mapping_audit.csv", pathway_mapping_audit, ["analysis", "pathway_id", "entrez_id", "gene_symbol", "ensembl_gene_ids", "mapping_status"])
    unmatched = [{"entity_type": "candidate_drug", **row} for row in candidate_mapping_audit if row["mapping_status"] != "matched_exact_inchikey"]
    unmatched.extend({"entity_type": "S1_gene", **row} for row in s1_audit if row["mapping_status"] != "mapped_unique_ensembl")
    unmatched.extend({"entity_type": "pathway_gene", **row} for row in pathway_mapping_audit if row["mapping_status"] != "mapped_unique_ensembl")
    write_csv(output / "unmatched_entities.csv", unmatched, ["entity_type", "pert_id", "pert_iname", "inchi_key", "mapping_status", "gene_id", "gene_symbol", "logFC", "adj.P.Val", "t", "direction", "ensembl_gene_id", "analysis", "pathway_id", "entrez_id", "ensembl_gene_ids", "graph_drug_id"])
    write_csv(output / "relation_conflicts.csv", conflicts, ["subject_id", "predicate", "object_id", "source_release", "source_assertion_json", "relation_conflict"])
    write_csv(output / "evidence_records.csv", evidence_rows, ["evidence_id", "source_release", "source_record_id", "subject_id", "predicate", "object_id", "source_assertion_json"])
    write_csv(output / "candidate_target_pathway_routes.csv", routes, ["pert_id", "drug_id", "target_gene_id", "pathway_id", "disease_context_id", "interpretation"])

    # Run an ontology-aware schema translation audit before blessing the bundle.
    # The version-aware Neo4j importer remains separate so BioCypher's batch
    # import path can never wipe or replace the live graph.
    try:
        from .biocypher_adapter import validate_bundle_directory
    except ImportError:  # direct CLI execution sets kg/scripts as sys.path[0]
        from biocypher_adapter import validate_bundle_directory
    biocypher_validation = validate_bundle_directory(output)

    input_paths = [s1_path, s1_mapping_path, s2_conditions_path, s2_pert_info, source_manifest_path,
                   ROOT / "kg" / "pyproject.toml", ROOT / "kg" / "uv.lock",
                   public_dir / "nodes" / "drug.parquet", public_dir / "nodes" / "gene.parquet", public_dir / "nodes" / "pathway.parquet",
                   public_dir / "edges" / "drug_gene.parquet", public_dir / "edges" / "pathway_gene.parquet",
                   enrichment_dir / "pathway_gene_links.csv", enrichment_dir / "go_up.csv", enrichment_dir / "go_down.csv",
                   enrichment_dir / "reactome_up.csv", enrichment_dir / "reactome_down.csv", enrichment_dir / "hallmark_gsea.csv"]
    input_paths.append(Path(__file__).resolve())
    if config.get("config_path"):
        input_paths.append(Path(config["config_path"]).resolve())
    input_hashes = {}
    for path in input_paths:
        try:
            key = path.relative_to(ROOT).as_posix()
        except ValueError:
            key = str(path.resolve())
        input_hashes[key] = sha256(path)
    manifest = {
        "bundle_version": "1", "status": "validated", "project_id": project_id, "project_slug": project_slug,
        "analysis_run_id": analysis_run_id, "s1_analysis_run_id": s1_run_id, "s2_analysis_run_id": s2_run_id,
        "enrichment_analysis_run_id": enrichment_run_id, "test_only": bool(config.get("test_only")),
        "software_versions": {"python": platform.python_version(), "duckdb": duckdb.__version__, "polars": pl.__version__, "pyarrow": pa.__version__, "biocypher": version("biocypher")},
        "public_kg_release": PUBLIC_RELEASE, "public_kg_license": PUBLIC_LICENSE,
        "lincs_release": LINCS_RELEASE, "mapping_policy": "exact InChIKey for compounds; unique Ensembl gene mapping; unresolved or ambiguous entities are retained in audit only",
        "cross_dose_policy": "retain every exact dose/time condition as its own S2Condition node; no per-drug best score or cross-condition rank",
        "input_hashes": input_hashes, "output_hashes": {},
        "counts": {"nodes": len(node_rows), "edges": len(edge_rows), "s1_significant_genes": len(s1_audit),
                   "s1_unique_ensembl_mapped": sum(row["mapping_status"] == "mapped_unique_ensembl" for row in s1_audit),
                   "s1_ambiguous_or_unmatched": sum(row["mapping_status"] != "mapped_unique_ensembl" for row in s1_audit),
                   "pathway_gene_links": len(pathway_mapping_audit), "pathway_gene_unique_mapped": sum(row["mapping_status"] == "mapped_unique_ensembl" for row in pathway_mapping_audit),
                   "candidate_perturbagens": len(candidate_mapping_audit), "exact_inchikey_mapped_drugs": sum(row["mapping_status"] == "matched_exact_inchikey" for row in candidate_mapping_audit),
                   "s2_condition_rows": len(conditions), "candidate_target_pathway_routes": len(routes), "relation_conflicts": len(conflicts), "unmatched_entities": len(unmatched)},
    }
    output_files = [output / name for name in ["subgraph_nodes.csv", "subgraph_edges.csv", "candidate_mapping_audit.csv", "s1_gene_mapping_audit.csv", "pathway_gene_mapping_audit.csv", "unmatched_entities.csv", "relation_conflicts.csv", "evidence_records.csv", "candidate_target_pathway_routes.csv", "biocypher_validation.json"]]
    manifest["output_hashes"] = {path.name: sha256(path) for path in output_files}
    (output / "bundle_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "bundle_checksums.json").write_text(json.dumps({**manifest["output_hashes"], "bundle_manifest.json": sha256(output / "bundle_manifest.json")}, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="按项目 S1/S2/富集运行构建可追溯 GraphBundle")
    parser.add_argument("--config", type=Path, required=True, help="项目运行生成的 JSON 配置文件")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = build_bundle(config)
    print(json.dumps({"status": result["status"], "project_id": result["project_id"], "analysis_run_id": result["analysis_run_id"], "output_dir": config["output_dir"], "counts": result["counts"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
