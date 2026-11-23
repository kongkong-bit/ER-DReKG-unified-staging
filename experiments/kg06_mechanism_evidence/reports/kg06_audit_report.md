# KG06 机制证据覆盖审计

审计时间（UTC）：2026-11-14T11:01:58.751870+00:00
正式 GraphBuild：`GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:a08001496a447f7f`；GraphBundle：`ANALYSIS_RUN:KG_GRAPH_BUNDLE:54530b3e-efcd-4629-9345-d61f5c4363f7`。

## Neo4j 实际 Schema

- 节点标签：Candidate, Disease, DiseaseContext, Drug, Gene, GeneSet, Pathway, S2Condition。
- 关系类型：ABOUT_DISEASE, CONTAINS_GENE, HAS_CANDIDATE, HAS_DEG, HAS_ENRICHED_GENE, HAS_ENRICHED_PATHWAY, HAS_S2_CONDITION, REFERENCES_DRUG, TARGETS。
- 当前 Schema 没有 `ProteinTarget` 或 `EvidenceRecord` 节点标签；靶点用 Drug→Gene 的 `TARGETS` 关系表示，EvidenceRecord 存在 PostgreSQL，并将 evidence IDs/source assertions 冗余写在关系属性中。
- GraphBuild 作用域内关系数：38,998；没有 evidence IDs 的关系数：0；缺 source release：0；缺 source assertion：0。
- PostgreSQL EvidenceRecord：38,998；Neo4j 当前 GraphBuild 去重 evidence ID：38,998；未能在 PostgreSQL 找到：0。

## Top50 覆盖

- Top50 候选节点：50/50 (100.0%)；精确化合物映射：30/50 (60.0%)。
- 有至少一个真实直接靶点：28/50 (56.0%)；有公共 KG pathway 路径：13/50 (26.0%)。
- 有 S1 富集通路交汇：24/50 (48.0%)；有 S1 DEG 直接交汇：24/50 (48.0%)。
- 路径行数：直接靶点 433、公共 Pathway 95、S1 富集交汇 1,494、S1 DEG 交汇 89。

## 判读边界

Top50 来源于 Exp006，WTCS、剂量稳定性等保留为独立关联证据；本审计不把 WTCS 负值转换为疗效。OptimusKG 关系断言中的 `TARGET`、`INHIBITOR` 等仅记录来源描述；没有明确作用词的关系不推断抑制/激活。路径表示来源关系交汇，不证明因果或临床疗效。没有映射或路径的候选在 CSV 中保留为零覆盖，不补造机制。

## 复现产物

- `results/neo4j_schema_audit.json`：实时 Neo4j 标签、关系、约束和属性审计。
- `results/top50_mechanism_coverage.csv`：逐候选覆盖率及 S2 稳定性字段。
- `results/kg06_mechanism_paths.jsonl`：逐路径边属性、来源断言、作用词、冲突标记和 evidence ID。
- `results/kg06_audit_manifest.json`：输入/输出 SHA-256 及验收状态。
