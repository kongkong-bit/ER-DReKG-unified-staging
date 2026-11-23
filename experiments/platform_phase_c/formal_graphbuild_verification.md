# 正式 ER+ GraphBuild 实际验收报告

检查时间（UTC）：2026-11-14T09:37:51.875898+00:00

正式 GraphBuild：`GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:a6aabb2147cb5f5e`。

## 数据与 Neo4j 核验

- Neo4j 实际查询：6,850 个节点、38,657 条关系。
- GraphBuild 版本范围检查：当前版本 DiseaseContext=1；旧版本上下文未混入。
- 图包含 738 个通路/基因集节点；所有 ID 均为 GO、Reactome 或 MSigDB 稳定 ID，没有将通路描述误作节点 ID。
- 通路—基因链接 31,991 条，其中 30,350 条唯一映射到 Ensembl。
- 候选 perturbagen 50 个；精确 InChIKey 映射到公共药物 30 个；240 个剂量条件；交汇路径 1,494 条。
- GraphBundle 所有输出文件均与 manifest 哈希一致；S2 条件数据库持久记录为 240 条。

## FastAPI 实际接口核验

- 图摘要：200，来源 `neo4j`，按 GraphBuild 关系过滤；当前版本 DiseaseContext=1。GraphBuild 数据库中旧 summary 留存其生成时统计，本报告使用修复后的实时版本内计数。
- 机制查询：候选 `BRD-A00147595` 返回 82 条版本内路径。
- 证据查询：返回 HTTP 200，可按 evidence ID 回溯。
- S1 GO 上调通路接口：206 项。S2 条件接口：240 项。

## 版本解释

先前两个 GraphBuild 保留在数据库中供审计；一个缺少 Ensembl 映射，另一个曾使用显示名称作为节点 ID。当前 GraphBuild 使用稳定 ID，是正式查询应选择的修正版。所有机制路径仍表示来源关系交汇，不证明因果、治疗效果或 ER 阳性特异性。

机器可读记录：`experiments/platform_phase_c/formal_graphbuild_verification.json`。
