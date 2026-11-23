# DiseaseContext 版本化持久化补充报告

日期：2026-11-14

## 实施内容

- 新增 PostgreSQL `disease_contexts` 表，主键由 GraphBuild ID 与上下文 ID 计算；唯一约束为 `(graph_build_id, context_id)`。项目、疾病标识、标签和原始上下文 JSON 均保留，覆盖 S1、S2、富集 AnalysisRun 引用。
- 导入只接受 GraphBuild 已登记 SHA-256 一致的 `subgraph_nodes.csv`；只写入 `type=DiseaseContext` 且 `project_id` 与当前 GraphBuild 项目一致的节点。重复写入幂等；哈希或已存内容变化会被拒绝。
- 新 GraphBuild 完成物化后持久化 DiseaseContext 数量、输入哈希和状态；历史 GraphBundle 由回填脚本逐版验证后补齐。没有重算或修改 S1/S2、GraphBundle、Neo4j 节点及关系。

## 运行结果

- Alembic 数据库版本：`d7e15b5a42c1 → e4f62ab7093c`，新增表和索引。
- 历史回填：7 个已物化 GraphBundle **PASS**，每个版本 1 条 DiseaseContext；共 7 条。1 个 legacy GraphBuild 按原策略 **SKIP**，0 个 BLOCKED。
- 正式 GraphBuild `a08001496a447f7f`：DiseaseContext 计数 1，`subgraph_nodes.csv` SHA-256 `16d3fdf3aae73e094811f3f9eea8f81ea930d026e772906892f7e14de09f23dc`。
- 新增 SQLite 单元测试：DiseaseContext 版本隔离、幂等重试和哈希变化拒绝均通过；EvidenceRecord 相关测试也通过（2 项）。
- 前端/API 只读集成验收：**PASS**，包括正式 GraphBuild 的上下文状态、数量和哈希摘要。
- 首次全量回归暴露测试进程继承开发 `.env` 的 `GRAPH_SOURCE=neo4j`，导致单元测试误触真实 Neo4j。新增 `backend/tests/conftest.py`，强制单测使用 CSV 测试适配器；Neo4j 查询路径另由显式 mock 测试覆盖。修复后全量后端回归 **47 passed**。
- 重新核验 Phase A 历史输入清单：22 个文件均存在，SHA-256 22/22 匹配。测试原始输出保存在 `backend_pytest_20261114.log`。

## 变更文件

- `backend/app/models.py`
- `backend/app/main.py`
- `backend/migrations/versions/e4f62ab7093c_add_disease_contexts.py`
- `backend/tests/test_api.py`
- `backend/tests/conftest.py`
- `scripts/backfill_graph_evidence_records.py`
- `scripts/verify_phase_d_frontend.py`
- `docs/architecture/database_design.md`
- `experiments/platform_phase_e_evidence/evidence_record_backfill.json`
- `experiments/platform_phase_e_evidence/backend_pytest_20261114.log`

