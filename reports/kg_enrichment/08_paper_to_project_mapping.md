# 参考论文方法与 ER-DReKG 当前模块的映射

这份映射以仓库现有组件和本轮实际产物为准。引用论文提供的是方法启发，不表示本项目已经复现其模型或结论。

| 参考工作 | 对应项目模块 | 可直接落实的改进 | 当前状态与边界 |
|---|---|---|---|
| Computationally repurposing drugs for breast cancer subtypes using a network-based approach (2022) | S1 差异表达、Reactome/Hallmark、S2 LINCS/WTCS、Top 10 KG | 保持亚型和表达逆转证据分层；用疾病基因与路径解释候选机制 | 现有 S1/S2 沿用，新增基因级对照字段；没有重跑筛药，也没有声称机制因果验证 |
| CAREPath (2026) | 候选机制路径 JSON、证据上下文与 API/UI | 路径需要语义上下文、来源证据、节点/关系类型检查；解释需保留条件和未知信息 | SIGNOR/OmniPath directed paths 带来源断言、映射证据、上下文和符号；ChEMBL→Reactome98 仍是独立注释路线；未实现 CAREPath 语义嵌入/模型 |
| Reactome current-2026-10 | S1 终点基因路径注释 | 用精确 UniProt→project gene crosswalk 添加 pathway membership；与调控路径分层展示 | 54,361 条 human membership 已规范化，48,709 条唯一基因-通路断言及 2,905 条层级边已导入 staging；另对离线路径终点做注释。不传播激活/抑制符号 |
| PrimeKG (Dataverse v2, CC0-1.0) | 外部药物靶点、疾病基因与蛋白互作证据 | 从大图谱抽取 Top10 exact identity 命中的局部关系；保留原生 relation 和未知方向 | 精确身份覆盖 6/10，规范化 1,026 条候选关系，其中 978 条成功导入 staging；92 个节点/端点映射拒绝均有记录。作为无方向关联层保留，不纳入预测评分或符号传播 |
| DrugMechDB (2023) | 独立路径参考与靶点一致性核验 | 以精确药物/疾病/实体 ID 构建独立参考集，检测训练/评测泄漏 | 已固定 v2.0.1，并按严格药名 + MESH:D001943 对照：Top10 命中 1 条乳腺肿瘤适应症路径，doxorubicin 直接靶点 TOP2A 与项目药理靶点重叠；单例不代表 ER+ 疗效或整条路径有效 |
| Scaling Network Medicine with LLMs for Combinatorial Drug Repurposing in ER+ Breast Cancer (2026 preprint) | ER+ 文献与机制网络 | ER+ 专属语境和文献证据需要单独标注，组合药物需要额外交互证据 | 当前审查表保留 ER+ 研究背景；未运行 LLM 文献抽取或组合预测 |
| XG4Repo (2024) | 图谱关系、路径输出和候选证据记录 | 以可读的有类型关系链解释药物—疾病假说，保存路径原始 assertion ID | 真实 signed regulatory paths 已构建；不做无来源 KG completion，且不把表达相关当成药效因果 |
| KGML-xDTD (2023) | Top 10 子图构建、方向推理、机制报告 | 将预测和机制描述分开；使用 DrugMechDB 做外部解释评价 | 子图与规则报告已建立；未训练 xDTD，也未完成 DrugMechDB 评价 |
| DrugReX (2025 preprint) | 证据索引与逐药报告 API | 文献解释应从检索到的 Evidence ID 生成，并校验引用可回溯 | 当前生成确定性规则报告，不调用 LLM；待接入经核验文献检索后再启用模型解释 |
| REx (IJCAI 2025) | 路径搜索和解释质量优化 | 对路径的可解释性、有效性和多样性做显式奖励与评估 | 当前 directed REGULATES 有向搜索及符号传播已用 SIGNOR/OmniPath 路径运行；尚无路径质量奖励、RL 搜索或盲审 |

## 外部知识库在当前工程的落点

- Reactome：已获取 current-2026-10 human pathway 名称、层级及 UniProt-gene membership，保留 license、原始文件 SHA 和来源行；层级为 child `SUBPATHWAY_OF` parent，membership 为 `CONTAINS_GENE`，sign unknown。两类注释均不等于药物因果机制。
- SIGNOR、OmniPath：已下载、按来源 schema 标准化、筛选并进入离线候选子图；保留版本、许可证、source hash、原记录及 PMID/ref。路径支持的 328 条断言通过 GraphBuild 导入任务专用 staging；其后 Reactome/PrimeKG 外部层以第二个 GraphBuild 导入。两次导入均重复运行验收幂等、精确 inventory。
- DrugMechDB：按 v2.0.1 固定并作为独立参考；只核对乳腺肿瘤适应症与靶点，不合并进预测图谱。
- PrimeKG：官方 Dataverse v2 数据许可已核验为 CC0-1.0，原始文件校验和已验证；Top10 子集以 ASSOCIATED_WITH 导入 staging，原生关系类型及映射拒绝均可追溯。

## 对后续开发的优先级

1. 将两个 staging GraphBuild 纳入常规部署和可视化验收，并保留版本化备份；尚未提升至生产。
2. 针对 Top 10 命中的源记录人工检查关系类型、组织、细胞背景与相反方向，先报告 conflict，再做路径质量评测。
3. 以冻结候选子图开展 source ablation 与 blind validity review；路径未知符号必须保持 unknown。
4. 扩充 DrugMechDB 精确药名/实体 crosswalk；当前只有 1 个严格匹配乳腺肿瘤案例，不能据此估计总体机制路径召回。
5. 只有检索证据可核验时才启用 CAREPath/DrugReX 类 LLM 解释；用 REx 类方法前先确保真实路径样本和有效评估指标充足。
