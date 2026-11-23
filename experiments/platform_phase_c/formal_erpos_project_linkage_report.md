# 正式 ER+ 项目历史分析运行登记与 GraphBundle 报告

运行时间（UTC）：2026-11-14T06:00:20.825696+00:00

## 工作范围

本次未重跑 limma 或 LINCS WTCS。现存 GSE42568 limma 表经平台预计算 DEG 接口登记并生成项目内标准化副本；先保留历史 GO/Reactome/Hallmark 文件的逐字节副本，再以项目标准化 S1 运行新的 R 富集及 Entrez—Ensembl 映射，避免旧结果缺少 Ensembl 列导致通路基因关联丢失。LINCS scheme B 结果按 Exp006 Top 50 规则形成项目级种子子集，并保留所有剂量条件。

## 阶段状态

### s1

```json
{
  "status": "completed",
  "dataset_id": "8a9693aa-aeb6-4b94-a87d-ea466f1a54a0",
  "analysis_run_id": "ANALYSIS_RUN:S1_PRECOMPUTED:9ebd6c43-9342-487e-a052-ae901461b58c",
  "source_sha256": "b3dafdae855a0f44cbe80dbc40d17693ed01f4b31d899acbabc60e5485ed21c4",
  "standardized_output_sha256": "dc1e42d34a1f165dff936ad77dcaabc26c856c962724d5c8666bd88be2b15888",
  "contrast": "Tumor - Normal",
  "input_rows": 21655,
  "unique_genes": 21653,
  "significant_genes": 7066,
  "up": 3422,
  "down": 3644,
  "historical_import": true,
  "limma_rerun": false
}
```

### enrichment

```json
{
  "status": "completed",
  "analysis_run_id": "ANALYSIS_RUN:S1_ENRICHMENT:eb409567-e846-4422-ae19-0055937871ea",
  "s1_analysis_run_id": "ANALYSIS_RUN:S1_PRECOMPUTED:9ebd6c43-9342-487e-a052-ae901461b58c",
  "output_dir": "data/processed/projects/3f18f4c1-713d-58c5-8a53-38eca5a5aaf9/s1_enrichment/eb409567-e846-4422-ae19-0055937871ea",
  "output_hashes": {
    "gene_mapping_audit.csv": "77d4fc11341a5a824c2a514ab042e2404c53a672b7c0e6d8dc6b7444c0ec5a48",
    "s1_up_genes.csv": "61858cb82af15d25191f7c3819b212d057068dff6c9af1f22bc7d27da977a7a6",
    "s1_down_genes.csv": "5b7bdeca648c3f82844b9c24757671db2dc335f2e88566a3ee1c4c7201d7c999",
    "go_up.csv": "6dc3ee2ace7792d8b9bcb17c91a851e1961246561501c83701a1fdf4db9d758d",
    "go_down.csv": "677652aaf7ef8eb525500f6f04c819d5ea1b7c9418584595acc5a8ae48954756",
    "reactome_up.csv": "8ef2b30e45015f5395a154502c00c8a4d6e768920c8257916257eefb4fefd2fa",
    "reactome_down.csv": "06d5d9852801a691cf71fc842290d9fac1d83631a06553702784c2e3d889ab57",
    "hallmark_gsea.csv": "34ac4c1cbb92495eb2afaea262e992f9d3da72aa26c4fe1b57256d84d56ff3da",
    "pathway_gene_links.csv": "986daaa1573f2f54df3dda9ff9dcce42a904ab5d6f256e42c53ab85b31b04117",
    "summary.json": "f34a8e33a45468a0c5f48bd932694b0dbcd7a7fd8b7bd93ab9695aa2410d9a3a",
    "enrichment_report.md": "1eed50ba46c4e2956d07345e98ba8aac04663d63384ac6202d7d64ce629b5ed4"
  },
  "historical_import_available": true,
  "active_run_is_recalculated_from_standardized_s1": true,
  "significant_pathway_counts": {
    "go_up": 206,
    "go_down": 343,
    "reactome_up": 135,
    "reactome_down": 26,
    "hallmark_gsea": 29
  },
  "pathway_gene_link_rows": 31991,
  "pathway_gene_links_include_ensembl_mapping": true
}
```

### s2_import

```json
{
  "status": "completed",
  "analysis_run_id": "ANALYSIS_RUN:S2_LINCS:c922f2b0-242e-5991-9f76-dcbc8f66ce57",
  "persisted_condition_count": 240,
  "project_seed_signatures": 315,
  "project_seed_perturbagens": 50,
  "dose_condition_rows": 240,
  "historical_import": true,
  "source_s1_hash_verified_against_project_upload": true
}
```

### graph_bundle

```json
{
  "status": "completed",
  "analysis_run_id": "ANALYSIS_RUN:KG_GRAPH_BUNDLE:d2a9cb1e-9853-4e41-88e6-70fb3c465ab3",
  "bundle_dir": "data/processed/projects/3f18f4c1-713d-58c5-8a53-38eca5a5aaf9/graph_bundle/runs/d2a9cb1e-9853-4e41-88e6-70fb3c465ab3",
  "counts": {
    "nodes": 7032,
    "edges": 38998,
    "s1_significant_genes": 7066,
    "s1_unique_ensembl_mapped": 6707,
    "s1_ambiguous_or_unmatched": 359,
    "pathway_gene_links": 31991,
    "pathway_gene_unique_mapped": 30350,
    "candidate_perturbagens": 50,
    "exact_inchikey_mapped_drugs": 30,
    "s2_condition_rows": 240,
    "candidate_target_pathway_routes": 1494,
    "relation_conflicts": 0,
    "unmatched_entities": 2020
  },
  "mapping_policy": "exact InChIKey for compounds; unique Ensembl gene mapping; unresolved or ambiguous entities are retained in audit only",
  "cross_dose_policy": "retain every exact dose/time condition as its own S2Condition node; no per-drug best score or cross-condition rank"
}
```

### graph_build

```json
{
  "status": "materialized",
  "graph_build_id": "GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:b874641cdb628d4e",
  "summary": {
    "node_count": 6850,
    "edge_count": 38657,
    "nodes_by_type": {
      "DiseaseContext": 1,
      "Disease": 1,
      "Pathway": 709,
      "Gene": 5790,
      "GeneSet": 29,
      "Drug": 30,
      "Candidate": 50,
      "S2Condition": 240
    },
    "source": "neo4j",
    "snapshot_kind": "按 GraphBuild ID 标记的 Neo4j 图谱版本",
    "neo4j_membership": "registered",
    "import_status": "PASS",
    "test_only": false,
    "neo4j_importer_sha256": "9ddb7497a0612c03a730949542469b3f123ab4d1c3a896470abbdbfa768faced"
  },
  "idempotent": true
}
```

### superseded_graph_build_audit

```json
{
  "retained_legacy_versions": [
    {
      "graph_build_id": "GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:92ccf8669de7c697",
      "reason_not_canonical": "旧通路链接无 Ensembl crosswalk；31,991 条链接唯一映射 0 条，交汇路径 0 条。"
    },
    {
      "graph_build_id": "GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:89efd9796240c910",
      "reason_not_canonical": "虽有 30,350 条唯一映射和 1,494 条交汇路径，但曾把通路显示名称误作节点 ID；本次 stable-ID 修复后另建版本。"
    }
  ],
  "action": "旧版本均保留供审计；新版本采用 GO、Reactome、MSigDB 稳定标识。"
}
```

## 溯源与解释边界

历史完整 limma 输入 SHA-256：`b3dafdae855a0f44cbe80dbc40d17693ed01f4b31d899acbabc60e5485ed21c4`。S1 结果仅由预计算表解析器标准化，未重跑差异分析。新的项目级富集以此标准化 S1 为输入，使用已安装的 R/Bioconductor 环境生成 Entrez 与 Ensembl 映射；历史富集副本仍留作原始来源。S2 是已有完整筛选的历史输出导入；其原始 S1 输入 SHA 与本项目登记数据集 SHA 一致，接口校验了项目上传文件及哈希。项目 GraphBundle 仅纳入 Exp006 Top 50 的 scheme B perturbagen，并保留每个药物所有剂量条件，不重新排序、不作疗效判断。

GraphBundle 中的公共药物靶点与通路关系仍来自其来源数据库；关系交汇表示可追溯证据共现，不证明因果、疗效或 ER 阳性特异机制。

## 机器可读记录

完整阶段信息见 `experiments/platform_phase_c/formal_erpos_project_linkage.json`。
