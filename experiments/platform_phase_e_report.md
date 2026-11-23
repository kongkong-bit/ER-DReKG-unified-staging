# Phase E：多项目隔离与数据库集成验收报告

日期：2026-11-13；最近验收更新：2026-11-14

## 验收范围

本报告记录 DiseaseGraph Lab 当前多项目隔离、数据库服务、Neo4j 图谱导入和前后端接口联调状态。测试项目数据仅用于软件隔离验证，不代表科研发现。

## 已通过

- **历史数据只读完整性**：将 Phase A 系统输入清单中的 22 个历史科研文件与当前文件逐一比较 SHA-256，22/22 一致，无缺失或不匹配。原始 S1、S2 和 Exp006–Exp011 文件未被本轮代码修改。
- **项目隔离（自动化测试）**：在同一测试数据库中创建历史 ER 阳性乳腺癌项目与两个不同疾病 ID 的测试项目。新项目不会显示历史项目的 S1、候选药物、图谱节点/边或机制路径；历史项目仍能读取已有结果。
- **数据库服务**：PostgreSQL 实际 Alembic 迁移已执行到 `4d2c7ea19a6b`（head）。2026-11-14 通过 Docker Engine 29.6.1 实际核验 PostgreSQL 与 Neo4j 容器均为 `healthy`；FastAPI 的 ER+ 项目 GraphBuild 返回 7,314 个节点、37,369 条关系。此前受限执行上下文的 Docker 访问失败已由提权状态检查解决。
- **Neo4j 导入**：Phase B 与 S1 富集扩展数据已导入。验证脚本连续执行两次导入并检查节点、关系及来源属性，幂等性验收通过。ER+ 项目 GraphBuild 为 7,314 个节点、37,369 条关系；2026-11-14 全实例直接计数为 8,468 个节点、74,937 条关系，包含多个项目和版本。历史路径校验得到 1,422 条候选路径，覆盖 22 个候选、22 个药物和 41 个靶点基因。关系数为 Neo4j 中合并后的关系数，不等于 CSV 证据行数。
- **Neo4j 机制与证据 API**：机制接口从数据库返回 163 条路径，其中 131 条关联本项目 S1 富集结果。抽查路径包含候选映射、药物靶点和 S1 分析的 4 个 evidence ID，均能通过证据接口返回来源和断言。
- **前端代理联调**：通过 Vite 的真实 `/api` 代理请求到 FastAPI，成功读取项目、Neo4j 图摘要、机制路径及全部 4 个来源记录。API 报告的图来源为 `neo4j`，不是模拟数据。
- **代码测试**：后端测试 14 项通过，覆盖项目隔离、S1 富集读取、Exp006–Exp011 证据矩阵、上传检查、Neo4j 机制查询和来源断言解析；Neo4j 导入器测试 4 项通过。前端生产构建通过。
- **图谱版本隔离**：新增 `graph_builds` 持久表和 Alembic 迁移 `4d2c7ea19a6b`。项目级 POST 接口按输入文件 SHA-256 生成稳定 GraphBuild ID，并调用版本化 Neo4j 导入器，将 ID 幂等写入源关系的 `graph_build_ids`。API 的图摘要、节点搜索、局部子图、药物机制和来源证据都支持指定 GraphBuild ID；GraphBuild 必须属于当前项目。已在真实 PostgreSQL 中登记 1 个版本，重复 POST 后仍只有 1 条记录；同一版本导入再次执行后，Neo4j 中该版本仍为 37,369 条关系且无重复版本 ID。API 按该 ID 返回 7,314 节点、30 节点/57 边的首屏子图、1 个 BRD-K44227013 搜索结果、163 条机制路径，来源证据能回溯到 OptimusKG 3.2。前端显示版本 ID、状态、6 项输入哈希和统计。后端隔离 CSV 模式 18 项测试通过，SQLite 内存数据库完成 Alembic 全链升级验证。

## 多项目与多版本真实验收（2026-11-13）

- 建立了一个显式标记为 `test_only` 的软件测试项目（项目 ID `89aa18d8-e1ca-4eb4-8046-634cd2911207`），没有疾病数据，也没有科研候选药物结论。测试夹具只借用公共知识图谱中已有的公开药物、基因、通路实体；项目候选、疾病上下文及其关系均标记为软件测试数据。
- 新项目两个 GraphBuild 均已真实写入 PostgreSQL 与 Neo4j：`GRAPH_BUILD:89aa18d8-e1ca-4eb4-8046-634cd2911207:1c6bdea6f9805fe8`（5 节点、5 关系）和 `GRAPH_BUILD:89aa18d8-e1ca-4eb4-8046-634cd2911207:191d70ff30906d0c`（5 节点、7 关系）。第二次输入发生变化后生成新版本；旧版本仍可按 ID 查询，旧版仍返回 5 条关系。
- 第二个版本的 API 查询返回 1 个测试候选搜索结果、2 条仅用于软件验证的关联路径；图摘要为 5 个节点、7 条关系，包含 1 个 Candidate、1 个 DiseaseContext、1 个公共 Drug、1 个 Gene、1 个 Pathway。
- 同一 `test_only` 项目通过真实 HTTP API 完成了两行合成预计算 DEG 的上传、S1 运行和读取闭环：上传记录先处于 `validation_pending`，完成后生成项目级 AnalysisRun，摘要为 2 个基因、1 个显著上调；上调基因接口和火山图返回同一项目的两行测试数据。运行清单保留输入与输出 SHA-256，未将测试结果写入 ER 项目。
- 共享实体复用已通过 Neo4j 实查：`CHEMBL1113`、`ENSG00000145864`、`REACT:R-HSA-1236394` 各只有一个节点；对应药物—基因关系也是单条，且同时属于历史 ER GraphBuild 与上述两个测试 GraphBuild。没有为测试项目复制公共实体节点。
- 历史 ER 项目（项目 ID `3f18f4c1-713d-58c5-8a53-38eca5a5aaf9`）查询仍返回其原 GraphBuild 的 7,314 节点和 37,369 关系。针对测试扰动 ID `SOFTWARE-TEST-PERT`，ER 项目的搜索结果和机制路径均为 0；测试项目的候选与关系未泄漏进历史 ER 项目。
- 验收时后端测试为 18/18 通过；Python 文件编译检查通过；前端 TypeScript/Vite 生产构建通过。构建仍有单个约 2.78 MB 的 JS 包体积提示，不影响本次验收。

## 尚未完成或尚未验证

- 浏览器核心页面烟雾验收已覆盖 Dashboard、S1、S2、Cytoscape 图谱和证据弹窗；本轮又在页面创建了 `test_only` 项目。上传数据已通过真实 Vite 代理和 FastAPI 请求登记为 `validation_pending`，但浏览器原生文件选择器自动化未完成，详见[新项目创建与数据登记验收报告](platform_phase_c/project_creation_upload_report.md)。
- 新项目已有预计算 DEG、limma microarray、edgeR-voom、通路富集、LINCS S2 条件结果持久化、GraphBundle 和 GraphBuild 功能。完整实际管线已在 test_only 项目验证；仍需由另一真实疾病数据集完成独立生物医学验证。
- 稳定公共实体 ID、Neo4j `MERGE`、关系多版本归属以及版本过滤已有 ER 历史项目加软件测试项目的端到端验证。软件测试项目只证明软件隔离和实体复用行为，不能作为第二个真实疾病项目的生物医学证据，也不能替代真实跨疾病项目验收。
- **双项目同时导入 Neo4j（2026-11-14）**：已在第一真实数据 `test_only` 项目仍保留于 Neo4j 时，新建第二独立 `test_only` 项目并导入软件测试夹具。两项目共同使用的 `CHEMBL2103991`、`ENSG00000132170` 与 `MSIGDB:HALLMARK_ADIPOGENESIS` 各只有一个节点；FastAPI 图摘要、搜索、子图、机制和双向跨 GraphBuild 查询边界均通过。第二项目 S1/S2/候选与项目关系都是显式软件夹具，不是科研数据。详细结果见[双项目 Neo4j 数据库验收报告](platform_phase_c/phase_e_neo4j_multi_project_report.md)。
- **正式 ER+ GraphBuild 映射修复与实际验收（2026-11-14）**：保留两个审计发现的问题版本后，正式修正版 `GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:a6aabb2147cb5f5e` 已登记到 PostgreSQL/Neo4j。GraphBundle 使用 GO/Reactome/MSigDB 稳定 ID；31,991 条通路—基因链接中 30,350 条唯一映射到 Ensembl，产生 1,494 条有来源的候选靶点—通路交汇路径。Neo4j 实际查询为 6,853 节点、38,657 条关系；FastAPI 机制、S1 通路、S2 条件和证据接口均通过。实际验收见[GraphBuild 报告](platform_phase_c/formal_graphbuild_verification.md)，运行登记见[项目历史运行报告](platform_phase_c/formal_erpos_project_linkage_report.md)。
- **BioCypher 标准化导入与正式版本验收（2026-11-14）**：BioCypher 0.17.0 translator 标准化了 7,032 个节点、38,998 条输入关系，版本化 Neo4j importer 消费其转换结果；新版 GraphBuild `GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:a08001496a447f7f` 已登记到 PostgreSQL/Neo4j，版本查询返回 6,850 节点、38,657 关系。同一 GraphBuild 实际重跑 importer 后计数不变，API evidence 回溯通过。详细记录见[BioCypher 集成验收报告](platform_phase_e_biocypher/biocypher_integration_report.md)。
- **GraphBuild 版本化 EvidenceRecord 持久化（2026-11-14）**：新增 PostgreSQL 表和只增迁移，为 7 个已物化 GraphBundle 版本保存 240,910 条唯一版本内证据记录；逐版本重新校验 Bundle/输出哈希后幂等回填。最新图版本与 Phase F 历史图版本都通过 API 按各自 GraphBuild ID 回查。详细记录见[EvidenceRecord 验收报告](platform_phase_e_evidence/evidence_record_persistence_report.md)。
- 仍需独立真实疾病队列完成跨疾病生物医学验证；跨条件药物总排名尚需预先定义并通过可靠性研究验证。
- 平台仍是开发版，身份认证、访问控制和生产部署加固尚未完成。

## 结论

历史输入哈希、项目 API 隔离、PostgreSQL Alembic 迁移、Neo4j 导入与来源溯源、Vite 至 FastAPI 代理已有验收记录。多项目软件隔离与正式 ER+ GraphBuild 的稳定 ID 映射均已通过；整体仍为**部分通过**，因为第二个真实疾病项目的生物医学验证、跨条件药物总排名验证和生产部署加固尚未全部完成。测试夹具中的图谱路径只验证软件行为，不代表疾病证据；所有科研图谱路径仍只表示可追溯关联，不证明因果关系、ER 阳性特异机制或治疗效果。

## 历史 ER+ 数据集的 Study 归属补全（2026-11-14）

- 按 NCBI GEO 的 GSE42568 系列记录，在正式 ER+ 项目中登记 Study `GSE42568`（标题 `Breast Cancer Gene Expression Analysis`、GPL570），并记录系列设计、GEO 链接及本项目使用的 67 例 ER+ 肿瘤、17 例正常样本与 `Tumor - Normal` 对比。
- 将原有两条 limma 数据集记录关联到该 Study；S1 原文件和 SHA-256 未修改。数据集列表 API 返回 Study accession/title，Dashboard 增加研究列。
- 新增同项目 Study 关联 API，拒绝跨项目数据集或 Study 关联。后端回归 45 项通过，前端生产构建通过；增强后的 Vite/FastAPI 验收报告确认 1 个 Study 和 2/2 个已关联数据集，见[Phase D 验收报告](platform_phase_d/phase_d_report.md)。

## DiseaseContext 按 GraphBuild 版本持久化（2026-11-14）

- 增加 PostgreSQL `disease_contexts`，从 SHA-256 验证通过的 `subgraph_nodes.csv` 保存 DiseaseContext 的项目/疾病标识、上下文 JSON 和关联分析运行；唯一键按 GraphBuild 与 context ID 隔离。
- Alembic 迁移 `e4f62ab7093c` 已应用。历史 7 个 GraphBundle 版本各回填 1 条（7 PASS、0 BLOCKED），legacy GraphBuild 1 个 SKIP；正式版输入哈希及计数经 Vite/FastAPI 验收。
- 首次回归发现单元测试继承开发 `.env` 的 `GRAPH_SOURCE=neo4j`，会误写本机 Neo4j。已新增测试隔离配置，固定普通单测使用 CSV fixture；显式 Neo4j mock 测试照常覆盖图查询分支。全量后端回归修复后 **47 passed**，详见[补充验收报告](platform_phase_e_evidence/disease_context_persistence_report.md)。

## AnalysisRun 来源链审计（2026-11-14）

- 对正式项目 PostgreSQL 做只读审计：13 个 S1/S2/富集/GraphBundle 运行均有参数、软件版本和输入哈希；Dataset 及上游运行引用全部同项目且可解析，9 个 GraphBuild 均指向有效 AnalysisRun。
- 来源链门禁 PASS。运行状态另行区分：12 个 completed、1 个历史 GraphBundle failed（保留失败记录，不当成功结果）；另有 1 个早期 Phase B legacy seed 运行不属于分析管线，缺输入哈希并已豁免。
- 明细见[来源链审计报告](platform_phase_e_provenance/run_provenance_audit.md)及机器可读[JSON](platform_phase_e_provenance/3f18f4c1-713d-58c5-8a53-38eca5a5aaf9_run_provenance.json)。

## 本机数据库网络暴露收敛（2026-11-14）

- PostgreSQL/Neo4j Docker 端口由全接口绑定改为仅 `127.0.0.1`，数据卷保留；本机 `.env` 和 `.env.example` 连接地址同步固定为 IPv4 回环，解决 Windows `localhost → ::1` 与 IPv4-only 端口绑定不匹配问题。
- 容器健康、FastAPI health、Alembic head、Vite/FastAPI/数据库集成验证均通过；完整后端回归 47 项通过。细节见[回环连接修复报告](platform_phase_e_provenance/local_service_loopback_report.md)。

## 浏览器数据上传闭环（2026-11-14）

- 独立无头 Edge 通过实际 Vite 页面完成 test_only 项目选择、DEG 类型选择、文件输入、提交和成功提示；PostgreSQL 新建 Dataset 为 `validation_pending`，存储 SHA-256 与 API 一致，上传前后 AnalysisRun 均为 4。
- UI/API 上传链 PASS；该验证未打开 Windows 原生文件选择对话框，准确边界和复跑方式见[浏览器上传 E2E 报告](platform_phase_c/browser_upload_e2e_report.md)。

## 补充实际写入与 Windows 原生上传验收（2026-11-14）

- 用户确认后，重跑 `scripts/run_phase_e_graphbundle_e2e.py`。该脚本将本轮 S1、富集、30 条 Signature 的 S2、GraphBundle 与图版本写入 `test_only` 项目 `89aa18d8-e1ca-4eb4-8046-634cd2911207`；各阶段状态均为 completed/materialized，FastAPI 查询通过，报告见 `platform_phase_c/phase_e_graphbundle_e2e_report.md`。没有写入正式 ER+ 项目，也未改动原始输入。
- 在独立 Edge 访客窗口中实际使用 Windows 原生“打开”对话框，把 64 字节的合成表达矩阵上传到 `test_only` 项目 `c493efde-981a-511c-9409-0fac7021b096`。API 校验为 `validation_pending`、1 行 × 3 列、2 个样本，要求补充样本分组信息；AnalysisRun 数量保持 4，未自动启动分析。
- 上传文件存储 SHA-256 与 API 一致。原生选择器、上传 UI、登记 API 和项目边界验收 PASS；明细见[浏览器上传 E2E 报告](platform_phase_c/browser_upload_e2e_report.md)及机器可读记录 `platform_phase_c/browser_upload_smoke_20261114.json`。





