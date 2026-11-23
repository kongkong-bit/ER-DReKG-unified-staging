# Phase E：Neo4j 双项目数据库隔离验收报告

运行时间（UTC）：2026-11-14T05:18:18.937930+00:00

## 验收范围

在实际 PostgreSQL 与 Neo4j 服务中，同时保留已有 GSE42568/LINCS `test_only` GraphBuild，并新建第二个 `test_only` 软件验证项目。第二项目复用第一项目图包中的公共药物、基因、通路 ID 与公开关系；新增 Candidate、S1/S2 关联、DiseaseContext 和 S2Condition 均明确标记为软件夹具，不作为科研数据。

## 实际结果

- 第一项目：`89aa18d8-e1ca-4eb4-8046-634cd2911207`，GraphBuild `GRAPH_BUILD:89aa18d8-e1ca-4eb4-8046-634cd2911207:52b0590ca225433b`，Neo4j 查询节点/关系数为 7283/37538。
- 第二项目：`c493efde-981a-511c-9409-0fac7021b096`，状态 `test_only`，GraphBuild `GRAPH_BUILD:c493efde-981a-511c-9409-0fac7021b096:phasee-multi-project`，该测试图包有 6 个节点、7 条边；API 返回 6 个节点、7 条关系。
- 第二项目没有伪造 S1/S2 结果：S1、S2、富集占位运行状态均为 `fixture_only`，API 的 S1/S2 summary 均返回 `available=false`；仅 GraphBundle 软件夹具运行状态为 `completed`。
- 两个项目共同复用的公共实体：`CHEMBL2103991`（Neo4j 中 1 份）, `ENSG00000132170`（Neo4j 中 1 份）, `MSIGDB:HALLMARK_ADIPOGENESIS`（Neo4j 中 1 份）。
- 两个 GraphBuild 的项目图摘要和 FastAPI 搜索/子图/机制接口均返回 200；第二项目专用哨兵药物只在第二项目可见，第二项目的测试 Perturbagen 在第一项目机制查询中无结果。
- 把对方的 GraphBuild ID 传给项目接口，两侧均返回 404。

## 验收状态

| 检查项 | 状态 |
|---|---|
| 两个项目同时存在于 PostgreSQL 和 Neo4j | 通过 |
| 公共 Drug/Gene/Pathway 按稳定 ID 复用，数据库各仅一份 | 通过 |
| 项目 Candidate、DiseaseContext、S1/S2 运行和条件关系隔离 | 通过 |
| 软件夹具不冒充已完成的 S1/S2 结果 | 通过 |
| FastAPI 子图、搜索、机制查询及 GraphBuild 项目归属限制 | 通过 |
| 软件夹具与科研结果边界清楚 | 通过 |

## 解释边界

第二项目新增候选链接、S1/S2 运行 ID 和项目边仅为 test_only 软件夹具；本验收证明数据库隔离和公共节点复用，不表示真实药物扰动实验、候选药物优劣或治疗效果。第一项目真实数据测试也仍不是全量 S2 筛选。

## 机器可读记录

完整运行 ID、GraphBuild、实际 API 状态码及复用实体见同目录 `phase_e_neo4j_multi_project_validation.json`。
