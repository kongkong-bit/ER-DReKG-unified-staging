# BioCypher 集成与正式 GraphBuild 验收

日期：2026-11-14  
正式项目：ER-positive breast cancer drug repositioning  
项目 ID：`3f18f4c1-713d-58c5-8a53-38eca5a5aaf9`

## 已完成

- KG ETL 虚拟环境使用 `BioCypher 0.17.0` 和 Neo4j Python Driver `6.4.1`。依赖声明在 `kg/pyproject.toml`，`kg/uv.lock` 已锁定 34 个包。
- 新增 `kg/config/biocypher_schema.yaml`，显式登记 8 类项目节点和 9 类输入关系，并将关系映射到规范关系名。
- GraphBundle 构建流程在验收和签发 manifest 前，通过 BioCypher translator 校验所有节点、关系类型、端点和属性。Neo4j 导入器随后读取同一输入并使用 BioCypher 返回的节点标签、关系标签、端点和属性执行持久化；不是仅做旁路检查。节点 ID、边 ID、边端点以及来源断言属性均经逐条检查。
- BioCypher 使用 headless、offline 翻译配置，不下载本体。Neo4j 持久化由 `kg/scripts/import_phase_b_to_neo4j.py` 消费 BioCypher 标准化实体，再执行 GraphBuild 感知的 `MERGE`，保留来源记录和版本成员资格。
- BioCypher 自带在线 Neo4j driver 的节点写入依赖 APOC；其关系合并身份只按端点和关系标签，不能表达本项目按 source release 区分的关系身份。本项目因此复用 BioCypher translator 输出，同时用受控 MERGE persistence 保存稳定 relation ID 与 GraphBuild membership，避免丢失证据或串并版本。
- Windows 默认 GBK 环境下，BioCypher 0.17 的默认 YAML 读取无法加载包内 UTF-8 配置。适配器在导入期间临时指定 UTF-8 文本读取，并切换到 KG 配置目录；处理后恢复原文件打开函数和工作目录。

## 正式数据验证

| 检查 | 结果 |
|---|---:|
| 输入 GraphBundle 节点 / 关系 | 7,032 / 38,998 |
| BioCypher 翻译节点 / 关系 | 7,032 / 38,998 |
| 输入关系类型映射 | 9 类全部通过 |
| 稳定节点 ID、关系 ID 与端点 | 全部保持 |
| 节点、关系来源属性 | 全部保持 |
| Neo4j GraphBuild 实际计数 | 6,850 节点 / 38,657 关系 |
| GraphBuild 状态 | `materialized`，来源 `neo4j` |

BioCypher 输入边类型映射为 `TARGETS`、`CONTAINS_GENE`、`HAS_CANDIDATE`、`REFERENCES_DRUG`、`HAS_DEG`、`HAS_ENRICHED_PATHWAY`、`HAS_ENRICHED_GENE`、`ABOUT_DISEASE` 和 `HAS_S2_CONDITION`。Neo4j 计数低于输入计数，是因为稳定 ID 和关系在数据库中按 MERGE 复用/去重；项目版本关系仍通过 `graph_build_ids` 隔离。

最终正式版本：

- GraphBundle：`ANALYSIS_RUN:KG_GRAPH_BUNDLE:54530b3e-efcd-4629-9345-d61f5c4363f7`
- GraphBuild：`GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:a08001496a447f7f`
- BioCypher 验证：`data/processed/projects/3f18f4c1-713d-58c5-8a53-38eca5a5aaf9/graph_bundle/runs/54530b3e-efcd-4629-9345-d61f5c4363f7/biocypher_validation.json`
- 校验文件 SHA-256：`31a02f844b3851eedb26dc3dfdf2fc055805599d30e94581a62449f68624cb8c`
- Neo4j 与 PostgreSQL 状态均通过 FastAPI 实际读取核验；版本计数与 GraphBuild 登记一致。
- 新版 importer 对同一 GraphBuild ID 实际重跑一次，返回 `PASS`，再次查询仍为 6,850 节点、38,657 条关系；没有新增重复版本关系。
- FastAPI 子图分页和 evidence API 实际联调通过，证据可按最新 GraphBuild ID 回溯。

## 测试与运行记录

- KG 测试：`10 passed`，覆盖 schema 翻译、类型映射、稳定 ID、来源属性保留、版本化关系身份和缺失端点拒绝。
- KG 测试直接由 `kg/.venv` 中的 pytest 运行，使用该环境内锁定的 BioCypher、Polars、PyArrow；单元测试未连接数据库。
- 正式运行曾遇到两项已修复问题：断言 CSV 超过 Python 默认 128 KB 字段上限；KG venv 缺少 Neo4j Driver。前者提高了读取上限，后者补入 `neo4j==6.4.1` 并重新锁定/同步环境。缺 Driver 的失败 GraphBuild 在连接数据库前退出，没有写入图数据；失败运行记录保留，未改标为成功。
- 中间 GraphBuild `...:70bf5e7a5a024dfa` 和 `...:25e3b3f52aa5d6fb` 保留在数据库中作为版本历史。最终版本 `...:a08001496a447f7f` 绑定 BioCypher schema、KG 配置、`pyproject.toml`、`uv.lock`、适配器代码哈希和 Neo4j Driver 版本；没有覆盖原历史版本。
- Phase F 的静态证据矩阵仍明确绑定其原始图版本 `...:a6aabb2147cb5f5e`；最新图谱查询使用 `...:a08001496a447f7f`。联调脚本分别检查这两个版本，没有把历史证据重新标记到新图谱上。
- 环境门禁：`uv sync --project kg --group test --locked` 完成；`uv lock --check` 通过。KG 实际版本为 BioCypher 0.17.0、Neo4j Driver 6.4.1、Polars 2.1.0、PyArrow 26.0.1、pytest 8.4.2。
- 回归：KG 测试 10/10 通过；后端测试 45/45 通过（`GRAPH_SOURCE=csv`、`DATABASE_URL=sqlite://`，隔离正式数据库）。Phase D Vite/FastAPI 只读联调和 evidence 回溯通过。

## 输出和局限

- 代码：`kg/scripts/biocypher_adapter.py`、`kg/scripts/build_project_graph_bundle.py`
- Schema 与配置：`kg/config/biocypher_schema.yaml`、`kg/config/biocypher_config.yaml`
- 依赖：`kg/pyproject.toml`、`kg/uv.lock`
- 单元测试：`kg/tests/test_biocypher_adapter.py`
- 数据库写入使用 BioCypher 翻译输出加版本化 Neo4j MERGE importer；没有执行 BioCypher 离线 batch import 或任何清库参数。
- 这次检查验证图类型和数据属性结构，不验证来源数据库的生物医学正确性，也不提供疗效或因果结论。
