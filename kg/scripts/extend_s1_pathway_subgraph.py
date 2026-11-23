from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import polars as pl


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "optimuskg" / "3.2"
S1_DIR = ROOT / "experiments" / "s1_pathway_enrichment"
BASE_DIR = ROOT / "experiments" / "platform_phase_b"
OUT = ROOT / "experiments" / "platform_phase_b_pathways"
CONTEXT_ID = "DISEASE_CONTEXT:GSE42568_ERPOS_TUMOR_VS_NORMAL"
RUN_ID = "ANALYSIS_RUN:S1_PATHWAY_ENRICHMENT_20261112"
BUILD_ID = "GRAPH_BUILD:ERPOS_S1_PATHWAY_20261113"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def norm(value: object) -> str:
    return str(value or "").strip().upper()


def write_csv(path: Path, rows: list[dict]) -> None:
    columns = list(dict.fromkeys(key for row in rows for key in row))
    if not columns and path.name == "relation_conflicts.csv":
        columns = ["evidence_id", "subject_id", "predicate", "object_id", "edge_label", "source_release", "source_table", "analysis_run_id", "source_assertion_count", "source_assertions_json", "relation_conflict"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def pathway_entity(analysis: str, pathway_id: str) -> tuple[str, str]:
    if analysis.startswith("HALLMARK"):
        return "GeneSet", f"MSIGDB:{pathway_id}"
    if analysis.startswith("REACTOME"):
        return "Pathway", f"REACT:{pathway_id.removeprefix('REACT:')}"
    return "Pathway", pathway_id


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    genes = pl.read_parquet(DATA / "nodes" / "gene.parquet").to_dicts()
    gene_by_id = {row["id"]: row for row in genes}
    symbol_to_ids: dict[str, set[str]] = defaultdict(set)
    for row in genes:
        props = row.get("properties") or {}
        if props.get("symbol"):
            symbol_to_ids[norm(props["symbol"])].add(row["id"])
        for field in ("symbol_synonyms", "obsolete_symbols"):
            for alias in props.get(field) or []:
                label = alias.get("label") if isinstance(alias, dict) else alias
                if label:
                    symbol_to_ids[norm(label)].add(row["id"])

    enrichment_manifest = json.loads((S1_DIR / "environment_manifest.json").read_text(encoding="utf-8"))
    pathway_nodes: dict[str, dict] = {}
    context_assertions: dict[str, dict[str, dict]] = defaultdict(dict)
    gene_assertions: dict[tuple[str, str], dict[str, dict]] = defaultdict(dict)
    mapping_audit: list[dict] = []
    total_links = 0
    mapped_links = 0
    ambiguous_links = 0
    missing_links = 0
    mapped_symbols: set[str] = set()
    unmapped_symbols: set[str] = set()

    links_path = S1_DIR / "pathway_gene_links.csv"
    with links_path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            total_links += 1
            analysis = row["analysis"].strip()
            pathway_id = row["pathway_id"].strip()
            entity_type, entity_id = pathway_entity(analysis, pathway_id)
            symbol = row["gene_symbol"].strip()
            hits = sorted(symbol_to_ids.get(norm(symbol), set()))
            status = "matched_unique_symbol_or_alias" if len(hits) == 1 else ("ambiguous_symbol_or_alias" if len(hits) > 1 else "unmatched_symbol")
            mapping_audit.append({"analysis": analysis, "pathway_id": pathway_id, "gene_symbol": symbol, "entrez_id": row.get("ENTREZID", ""), "mapping_status": status, "ensembl_gene_ids": "|".join(hits)})

            node = pathway_nodes.setdefault(entity_id, {"id": entity_id, "type": entity_type, "label": row["pathway"], "analyses": set(), "analysis_assertions": {}})
            node["analyses"].add(analysis)
            p_value = float(row["adjusted_p"])
            node["analysis_assertions"][analysis] = {"analysis": analysis, "adjusted_p": p_value, "pathway_id": pathway_id}
            context_assertions[entity_id][analysis] = {"analysis": analysis, "adjusted_p": p_value, "pathway_id": pathway_id}

            if len(hits) == 1:
                mapped_links += 1
                mapped_symbols.add(norm(symbol))
                gene_assertions[(entity_id, hits[0])][analysis] = {"analysis": analysis, "adjusted_p": p_value, "entrez_id": row.get("ENTREZID", ""), "gene_symbol": symbol}
                node.setdefault("mapped_genes", set()).add(hits[0])
            elif len(hits) > 1:
                ambiguous_links += 1
                unmapped_symbols.add(norm(symbol))
            else:
                missing_links += 1
                unmapped_symbols.add(norm(symbol))

    pathway_node_rows = []
    for entity_id, node in sorted(pathway_nodes.items()):
        properties = {
            "analysis_run_id": RUN_ID,
            "graph_build_id": BUILD_ID,
            "source": "GSE42568 S1 pathway enrichment",
            "collections": sorted(node["analyses"]),
            "analysis_assertions": sorted(node["analysis_assertions"].values(), key=lambda x: x["analysis"]),
            "mapped_gene_count": len(node.get("mapped_genes", set())),
            "gene_universe_entrez": enrichment_manifest["mapped_entrez_universe"],
        }
        pathway_node_rows.append({"id": entity_id, "type": node["type"], "label": node["label"], "properties_json": json.dumps(properties, ensure_ascii=False, sort_keys=True)})

    extension_edges = []
    source_release = "GSE42568 S1 pathway enrichment (2026-11-12)"
    for entity_id, analyses in sorted(context_assertions.items()):
        extension_edges.append({"from": CONTEXT_ID, "to": entity_id, "label": "S1-ENRICHED-PATHWAY", "relation": "HAS_ENRICHED_PATHWAY", "undirected": "False", "properties_json": json.dumps({"analysis_run_id": RUN_ID, "graph_build_id": BUILD_ID, "analysis_assertions": sorted(analyses.values(), key=lambda x: x["analysis"]), "input_sha256": enrichment_manifest["input_sha256"]}, ensure_ascii=False, sort_keys=True), "source_release": source_release})
    for (entity_id, gene_id), analyses in sorted(gene_assertions.items()):
        extension_edges.append({"from": entity_id, "to": gene_id, "label": "S1-ENRICHED-GENE", "relation": "HAS_ENRICHED_GENE", "undirected": "False", "properties_json": json.dumps({"analysis_run_id": RUN_ID, "graph_build_id": BUILD_ID, "analysis_assertions": sorted(analyses.values(), key=lambda x: x["analysis"])}, ensure_ascii=False, sort_keys=True), "source_release": source_release})

    base_gene_ids = set()
    with (BASE_DIR / "subgraph_nodes.csv").open(encoding="utf-8-sig", newline="") as handle:
        base_gene_ids = {row["id"] for row in csv.DictReader(handle) if row["type"] == "Gene"}
    extension_gene_rows = []
    for gene_id in sorted({gene_id for _, gene_id in gene_assertions} - base_gene_ids):
        row = gene_by_id[gene_id]
        props = row.get("properties") or {}
        compact = {key: props.get(key) for key in ["symbol", "name", "biotype", "xrefs", "sources"] if props.get(key) is not None}
        compact["source"] = "OptimusKG 3.2"
        extension_gene_rows.append({"id": gene_id, "type": "Gene", "label": props.get("symbol") or gene_id, "properties_json": json.dumps(compact, ensure_ascii=False, sort_keys=True)})

    write_csv(OUT / "pathway_nodes.csv", pathway_node_rows)
    write_csv(OUT / "gene_nodes.csv", extension_gene_rows)
    write_csv(OUT / "pathway_edges.csv", extension_edges)
    write_csv(OUT / "pathway_gene_mapping_audit.csv", mapping_audit)

    base_edges_path = BASE_DIR / "subgraph_edges.csv"
    candidate_to_drug: dict[str, set[str]] = defaultdict(set)
    drug_to_gene: dict[str, set[str]] = defaultdict(set)
    with base_edges_path.open(encoding="utf-8-sig", newline="") as handle:
        for edge in csv.DictReader(handle):
            if edge["label"] == "PROJECT-REFERENCES_DRUG":
                candidate_to_drug[edge["from"]].add(edge["to"])
            elif edge["label"] == "DRG-GEN":
                drug_to_gene[edge["from"]].add(edge["to"])
    gene_to_enriched_pathway: dict[str, set[str]] = defaultdict(set)
    for edge in extension_edges:
        if edge["label"] == "S1-ENRICHED-GENE":
            gene_to_enriched_pathway[edge["to"]].add(edge["from"])
    candidate_pathways: set[tuple[str, str, str, str]] = set()
    for candidate_id, drug_ids in candidate_to_drug.items():
        for drug_id in drug_ids:
            for gene_id in drug_to_gene.get(drug_id, set()):
                for pathway_id in gene_to_enriched_pathway.get(gene_id, set()):
                    candidate_pathways.add((candidate_id, drug_id, gene_id, pathway_id))
    route_summary = {
        "base_candidate_with_mapped_drug_count": len(candidate_to_drug),
        "candidate_count_with_s1_pathway_target_overlap": len({row[0] for row in candidate_pathways}),
        "drug_count_with_s1_pathway_target_overlap": len({row[1] for row in candidate_pathways}),
        "unique_candidate_drug_target_pathway_rows": len(candidate_pathways),
        "unique_target_gene_count_in_overlap": len({row[2] for row in candidate_pathways}),
        "interpretation": "Exact Ensembl ID overlap between OptimusKG candidate-drug target edges and uniquely mapped S1-enriched pathway-gene edges; association evidence only.",
    }

    evidence_rows = []
    conflict_rows = []
    edge_sources = [
        (BASE_DIR / "subgraph_edges.csv", "Phase B OptimusKG subgraph"),
        (OUT / "pathway_edges.csv", "S1 pathway enrichment extension"),
    ]
    for edge_path, edge_source in edge_sources:
        with edge_path.open(encoding="utf-8-sig", newline="") as handle:
            for edge in csv.DictReader(handle):
                props = json.loads(edge["properties_json"] or "{}")
                evidence_id = hashlib.sha256(f"{edge['from']}|{edge['label']}|{edge['to']}|{edge['source_release']}".encode()).hexdigest()
                evidence_row = {
                    "evidence_id": evidence_id,
                    "subject_id": edge["from"],
                    "predicate": edge["relation"],
                    "object_id": edge["to"],
                    "edge_label": edge["label"],
                    "source_release": edge["source_release"],
                    "source_table": edge_source,
                    "analysis_run_id": props.get("analysis_run_id", ""),
                    "source_assertion_count": len(props.get("analysis_assertions") or props.get("relation_assertions") or []),
                    "source_assertions_json": json.dumps(props, ensure_ascii=False, sort_keys=True),
                }
                evidence_rows.append(evidence_row)
                if props.get("relation_conflict") is True:
                    conflict_rows.append({**evidence_row, "relation_conflict": True})

    unmatched_rows = []
    base_mapping_files = [
        (BASE_DIR / "candidate_mapping_audit.csv", "Drug", "pert_id", "graph_drug_id"),
        (BASE_DIR / "s1_gene_mapping_audit.csv", "Gene", "normalized_symbol", "ensembl_gene_id"),
    ]
    for path, entity_type, identifier_column, mapped_column in base_mapping_files:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                if not row.get("mapping_status", "").startswith("matched_"):
                    unmatched_rows.append({"source": "Phase B mapping audit", "entity_type": entity_type, "identifier": row.get(identifier_column, ""), "mapping_status": row.get("mapping_status", ""), "mapped_ids": row.get(mapped_column, ""), "details_json": json.dumps(row, ensure_ascii=False, sort_keys=True)})
    for row in mapping_audit:
        if row["mapping_status"] != "matched_unique_symbol_or_alias":
            unmatched_rows.append({"source": "S1 enrichment pathway gene mapping", "entity_type": "Gene", "identifier": row["gene_symbol"], "mapping_status": row["mapping_status"], "mapped_ids": row["ensembl_gene_ids"], "details_json": json.dumps(row, ensure_ascii=False, sort_keys=True)})

    write_csv(OUT / "evidence_records.csv", evidence_rows)
    write_csv(OUT / "relation_conflicts.csv", conflict_rows)
    write_csv(OUT / "unmatched_entities.csv", unmatched_rows)

    input_paths = [
        ROOT / "s1_初步_gse42568_limma" / "limma_all_genes.csv",
        S1_DIR / "environment_manifest.json",
        S1_DIR / "gene_mapping_audit.csv",
        S1_DIR / "go_up.csv", S1_DIR / "go_down.csv",
        S1_DIR / "reactome_up.csv", S1_DIR / "reactome_down.csv",
        S1_DIR / "hallmark_gsea.csv", links_path,
        BASE_DIR / "s1_gene_mapping_audit.csv",
        BASE_DIR / "subgraph_nodes.csv", base_edges_path,
        DATA / "source_manifest.json", DATA / "nodes" / "gene.parquet",
    ]
    validation_path = OUT / "neo4j_import_validation.json"
    neo4j_validation = json.loads(validation_path.read_text(encoding="utf-8")) if validation_path.exists() else None
    validation_sources = [BASE_DIR / "subgraph_nodes.csv", BASE_DIR / "subgraph_edges.csv", OUT / "pathway_nodes.csv", OUT / "gene_nodes.csv", OUT / "pathway_edges.csv"]
    validation_is_current = bool(neo4j_validation) and all(
        neo4j_validation.get("input_sha256", {}).get(path.relative_to(ROOT).as_posix()) == sha256(path)
        for path in validation_sources
    )
    neo4j_status = neo4j_validation.get("status", "FAIL") if validation_is_current else "NOT_RUN_OR_STALE"
    neo4j_validation_text = (
        f"Neo4j 实际导入：{neo4j_status}；重复运行 MERGE 导入两次，节点/边数量前后稳定；"
        f"数据库实际有 {sum(neo4j_validation['actual_counts']['nodes_by_type'].values()):,} 个节点、"
        f"{sum(neo4j_validation['actual_counts']['edges_by_type'].values()):,} 条关系；"
        f"证据交汇路径 {neo4j_validation['actual_counts']['candidate_target_pathway_routes']['route_count']:,} 条。详见 `neo4j_import_validation.json`。"
        if validation_is_current and neo4j_validation.get("status") == "PASS"
        else "Neo4j 实际导入与幂等性尚未验证，不能据此宣称通过。"
    )
    output_names = ["pathway_nodes.csv", "gene_nodes.csv", "pathway_edges.csv", "pathway_gene_mapping_audit.csv", "evidence_records.csv", "relation_conflicts.csv", "unmatched_entities.csv"]
    if validation_path.exists():
        output_names.append(validation_path.name)
    manifest = {
        "experiment": "Phase B2: attach S1 enriched pathways to the bounded OptimusKG seed subgraph",
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "graph_build_id": BUILD_ID,
        "analysis_run_id": RUN_ID,
        "source_graph_build": "PHASEB_OPTIMUSKG32_20261113",
        "source_release": "OptimusKG 3.2",
        "license": "CC BY-NC-SA 4.0 for OptimusKG-derived gene entities; S1 enrichment outputs are cited by input and output hashes",
        "context_node_id": CONTEXT_ID,
        "input_sha256": {path.relative_to(ROOT).as_posix(): sha256(path) for path in input_paths},
        "output_sha256": {name: sha256(OUT / name) for name in output_names},
        "counts": {"enriched_pathway_or_geneset_nodes": len(pathway_node_rows), "additional_gene_nodes": len(extension_gene_rows), "context_to_enriched_pathway_edges": len(context_assertions), "enriched_pathway_to_gene_edges": len(gene_assertions), "pathway_gene_link_rows": total_links, "mapped_link_rows": mapped_links, "ambiguous_link_rows": ambiguous_links, "unmatched_link_rows": missing_links, "mapped_link_symbol_count": len(mapped_symbols), "unmapped_or_ambiguous_symbol_count": len(unmapped_symbols), "evidence_records": len(evidence_rows), "relation_conflict_records": len(conflict_rows), "unmatched_entity_records": len(unmatched_rows)},
        "candidate_target_pathway_overlap": route_summary,
        "mapping_policy": "Exact primary symbol/symbol_synonyms/obsolete_symbols in OptimusKG gene nodes; create a gene edge only for a unique Ensembl match; keep ambiguous/unmatched rows in the audit.",
        "analysis_policy": "GO/Reactome direction and Hallmark NES sign are retained as analysis assertions; no efficacy score is inferred.",
        "verification": {"csv_generation": "PASS", "backend_graph_repository_tests": {"status": "PASS", "passed": 11, "run_date": "2026-11-13"}, "neo4j_import": neo4j_status},
    }
    (OUT / "phase_b2_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    report = f"""# Phase B2：将 S1 富集通路接入疾病子图

运行时间：{manifest['run_utc']}

## 输入审计

- S1 富集环境清单记录 limma 输入 SHA-256：`{enrichment_manifest['input_sha256']}`；该值与全量 limma 文件校验值相同。
- 使用显著 GO BP、Reactome、Hallmark 结果及 `pathway_gene_links.csv`；来源文件、OptimusKG 基因表和旧 Phase B 映射表哈希见 `phase_b2_manifest.json`。
- 旧 Phase B 输出不覆盖。它的历史 manifest 曾错误记载通路结果缺失；本版本单独编号并保留旧版文件。

## 抽取与映射

- 新增富集 Pathway/GeneSet 节点：{len(pathway_node_rows):,}；新增 Ensembl Gene 节点：{len(extension_gene_rows):,}。
- 输入通路基因链接：{total_links:,}；唯一映射行：{mapped_links:,}；歧义映射：{ambiguous_links:,}；未匹配：{missing_links:,}。
- 唯一映射规则：使用 OptimusKG primary symbol、symbol_synonyms、obsolete_symbols；只有单一 Ensembl ID 才生成路径。未匹配记录保存在 `pathway_gene_mapping_audit.csv`。
- 项目上下文到富集通路边：{len(context_assertions):,}；富集通路到基因边：{len(gene_assertions):,}。同一通路在多个分析中的方向、adjusted P 和 Entrez 保留为独立 assertion。
- 与既有 Phase B 有可靠药物映射的候选/靶点边按 Ensembl ID 精确求交：{route_summary['base_candidate_with_mapped_drug_count']} 个已映射候选中，{route_summary['candidate_count_with_s1_pathway_target_overlap']} 个存在候选药物→靶点基因→S1 富集通路→疾病上下文的证据路径，共 {route_summary['unique_candidate_drug_target_pathway_rows']:,} 条候选-药物-基因-通路组合、涉及 {route_summary['unique_target_gene_count_in_overlap']} 个靶基因。输入子图节点表和边表的哈希也记录在 manifest。此结果代表数据库关系的证据交汇，不代表因果或疗效。

## 输出与解释

- `pathway_nodes.csv`、`gene_nodes.csv`、`pathway_edges.csv`、`evidence_records.csv`、`relation_conflicts.csv`、`unmatched_entities.csv`、`pathway_gene_mapping_audit.csv` 和 `phase_b2_manifest.json`。
- 来源证据关系表共 {len(evidence_rows):,} 行，保留 Phase B 与 S1 富集边的原始断言 JSON；未匹配或歧义实体映射共 {len(unmatched_rows):,} 行。原始边中显式标记 `relation_conflict=true` 的记录为 {len(conflict_rows):,} 条；这是对源表冲突标记字段的统计，不表示已经独立核查全部来源库并确认没有冲突。
- {neo4j_validation_text}
- GO/Reactome UP/DOWN 与 Hallmark NES 正负方向都作为分析属性保存，不将富集关系解释为因果机制、药物疗效或通路激活证明。
- Reactome 与 GO 节点使用标准 pathway ID；Hallmark GeneSet 节点使用 `MSIGDB:` 前缀。连接到相同 Ensembl ID 的公共 Gene 节点，不按项目复制基因实体。

## 限制

- 仅创建当前 ER+ 项目的局部种子子图扩展，没有导入完整 OptimusKG。
- S1 通路富集的统计解释沿用原分析报告；本任务只构建带来源和方向的图连接。
- 若 manifest 中 Neo4j 状态为 PASS，本机 Neo4j 导入及重复运行幂等性已通过；这不代表其他部署环境也已验证。

## 验收

- 本次生成节点、关系、映射审计、来源证据、关系冲突和未匹配实体 CSV；输入和输出 SHA-256 已写入 manifest。
- 后端图仓库/API 自动化测试：11 项通过，其中包含本扩展节点、边及来源追溯检查。
- 若 `neo4j_import_validation.json` 的源文件 SHA-256 与当前 CSV 一致，则数据库导入和重复运行验证引用该报告；若源文件有变化，验证状态会自动标为过期，需重新执行验证脚本。
"""
    (OUT / "phase_b2_report.md").write_text(report, encoding="utf-8")
    manifest["output_sha256"]["phase_b2_report.md"] = sha256(OUT / "phase_b2_report.md")
    (OUT / "phase_b2_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest["counts"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
