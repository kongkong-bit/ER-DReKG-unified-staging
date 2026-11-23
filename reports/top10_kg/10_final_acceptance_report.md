# 阶段验收报告（隔离 staging 验收完成）

## 已完成并核验

- 正式 Top 10 名单哈希冻结，10/10 原样保留。
- 基于交付正式 A+ S2 表筛选 Top 10 所有条件：51 行、10 个唯一 perturbagen，无剂量合并。
- 现有 GraphBundle 构建脚本在隔离输出目录完成离线构建，manifest=`validated`，BioCypher 离线结构校验 PASS。
- Bundle 输出哈希 11/11 匹配；节点 6,639、关系 38,388；冲突记录 0。
- 精确 InChIKey 映射 8/10；靶点语义覆盖 8/10；靶点—S1 通路交汇覆盖 6/10。
- 十份新 bundle 对应的逐药档案及证据/覆盖文件已生成。
- 新 bundle 靶点与既有 LINCS target-gene COMPZ 导出的探索性交叉得到 23 条可连接记录，覆盖 5 个药物，见 `07_target_s1_s2_expression.csv`；该 COMPZ 导出为历史结果，不等同于本轮从原始 GCTX 重算。
- 两个未映射本地 KG 节点的药物身份已用同一 InChIKey 在 PubChem/ChEMBL/SGC 来源交叉核实；外部机制主张分开登记，未伪装为已写入图谱。
- Top 10 的 `sig_id` 已从正式签名表按完整条件键精确解析，10/10 唯一匹配且 WTCS 数值一致（容差 1e-12）。
- External overlay 13/13 文件哈希匹配；节点 6,643、关系 38,394、证据 48,733、候选身份解析 10/10、来源支持靶点语义覆盖 10/10、靶点—S1 通路交汇 8/10（528 路径行）。
- 独立 external evidence overlay 添加 PHA-767491、PFI-1 的标准化身份与 4 条来源支持靶点断言，overlay BioCypher 校验 PASS：10/10 身份解析、10/10 靶点语义覆盖、6,643 节点/38,394 关系。
- 原始 LINCS GCTX 对 41 条靶点语义关系提取 41 个冻结主条件签名响应记录；38 个靶点有可用表达值，8 个与 S1 DEG 方向相反，6 个同向。仅为单签名、靶点转录本描述。逐药材料见 `08_target_s2_response.csv` 和 manifest。
- 回归测试：从 `kg/` 项目环境运行完整 `tests/`，29 项全部通过（包含 bundle、BioCypher、Neo4j importer、snapshot、verifier 和 Top 10 schema/importer allowlist 单元测试；不构成真实 Neo4j E2E）。
- 新增 Top 10 专项只读 API：`GET /api/v1/projects/{project_id}/top10/mechanisms` 与 `GET /api/v1/projects/{project_id}/top10/mechanisms/{pert_id}`。仅对冻结榜单所属项目提供数据；接口校验 bundle、正式榜单和 S2 响应哈希，并明确返回未注册/未入 Neo4j 状态。
- 新增前端“Top 10 机制图谱”页：保留正式排名，支持候选切换、身份/证据/来源筛选、通路过滤、S1/S2 靶点响应查看和单药 JSON 导出。直接靶点语义与 ENZYME/TRANSPORTER/CARRIER 等一般药物—基因关联分开呈现。
- Top 10 单药页已增加 Cytoscape 关系图：节点按候选、基因/靶点、ChEMBL target entity、Protein、Pathway 分类；支持节点类型、真实关系类型及证据类别筛选，缩放、适配和重置布局；点击节点显示实体属性，点击关系显示方向、来源链接/记录号、文献、实验条件以及等级/矛盾审查的明确缺失状态。单药图限 120 条关系并提示截断，S1/S2 全基因证据仍由独立表格筛选展示，避免全量基因挤入主图。
- 按方案 8.4 增加 A/B/C/U 人工机制证据等级：A 3、B 6、C 1、U 0；逐药理由与靶点/疾病来源写入 `mechanism_evidence_grade.csv`，hash manifest 绑定冻结名单、target dossier、ChEMBL 和疾病证据。API 返回并校验等级；前端逐候选展示 rationale、PMID/DOI、靶点记录及限制。等级不是疗效概率，也不是自动生成。
- Top 10 API 与图谱 API 回归用例通过；在排除受 Windows sandbox socketpair 阻塞的既有 TestClient HTTP 上传用例后，backend 全套可运行测试 66 项通过。完整 backend 测试尚不能报告全绿。
- `frontend/` 执行 `npm run build` 成功（TypeScript 检查及 Vite 构建通过）。Vite 对既有大型 chunk 给出体积提示，不影响构建成功。
- 最新项目级 GraphBundle `7e70628f-7c76-4a2e-9dd5-56004e9c8c21` 已在独立 Docker Compose staging（PostgreSQL 15432、Neo4j Bolt 17687）完成真实登记和 Neo4j 导入；GraphBuild ID 为 `GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:5bb1e749e1caa6e2`。
- staging Neo4j 精确验收 PASS：6,866 节点、38,890 关系，CSV 期望计数与数据库一致；逐节点/关系 ID、类型和属性比较差异 0；缺来源断言/证据 ID 0、未版本化成员 0、孤立节点 0。相同输入连续执行 importer 两次均 PASS，幂等前后状态一致。机器可读报告：`neo4j_import_validation_7e70628f-7c76-4a2e-9dd5-56004e9c8c21.json`。
- 已对 staging GraphBuild 完成回滚演练：预览确认 38,890 条关系、38,890 条 EvidenceRecord 和 1 条 DiseaseContext；执行后删除这些版本数据及 GraphBuild，保留 AnalysisRun 和共享 Neo4j 节点。回查确认 GraphBuild 不存在、关系/证据/疾病上下文均为 0，AnalysisRun 仍存在，Neo4j 共享领域节点仍有 6,785 个。
- 本次数据库验收只写入独立 staging volume；生产/默认开发数据库未作为导入目标。staging 数据卷保留供审计。

## 未完成事项与适用范围

- staging 注册/导入/回滚门禁已完成；本次没有把此 Top 10 GraphBuild 注册到生产或默认开发 PostgreSQL/Neo4j。既有正式 A+ build 的历史导入 PASS 仍只由交付转录证明，本轮未对其生产数据做实时复核。
- 浏览器 UI 的实时端到端交互尚未在浏览器中验收；API 的 GraphBuild 写入路径已用于实际 staging 导入。离线 Top 10 详情 API 与真实 Neo4j build 的所有展示联动仍需按产品发布目标验收。
- PubMed/临床/反证系统获取与药物—ER+ 疾病关系证据分级尚未完整完成；现有公共 KG provenance 不等于文献级验证。
- 原始 GCTX 已按冻结 `sig_id` 进行靶点响应提取；41 条来源支持靶点关系中 38 条有数值。未测得值和无显著 S1 方向均保留为空/未判定，不作推断。
- 专项图页和 API 已实现，但仍使用只读、经哈希校验的离线 artifact；须待数据库服务可用后完成正式 GraphBuild 注册、增量导入及浏览器端 E2E。
- 全量 backend 测试中 `test_http_project_creation_and_upload_remains_pending` 在当前 Windows 环境进入 Starlette TestClient 前，卡在 asyncio Windows Proactor 创建 socketpair（faulthandler 指向 `socket.accept`）；不是应用路由断言失败。该用例需在支持该 sandbox socketpair 的环境复跑。

验收状态：`STAGING_PASS / GraphBundle registered, imported, exact-inventory verified, idempotency verified, and rolled back in isolated staging; production/default databases untouched; browser E2E and historical production build not revalidated`。
- ER+ 疾病背景定向文献筛查当前为 11 条人工记录、覆盖 10/10 冻结候选；另存 1,314 条候选—PMID PubMed 检索快照（未人工筛选，不作为图边）。mocetinostat 的 PMID 42464636 和 DOI 已回填疾病表与单药档案，API 按 SHA 校验并提供；多篇人工记录按最新表内记录汇总，详情保留全部记录。疾病证据不转为药物—疾病图边。
- 身份标准化表及可重建脚本交付在 `data/top10_kg/identity/`，明确区分 8/10 OptimusKG 精确映射和 2/10 外部 InChIKey overlay；专项范围身份核查 10/10，无未解决候选。
- 从现存 Exp006–Exp011 结果生成 `top10_reproducibility_evidence.csv`，10/10 冻结候选有记录；Exp009、Exp010、Exp011 的原始输出各覆盖 5/10。API 与页面逐实验展示可用指标，缺行按未覆盖/未匹配解释，不视作负结果。
- 全基因 S1/S2 交叉从原始 LINCS GCTX 针对冻结 10 个 `sig_id` 完成，输出 123,280 条 gene-signature 行、每药 12,328 个可测基因，每药 4,667 个显著 S1 基因交集。方向统计和 hash manifest 已接入 API/页面，严格作为单签名描述性证据展示。
- 可重复的本地构建、测试和隔离数据库门禁步骤见 `11_rebuild_and_import_runbook.md`；新增 `docker-compose.top10kg-staging.yml` 使用独立 volume 与端口，本次 staging 已启动并完成 GraphBuild 导入、幂等验证及回滚验收。
- 按精确候选身份抓取 ChEMBL 与 DGIdb 源证据：10 条 ChEMBL mechanism、4,852 条 activity、278 条 DGIdb interaction 及 19 条 mechanism-target component 注释。原始 JSON、请求状态、规范化 CSV 和 hash manifest 已保存；3 个 ChEMBL activity 查询触及 1,000 条上限，DGIdb 精确药名仅覆盖 8/10，178 条未解析药物变体互动没有归并。记录未自动升级为图边，逐候选汇总见 `data/top10_kg/evidence/top10_source_evidence_summary.csv`。
- ChEMBL mechanism、靶点组件注释、精确名称 DGIdb 互动和活性覆盖计数现通过校验源 manifest 的单药 API 提供，并在 Top 10 页面独立显示；界面明确说明 assay 活性和聚合互动不是已复核直接靶点，未解析变体不并入候选。专项 API 测试通过，前端生产构建通过。
- 通过 Reactome Content Service release 98 按 14 个精确 UniProt accession 获取 316 条人类 target-component–pathway 映射（101 个通路），并保存 217 条 pathway parent-child 层级关系、原始响应和请求状态；0 个 API 错误。该路径只表达蛋白组件参与/映射。单药 API 按源哈希加载，页面与 S1 交汇路径分开展示，并保留 ChEMBL protein-family 语义。
- 新增项目级 Top 10 ChEMBL/Reactome GraphBundle，父包为 `3928c54d_external_v1`，运行 ID `66108369-35fe-44a4-bd44-5c8d97be5a11`。离线校验通过：6,855 节点、38,868 关系、38,868 EvidenceRecords；含 9 条 ChEMBL Drug–Target、14 条 Protein–Gene、205 条 Protein–Reactome pathway、217 条 pathway hierarchy 关系，14 个靶点组件均解析到唯一标准基因，未解析组件 0。Protein family 保留为 ChEMBLTarget 实体，不被展开成未经支持的每蛋白直接靶点。
- GraphBundle 的注册模板已生成；另以隔离 SQLite 调用实际 GraphBuild API 处理该 bundle，并验证 38,868 条证据落库。此项只验证应用层解析与注册路径，不代表主 PostgreSQL 注册或 Neo4j 导入。
- 新增 `backend/tools/register_analysis_run.py`：默认 dry-run、逐项校验项目路径和 bundle/AnalysisRun/checksum SHA，显式 `--apply` 才登记，远程 PostgreSQL 需要额外确认。新增 `backend/tools/rollback_graph_build.py`：默认 dry-run、按 GraphBuild ID 删除版本关系和 PostgreSQL 证据记录，保留共享 Neo4j 节点及 AnalysisRun；隔离 SQLite/伪 Neo4j 单测通过。本次已在真实隔离 staging PostgreSQL/Neo4j 执行登记、导入和回滚。
- 新增 BioCypher schema/importer 白名单专项测试通过；须在全量 KG 回归中复核。
- 最新回归：疾病证据 CSV 和历史稳健性 CSV 均按 manifest 哈希核验；KG 29 项通过，backend 66 项通过、1 项 Windows socketpair 用例排除；注册/回滚工具隔离测试 6 项通过；前端 TypeScript 检查及生产构建通过，staging Compose 配置通过，项目 GraphBundle 15 项文件 SHA 全部匹配，`git diff --check` 通过。
- 交付包内 2026-11-20 的历史只读验收转录记录正式 A+ GraphBuild `d570eb8deb3e5eea` 当时已登记且 Neo4j 导入 PASS。当前会话未能启动 Docker daemon，因此未对实时 PostgreSQL/Neo4j 复核；历史转录不替代实时检查。

## PubMed 元数据解析修复（2026-11-21）

- PubMed EFetch 解析器此前只读取 `PubmedArticle`，导致 3 条 Bookshelf 记录没有题名。现已支持 `PubmedBookArticle`，题名、来源书名、出版年份、摘要和书籍/条目类型均从缓存原始 XML 提取；不会把检索命中变成图关系或升级为机制证据。
- 重建后检索快照仍为 1,314 条候选—PMID 记录；空题名从 3 条降为 0，空摘要从 27 条降为 24。3 条书籍记录分别为 ponatinib 的 LiverTox、doxorubicin 的 StatPearls “Anthracycline Toxicity”和 LiverTox “Cytotoxic Antibiotics”。manifest 的 CSV SHA-256 与输出匹配，全部 API 请求使用既有缓存（0 次网络请求）。
- 新增解析器回归测试 2 项，通过；通用系统 Python 未安装 pytest，使用 `kg/.venv` 执行专项测试。检索未人工筛查、每组最多 100 条及书籍条目属于背景性文献等限制仍然有效。

## ER+ 疾病上下文证据图（2026-11-21）

- 针对 P4/P6，将 11 条已人工审查的逐药疾病背景记录加入新的项目级 GraphBundle：11 个 `DiseaseEvidence` 节点、11 条 `Drug-HAS_DISEASE_CONTEXT_EVIDENCE->Evidence` 和 11 条 `Evidence-CONCERNS_DISEASE->MONDO:0007254`。每个节点保留亚型/模型上下文、主张类型、方向、来源、审查状态和限制。
- 该图明确表达“某药物有这条经审查的研究背景记录”，不创建 Drug—Disease `ASSOCIATED_WITH` 治疗关系；阴性、混合、其他亚型和检索缺口都按原始分类保留。
- 新 GraphBundle run `7e70628f-7c76-4a2e-9dd5-56004e9c8c21` 离线验证通过：6,866 节点、38,890 关系、38,890 EvidenceRecords；13/13 图包输出哈希及 15/15 registration checksum 均匹配。Top 10 离线 API 已指向该校验包；详情 API 返回每候选疾病证据子图，前端关系图显示候选药物、标准药物、DiseaseEvidence 和疾病节点，并可筛选这些关系。
- 验证：KG 全量测试 29 项通过；后端专项 API 测试覆盖全部 10 个候选的证据节点、两段关系和 review 状态，并以隔离 SQLite GraphBuild 流程确认 38,890 条证据记录及 22 条疾病证据关系落库（3 项专项用例通过）；前端 TypeScript 与 Vite 生产构建通过。另已在隔离 staging 完成真实 Neo4j 导入、精确清单和幂等验证；当前 staging GraphBuild 已按计划回滚，生产/默认数据库未写入。
- 本轮重新检查默认端口 5432/7687/7474 和隔离端口 15432/17687/17474，均未监听；没有对主数据库或 Neo4j 写入。
