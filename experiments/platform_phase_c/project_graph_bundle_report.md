# 项目级 GraphBundle 实施与审计报告

日期：2026-11-13

## 目的

为项目级图谱构建补齐可复现的 GraphBundle 生成、校验和导入路径。报告记录工程实现和软件验收状态；不把合成夹具或历史数据目录冒充为本次真实项目构建结果。

## 本次实现

1. 新增 `kg/scripts/build_project_graph_bundle.py`。脚本从明确指定的 S1 差异结果、S1 基因映射审计、S2 药物条件汇总、LINCS `pert_info` 与公开 OptimusKG 3.2 文件中构建版本化图包。
2. LINCS 化合物仅按 InChIKey 精确匹配；名称相同但结构标识缺失的药物保留在映射审计表，不建立猜测的药物关系。基因仅依据唯一 Ensembl 映射连边，未匹配和歧义映射保留在审计表。
3. 每个剂量/处理时间单独保留为 `S2Condition`，不跨条件合并分数，也不取每种药物的最佳条件。输出节点、关系、候选映射、S1 映射、通路基因映射、未匹配实体、关系冲突、证据记录、候选药物到靶点/通路路径及文件哈希清单。
4. 构建 API 校验同一项目的 S1、S2 和富集运行状态及 S1 来源关联，验证输入文件哈希，并把每次 GraphBundle 保存到独立运行目录；历史包不会被覆盖。
5. 图谱构建 API 可选指定已完成的 GraphBundle 运行。默认取当前项目最近完成版本；导入前重新核验 manifest、checksum 和所有输出文件。旧的 ER+ 静态 Phase B 导入路径仍保留。
6. 图谱页面新增 GraphBundle 生成与导入入口。图谱 schema 和 API 合约同步新增项目 S2 条件关系及 GraphBundle 接口。

## 当前数据门禁审计

- 先前受限环境读取到的是 SQLite 测试快照；提升权限后确认实际运行数据库为 PostgreSQL，其中有 ER+ 主项目和一个 `test_only` 多项目软件验证项目。正式 ER+ 主项目仍只有历史 Phase B seed run，没有同一运行链的项目级 S1/S2/富集三件套，因此没有为正式项目拼接生成 GraphBundle。
- 在已有 `test_only` 验证项目中，已复制 GSE42568 全量 limma 表作为明确标记的测试工作流输入，按平台执行 S1 标准化、S1 通路富集、受限真实 LINCS S2、GraphBundle、Neo4j 导入及 FastAPI 查询。这个闭环不代表正式筛药结果，也不修改原始 S1/S2 文件。
- LINCS 压缩 `pert_info` 文件存在，大小 82,376 字节；已实际读取表头及前三条记录，字段为 `pert_id`、`canonical_smiles`、`inchi_key`、`pert_iname`、`pert_type`。构建器已支持 `.gz` 文本读取。
- OptimusKG 3.2 本地清单列出 5 个已下载 Parquet 表，并注明 CC BY-NC-SA 4.0；这不是完整 OptimusKG 图数据库。
- 上述关于“没有生成真实项目 GraphBundle”的判断是端到端验证前的旧状态，现已由下文测试项目闭环更新。当前已在 `test_only` 项目完成 GraphBundle、Neo4j 导入及 FastAPI 查询；正式 ER+ 项目仍没有同一项目内关联的 S1/S2/富集运行组合，因此正式项目图包仍未生成。

## 验收结果

| 检查项 | 结果 | 说明 |
|---|---|---|
| GraphBundle 构建器测试 | 通过 | 测试夹具验证精确 InChIKey 映射、未知药物不猜测、剂量分开保存、关系冲突留痕及重复关系断言可序列化；LINCS 元数据使用 gzip 输入 |
| KG 全套测试 | 通过 | 当前 `kg/tests` 共 7 项通过，含大 CSV 断言字段读取与重复边序列化 |
| 项目 GraphBundle 选择与哈希校验测试 | 通过 | 校验版本目录选择、manifest/AnalysisRun 一致性和输入文件被篡改后的拒绝行为 |
| 图谱版本相关后端测试 | 通过 | 直接 API/函数测试通过，使用 `GRAPH_SOURCE=csv` 隔离外部图数据库 |
| 后端隔离模式测试 | 通过 | 本轮实际复跑 34 项通过；未包含此前受本机 loopback 限制的单独 HTTP 上传测试 |
| Python 语法检查 | 通过 | `main.py`、GraphBundle 构建器和 Neo4j 导入器通过 `py_compile` |
| OpenAPI 路由检查 | 通过 | 29 个路由可生成；GraphBundle POST 和 `bundle_run_id` 参数均存在 |
| 前端生产构建 | 通过 | TypeScript 检查和 Vite 构建通过；打包器提示单 JS chunk 大于 500 KB |
| 测试项目 GraphBundle + Neo4j + FastAPI 端到端 | 通过 | 使用 21,653 个标准化 S1 基因、真实 S1 富集结果和 30 条真实 MCF7 Signature；生成 7,299 节点、37,558 条图包关系并导入 Neo4j；API 查询及跨项目 GraphBuild 过滤均已实际执行，细节见[中文端到端报告](phase_e_graphbundle_e2e_report.md) |
| 正式 ER+ 项目 GraphBundle | 尚未执行 | 正式项目没有同一分析链的项目级 S1/S2/富集运行；测试项目的成功不代表正式项目已完成 |

## 变更文件

- `kg/scripts/build_project_graph_bundle.py`
- `kg/tests/test_project_graph_bundle.py`
- `backend/app/main.py`
- `backend/app/schemas.py`（沿用现有 GraphBundle 请求模型）
- `backend/tests/test_api.py`
- `kg/scripts/import_phase_b_to_neo4j.py`
- `docs/graph_schema/graph_schema.yaml`
- `docs/api/api_contract.yaml`
- `frontend/src/api.ts`
- `frontend/src/App.tsx`

## 正式项目运行前置条件

正式 ER+ 项目仍需在同一 project ID 下登记并完成 S1 运行、以该 S1 为来源的正式 S2 LINCS 运行、以及以同一 S1 为来源的 S1 通路富集运行。页面的 GraphBundle 入口会检查 provenance；满足后每次运行单独保存参数、输入与输出 SHA-256。
