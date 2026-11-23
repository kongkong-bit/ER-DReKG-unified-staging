# KG06 Top50 EvidencePackage 重建报告（v2）

执行时间：2026-11-14。使用当前 KG06 API 代码，从本地 Postgres 与 Neo4j 只读重建 EvidencePackage。原始 `evidence_packages/` 保留；本次输出另存于 `results/evidence_packages_v2/`。

## 验收结果

- Top50 请求：50；成功：50；失败：0。
- GraphBuild：`GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:a08001496a447f7f`。
- EvidencePackage 路径数：2,111；所有包的 `evidence_integrity_pass` 均为 true。
- S2 条件数：240；每个条件都有一个 Evidence ID，共 240 个。240/240 在当前 GraphBuild 的 PostgreSQL EvidenceRecord 中核验通过。
- 每个包包含对应项目的 AnalysisRun、WTCS/Exp006 及已有的 Phase F/PRISM 字段；路径原始来源、source record、作用描述和冲突状态由 KG06 API 返回。
- 本次为派生 JSON/CSV 输出，不写入或修改 S1、S2、GraphBundle、PostgreSQL 或 Neo4j。

## 复现产物

- `results/evidence_packages_v2/`：50 个逐候选 JSON、索引和 SHA-256 manifest。
- `run_top50_packages.py`：可用 `KG06_BASE_URL` 与 `KG06_PACKAGE_OUT` 环境变量指定 API 和输出目录。
- `kg07_top50_explanation_coverage_report.md`：基于 v2 EvidencePackage 的解释输入覆盖审计。

路径和 Evidence ID 完整性只能证明检索对象与数据库记录对应，不证明某个解释句子的生物学语义正确。无来源 URL、无映射或无路径仍保留为缺口。
