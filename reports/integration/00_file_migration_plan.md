# 文件级迁移计划

目标根目录：`D:\CLASS\ER-DReKG-unified-staging`（基于 syh 的快照）。遵循按功能适配，不整目录覆盖。

| 来源 | 精确文件/入口 | 依赖与数据契约 | 目标与处理 | 验证 |
|---|---|---|---|---|
| syh（主线） | `backend/app/main.py`：S1/S2、`/kg06/*`、`/kg07/interpret/{pert_id}`、`/top10/mechanisms/*`、`/graph-bundles`、`/graph-builds` | SQLAlchemy/Alembic、项目/run ID、Neo4j `project_id` / graph build；S2 `pert_id` | 原样保留为 staging 基线；后续集中重构需基于差异，不覆盖用户改动 | Python import、API 测试、隔离 PostgreSQL/Neo4j、真实 Top10 前端流程 |
| syh（主线） | `frontend/src/pages/Top10MechanismsPage.tsx`、`frontend/src/App.tsx`、`frontend/src/api.ts` | 现有 `/api/v1/projects/{project_id}/top10/mechanisms` 与机制详情/报告端点 | 保留其页面/路由及设计；检查错误状态与数据 ID 联动 | `npm run build`、浏览器调用真实 API |
| syh（主线） | `kg/scripts/build_project_graph_bundle.py`、`import_phase_b_to_neo4j.py`、`verify_neo4j_import.py`、`config/biocypher_schema.yaml` | BioCypher bundle manifest、PostgreSQL graph build、Neo4j 导入和版本字段 | 保留当前主线；以交付包作为正式运行证据对齐输入与输出，而非复制替换 | bundle hashes、测试、隔离 Neo4j 导入/验证；不得触碰正式库 |
| KG delivery | `04_code/kg/scripts/build_project_graph_bundle.py`；`import_phase_b_to_neo4j.py`；`verify_neo4j_import.py`；`compare_graph_build_snapshots.py`；对应 `kg/tests/*` | A+ frozen inputs、`03_GraphBundle/e0421796-...`、正式 build `d570eb8deb3e5eea` | 逐文件与 staging `kg/` 比较；重复逻辑不复制，差异用于核验；保留正式证据 ID/计数 | 比较 SHA/语义差异；核对 run/build IDs 和验证报告；隔离服务复现 |
| KG delivery | `04_code/backend/app/main.py` 和 `patches/main_collab_removal.diff` | FastAPI 路由；派生代码特意删除 collab 导入 | 不整体迁移。只抽取与 syh 缺失的 GraphBuild 状态转换，适配 syh 已有入口 | API contract/API tests；检查 syh 的协作和其它路由仍注册 |
| KG delivery | `01_inputs/aplus_freeze/*`、`01_inputs/aplus_adapted/*`、`02_S2_run/eab2f02a-.../*` | manifest、SHA256、4,385 signature score；不同 S2 lineage | 作为版本化数据/证据保留，可登记为单独 analysis run；不得覆盖 syh 正式数据 | 哈希链、候选映射、Top10 对比和 run provenance |
| wd | `kg/scripts/build_seed_subgraph.py`、`extend_s1_pathway_subgraph.py`、`fetch_optimuskg_subset.py`、`build_phase_e_test_fixture.py`、`tests/test_seed_subgraph.py`、`test_biocypher_adapter.py` | OptimusKG 外部许可数据、Reactome/S1 pathway、BioCypher | 检查 syh 是否等效；仅移入缺失的通用算法/测试，测试数据不冒充正式数据 | KG 单测、许可/来源审计、Neo4j fixture integration |
| wd | `experiments/kg07_mechanism_interpretation/*`（`run_top50_explanations.py`、evaluation/scoring、rule templates、manifest） | kg07 API、证据包、可能的 GLM 配置和运行日志 | 先审计 provider 与结果来源；纳入独特评估脚本/报告到 `experiments/`，禁止把模板结果称为在线 AI | 无密钥/超时与 citation 验证；离线评估复现 |
| wd | `scripts/verify_formal_erpos_graphbuild.py`、`run_phase_e_graphbundle_e2e.py`、`register_erpos_historical_project_runs.py`、`audit_project_run_provenance.py` | PostgreSQL/Neo4j；运行路径和项目 ID | 从本机绝对路径改为 CLI 参数/配置后，以运维工具方式纳入 `scripts/`（仅确有缺口时） | dry-run 与隔离数据库；无副作用检查 |
| zq | 当前没有文件 | 不适用 | 无可迁移内容；若目录在之后出现新文件，重新审计 | `rg --files` 清单 |

## 依赖顺序

1. 确认快照完整性和数据 lineage；2. 对比模型/迁移与 graph contract；3. 先验证 KG 构建与导入适配；4. 验证 API 的 project/drug/run ID 契约；5. 接入前端交互；6. 核验 GLM provider 与报告持久化；7. 运行隔离部署和 E2E。
