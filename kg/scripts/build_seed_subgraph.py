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
OUT = ROOT / "experiments" / "platform_phase_b"
S1 = ROOT / "s1_初步_gse42568_limma" / "limma_significant_genes_FDR05.csv"
CANDIDATES = ROOT / "experiments" / "exp006_ranking_reliability" / "results" / "candidate_drugs_top50.csv"
MAPPING = ROOT / "experiments" / "exp011_prism_validation" / "results" / "candidate_mapping_audit_top50.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(x: object) -> str:
    return str(x or "").strip().upper()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    drugs = pl.read_parquet(DATA / "nodes" / "drug.parquet").to_dicts()
    genes = pl.read_parquet(DATA / "nodes" / "gene.parquet").to_dicts()
    pathways = pl.read_parquet(DATA / "nodes" / "pathway.parquet").to_dicts()
    dg = pl.read_parquet(DATA / "edges" / "drug_gene.parquet").to_dicts()
    pg = pl.read_parquet(DATA / "edges" / "pathway_gene.parquet").to_dicts()

    def prop(row: dict) -> dict:
        return row.get("properties") or {}

    drug_by_inchi: dict[str, list[dict]] = defaultdict(list)
    for row in drugs:
        key = norm(prop(row).get("inchi_key"))
        if key:
            drug_by_inchi[key].append(row)

    symbol_to_genes: dict[str, set[str]] = defaultdict(set)
    for row in genes:
        p = prop(row)
        if p.get("symbol"):
            symbol_to_genes[norm(p["symbol"])].add(row["id"])
        for field in ("symbol_synonyms", "obsolete_symbols"):
            for alias in p.get(field) or []:
                label = alias.get("label") if isinstance(alias, dict) else alias
                if label:
                    symbol_to_genes[norm(label)].add(row["id"])

    candidate_map = {}
    mapping_audit = []
    with MAPPING.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if row.get("pert_id"):
                candidate_map[row["pert_id"]] = row
    candidate_rows = []
    with CANDIDATES.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            pert = row["pert_id"]
            audit = candidate_map.get(pert, {})
            key = norm(audit.get("inchi_key"))
            hits = drug_by_inchi.get(key, []) if key else []
            status = "matched_exact_inchikey" if len(hits) == 1 else ("ambiguous_inchikey" if len(hits) > 1 else "unmatched_no_exact_inchikey")
            mapped = hits[0] if len(hits) == 1 else None
            x = {**row, "inchi_key": key, "graph_drug_id": mapped["id"] if mapped else "", "mapping_status": status, "mapping_method": "exact InChIKey" if mapped else "none"}
            candidate_rows.append(x)
            mapping_audit.append(x)

    s1_rows = []
    with S1.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if float(row.get("adj.P.Val", "1") or 1) >= .05:
                continue
            symbol = norm(row.get("gene_symbol"))
            ids = sorted(symbol_to_genes.get(symbol, set())) if symbol else []
            status = "matched_unique_symbol_or_alias" if len(ids) == 1 else ("ambiguous_symbol_or_alias" if len(ids) > 1 else "unmatched_symbol")
            s1_rows.append({**row, "normalized_symbol": symbol, "ensembl_gene_id": ids[0] if len(ids) == 1 else "", "mapping_status": status})

    s1_by_gene = {r["ensembl_gene_id"]: r for r in s1_rows if r["ensembl_gene_id"]}
    pathway_by_id = {r["id"]: r for r in pathways}
    drug_to_targets: dict[str, list[dict]] = defaultdict(list)
    for edge in dg:
        drug_to_targets[edge["from"]].append(edge)
    gene_to_pathways: dict[str, list[dict]] = defaultdict(list)
    for edge in pg:
        gene_to_pathways[edge["to"]].append(edge)

    selected_drugs = {r["graph_drug_id"] for r in candidate_rows if r["graph_drug_id"]}
    selected_genes = set(s1_by_gene)
    selected_pathways = set()
    selected_edges = []
    route_rows = []
    for drug_id in sorted(selected_drugs):
        for drug_edge in drug_to_targets.get(drug_id, []):
            gene_id = drug_edge["to"]
            if gene_id not in selected_genes:
                continue
            selected_edges.append({"from": drug_edge["from"], "to": gene_id, "label": drug_edge["label"], "relation": drug_edge["relation"], "undirected": drug_edge["undirected"], "properties_json": json.dumps(drug_edge.get("properties") or {}, ensure_ascii=False, sort_keys=True), "source_release": "OptimusKG 3.2"})
            for path_edge in gene_to_pathways.get(gene_id, []):
                pathway_id = path_edge["from"]
                if pathway_id not in pathway_by_id:
                    continue
                selected_pathways.add(pathway_id)
                selected_edges.append({"from": pathway_id, "to": gene_id, "label": path_edge["label"], "relation": path_edge["relation"], "undirected": path_edge["undirected"], "properties_json": json.dumps(path_edge.get("properties") or {}, ensure_ascii=False, sort_keys=True), "source_release": "OptimusKG 3.2"})
                route_rows.append({"drug_id": drug_id, "target_gene_id": gene_id, "pathway_id": pathway_id, "disease_context_id": "GSE42568_ERPOS_TUMOR_VS_NORMAL", "logFC": s1_by_gene[gene_id]["logFC"], "adj.P.Val": s1_by_gene[gene_id]["adj.P.Val"], "direction": "UP" if float(s1_by_gene[gene_id]["logFC"]) > 0 else "DOWN", "drug_target_assertion": json.dumps(drug_edge.get("properties") or {}, ensure_ascii=False, sort_keys=True), "pathway_gene_assertion": json.dumps(path_edge.get("properties") or {}, ensure_ascii=False, sort_keys=True)})

    nodes = []
    context_id = "DISEASE_CONTEXT:GSE42568_ERPOS_TUMOR_VS_NORMAL"
    run_id = "ANALYSIS_RUN:PHASEB_OPTIMUSKG32_20261113"
    nodes.append({"id": context_id, "type": "DiseaseContext", "label": "ER-positive breast cancer (GSE42568)", "properties_json": json.dumps({"project_id": "PROJECT:ERPOS_GSE42568", "project_slug": "erpos-gse42568", "dataset": "GSE42568", "contrast": "Tumor - Normal", "subtype": "ER-positive", "analysis_run_id": run_id}, ensure_ascii=False, sort_keys=True)})
    drug_by_id = {r["id"]: r for r in drugs}
    gene_by_id = {r["id"]: r for r in genes}
    for row in candidate_rows:
        candidate_id = f"CANDIDATE:{row['pert_id']}"
        nodes.append({"id": candidate_id, "type": "Candidate", "label": row.get("drug_name", row["pert_id"]), "properties_json": json.dumps({"project_id": "PROJECT:ERPOS_GSE42568", "project_slug": "erpos-gse42568", "analysis_run_id": run_id, "pert_id": row["pert_id"], "rank": row.get("rank"), "wtcs_median_B": row.get("wtcs_median_B"), "mapping_status": row["mapping_status"]}, ensure_ascii=False, sort_keys=True)})
        selected_edges.append({"from": context_id, "to": candidate_id, "label": "PROJECT-HAS_CANDIDATE", "relation": "HAS_CANDIDATE", "undirected": False, "properties_json": json.dumps({"analysis_run_id": run_id, "rank": row.get("rank")}, ensure_ascii=False, sort_keys=True), "source_release": "local Exp006 run"})
        if row["graph_drug_id"]:
            selected_edges.append({"from": candidate_id, "to": row["graph_drug_id"], "label": "PROJECT-REFERENCES_DRUG", "relation": "REFERENCES_DRUG", "undirected": False, "properties_json": json.dumps({"mapping_method": "exact InChIKey", "lincs_pert_id": row["pert_id"]}, ensure_ascii=False, sort_keys=True), "source_release": "LINCS/Exp011 mapping audit"})
    for gene_id, s1row in s1_by_gene.items():
        selected_edges.append({"from": context_id, "to": gene_id, "label": "PROJECT-HAS_DEG", "relation": "HAS_DEG", "undirected": False, "properties_json": json.dumps({"analysis_run_id": run_id, "dataset": "GSE42568", "contrast": "Tumor - Normal", "gene_symbol": s1row["normalized_symbol"], "logFC": s1row["logFC"], "adj.P.Val": s1row["adj.P.Val"], "direction": "UP" if float(s1row["logFC"]) > 0 else "DOWN"}, ensure_ascii=False, sort_keys=True), "source_release": "S1 limma result"})
    for node_id in sorted(selected_drugs):
        row = drug_by_id[node_id]; p = prop(row); compact = {k: p.get(k) for k in ["name", "inchi_key", "canonical_smiles", "accession_numbers", "source_ids", "synonyms", "sources"] if p.get(k) is not None}; nodes.append({"id": node_id, "type": "Drug", "label": p.get("name", node_id), "properties_json": json.dumps(compact, ensure_ascii=False, sort_keys=True)})
    for gene_id in sorted(selected_genes):
        row = gene_by_id[gene_id]; p = prop(row); compact = {k: p.get(k) for k in ["symbol", "name", "biotype", "xrefs", "sources"] if p.get(k) is not None}
        nodes.append({"id": gene_id, "type": "Gene", "label": p.get("symbol", gene_id), "properties_json": json.dumps(compact, ensure_ascii=False, sort_keys=True)})
    for pathway_id in sorted(selected_pathways):
        row = pathway_by_id[pathway_id]; p = prop(row); compact = {k: p.get(k) for k in ["name", "species", "sources"] if p.get(k) is not None}
        nodes.append({"id": pathway_id, "type": "Pathway", "label": compact.get("name", pathway_id), "properties_json": json.dumps(compact, ensure_ascii=False, sort_keys=True)})

    def write_csv(name: str, rows: list[dict]) -> None:
        if not rows:
            (OUT / name).write_text("", encoding="utf-8")
            return
        columns = list(dict.fromkeys(key for row in rows for key in row))
        with (OUT / name).open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
            writer.writeheader(); writer.writerows(rows)

    write_csv("candidate_mapping_audit.csv", mapping_audit)
    write_csv("s1_gene_mapping_audit.csv", s1_rows)
    write_csv("unmatched_entities.csv", [r for r in mapping_audit if r["mapping_status"] != "matched_exact_inchikey"] + [r for r in s1_rows if r["mapping_status"] != "matched_unique_symbol_or_alias"])
    write_csv("subgraph_nodes.csv", nodes)
    write_csv("subgraph_edges.csv", selected_edges)
    write_csv("candidate_target_pathway_routes.csv", route_rows)

    input_paths = [S1, CANDIDATES, MAPPING, DATA / "source_manifest.json"]
    output_paths = [OUT / name for name in ["candidate_mapping_audit.csv", "s1_gene_mapping_audit.csv", "unmatched_entities.csv", "subgraph_nodes.csv", "subgraph_edges.csv", "candidate_target_pathway_routes.csv"]]
    results = {
        "experiment": "Phase B bounded seed-driven subgraph extraction",
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "project_id": "ERPOS_GSE42568",
        "analysis_run_id": run_id,
        "graph_source": "OptimusKG 3.2",
        "license": "CC BY-NC-SA 4.0",
        "disease_specific_pathway_seed": "NOT_AVAILABLE: S1 GO/Reactome/Hallmark CSV results absent in current workspace; routes use S1 DEG seeds only and are not described as ER+ specific pathways.",
        "input_sha256": {p.relative_to(ROOT).as_posix(): sha256(p) for p in input_paths},
        "output_sha256": {p.relative_to(ROOT).as_posix(): sha256(p) for p in output_paths},
        "counts": {
            "candidate_drugs": len(candidate_rows),
            "candidate_drugs_exact_inchikey_mapped": sum(r["mapping_status"] == "matched_exact_inchikey" for r in candidate_rows),
            "candidate_drug_nodes_in_subgraph": len(selected_drugs),
            "s1_fdr05_genes": len(s1_rows),
            "s1_genes_unique_symbol_or_alias_mapped": sum(r["mapping_status"] == "matched_unique_symbol_or_alias" for r in s1_rows),
            "s1_genes_ambiguous_or_unmatched": sum(r["mapping_status"] != "matched_unique_symbol_or_alias" for r in s1_rows),
            "target_gene_pathway_routes": len(route_rows),
            "unique_target_genes_in_routes": len({r["target_gene_id"] for r in route_rows}),
            "unique_pathways_in_routes": len(selected_pathways),
            "subgraph_nodes": len(nodes),
            "subgraph_edges": len(selected_edges),
        },
        "notes": ["Drug mapping uses exact InChIKey only; salts/stereoisomers are not fuzzy merged.", "All edge properties retain source assertions and relation conflict metadata.", "No drug effect or therapeutic efficacy is inferred from graph paths."],
    }
    (OUT / "phase_b_manifest.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    report = f"""# Phase B：基于真实数据的候选药物子图原型

## 人话摘要

从 Exp006 Top50 候选开始，用化学结构 InChIKey 精确匹配 OptimusKG 药物；再把 S1 显著基因映射到 Ensembl，查找图谱中已有的药物—基因靶点关系和通路—基因关系。只有实际存在、带来源的关系才进入结果。

## 数据来源与范围

- OptimusKG Harvard Dataverse 发布版 **3.2**，许可 **CC BY-NC-SA 4.0**。
- 仅下载 5 个 Parquet 表，共 {sum(p.stat().st_size for p in [DATA/'nodes/drug.parquet',DATA/'nodes/gene.parquet',DATA/'nodes/pathway.parquet',DATA/'edges/drug_gene.parquet',DATA/'edges/pathway_gene.parquet']):,} 字节；完整图谱没有下载。
- 每个源文件的 Dataverse 文件 ID、MD5、SHA-256 见 `data/optimuskg/3.2/source_manifest.json`。

## 映射和路径结果

- Exp006 候选药物：{len(candidate_rows)} 个；精确 InChIKey 映射成功 {sum(r['mapping_status']=='matched_exact_inchikey' for r in candidate_rows)} 个。
- S1 FDR<0.05 基因：{len(s1_rows)} 个；唯一 Symbol/别名映射到 Ensembl {sum(r['mapping_status']=='matched_unique_symbol_or_alias' for r in s1_rows)} 个；歧义或未匹配 {sum(r['mapping_status']!='matched_unique_symbol_or_alias' for r in s1_rows)} 个。
- 子图包含 {len(route_rows)} 条候选药物→靶基因→通路路径，{len(selected_drugs)} 个药物节点、{len(selected_genes)} 个 S1 基因节点、{len(selected_pathways)} 个通路节点。
- 当前缺少本地 S1 GO/Reactome/Hallmark 富集结果；这些路径仅表示公共知识图谱中的靶点与通路关系和 S1 差异基因重合，不代表通路已被本项目富集验证，更不代表 ER+ 特异性或疗效证据。

## 可追溯文件

- `candidate_mapping_audit.csv`：Top50 每个 LINCS 药物的精确结构匹配状态。
- `s1_gene_mapping_audit.csv`：S1 基因映射、方向及 limma 原始统计量。
- `unmatched_entities.csv`：未匹配及有歧义条目。
- `subgraph_nodes.csv`、`subgraph_edges.csv`：局部子图。边的 `properties_json` 保留原始 relation、数据源和冲突字段。
- `candidate_target_pathway_routes.csv`：路径和两条源关系断言。
- `phase_b_manifest.json`：输入/输出哈希、运行 ID、许可、计数。

## 限制

OptimusKG 汇总了多个来源；一条图边不能替代源数据库原始证据审查。药物映射仅使用完全相同 InChIKey；不同盐型和立体异构体不会自动合并。当前未加载 Neo4j，因此结果是可导入、可复跑的子图原型，还不是在线图数据库服务。
"""
    (OUT / "phase_b_report.md").write_text(report, encoding="utf-8")
    print(json.dumps(results["counts"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
