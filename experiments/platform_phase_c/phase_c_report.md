# Phase C–D：平台后端与前端 MVP 实施报告

最近验收更新：2026-11-14

## 已实现

- FastAPI 后端以幂等方式登记现有 ER+ 项目、S1 数据、Phase B AnalysisRun 和 50 个候选。
- 提供项目、运行、S1 汇总/通路、数据集列表/上传、候选分页、Exp006–Exp011 综合证据矩阵、图谱汇总/搜索/分页子图、药物机制、证据、任务状态和图谱构建入口。
- 新增 PostgreSQL `graph_builds` 表、项目级快照登记和快照列表 API。GraphBuild ID 随关系导入写入 Neo4j 关系的 `graph_build_ids` 属性，公共实体节点仍以标准 ID 共享。
- 图谱查询使用固定查询模板，限制最多 200 个节点、最多 2 跳；支持 CSV 离线模式与 Neo4j 数据库模式。前端不直接连接 Neo4j。
- Neo4j 导入脚本使用 `MERGE` 和白名单标签/关系，保留来源断言和 evidence ID；S1 富集扩展独立版本保存，不覆盖旧 Phase B 文件。
- React + TypeScript 前端实现项目切换、Dashboard、全量 limma 火山图、上下调基因表、S1 通路、S2 证据、Cytoscape 局部图谱（支持节点/关系类型筛选和已加载子图最短路径高亮）、候选药物机制、数据集登记和上传校验。
- 上传支持 CSV/TSV/TXT，流式写入并计算 SHA-256，执行字段、数值、重复样本 ID 和分组数量检查；上传仅登记为 `validation_pending`，不会自动启动差异分析。
- 新增项目级预计算 DEG S1 运行入口：只能消费本项目登记、哈希一致且字段校验通过的 `precomputed_deg` 文件；调用者需指定 logFC 正方向组、反方向组和 FDR 阈值。处理会保留原始上传文件，生成项目目录中的标准结果与运行清单，记录输入/输出 SHA-256、参数、统计量、软件版本和 `AnalysisRun ID`，并在成功后将 Dataset 标为 `validated`。
- 新项目 S1 支持预计算 DEG、log2 标准化微阵列 limma，以及 RNA-seq 原始整数 counts 的 edgeR 过滤/TMM 标准化/limma-voom。三类运行各自记录 contrast、输入/输出哈希与软件来源；新项目查询只读取本项目 S1 AnalysisRun，不套用 ER 历史结果。RNA-seq 插件拒绝 TPM/FPKM/CPM 或小数表达值。
- 新项目 S1 支持独立 GO BP、Reactome ORA 与 Hallmark GSEA：ORAs 使用 S1 实测且成功映射的 Entrez 背景，完整映射审计、富集结果、通路基因链接和图表按独立 AnalysisRun 保存；API 不会在 S1 更新后误显示旧富集结果。真实完整 GSE42568 输入验证与结果见[项目级通路富集报告](project_s1_pathway_enrichment_report.md)。
- 新增通用项目级 S2 LINCS CLI 与运行/导入/摘要/条件查询 API：前端可选择本项目已完成 S1 并配置 FDR、Top N、细胞、扰动类型、时间和 QC；TestOnly 项目必须设置 Signature 上限，完整筛选需在界面明确确认。运行日志、参数、输入哈希和软件版本写入 AnalysisRun。S1→BING 映射审计、GCTX 按 Signature 行读取、WTCS 及剂量分层汇总均已实现；结果按条件持久化到 PostgreSQL。另增加跨剂量 Top N 名次复现摘要，按细胞/扰动/时间分层，不合并 WTCS，也不生成未经验证的 Candidate 总排名。
- 后续补齐项目级版本化 GraphBundle 生成：严格检查同项目 S1/S2/富集 provenance，按唯一 Ensembl 与精确 InChIKey 映射，保留剂量/时间分层、冲突与失败映射审计、来源和哈希清单；图谱页提供生成与导入入口。实际项目数据包仍须以同项目登记完成的运行执行，未由本地测试夹具替代。

## 验收记录

- 后端隔离 CSV 模式测试 31 项通过（含 limma 和 edgeR-voom 的 R 运行、项目级 S1 富集 AnalysisRun 编排及结果查询、RNA-seq 输入拒绝、S2 条件结果持久化/幂等导入、S2 CLI 调度导入闭环，以及新项目创建和上传的 HTTP 闭环测试）；S2 工程测试 9 项通过。Neo4j 模式机制路径/evidence 解析测试及 Neo4j 导入器 4 项有既往验收记录。
- 本机 OpenAPI 实测为 27 条路径，包含项目 S2 运行/导入/查询路由和 microarray/RNA-seq S1 路由。上传请求体以 `application/octet-stream` 流式接收。
- PostgreSQL Alembic 迁移已执行至 `1a9c43d820ef`，新增项目 S2 条件结果表；首次 Neo4j 图导入快照曾返回 7,314 个节点、37,369 条去重关系，后续 GraphBuild 版本及实体去重口径已有变化，不能把这组历史快照当作当前统计；真实 API 机制查询返回 163 条版本内路径。
- Vite `/api` 代理已实测能够访问 FastAPI，返回项目、图摘要、机制路径和证据来源。S1 接口返回火山图 21,655 个点、显著上调 3,422 和下调 3,644 个，与历史 limma 汇总一致；已通过 Edge 浏览器检查 Dashboard、S1、S2、图谱、药物机制和证据弹窗。新建 `test_only` 项目已在页面实际创建；上传请求通过 Vite 代理与 FastAPI 在隔离 SQLite 环境真实验收，浏览器原生文件选择器自动化尚未完成。
- 前端 `npm run build` 成功；S1 页面现可从匹配的表达矩阵和样本注释发起 limma 分析。主 bundle 约 2.81 MB（gzip 约 918 KB），超过 500 KB 的提示仍待按路由拆包优化。
- S1 GO、Reactome、Hallmark 结果接入 API；富集背景为 17,649 个成功映射 Entrez 基因，显著项 GO UP/DOWN 为 206/343、Reactome UP/DOWN 为 135/26、Hallmark 为 29。
- S1 富集子图扩展包含 738 个通路/基因集节点、95 个补充 Gene 节点、738 条上下文到通路关系及 29,441 条通路到基因关系；其中 29,441 条唯一映射、2,550 条歧义、0 条未匹配。歧义映射保留审计，不计为唯一映射。
- 新 S1 真实 HTTP smoke test 使用仅标记 `test_only` 的软件测试项目和两行合成表：上传初始状态为 `validation_pending`，调用运行端点后得到独立 AnalysisRun 和项目级输出；S1 summary 返回 2 个输入基因、1 个显著上调基因，火山图和基因表均返回对应结果。该数据不是科研结果。ER 历史项目仍返回原有 21,655 个检验基因；其原始输入及 S1 结果没有被重写。
- 新增上传 HTTP 自动测试：创建临时测试项目，经真实 FastAPI TestClient 上传一行 DEG CSV，响应与登记结果均为 `validation_pending`、`analysis_started=false`，哈希和文件字节核验一致；数据写入临时目录并随测试清理。该测试证明接口行为，不代表 Windows 浏览器提交流程已完成视觉验收。沙箱默认拦截 TestClient 本机 loopback socket，测试在隔离临时 SQLite 环境中经批准执行后通过。
- 新 S2 项目级 E2E 使用两个人工查询基因和真实 MCF7 Level 5 LINCS signature，完成 S1/S2 AnalysisRun、5 条 signature 评分、5 个分剂量条件行、PostgreSQL 登记和 HTTP 查询；重复导入幂等，正式 ER 项目没有显示 test_only S2 结果。另完成“合成矩阵 → limma S1 → 真实 LINCS smoke S2 → API 查询”闭环。所有这些输入只用于软件验收，不是科研候选结果；详见 [S2 报告](project_s2_pipeline_report.md#本机-api-端到端联调记录) 和 [limma S1 报告](project_s1_limma_report.md)。
- 新 limma microarray E2E 在同一隔离 test_only 项目上传 3 个 feature × 4 个样本的合成 log2 表达矩阵及分组文件，真实调用 R 4.4.3/limma 3.62.2；HTTP 查询返回 3 个检验 feature、1 上调、1 下调，contrast 为 Tumor − Normal。合成数据只用于软件测试，不是科研结果。
- 新 RNA-seq E2E 在隔离 `test_only` 项目上传 200 个 feature × 6 个样本的合成整数 counts 和分组文件，真实调用 edgeR 4.4.2/limma 3.62.2：`filterByExpr` 过滤 20 个全零 feature，180 个进入检验；contrast 为 Tumor − Normal，输出 1 上调、1 下调。AnalysisRun 为 `ANALYSIS_RUN:S1_RNASEQ:e51f024a-805f-4e21-8ddd-a7fcc6cacad6`，输出 SHA-256 为 `514ed4618d7bb460b769f92c6e4bf599f0d28f736e4c72c79665d37eadfc6ee4`。这是合成数据的软件闭环验收，不是疾病研究结果。详见 [RNA-seq 报告](project_s1_rnaseq_report.md)。
- Phase A 输入清单中的 22 个历史文件当前 SHA-256 全部匹配；原始 S1/S2/Exp006–Exp011 科研文件未被本轮修改或重算。

## 尚未完成

- 项目创建页面与 `test_only` 状态已实际验收；上传请求通过 Vite `/api` 代理完成真实 HTTP 闭环并保持 `validation_pending`，但浏览器原生文件选择器交互尚未验收。详见[新项目创建与数据登记验收报告](project_creation_upload_report.md)。
- R 4.4.3、limma 3.62.2 和 edgeR 4.4.2 已安装在项目隔离环境 `experiments/s1_pathway_enrichment/r-env`；本轮实际加载 clusterProfiler、ReactomePA、org.Hs.eg.db、fgsea 和 ggplot2 均成功。正式 ER+ 项目已登记项目级 S1、历史 S2 输出导入与 R 富集运行。首两个 GraphBuild 审计发现映射/稳定 ID 问题并保留为历史版本；最终修正版正式 GraphBuild `GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:a6aabb2147cb5f5e` 已通过 Neo4j 与 FastAPI 实际验收。详情见[正式 GraphBuild 验收报告](formal_graphbuild_verification.md)。
- 项目级 S2 已可从页面选择已完成 S1 并启动筛选，条件级评分和跨剂量稳定性摘要均可查询与展示；尚未定义通用 Candidate 的药物总排名规则，因此不会把稳定性摘要当作总排名。未执行全量 S2，不应将 test_only smoke 记录解释为候选排名。稳定性实现及测试见[项目级 S2 稳定性报告](project_s2_stability_report.md)。
- Phase E 的 GraphBundle 级与 Neo4j 数据库级多项目软件验收均已通过：两个 test_only 项目共享稳定 Drug/Gene/GeneSet ID，Neo4j 中各只有一份；各自 Candidate、DiseaseContext、S1/S2 运行及关系由 GraphBuild 隔离，FastAPI 子图、搜索和机制查询均经实际服务验证，跨项目 GraphBuild 请求返回 404。第二项目项目关系是明确标记的测试夹具，不代表疾病实验结果；详见[双项目数据库验收](phase_e_neo4j_multi_project_report.md)及[Phase E 总报告](../platform_phase_e_report.md)。
- 正式 ER+ 项目最终修正版 GraphBuild 的实时版本过滤统计为 Neo4j 6,850 个节点、38,657 条边，其中当前版本 DiseaseContext 为 1 个；之前报告的 6,853 节点包含 3 个旧版本上下文，是 `[*0..2]` 零跳路径过滤缺陷导致的过计数。31,991 条通路—基因链接中 30,350 条唯一映射，50 个候选保留 240 个剂量条件并得到 1,494 条证据交汇路径。FastAPI 机制、S1 通路和证据接口均已核验；数据库中的 GraphBuild 历史 summary 保持原样并在实时验收报告中明确标注。先前两个映射不完整/ID 不规范版本保留为审计历史，不作为正式当前版本。详见[GraphBuild 实际验收报告](formal_graphbuild_verification.md)。
- 平台目前为开发版，生产认证、授权和部署加固未完成。

## 解释边界

候选路径表示可追溯的来源关系和证据共现，不证明因果关系、ER 阳性乳腺癌特异机制或药物疗效。数据库去重关系数不能和 CSV 证据行数直接等同。

## 2026-11-14 回归验收更新

- 后端隔离 CSV/SQLite 模式全套测试：最近一次 43 项通过。配置与本机 `.env` 中的 Neo4j 连接隔离，HTTP 上传测试在获准的本机 TestClient 环境执行。
- GraphBundle 构建器及 Neo4j 导入器测试：7 项通过；Neo4j 双项目实际服务验收与复跑均为 PASS。
- 此处记录的是 2026-11-14 较早一次构建；本轮版本按需加载 ECharts/Cytoscape 后重新构建成功，分块大小见 Phase D 报告。仍有大包体积提示。
- Phase A 输入审计清单 22 个历史 S1/S2/Exp006–Exp011 文件再次校验，SHA-256 为 22/22 一致。
- Docker Engine 29.6.1，PostgreSQL 与 Neo4j 容器均报告 `healthy`；Neo4j 全实例为 8,468 个节点、74,937 条关系。该全局数包含多个项目与 GraphBuild。
- 双项目数据库验收详见[Phase E 双项目报告](phase_e_neo4j_multi_project_report.md)；测试验证软件隔离，不构成第二疾病的科研证据。

## 2026-11-14 后续修正

- 图谱查询的 GraphBuild 版本隔离修复已通过后端定向测试和真实 Neo4j/FastAPI 只读核验；修正后的实时数字与历史 GraphBuild `summary_json` 的旧值分别保留，见[正式版本复核报告](formal_graphbuild_verification.md)。
- Phase D 药物详情增加 S2 条件、剂量稳定性、独立 S1、PRISM 和机制证据分项；ECharts 与 Cytoscape 改为动态加载。具体验收与仍未完成事项见[前端规划](../../docs/architecture/frontend_plan.md)。
- Phase F 新建独立整合结果，将 819 个 Exp006–Exp011 候选按 LINCS ID 与正式 GraphBuild 的 1,494 条来源支持路径联结；不生成加权疗效排名。见[Phase F 报告](../phase_f_integrated_evidence/phase_f_report.md)。

## 2026-11-14 补充验收

- 已在独立 Edge 访客窗口中操作 Windows 原生文件选择器，并将 64 字节合成表达矩阵上传至 `test_only` 项目。API 返回 `validation_pending`，要求样本分组注释，AnalysisRun 数量保持不变。此前“原生文件选择器尚未验收”只适用于本报告前面的历史执行记录；最新实测见[浏览器上传 E2E 报告](browser_upload_e2e_report.md)。
- 用户确认后重新执行隔离 Phase E GraphBundle E2E，S1、富集、30 条真实 LINCS Signature 的软件 Smoke Test、GraphBundle、Neo4j GraphBuild 和 FastAPI 查询均完成。该脚本仅写入 `test_only` 项目；正式 ER+ GraphBuild 的独立只读复核 PASS。详见[GraphBundle E2E 报告](phase_e_graphbundle_e2e_report.md)。
- 按实施方案补齐 DuckDB：GraphBundle 节点输入使用列投影扫描 OptimusKG Parquet，ETL 依赖锁定 DuckDB 1.5.6；运行清单记录 Python/DuckDB/Polars/PyArrow/BioCypher 版本及 `kg/pyproject.toml`、`kg/uv.lock` 哈希。知识图谱 ETL 回归 11/11 通过，正式 ER+ GraphBundle 临时重建的 9 个 CSV 输出与历史版本逐字节一致、计数一致；未覆盖正式 GraphBundle 或 Neo4j。详情见 `duckdb_graphbundle_equivalence.json`。

- 增加同项目同类型 AnalysisRun 比较 API 与前端 `/compare` 页面：并列展示参数、软件版本、输入 SHA-256 和结果摘要；S2 仅按完全相同的剂量/时间条件键及 perturbagen 比较 WTCS 与条件内排名，不合并不同条件。正式项目实际 API smoke test 使用两个 GraphBundle 运行返回 HTTP 200；定向单元测试覆盖 S2 条件严格匹配。
- 修复后端 `.env` 路径依赖进程当前目录的问题：配置现以 `backend/app/core/config.py` 所在工程根目录解析 `.env`，避免从工程根目录调用审计脚本时误用默认 SQLite。

## 2026-11-14 AnalysisRun 比较增量验收

- 后端新增 `GET /api/v1/projects/{project_id}/runs/compare`。仅接受同一项目中两个不同、已完成、同一类型的 AnalysisRun；项目归属不符返回 404，类型不同或重复选择返回 422。响应并列列出软件版本、运行参数、输入 SHA-256 和类型相关结果摘要。
- S2 比较以 `(condition_key, pert_id)` 精确匹配，只统计共有/独有条件药物行、WTCS 差值和条件内排名差值；不合并剂量或时间，也不形成药效总排名。GraphBuild 历史计数明确标记为创建时快照。
- 正式 ER+ 项目实际比较两次 GraphBundle 运行返回 HTTP 200；状态 API 对真实 AnalysisRun 返回 completed/100。前端 `/compare` 已加入导航与页面；完整后端隔离测试最近为 43 项通过，KG 构建测试 7 项通过，前端生产构建成功。桌面文件选择器视觉操作仍未验收。
- 图谱页补齐关系范围切换（全部、直接药物—Gene/ProteinTarget、其他上下文关系）及 Cytoscape 关系点击 evidence 弹窗；真实 GraphBuild 子图中 evidence ID 的 API 回溯返回 HTTP 200。当前本机 Vite/FastAPI 联调报告见[Phase D 验收](../platform_phase_d/phase_d_report.md)。
- 新增同步运行状态 API `GET /api/v1/jobs/{job_id}`，job_id 明确等于 AnalysisRun ID；首页列出最近十条实际运行记录并可查看状态。没有 Celery/Redis 队列时不伪造进度百分比。
- S1 页面新增 Exp010/GSE139038 外部配对队列复核摘要和剂量/时间分层的外部 LINCS 名次；FastAPI 仅在 ER+ 项目开放，读取前校验 manifest 中的摘要、队列清单和排名 CSV SHA-256。14 对 ER+ 患者外部结果和 3,715 个药物条件已通过 Vite/FastAPI 真实 HTTP 验收；不解释成临床疗效。
- ECharts 按需核心包只加载柱状图、折线图、散点图与实际组件；图表动态分块 573.89 KB，较原整包约 1,145.86 KB 减半。当前生产构建入口 1,233.95 KB，仍有大分块告警；未声称已完成路由级拆分。





