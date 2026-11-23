# 项目级 S1 RNA-seq edgeR-voom 实施与验收报告

日期：2026-11-13

## 目的与范围

为新建项目增加 RNA-seq 差异表达入口，读取原始整数 read counts 和样本分组表，生成可追溯的 S1 差异分析结果。该实现与已有微阵列 limma 入口分开；不修改历史 ER+ 乳腺癌 S1、S2 或 Exp006–Exp011 数据。本报告中的 HTTP smoke 使用合成数据，仅验证软件，不是疾病研究结果。

## 输入审计与方法

- 输入必须是非负、有限、整数型 read counts；拒绝负数、缺失、全零样本、分数值以及 TPM/FPKM/CPM 等归一化表达量。
- Feature ID 必须唯一。表达矩阵样本列与样本注释中的 sample ID 必须一一相同。只允许明确指定的两组，每组至少 2 个样本。
- Contrast 明确为 `positive_group - negative_group`，例如 `Tumor - Normal`；正 logFC 表示正向组表达更高。
- 分析步骤为 `edgeR::filterByExpr` 过滤低表达特征、`edgeR::calcNormFactors(method="TMM")` 归一化、`limma::voom` 估算均值-方差关系、`lmFit`、`contrasts.fit` 和 `eBayes(robust=TRUE)`；多重检验使用 BH。输出包括 gene ID、logFC、AveExpr、t、P.Value、adj.P.Val、B 和方向。
- 该流程参考 Bioconductor 对 RNA-seq 计数数据的 edgeR/voom 工作流；项目新增部分是 API 输入门禁、项目隔离、运行哈希与软件验收流程。[limma User’s Guide](https://bioconductor.org/packages/release/bioc/vignettes/limma/inst/doc/usersguide.pdf)、[edgeR Bioconductor 页面](https://bioconductor.org/packages/release/bioc/html/edgeR.html)。

## 工程实现

- R 脚本：`backend/app/pipelines/rnaseq_edger_voom.R`。
- Python 调用与环境检测：`backend/app/s1_expression.py`；运行时显式配置隔离 R_HOME、PATH、DLL 搜索路径及 UTF-8 locale。
- API：`POST /api/v1/projects/{project_id}/datasets/{dataset_id}/s1/rnaseq-edger-voom`。请求中要求指定样本注释数据集、正负分组及 ID 类型。AnalysisRun 记录参数、软件版本、输入输出 SHA-256、日志与状态；失败会保留失败运行信息。
- S1 查询和 S2 来源门禁可识别 `s1_rnaseq_edger_voom` AnalysisRun。RNA-seq 与微阵列结果都在各自项目/运行目录保存。
- 环境：R 4.4.3、Bioconductor 3.20、edgeR 4.4.2、limma 3.62.2、locfit 1.5-9.12、BiocManager 1.30.27。版本与下载来源记录于 [RNA-seq 环境清单](rna_seq_environment_manifest.json)。

## 软件测试

`backend/tests/test_s1_expression.py` 覆盖微阵列方向和样本 ID 校验，以及 RNA-seq 合成数据的过滤、TMM/voom 运行、contrast 方向和 normalized fractional values 拒绝。完整后端/S2 测试状态以本次最终实际运行记录为准；不得把合成软件测试解释为生物学结论。

## HTTP 端到端 smoke 记录

在隔离 `test_only` 项目 `89aa18d8-e1ca-4eb4-8046-634cd2911207` 中上传 200 个 feature × 6 个样本的合成整数 counts（Tumor、Normal 各 3 个样本）与样本注释。20 个全零 feature 被过滤，180 个 feature 进入检验；Contrast 为 `Tumor - Normal`，产生 1 个上调、1 个下调结果。

- AnalysisRun：`ANALYSIS_RUN:S1_RNASEQ:e51f024a-805f-4e21-8ddd-a7fcc6cacad6`
- R：4.4.3；edgeR：4.4.2；limma：3.62.2
- 输出 `limma_all_genes.csv` SHA-256：`514ed4618d7bb460b769f92c6e4bf599f0d28f736e4c72c79665d37eadfc6ee4`
- API summary 查询确认 run 类型、对比方向和输出数；结果仍标记为 `test_only`。

后续曾使用该 test-only S1 运行少量真实 MCF7 LINCS signature 的 S2 软件闭环。该步骤只验证接口和文件兼容，不是 ER+ 乳腺癌 RNA-seq 研究，也未产生正式候选药物结论。

## 局限与后续工作

- 当前仅支持双组比较，不支持批次、配对设计、协变量、多因素模型或复杂 contrast；有这些设计时不能把样本标签简化后直接套用本插件。
- 不负责原始 FASTQ 定量、样本质控、基因 ID 标准化、一对多映射处理或探针注释；应在上传前完成并记录上游流程。
- 目前采用 limma-voom，不提供 DESeq2 流程。全新项目的 GO/Reactome/Hallmark 富集已可单独运行；富集结果自动生成通用 GraphBundle 仍未实现。
- HTTP 分析为同步执行，尚未转为后台任务；大数据需评估资源和执行时限。
- 当前 smoke 使用合成输入，尚无真实 RNA-seq 队列在此插件上的科研结果。
