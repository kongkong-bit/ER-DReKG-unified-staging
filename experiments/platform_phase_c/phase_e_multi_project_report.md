# Phase E：多疾病项目隔离与公共实体复用验证

日期：2026-11-13；最近验收更新：2026-11-14

## 验证目标

使用明确标记为 `test_only` 的小型夹具，验证两个不同疾病项目能够独立构建图谱包，共享稳定公共实体 ID，并保留彼此独立的 DiseaseContext、Candidate、S2Condition 与 AnalysisRun 来源。另以真实 GSE42568/LINCS 数据开展受限的软件端到端验证，导入测试 Neo4j 并通过 FastAPI 查询；不使用患者科研结论，也不写入正式 ER+ 项目。

## 方法

扩展 `kg/tests/test_project_graph_bundle.py`，复用同一份小型 OptimusKG Parquet 夹具、S1/S2/富集表和 LINCS perturbagen 结构元数据，分别构建乳腺癌与肺癌两个独立 GraphBundle：

- 项目、疾病、S1/S2/富集运行 ID 均分别设置。
- 两个项目的公开药物、Ensembl 基因和 GO 通路使用相同稳定 ID。
- 项目候选、疾病上下文及 S2 条件使用项目 ID 和运行 ID 命名空间。
- 检查第二个项目的候选/条件边只引用第二个 S2 AnalysisRun，疾病上下文只引用第二个疾病和 S1 AnalysisRun。
- 将第一个项目相同输入再次构建到另一版本目录，比较文件哈希并确认旧版本文件未改变。

## 验收

| 要求 | 状态 | 证据 |
|---|---|---|
| 两个测试项目可以分别生成 GraphBundle | 通过 | 同一测试运行中分别完成两个 `build_bundle` 调用，清单均为 `validated` 且 `test_only=true` |
| 公共实体跨项目复用稳定 ID | 通过 | 两个包均包含相同 ID 的测试药物、基因和 GO 通路 |
| 项目 S1/S2 结果不串项目 | 通过 | DiseaseContext 记录各自 disease/S1 run；第二项目 S2 关系仅带第二项目 S2 run；候选、context、condition ID 命名空间互不重叠 |
| 重新构建不破坏旧版本 | 通过 | 同一运行输入写入独立目录后输出哈希一致，原始版本节点文件 SHA-256 保持不变 |
| 合成夹具标记与科研数据隔离 | 通过 | 所有测试包均标记 `test_only=true`；未写入正式项目或原始 S1/S2 目录 |
| 单个测试项目的 Neo4j/FastAPI 联调 | 通过 | 实际测试项目图包导入 Neo4j；汇总、搜索、子图、机制、证据 API 均返回 200；使用其他 GraphBuild ID 查询返回 404。完整真实数据记录见[端到端报告](phase_e_graphbundle_e2e_report.md) |
| 两个不同项目同时导入 Neo4j 的隔离验证 | 通过 | 2026-11-14 在实际 PostgreSQL/Neo4j 中保留第一真实数据 `test_only` 项目并导入第二独立 `test_only` 软件夹具；公共 Drug/Gene/GeneSet 节点各一份，FastAPI 搜索、子图、机制与跨 GraphBuild 404 均通过。详见[双项目数据库验收报告](phase_e_neo4j_multi_project_report.md) |

## 运行记录

命令：

```powershell
.\s2_lincs\.venv\Scripts\python.exe -m pytest kg/tests/test_project_graph_bundle.py -q
```

结果：`1 passed`。该测试是软件架构验证，不代表任何疾病的药物筛选实验。

## 补充：真实数据测试项目闭环

2026-11-13 已在 PostgreSQL 中的 `test_only` 项目运行受限闭环：标准化 S1、真实 S1 通路富集、30 条 MCF7 真实 LINCS Level 5 Signature、GraphBundle 构建、Neo4j 导入及 FastAPI 查询。GraphBundle 含 7,299 个节点和 37,558 条关系；FastAPI 汇总、搜索、子图、机制及证据接口均完成实际请求。该 S2 子集是软件验收数据，不是全量筛药或正式候选排名。查询结果中的通路重叠也不代表药物疗效。

## 结论与剩余工作

GraphBundle 层与实际数据库级双项目测试均已证明公共实体可按稳定 ID 共用，同时项目 Candidate、DiseaseContext、S1/S2 运行和 GraphBuild 查询范围保持隔离，重复导入不复制公共节点。第二项目的项目关系为显式 `test_only` 软件夹具，不代表第二种疾病的实验发现。正式 ER+ 项目仍须使用其本身同源 S1/S2/富集运行后再生成图包。

2026-11-14 新增实际 PostgreSQL/Neo4j 验收：两个项目同时存在；药物 `CHEMBL2103991`、基因 `ENSG00000132170` 和 MSigDB GeneSet `MSIGDB:HALLMARK_ADIPOGENESIS` 在 Neo4j 中各仅一份。FastAPI 的两个 GraphBuild 查询均返回正确项目数据，将对方 GraphBuild ID 用于查询均返回 404。第二项目保留在数据库中并标记 `test_only`，便于查看软件隔离结果。详细计数、ID 和 API 检查见[数据库验收报告](phase_e_neo4j_multi_project_report.md)。

复跑命令（从工程根目录）：

```powershell
backend\.venv\Scripts\python.exe scripts\verify_neo4j_multi_project.py
```

结果：`PASS`。同一第二项目和 GraphBuild 被幂等重用；公共节点各 1 份，未复制。Docker Engine 29.6.1、PostgreSQL 与 Neo4j 容器状态已实际检查为 healthy。Neo4j 全实例总计 8,468 个节点、74,937 条关系；该数值包含多个项目和 GraphBuild，不等于任一单项目子图规模。
