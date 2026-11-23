# 图谱增强阶段评估（部分离线结果）

## 已有证据与本轮改动

Top 10 名单沿用冻结 manifest。离线子图保留 OptimusKG/BioCypher 原关系，并加入 SIGNOR Oct2026 人类 direct protein-protein signed causal records、OmniPath academic-filtered core resource/evidence records、精确 UniProt↔gene mapping，以及项目现存 ChEMBL/Reactome98 context snapshots。Reactome current-2026-10 hierarchy 与人类 gene-pathway membership 已规范化；唯一 membership 和 hierarchy 断言作为无符号注释层导入独立 staging。PrimeKG Dataverse v2 CC0-1.0 已核验并抽取 Top10 子集，以无方向 ASSOCIATED_WITH 关系导入 staging；该关联不扩展或赋符号给调控链。每条机制路径保留调控断言 ID、逐来源 evidence、映射 evidence、release、许可及 source hash。调控路径仅沿 directed REGULATES 搜索，最多 4 个调控步；通路参与仍不用于 sign propagation。

## 指标和边界

{
  "schema_version": 1,
  "status": "staging_graph_imported_research_evaluation_partial",
  "baseline": {
    "source": "reports/top10_kg/09_before_after_comparison.md",
    "old_graph_direct_target_coverage": "5/10 (historical file-based audit)",
    "old_path_coverage": "5/10 (historical GraphBuild a6aabb2147cb5f5e)"
  },
  "external_data": {
    "SIGNOR": {
      "release": "Oct2026",
      "records_raw": 43727,
      "records_valid": 18286,
      "records_rejected": 25441,
      "sha256": "63db6f65e9148e81354f564c3c3cdfc9ee45dc421553bd0926e5fae511ef9d06"
    },
    "OmniPath": {
      "release": "API-current-2026-11-22",
      "records_raw": 86189,
      "signed_source_assertions": 73915,
      "records_rejected": 15650,
      "sha256": "1092e4ee04f02bac0da89d0ea8d93570b2c54178be69656bf2a6780f8d6977e5",
      "license_filter": "academic; per-resource license retained"
    },
    "Reactome_current_gene_pathways": {
      "release": "current-2026-10",
      "records_valid": 54361,
      "records_rejected": {
        "unmapped_or_ambiguous_uniprot": 108281
      },
      "sha256": "b56bdfeeece937ff12de31ad637fe4b5443ec091915776044850f4c0f31235fb",
      "top10_terminal_gene_annotations": 17504,
      "sign": "unknown; annotation only; imported as CONTAINS_GENE"
    },
    "PrimeKG": {
      "release": "Harvard Dataverse v2 (2022-05-02)",
      "license": "CC0-1.0",
      "sha256": "0a5a010fcd88dcec572a573d98c26c1c244a11567092b6161d3ded611cfb5c69",
      "candidate_identity_coverage": "6/10",
      "subset_edges": 1026,
      "status": "imported_to_isolated_staging_as_unsigned_associations"
    },
    "DrugMechDB": {
      "schema_version": 1,
      "status": "independent_reference_coverage_and_target_overlap_partial",
      "dataset": "DrugMechDB",
      "release": "2.0.1",
      "license": "CC0 1.0 Universal (pinned repository LICENSE retained)",
      "source_file": "data/kg_enrichment/raw/drugmechdb/2.0.1/indication_paths.yaml",
      "source_sha256": "b973118ff3a43450aac9facc9957ec5ce1310efa049ed11b6e94b42807050ee7",
      "raw_path_record_count": 4846,
      "disease_scope": {
        "mesh_id": "MESH:D001943",
        "label": "Breast Neoplasms",
        "interpretation": "broad breast-neoplasm indication; not ER+ subtype evidence"
      },
      "candidate_matching": "case-insensitive exact alphanumeric drug-name match; no alias/name inference",
      "top10_exact_drug_path_matches_any_disease": 16,
      "top10_exact_breast_neoplasm_path_count": 1,
      "top10_coverage": "1/10",
      "unique_mapped_direct_target_pairs": 1,
      "unique_target_overlap_pairs": 1,
      "target_overlap_fraction": "1/1",
      "malformed_matching_records_rejected": 0,
      "matches_csv": "reports/kg_enrichment/08_drugmechdb_breast_path_matches.csv",
      "interpretation_limit": "Independent curation provides indication and target-overlap support only; it does not validate ER+ benefit or the candidate regulatory path to S1 genes."
    }
  },
  "enhanced_offline_bundle": {
    "top10_exact_identity": "10/10 (8 OptimusKG exact + 2 explicit external overlay)",
    "target_assertion_coverage": "10/10 (any retained target assertion; relation types remain separate)",
    "candidate_to_S1_pathway_routes": "8/10; 528 historical graph intersection rows (not regulatory paths)",
    "signed_regulatory_path_coverage": "9/10",
    "signed_regulatory_path_count": 349,
    "signed_paths_by_pert_id": {
      "BRD-K44227013": 181,
      "BRD-K16485616": 21,
      "BRD-K56405753": 22,
      "BRD-K92093830": 1,
      "BRD-K76694128": 0,
      "BRD-K50000283": 61,
      "BRD-K11153516": 11,
      "BRD-A00147595": 14,
      "BRD-K13094524": 7,
      "BRD-K83837640": 31
    },
    "path_assertions_by_source_unique_within_top10": {
      "SIGNOR": 157,
      "OmniPath": 171
    },
    "potential_or_contextual_conflict_pairs_after_hub_filter": 107,
    "ChEMBL_to_Reactome98_context_route_coverage": "5/10",
    "ChEMBL_to_Reactome98_context_route_count": 316,
    "context_routes_by_pert_id": {
      "BRD-K44227013": 0,
      "BRD-K16485616": 111,
      "BRD-K56405753": 19,
      "BRD-K92093830": 0,
      "BRD-K76694128": 13,
      "BRD-K50000283": 0,
      "BRD-K11153516": 0,
      "BRD-A00147595": 8,
      "BRD-K13094524": 0,
      "BRD-K83837640": 165
    },
    "traceable_assertions": "path edge IDs, UniProt-gene mapping evidence, source records, PMID refs and source hashes attached in per-drug artifacts",
    "offline_biocypher_extension": {
      "status": "offline_biocypher_validated_not_imported",
      "nodes": 297,
      "edges": 461,
      "signed_assertions": 328,
      "importer_row_preparation": "PASS",
      "neo4j_write_performed": false
    },
    "registered_staging_graph_build": {
      "status": "PASS",
      "method": "existing project GraphBuild API and importer",
      "analysis_run_id": "ANALYSIS_RUN:KG_GRAPH_BUNDLE:634be378-67ba-4b0c-b649-d61761b5b4dc",
      "graph_build_id": "GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:c48926d9a9983865",
      "nodes": 6985,
      "edges": 39351,
      "signed_regulatory_assertions": 328,
      "source_evidence_records": 39218,
      "pathway_gene_relations_remain_unsigned": true
    },
    "registered_external_graph_build": {
      "analysis_run_id": "ANALYSIS_RUN:KG_GRAPH_BUNDLE:6b5e4d6e-40c4-4cfb-9a72-692dafe2b4e6",
      "graph_build_id": "GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:6ea657f0a3a95099",
      "nodes": 9526,
      "relationships": 91943,
      "evidence_records": 91810,
      "preflight": "PASS",
      "import_status": "PASS",
      "import_runs": [
        "PASS",
        "PASS"
      ],
      "exact_inventory_problems": 0
    },
    "external_graph_build_audit": "reports/kg_enrichment/09_external_layer_import_audit.json",
    "external_layer_rollback_status": "PASS",
    "drugmechdb_independent_breast_reference": "1 exact drug-name-matched breast-neoplasm reference path(s); direct target overlap 1/1",
    "er_context_records": 11,
    "manual_grade_distribution": {
      "A": 3,
      "B": 6,
      "C": 1,
      "U": 0
    }
  },
  "interpretation": "Coverage definitions differ across historical bundle versions; the old/new target counts are not a controlled ablation. SIGNOR and OmniPath now contribute source-traceable signed regulatory paths for a subset of candidates. The computed path sign describes propagation across molecular regulation edges; it is not combined with drug action or interpreted as protein activity from S1 mRNA. ChEMBL→Reactome98 routes remain annotation context. DrugMechDB evaluation found one strict breast-neoplasm indication/target-overlap case; this is not population-wide recall. No blind path validity review has been run.",
  "not_evaluated": [
    "source ablations under one identical evaluator",
    "blind path validity",
    "drug-action-to-terminal-protein direction versus disease activity",
    "broad independent DrugMechDB recall (only exact Top10 drug-name/breast-neoplasm matches reported)",
    "browser E2E and mechanism path UI acceptance",
    "production deployment/promotion"
  ]
}

旧版与新版覆盖口径不完全一致，故此处不声称受控实验提升。当前 signed regulatory paths 和冲突对数量见上方机器可读评估；这些统计是候选子图命中数，不等同于独立实验数或路径有效性。S1 transcript direction 未用于推断蛋白活性；MCF7 与 SIGNOR BTO cell/tissue context 尚未统一映射。DrugMechDB v2.0.1 是独立参考，不并入预测图；严格药名 + Breast Neoplasms MeSH 匹配仅得 1 条，且只支持 doxorubicin-TOP2A 靶点重叠，不验证 ER+ 疗效或完整机制。未做盲法专家路径核验。任务专用 staging Neo4j 已完成只读审计、冷备份、恢复验证和两个 GraphBuild 导入；两版本幂等及精确清单均通过，独立恢复副本的回滚演练通过。主数据库未修改。

## 缺失与失败解释

部分药物没有 ChEMBL direct mechanism 或可精确匹配的 human protein component/Reactome 98 映射；部分药物也没有当前报告可用的基因级 S2 响应，不能用药物层面的 WTCS 填补。没有调控边可使目标到 S1 疾病基因的因果路径无法搜索；缺少 ER+ 的药物特异文献时只报告已有审查表记录，不做外推。

## 下一步

首个 GraphBuild 导入 328 条路径支持的有向调控断言（6,985 节点、39,351 条关系、39,218 条 EvidenceRecord）。第二个 GraphBuild 导入 Reactome/PrimeKG 外部层（9,526 节点、91,943 条关系、91,810 条 EvidenceRecord）：Reactome 48,709 条唯一基因-通路断言和 2,905 条层级边；PrimeKG 978 条 ASSOCIATED_WITH 关联。两次导入均通过双次幂等、精确 inventory、来源字段核验和独立恢复副本回滚演练。剩余研究工作包括冻结 Top 10 下的 source ablations、盲审路径有效性、统一 MCF7/组织背景、浏览器端到端验收和生产部署评估。
