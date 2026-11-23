# GraphBuild 版本化 EvidenceRecord 持久化验收

日期：2026-11-14  
项目：ER-positive breast cancer drug repositioning  
项目 ID：`3f18f4c1-713d-58c5-8a53-38eca5a5aaf9`

## 本次补齐

- 新增 PostgreSQL `evidence_records` 表，记录 GraphBuild、项目、稳定 evidence ID、来源发布版、原始记录 ID、主谓宾关系、原始断言 JSON、来源 URL 和断言 SHA-256。
- 唯一约束为 `(graph_build_id, evidence_id)`。相同 evidence ID 在不同 GraphBuild 中分别保存，不会覆盖或重新标记历史证据。
- `POST /api/v1/projects/{project_id}/graph-builds` 在 Neo4j 图谱成功物化后，按已校验 GraphBundle 的 `evidence_records.csv` 分批写入 PostgreSQL。写入前复核文件哈希、断言 JSON、字段和 evidence ID 唯一性；事务失败可回滚，重复请求核验现有记录并幂等补齐。
- 指定 `graph_build_id` 的 Evidence API 优先从对应 PostgreSQL EvidenceRecord 返回来源记录；未迁移的旧格式图仍使用已存在的图谱回退查询。
- GraphBuild 摘要登记该版本的记录数量、输入哈希和持久化状态。Neo4j 节点/关系没有重写，GraphBundle 和历史科研文件保持不变。

## 数据库与逐版本核验

- Alembic 从 `b6d3e9a24f10` 升级到 `d7e15b5a42c1`，只创建 EvidenceRecord 表及三个索引，没有删除或改写现有表。
- 对正式项目全部 GraphBuild 版本，逐个调用 `_graph_build_inputs` 的完整验证路径，核实项目/运行归属、AnalysisRun manifest、Bundle manifest、校验清单和所有输出 SHA-256；7 个已物化 GraphBundle 版本的 `evidence_records.csv` 哈希均与 GraphBuild 原始输入哈希一致。
- 回填后 PostgreSQL 实查：**7 个 GraphBuild、240,910 条记录、240,910 个版本内唯一 evidence ID**。各版记录数为：

| GraphBuild 后缀 | EvidenceRecord 数 | 状态 |
|---|---:|---|
| `25e3b3f52aa5d6fb` | 38,998 | 已持久化 |
| `70bf5e7a5a024dfa` | 38,998 | 已持久化 |
| `89efd9796240c910` | 38,240 | 已持久化 |
| `92ccf8669de7c697` | 7,680 | 已持久化 |
| `a08001496a447f7f` | 38,998 | 已持久化 |
| `a6aabb2147cb5f5e` | 38,998 | 已持久化；保持 Phase F 原版本关联 |
| `b874641cdb628d4e` | 38,998 | 已持久化 |

- Phase B GraphBuild `28ac2382bd7f7ea9` 使用 legacy bundle，不关联 KG GraphBundle Evidence CSV，故按设计跳过；失败版本 `610bf2b2269209ae` 保持失败审计状态，未写入记录或改状态。
- 最新版本 `a08001496a447f7f` 的证据文件 SHA-256：`4a1a3a5cf7ece3a8ef43cf3b950b2aa6a18442938e940f19ab263e8142ed91c6`。同一 evidence ID 已分别从最新版本和历史 Phase F 版本 `a6aabb2147cb5f5e` 成功读取，API 返回的 GraphBuild ID 与请求一致。

## 测试结果

- EvidenceRecord 单元测试通过：真实 SQLite schema、GraphBuild 版本隔离、幂等写入、来源字段/哈希回读，以及输入哈希变化时拒绝写入。
- 后端隔离回归：**46 passed**（CSV 图源、SQLite 数据库）。
- Vite/FastAPI 实际联调：**PASS**，检查了最新版本 38,998 条证据计数、其 manifest SHA-256、最新图边证据及 Phase F 历史版本证据。
- 历史 S1/S2/Exp006–Exp011 22 个输入文件 SHA-256 仍与原清单一致。

## 可复现记录

- 回填命令：`backend/.venv/Scripts/python.exe scripts/backfill_graph_evidence_records.py --project-id 3f18f4c1-713d-58c5-8a53-38eca5a5aaf9 --apply`
- 逐版本回填机器记录：`experiments/platform_phase_e_evidence/evidence_record_backfill.json`
- 前后端联调记录：`experiments/platform_phase_d/phase_d_verification.json`
- 迁移：`backend/migrations/versions/d7e15b5a42c1_add_versioned_evidence_records.py`

本项只补齐来源断言的数据库持久化和 GraphBuild 版本检索，不验证生物医学来源断言的科学正确性，也不增加药物疗效或因果结论。
