# 外部数据与标准化清单

## 已接入的证据

- 冻结 Top 10、项目 GraphBundle 与逐候选文献/S1-S2 证据作为本地输入；身份与目标关系仍按原 bundle 语义保留。
- 项目已有的 ChEMBL 机制快照、ChEMBL target-component 映射和 Reactome 98 UniProt-pathway 映射，按精确 `pert_id`、ChEMBL target 与 UniProt accession 对齐，构成候选专属的 `drug → ChEMBL target → human UniProt protein → Reactome pathway` 上下文。只有标记为 direct interaction 的机制、human protein component 和非推断 Reactome membership 被纳入。此路由代表证据共现/注释，不是因果链，不表示 ER+ 疗效。
- Reactome 当前 human pathway 节点及 pathway hierarchy 已下载并标准化为 CC0 数据。原始文件与规范化输出均保留版本、SHA-256、源记录和物种过滤信息。当前 release 路径标记为 `current-2026-10`。
- Reactome `UniProt2Reactome_All_Levels.txt` 人类成员关系已下载并标准化：946,459 原始行中有 162,642 条 human rows；精确 UniProt→OptimusKG gene 一对一映射后保留 54,361 条唯一 gene-pathway 记录，108,281 条因 accession 未映射或歧义而拒绝。当前 S1 终点基因的 Reactome membership 现作为独立路径注释写入 Top10 离线子图，不赋予调控方向，也不扩展因果路径。
- SIGNOR Oct2026 release 按原始 schema 流式标准化，只接纳 human、direct、UniProt protein→protein 且 effect 明确为 up/down-regulation 的断言。保留 PMID、SIGNOR_ID、cell/tissue、mechanism、行号与 raw row；不合格记录进入 reject 文件。
- OmniPath API-current-2026-11-22 下载 academic-filtered core interactions 和 resource metadata。按 `evidences` 展开逐来源 signed assertions，只保留 `dataset=omnipath` 的正/负证据，并保留 resource、reference 和每个来源的许可证；不以聚合 consensus 替代证据。
- OptimusKG 3.2 gene parquet 的 `associated_proteins` 字段用于构建精确 UniProt↔项目 gene crosswalk。当前 27,895 个 accession 均唯一映射；该 crosswalk 是 ID 映射证据，不是调控边。
- DrugMechDB 2.0.1 `indication_paths.yaml` 已固定下载，官方 CC0 LICENSE 原文也留存。仅作为独立参考集：用严格药名匹配与 Breast Neoplasms MeSH `D001943` 对照 Top 10 的直接蛋白靶点；未把基准边合并进预测 KG。
- PrimeKG Harvard Dataverse v2 (2022-05) 的 `kg.csv` 和原始格式 `nodes.tab` 已下载，官方 MD5 均通过校验；数据集许可证由 Dataverse 元数据确认为 CC0-1.0（不是只依据代码仓库 MIT 许可）。对冻结 Top10 执行精确 canonical/alias 药名映射后覆盖 6/10；1,026 条去重子集关系中，978 条通过唯一节点映射导入 staging GraphBuild（58 drug-protein、528 protein-protein、392 disease-protein），48 条含未映射端点的关系和 44 个歧义/缺失基因节点被拒绝。PrimeKG 原生关系作为关联证据、符号 unknown；未纳入 signed path propagation 或评分输入。

## 规范化和质量控制

通用映射规范化器支持显式列名或零基列号、常量、unknown 值及 `sign_from:<stimulation>,<inhibition>`。两个布尔值同时为真时标记 conflicting，均不为真时标记 unknown。它不会从 Reactome membership 或无向 PPI 推断调控方向。每条接纳记录保留原始行、来源版本、许可、物种、源文件 SHA-256、行号、原关系 ID（或稳定行哈希）和 assertion ID；拒绝行单独记录。

Reactome 当前下载为无表头三列 pathway 表及 parent-child 层级表。规范化后保留 2,889 个 human pathway 节点、2,905 条 human hierarchy 关系；过滤掉 20,857 条不满足两端均为 human pathway 的层级记录。方向存为 child `SUBPATHWAY_OF` parent，sign 为 unknown。

## 下载与许可

Reactome pathway data 使用 CC0 1.0 Universal；SIGNOR 4.0 使用 CC BY 4.0；OmniPath 关系按上游资源继承许可并逐资源记录；PrimeKG 数据集版本 v2 由 Harvard Dataverse 官方元数据列为 CC0-1.0，相关原始文件校验和已核实。DrugMechDB 2.0.1 官方 LICENSE 为 CC0 1.0，原文与数据版本一起保留。

Reactome 首次下载失败及后续成功均保留在 source manifests。SIGNOR/OmniPath 已标准化并用于候选子图，路径所需的 328 条 source assertions 已随 GraphBuild 注册并写入任务专用 staging Neo4j。Reactome current-2026-10 hierarchy 与 gene-pathway 子集、PrimeKG exact Top10 target subset 已作为独立 unsigned association/annotation layer 增量导入第二个 GraphBuild；导入前停机备份、恢复检查、精确清单、幂等重放和备份克隆回滚均通过。全量规范化网络仍保存在离线文件，不会不加筛选地灌入图谱。DrugMechDB 仅作独立外部参考评估。原始文件、许可、manifest、规范化输出和 reject 文件保存在 `data/kg_enrichment/`。

## 解释边界

Top10 离线子图的 SIGNOR/OmniPath layer 有 7,306 条断言映射到候选相关基因；过滤 5 个 outdegree>100 的 hub 后保留 6,274 条。候选命中 9/10，共 349 条有向调控路径。这些是图谱覆盖，不等同路径验证或药物效应。冲突/上下文不明方向配对保持 unknown；S1 mRNA 不解释成蛋白活性。Reactome hierarchy 不参与调控符号传播。路径所需的 328 条断言现已随注册 GraphBuild 持久化；path discovery 与评分仍由可复现的离线流程生成。
