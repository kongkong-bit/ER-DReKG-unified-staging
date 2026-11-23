# Exp011：S2 候选药物的 PRISM 外部敏感性验证

## 用通俗的话说

S2 根据 LINCS 细胞实验推测哪些药物能把乳腺癌异常表达往反方向推；PRISM 则是在很多癌细胞系里实际测药物处理后细胞存活变化。本实验把两边能用化学结构确认是同一种药的药物配起来，检查 S2 排名和 PRISM 敏感性是否有一致趋势。它是细胞系层面的外部对照，不等于临床疗效。

## 数据与匹配

- 来源版本：Broad/DepMap PRISM Repurposing **Primary**；官方页面描述该 release 为 4,518 compounds、约 578/562 cell lines。本地 replicate-collapsed 文件实读到 4686 个 condition columns，其中同药多剂量/不同 screen 会分别占列。PRISM 官方页：[depmap.org/repurposing](https://depmap.org/repurposing/)；该页面提供 README、细胞注释、replicate-collapsed LFC 与 treatment metadata。受体注释使用 DepMap Public 24Q4 `Model.csv`（[下载地址](https://ndownloader.figshare.com/files/51065297)），不是把 PRISM 细胞来源当作受体状态。
- 授权审计：本次下载的 PRISM README 和官方数据页列出数据来源及引用信息，但没有随文件提供单独 LICENSE 文件，也没有在所审页面显示逐文件许可条款；后续公开使用应按 PRISM/DepMap 页面提供的原始研究与数据集引用方式注明来源。
- PRISM Primary：矩阵包含 578 个细胞系和 4686 个药物剂量/筛选条件；细胞系 ID 注释表有 588 行，其中 568 个模型可按 ACH ID 连入 DepMap Public 24Q4。矩阵不含控制条码行，未能连入的行不纳入 ER 分型。
- 按 PRISM 注释识别乳腺癌细胞系 26 个；DepMap Public 24Q4 `ModelSubtypeFeatures` 中标为 ER+ 9 个，标为 ER−/TNBC 13 个，受体亚型未知 4 个。MCF7 单独保留。
- 药物身份只接受 Broad ID 完全相同或由有效 SMILES 推导出的 InChIKey 完全相同。候选药物名称只用于核查，不用于药物身份归并；未做模糊匹配。
- Exp006 Top50 中有 37/50 个通过结构标识匹配；Exp006 全部 819 个候选中有 683/819 个通过结构标识匹配。其余未匹配条目保留在 mapping audit，不能据此解释为实验没有测过。
- PRISM 每个药物的剂量/屏幕记录先在每个细胞系内取中位数，不挑最有利剂量。敏感性定义为 `−log2 fold change`，越大表示细胞存活下降越强。

## 主要结果

见 `candidate_sensitivity_results.csv`、`s2_prism_rank_correlation.csv` 与 `candidate_vs_random_test.csv`。Top50 结构匹配药物数为 37；相关性及置信区间仅对同时有 S2 排名和 ER+ PRISM 结果的化合物计算。候选组与随机组比较是从有 ER+ PRISM 记录的其他结构唯一化合物中抽取同样大小集合，固定种子 20261112，重复 10,000 次。

`candidate_vs_random_test.csv` 给出单侧经验 P 值（候选组是否较随机组更敏感）；随机化合物还按每个药物有 PRISM 结果的 ER+ 细胞系数量分层匹配（{"9": 35, "8": 2}）。经验 P 值的最小分辨率是 1/10,001；若观测值达到这个下限，应读作“≤约 0.0001”，不是无限精确的概率。若 P 值不小，或区间/样本数不足，就不能说候选整体更有效。ER− TNBC 和 MCF7 的结果分别保存在逐药/逐细胞结果中；ER status 未明确的乳腺细胞不并入 ER−组。

ER 特异性另作比较：在 37 个结构匹配 Top50 候选中，ER+ 平均敏感性减去 TNBC 平均敏感性的均值为 -0.327（bootstrap 95% CI -0.517 至 -0.145）；按 ER+ 与 TNBC 可用细胞系数量匹配的随机药物集单侧 P=0.9998。该差值若为正才表示更偏向 ER+；结果按实际方向解释，不预设候选有 ER+ 选择性。

## 结果边界

WTCS 与 PRISM 是两个不同终点：WTCS 看药物引起的表达变化是否与疾病表达相反；PRISM 看药物是否让细胞生长/存活下降。WTCS 很负但 PRISM 杀伤不明显，不代表 WTCS 算错；PRISM 杀伤很强也不能证明它通过表达逆转机制起效。

1. PRISM 测的是体外细胞存活，不测患者疗效，也不直接测 ER+ 乳腺癌患者获益。
2. PRISM 主要筛选数据是多药剂量/批次的细胞活力实验；本报告在单细胞系内对剂量/屏幕取中位数，以减少挑选最有利剂量造成的偏差。
3. Top50 结构匹配数有限时，相关性和随机集合检验只能作探索性结果，不外推到未匹配药物或最终 Top10。
4. DepMap 24Q4 受体亚型注释与 PRISM 文件中的模型 ID 通过 ACH ID 连接；只接受明确含 ER 或 TNBC 标注的字段，其他标为未知。非乳腺细胞及控制条码不用于乳腺亚型统计。
5. PRISM SMILES 中不能解析的记录不参与结构匹配；数据字典提供了 SMILES 字段，但具体文件含空值/非 SMILES 占位值。
6. Fulvestrant、tamoxifen 和 raloxifene 在 PRISM 中有药物记录，逐药 ER+ / MCF7 敏感性结果见 `positive_control_sensitivity.csv`；它们用于核对 assay 是否覆盖已知内分泌药，不作为候选集有效性的证明。

## 文件

- `results/candidate_mapping_audit_top50.csv`、`candidate_mapping_audit_full.csv`：逐药标识映射审计。
- `results/cell_line_inventory.csv`：PRISM 细胞注释与 ER 分组来源。
- `results/candidate_prism_condition_map.csv`：通过结构映射的剂量/屏幕条件。
- `results/candidate_sensitivity_matrix.csv`：按 cell line × InChIKey 聚合的真实 PRISM LFC 与 sensitivity。
- `results/candidate_sensitivity_results.csv`：候选层汇总、S2 排名与 PRISM 敏感性。
- `results/s2_prism_rank_correlation.csv`：Spearman、Kendall 与 bootstrap 95%区间。
- `results/candidate_vs_random_test.csv` / `candidate_vs_random_null.csv`：同大小随机对照。
- `results/er_specificity_candidate_summary.csv`、`er_specificity_random_test.csv`、`positive_control_inventory.csv`：ER 分组逐药敏感性、覆盖数匹配随机检验和内分泌阳性对照清单。
- `results/positive_control_sensitivity.csv`：fulvestrant、tamoxifen、raloxifene 在 ER+ 组及 MCF7 的 PRISM 敏感性。
- `results/run_manifest.json`：来源、参数及输入 SHA-256。
- `figures/s2_prism_rank_scatter.png`、`candidate_vs_random.png`、`er_specificity_scatter.png`：由实际结果生成。

## 可复现信息

随机种子 20261112；随机对照 10,000 次；Spearman bootstrap 5,000 次；RDKit 2026.09.2。DepMap model 元数据：Public 24Q4。输入哈希保存在 manifest。
