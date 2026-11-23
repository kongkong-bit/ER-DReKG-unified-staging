# 项目级 S2 LINCS 管线实施与 smoke 验收报告

日期：2026-11-13

## 管线功能

- 新增 `s2_lincs/project_screen.py`，供项目级 CLI 调用；读取项目自己的标准 S1 差异表和现有 GSE70138 Level 5 数据。它不读写历史正式 S2/Exp006–Exp011 结果。
- 基因映射从 LINCS `gene_info` 的 BING 标记开始。支持精确 Gene Symbol 和 `pr_gene_id`（Entrez）映射；一对多 Symbol 标记为歧义，不任意选一个；Ensembl 没有本地交叉表时，生成逐基因审计并以 `BLOCKED` 结束，不输出分数。
- 先限制到 BING 唯一映射基因，再按预设 FDR、adj.P.Val 升序、|logFC| 降序，分别取 UP/DOWN 前 N 个。保留映射率、歧义、未匹配、输入统计量和是否入选等审计字段。
- 主条件默认为 MCF7、`trt_cp`、24 h、`distil_cc_q75 >= 0.2`。先核对 Signature ID 与 GCTX 列 ID；只按行读取需要的 signature，基因背景限于 GCTX 中有对应 LINCS BING 注释的基因，不把 5.82 GB 矩阵整体载入内存。
- 每条 signature 输出 ES_UP、ES_DOWN、原始 WTCS、`reversal_score=-WTCS`、质量值和 S1 基因覆盖率。新评分模块 `s2_lincs/scoring.py` 的数值与原 Smoke Test 算法在测试向量上一致。WTCS 是表达关联分数，不能解释成治疗效果。
- 药物条件汇总按 perturbagen、细胞、扰动类型、剂量、时间分组，保留 median、mean、SD、MAD、signature 数和质量中位数。排序只在完全相同的剂量/时间条件内进行，禁止跨剂量混合或挑每个药物最有利的一条 signature。
- 输出 `s1_gene_mapping_audit.csv`、`signature_scores.csv`、`drug_condition_summary.csv`、`qc_summary.json`、`run_manifest.json`，清单记录参数、来源文件大小与 SHA-256、输出哈希、运行 ID、test_only 和解释边界。

## 实际 smoke test

本次使用多项目隔离验收中的 `test_only` 项目，人工构造仅供软件验证的两个查询基因（A2M 上调、A4GALT 下调；统计量为合成值），并从实际 LINCS 文件读取真实签名。它是软件集成测试，不是疾病分析结果，不能作为候选药物证据。

- 查询基因映射到 BING：2/2 唯一映射；上下调查询各 1 个基因，且各自都在实际 GCTX BING 背景中测量。
- 全部 MCF7、`trt_cp` metadata：12,737 条；24 h：11,850 条；`distil_cc_q75 >= 0.2`：5,861 条；均与 GCTX Signature ID 对齐。本次只取按固定顺序前 5 条做 smoke test。
- 真实 GCTX Signature ID：`REP.A012_MCF7_24H:B11`、`REP.A012_MCF7_24H:B09`、`REP.A012_MCF7_24H:B07`、`REP.A012_MCF7_24H:B16`、`REP.A012_MCF7_24H:B15`。共来自 2 个 perturbagen，并形成 5 个独立药物-剂量-时间条件；没有合并剂量。
- 输出目录：`data/processed/projects/89aa18d8-e1ca-4eb4-8046-634cd2911207/s2_software_smoke/results/`；运行 ID：`S2_PROJECT_20261113T125247Z_d11582c225a1`；清单 `test_only=true`。GCTX SHA-256：`1f31891cc7138205688f9d1f2282004517c9e61a14c1c3d64a241b7582976a2e`。
- LINCS 对照空间实查：MCF7 trt_cp 共 12,737 signature，24 h 共 11,850，质量达阈值且对齐 GCTX 的 signature 为 5,861。
- S2 工程测试：9/9 通过，覆盖 WTCS 参考方向/数值、与历史 smoke 算法一致、签名过滤、质量门槛、dose 分层、signature 读取、Ensembl 缺少交叉表时阻断并保留审计。

## 项目接口与页面接入状态

- 已增加项目 S2 结果导入接口、摘要接口和按剂量/时间返回条件汇总的接口。导入时会校验项目级 S1 AnalysisRun、输入文件哈希、运行清单、test_only 标志和 S2 输出文件哈希；重复导入按 AnalysisRun ID 幂等处理。test_only 数据不能导入正式科研项目。
- 前端 API 客户端和项目 S2 页面已接入条件汇总展示，显示药物、剂量、时间、signature 数、WTCS 汇总和 test_only 标记。前端生产构建已成功。
- 本机 API 在线端到端联调已完成，详细运行记录见下节。FastAPI OpenAPI 实际返回 24 条路径，含 S2 导入、摘要和条件查询 3 条接口。
- 后端自动化测试在隔离 CSV 模式 23/23 通过；S2 工程测试 9/9 通过。Neo4j 相关测试在无 Neo4j 服务/端口权限的默认环境会失败；隔离 CSV 模式测试不依赖 Neo4j。

## 本机 API 端到端联调记录

- 使用隔离的 `test_only` 项目 `89aa18d8-e1ca-4eb4-8046-634cd2911207`。通过真实 HTTP 上传 2 行合成 DEG 表并创建 S1 AnalysisRun：`ANALYSIS_RUN:S1_PRECOMPUTED:115ad849-145b-468f-8131-5b46414be0fc`。该输入只验证软件链路，不是疾病差异分析结果。
- 使用该 S1 AnalysisRun 和真实 LINCS Level 5 GCTX 执行 5 条 signature smoke test，S2 AnalysisRun 为 `ANALYSIS_RUN:S2_LINCS:e0bc64a29f974f1285c30f7dcc72cb57`。QC：实际评分 5 条 signature、2 个药物、5 个药物-剂量-时间条件；MCF7/trt_cp 元数据 12,737 条，24 h 11,850 条，质量达阈值且与 GCTX 对齐 5,861 条。上下调查询各 1 个基因，BING/GCTX 映射均成功。
- S2 结果经 `POST /api/v1/projects/{project_id}/s2/import` 导入 Postgres 为 `completed` AnalysisRun；重复导入返回 `idempotent=true`。摘要接口返回 `test_only=true`、5 signatures、2 drugs、5 条条件汇总；条件接口实际返回 balaglitazone 和 flutrimazole 分剂量记录。没有跨剂量合并，也没有把结果写入 Candidate 表。
- 对应输入 S1 SHA-256：`2f55823f58bc7a997cb7822ecdebfaeb7ef4b83ef8e11eef16d74595ca848cb0`。导入时的 S1 哈希核验通过。输出哈希：`signature_scores.csv` `e69d79d7bdac0c44f4d591331edff5c3c320112876a5b3e0e2a6c27b4575e1dd`；`drug_condition_summary.csv` `75ff5198111689a04a4aff605075585bc1dbb2477ae3d091327827b8a6c5af57`；`s1_gene_mapping_audit.csv` `1c0aed705617f5c6ea22e44c70475a20aa5834542fe5d31f150c4f834d752d66`；`qc_summary.json` `b4d9221eb780f58e26e18e1382097926762698f9d836d96c19a2a3ff6aa845f6`。接口只在哈希一致后登记运行。
- 对历史正式 ER 项目查询 S2 摘要仍返回 `available=false`，表明 test_only 运行没有混入正式项目。API 实际验收通过；前端构建通过，但本轮没有另行做浏览器可视化验收。

## 限制和后续工作

- 本次五条真实 LINCS 记录及其数据库记录只用于软件联调；查询基因来自合成测试输入，不能作为科研结果或候选药物证据。结果保存在隔离 test_only 项目，不进入项目 Candidate 表。
- 项目级 S2 当前提供可复跑 CLI、页面配置/运行入口、经文件哈希门禁保护的导入 API，以及按条件结果持久化和查询。跨剂量 Candidate 总分规则尚未设定；完整筛选应由项目页面明确启动，不能把五条 smoke 签名当作完整排行榜。新运行入口的验收记录见 [S2 配置与运行报告](project_s2_run_report.md)。
- 输入若为 Ensembl，当前 LINCS 元数据本身缺少 Ensembl 交叉映射，将阻断并输出原因；需先加入有来源和版本的 ID 映射资源。
- R 4.4.3、limma 3.62.2 和 edgeR 4.4.2 位于项目隔离环境；虽未将 `Rscript` 加入系统全局 PATH，后端会显式配置 `R_HOME`/DLL 路径。微阵列和 RNA-seq 插件分别见 [项目级 S1 limma 报告](project_s1_limma_report.md) 与 [项目级 S1 RNA-seq 报告](project_s1_rnaseq_report.md)。
- 历史 `s2_lincs/smoke.py`、正式 S2 输出及 Exp006–Exp011 文件均保持不变；通用项目评分代码和测试独立新增。
