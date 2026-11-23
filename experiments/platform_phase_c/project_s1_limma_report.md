# 项目级 S1 limma 微阵列插件实施与验收报告

日期：2026-11-13

## 实现范围

- 新项目现在可上传连续型、log2 标准化微阵列表达矩阵及独立样本分组表，并在 S1 页面配置正向组、负向组、FDR 阈值和 Gene ID 类型运行 limma。
- 上传仍先做结构检查并标记 `validation_pending`；分析时再次核对项目归属、文件路径和 SHA-256。矩阵样本列与样本注释 ID 必须完全匹配，注释恰好包含所选两组，每组至少两个样本。未知样本、不匹配样本、重复 feature ID 或无效数据会使分析失败并保留失败运行记录。
- 分析方法是 `limma::lmFit` + `contrasts.fit` + `eBayes(robust=TRUE)`，BH 调整。contrast 固定明确为 `positive_group - negative_group`，例如 `Tumor - Normal`。保留 logFC、平均表达量、t、原始 P、adj.P、B 统计量和方向。
- 该插件只接收 log2 标准化连续型微阵列数据，不把 RNA-seq 原始 counts 误当作微阵列表达。RNA-seq 原始 counts 另有独立的 edgeR-voom 插件，见 [RNA-seq S1 报告](project_s1_rnaseq_report.md)；若输入为原始 counts，不应选择本入口。
- R 4.4.3 和 limma 3.62.2 已位于 `experiments/s1_pathway_enrichment/r-env/` 项目隔离环境。`Rscript` 没有加入系统全局 PATH；新 Python runner 显式配置 `R_HOME`、依赖 DLL 路径和 UTF-8 子进程输出，不依赖全局安装。`run_enrichment.ps1` 同步修复为使用同一环境内的 Rscript 和 DLL 搜索路径。
- 结果写入项目独立目录 `data/processed/projects/{project_id}/s1/{run_uuid}/`，包括 `limma_all_genes.csv`、运行摘要和 `run_manifest.json`。AnalysisRun 记录输入数据集、样本注释、参数、软件版本、输入/输出哈希和状态；历史 S1 文件保持不变。
- 项目 S1 summary、基因表、火山图和 S2 来源门禁现在能识别 `s1_limma_microarray` 类型。旧的 precomputed DEG 入口保留，互不覆盖。

## 软件验收

- 微阵列插件交付时的后端隔离 CSV 测试为 25 项通过；本轮新增 RNA-seq 插件后，当前后端完整测试为 27 项通过（含 edgeR-voom 和小数 counts 拒绝测试）。`compileall` 通过。
- 前端 S1 页新增矩阵与样本注释选择器、Gene ID 类型和 contrast 参数；`npm run build` 通过。包体仍有大 chunk 提示。
- 微阵列插件交付时的在线 OpenAPI 为 25 条路径；增加 RNA-seq 和项目 S2 运行路由后，当前 OpenAPI 为 27 条路径。微阵列 endpoint 为 `POST /api/v1/projects/{project_id}/datasets/{dataset_id}/s1/limma-microarray`。

## 真实 HTTP 端到端 smoke

本次仅在隔离 `test_only` 软件测试项目 `89aa18d8-e1ca-4eb4-8046-634cd2911207` 中上传合成数据。它不是疾病研究数据：表达矩阵 3 个 feature × 4 个样本，两组各 2 个样本，包含 A2M、A4GALT 和 GAPDH。

- limma AnalysisRun：`ANALYSIS_RUN:S1_LIMMA:9b9000e2-b35d-42de-82d7-1451ed69db84`
- contrast：`Tumor - Normal`；运行结果：3 个 tested features，1 上调、1 下调；方向和差异幅度符合输入构造。
- 输入 SHA-256：表达矩阵 `f92f47757da5ff5482e8d7af30ddef89c6baf133757aaea52f62f872979111f5`；样本注释 `9223e8ee463c367fc37bffa3bf5bacc9d4df5593ef104653546c6e9a92fa4c71`。
- `limma_all_genes.csv` SHA-256：`f401731db2c8d373dc301a968323d303d2e29428ac98defb0cd3c9fa5484fc4c`。
- 再将该 S1 AnalysisRun 交给项目 S2 CLI，按 LINCS gene_info 的 BING 空间唯一映射 3/3，提取并评分 5 条真实 MCF7 Level 5 signature；质量和 GCTX ID 筛选总览与已有 LINCS 审计一致：合格并对齐 5,861 条，smoke 实际读取 5 条，形成 5 个剂量条件。之后成功通过 S2 导入接口登记并查询。
- S2 AnalysisRun：`ANALYSIS_RUN:S2_LINCS:529848443d1c4ebcbd0dfe24d71ff4ce`，关联的 S1 ID 是上述 limma run。API 返回 `test_only=true`；正式 ER 项目没有显示这次软件测试结果。

## 限制

- 这次数据仅证明代码和接口链路可运行，不能作为 ER 阳性乳腺癌差异结果、候选药物排名或疗效证据。
- 当前插件不做批次校正、探针注释、重复探针折叠或 ID 标准化；上传者必须提供唯一 feature ID 和合适的预处理表达矩阵。分析结果中的 ID 类型作为参数记录。
- 协变量模型和多因素设计待独立统计插件实现。基因通路富集现可作为独立项目 S1 AnalysisRun 执行，方法与边界见[项目级通路富集报告](project_s1_pathway_enrichment_report.md)。
- 单机 HTTP 分析为同步执行，最大 30 分钟；大矩阵需要迁移至后台任务并增加资源限制。
