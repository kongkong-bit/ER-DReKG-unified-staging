# ER+ 乳腺癌药物重定位：正式基线审计与 Exp013–Exp015 方案

审计类型：只读基线核查与实验准备。未运行新的全量评分/置换/bootstrap，未修改任何历史输入、输出或报告。

## 1. 执行摘要

- 当前正式候选表是 `experiments/final_results/results/final_top10.csv`，上游冻结版本见 `final_data_manifest.json`。它基于 5,861 条 stable-ID 合并、QC 合格的 GSE70138 Level 5 签名和 GSE42568 派生的 BING Top100 UP/DOWN 查询；主条件为 MCF7、`trt_cp`、24 h、CC q75≥0.2；主剂量按药物覆盖最大值事先选为 10 μM。按 `pert_id × cell × pert_type × dose × time` 汇总 WTCS 中位数，升序排序。
- 该榜的可重复计算性强：历史共同 4,761 条签名 WTCS 重算差异最大约 6.65e-14；但 Top10 个体支持弱：每药在正式主剂量都只有一条 Level 5 共识签名。共识签名下的 2–3 个 L1000 实例/板是同一处理条件的重复，不是独立患者/独立研究。
- 已存算法排名存在“比较对象/统计单位/版本”混用。可复核的 Exp008 基线是 4,761 个历史签名、B200、3,715 个共同药物-剂量-时间条件；其 Top10 交集统计的单位是**条件行**，不是正式榜按 10 μM 得出的唯一药物。Exp008 可复核的 WTCS 与 Classic KS/Zhang/XSum 条件 Top10 交集为 1/10、2/10、4/10。`final_research_report.md` 写的 3/10、5/10、0/10 在已保存 Exp008 输出中找不到对应的同口径证据，不能与前者并列引用；其确切来源无法从现存产物确定。
- 当前 Top10 的历史 B200 置换交叉核对中，5 个主剂量分数与 Final 正式 WTCS 精确相同，另 5 个无同剂量历史匹配。前 5 个的经验 P=0.00049975、历史 BH FDR=0.0039334；P 受 2,000 次置换的分辨率限制，FDR 是历史 3,715 条条件的校正值，不是当前 5,861 签名/10 μM 正式候选家族的统一重算结果。
- 推荐定位：M0/M1/Exp014 输出作为**可复现候选优先级**，不是疗效概率或临床排名。Exp010、Exp011 已完成，不重复；新独立实验留作 Exp015。

## 2. 正式基线与版本锁定

### 2.1 冻结的 M0 基线

| 项 | 当前正式定义 |
|---|---|
| 疾病队列 | GSE42568；67 ER+ 肿瘤、17 正常；limma；21,655 基因中 FDR<0.05 有 7,066 个（3,422 上调、3,644 下调） |
| 查询集 | 按发现队列差异方向，在 LINCS BING 背景中各取 Top100 UP / Top100 DOWN；冻结文件 `s2_lincs/s1_bing_top100_up.txt`、`s1_bing_top100_down.txt` |
| LINCS | GSE70138 Level 5 COMPZ；MCF7、`trt_cp`、24 h；稳定 ID 联结 `sig_id + pert_id + pert_type` |
| QC | `distil_cc_q75 >= 0.2`（项目预设，不是普适官方阈值） |
| 评分 | Broad-style 双向加权 KS WTCS；负值为逆向表达关联 |
| 主剂量 | 覆盖合格药物最多的统一剂量 10.0 μM；覆盖 1,032 个 pert_id；不为每个药单独挑最优剂量 |
| 聚合与排序 | 同一 `pert_id/cell/type/dose/time` 下合格签名 WTCS 中位数；按中位数升序；平局按 pert_id 确定性排序 |
| 规模 | 5,861 合格签名、1,471 个药物；10 μM 主条件 1,032 个药物 |
| 不参与排序 | 知识图谱、文献、Exp010 外部 S1、Exp011 PRISM |

Top10 ID 与 M0 分数：ponatinib `BRD-K44227013` -0.516654；mocetinostat `BRD-K16485616` -0.505900；MK-2461 `BRD-K56405753` -0.484092；doxorubicin `BRD-K92093830` -0.467169；rebastinib `BRD-K76694128` -0.457846；PHA-767491 `BRD-K50000283` -0.456419；iniparib `BRD-K11153516` -0.455273；balaglitazone `BRD-A00147595` -0.452738；PFI-1 `BRD-K13094524` -0.451376；JNJ-26481585 `BRD-K83837640` -0.446602。

### 2.2 已核实的版本/错误历史

- 原正式榜与稳定 ID 修正榜 Top10 只重合 5/10。稳定 ID 修正找回约 1,100 条名称键曾漏掉的真实匹配签名。Final manifest 还记载 Exp009 旧 stable-ID 排序实现有命中权重与位置错配，4,761 条共同签名中 3,870 个 WTCS 不一致；这批 Exp009 WTCS 不能拿来当正式 M0。
- Exp007 是 S1 基因集大小敏感性（历史 Q2 4,761 签名），Exp008 是方法敏感性/随机查询（同为 4,761 签名）。Final M0 是 5,861 条修正 stable-ID 集；二者不可未经 ID/查询/过滤和聚合对齐直接拼表。
- Exp008 的 `algorithm_topk_overlap.csv` 与 `method_comparison.csv` 可复核。Exp008 计算先按 3,715 个 `pert_id × dose × time` 条件分别取签名中位数；Top10 是这些**条件**中分数最负的 10 行，允许同一药物多个剂量重复入选。因此报告把它简写成“药物 Top10”会误导。
- 最终研究报告所写算法交集 3/10、5/10、0/10，没有对应的签名级或条件级保存表/manifest；现存 Exp008 表是 1/10、2/10、4/10。最可能的口径差异是用了不同版本/统计单位/筛选或聚合，但证据不足以断定具体来源。应标为不可复现的报告冲突，而不是选择更好看的数字。
- 本轮未对 5,861 条签名重算三个非 WTCS 算法，故**当前正式 M0 的四算法对照尚未完成**。冻结的 Exp008 表只可作为旧版本同数据内比较的历史参照。

### 2.3 重复与质量审计

十个正式主条件全是单个 Level 5 consensus signature；其底层通常 3 个实例/板，doxorubicin 为 2 个，均不能视为独立生物学研究。主条件 CC q75 / 底层实例数分别为：ponatinib .63/3、mocetinostat .74/3、MK-2461 .60/3、doxorubicin .58/2、rebastinib .77/3、PHA-767491 .69/3、iniparib .42/3、balaglitazone .28/3、PFI-1 .60/3、JNJ-26481585 .83/3。Balaglitazone 只略高于门槛；iniparib 另有一条 CC=.18 的主条件 LJP008 签名被排除，正式计分使用 REP.A005 的 CC=.42 签名。

## 3. 置换统计审计与重算规格

历史 Exp008 使用 2,000 个共享随机 BING UP/DOWN 基因集（B200 各 100 个、上下调不重叠），对每个药物-剂量-时间 WTCS 中位数作单侧下尾经验 P，并对当时 3,715 个条件作 BH。

| 正式 Top10 的主剂量 | 与历史观察 WTCS 精确匹配 | 历史 P / BH q | 当前解释 |
|---|---:|---|---|
| Ponatinib、mocetinostat、doxorubicin、iniparib、balaglitazone | 是，差值 0 | 各 P=.00049975、q=.0039334 | 观察值可对上历史；P 在 1/2001 的分辨率下限。历史 q 的检验家族/旧签名全集口径不等同当前正式 M0 家族，不能写成当前统一 FDR。 |
| MK-2461、rebastinib、PHA-767491、PFI-1、JNJ-26481585 | 无同剂量历史匹配 | 缺失 | **无可对齐历史统计**，不是 P 不显著，也不是实验阴性。 |

Exp013/014 后的正式置换重算建议（另立版本，不覆盖 Exp008）：固定 M0 与 M1 各自的 S1 查询，按冻结的 5,861 签名 stable-ID/QC 集重算 10 μM 条件；每个查询用预注册随机种子和至少 10,000 次匹配大小的 BING 不重叠 UP/DOWN 抽样；零模型须说明是否按表达量/方差匹配，并对**同一预设候选检验家族**统一 BH。报告 raw WTCS、P、q、置换分辨率与零模型；不得把随机基因集 P 称为 CMap NCS/Tau。统计家族应在计算前锁定（建议正式主剂量所有 1,032 个药物条件，而不是只校正看完后挑出的 Top10）。

## 4. 历史实验与新实验的对应关系

| 已有实验 | 已回答的问题 | 新轮处理 |
|---|---|---|
| Exp006 | A/B 排序、剂量和 QC 稳定等级；Top50 多数签名支持少 | 不重复；作为问题基线，保留其稳定等级与剂量限制 |
| Exp007 | S1 基因集规模改变时排序变化 | 不重复旧敏感性；Exp013 改为患者抽样不确定性下的稳定特征 M1，与原 M0 同签名集比较 |
| Exp008 | 4,761 历史签名上的 WTCS/Classic KS/Zhang/XSum 及随机基因集零模型 | 不重做历史；新一轮补齐 5,861 正式 stable-ID M0/M1 的同口径算法基线及统一置换统计 |
| Exp009 | LINCS CC/TAS/QC 阈值敏感性、稳定 ID 合并问题 | 不重复阈值实验；保留 Q2 CC≥.2 为 M0，沿用逐签名 QC 元数据 |
| Exp010 | 一个 14 对 ER+ 患者外部队列的 S1 复现 | 不重复 GSE139038；Exp015 外部验证使用未参加建模/选参的新独立队列，或新实验批次 |
| Exp011 | PRISM 细胞敏感性与 S2 排名、ER+ 特异性 | 不重复 PRISM 汇总；Exp015 做预注册、ER+ 多模型湿实验验证 |
| Final05 | 对 Final Top10 的 Level 5、置换交叉核对、机制/证据缺口审计 | 作为基线审计来源，不覆盖；本报告补四算法口径冲突及 Exp013–015 前瞻方案 |

## 5. Top10 逐候选证据缺口

“无数据/未映射”与“有数据但不支持”分开写。外部 S1 与 PRISM 只覆盖 5/10，未覆盖者不是阴性结果。

| Drug | 10 μM WTCS / CC / dose-negative | Exp010 外部 S1 | Exp011 PRISM ER+ | KG/机制当前缺口 |
|---|---|---|---|---|
| Ponatinib | -.5167 / .63 / 1/5 | rank 125，非 Top10；一条签名 | 有，9 条 ER+ 线 | 已映射；21 条直接靶点断言、131 条靶点-通路路径；断言不等于抑制/靶点占有 |
| Mocetinostat | -.5059 / .74 / 4/6 | rank 26，非 Top10 | 有，9 条 ER+ 线 | 已映射；5 靶点断言、37 条路径；未在 ER+ 实验验证 |
| MK-2461 | -.4841 / .60 / 2/5 | 无精确结构匹配的外部分数 | 无匹配 PRISM ER+ 观察 | 当前图谱无精确药物节点；不是阴性药效证据 |
| Doxorubicin | -.4672 / .58 / 5/6 | rank 352 | 有，9 条 ER+ 线 | 有映射/机制路径；已有乳腺癌用药背景，广谱细胞毒/应激可驱动逆转分数，不应包装为新发现 |
| Rebastinib | -.4578 / .77 / 3/6 | 无精确匹配 | 无匹配 PRISM ER+ 观察 | 当前图谱无精确药物节点 |
| PHA-767491 | -.4564 / .69 / 1/6 | 无精确匹配 | 无匹配 PRISM ER+ 观察 | 当前图谱无精确药物节点；剂量方向支持弱 |
| Iniparib | -.4553 / .42 / 3/4 | rank 155 | 有，9 条 ER+ 线 | 有映射但仅 1 条直接靶点断言；不可解释为已验证 PARP 抑制剂，机制存在反证 |
| Balaglitazone | -.4527 / .28 / 1/3 | rank 40 | 有，9 条 ER+ 线 | 有映射；CC 接近门槛，当前作用/ER+ 机制仍是假设 |
| PFI-1 | -.4514 / .60 / 3/4 | 无精确匹配 | 无匹配 PRISM ER+ 观察 | 当前图谱无精确药物节点 |
| JNJ-26481585 | -.4466 / .83 / 6/6 | 无精确匹配 | 无匹配 PRISM ER+ 观察 | 当前图谱无精确药物节点；剂量方向支持最好，但仍只有一个主条件 consensus signature |

Top10 共有缺口：每药主剂量仅一条共识签名；没有当前正式 5,861 签名版本的统一四算法比较与统一置换检验；仅单一 LINCS 细胞系/时间用于主榜；PRISM 排名相关性在 Top50 层面不明确（ρ=.260，95% CI [-.105,.573]），ER+−TNBC 敏感性差为负（-.327，95% CI [-.517,-.145]）；均无本项目 ER+ 湿实验靶点结合/剂量反应验证。

## 6. Exp013：Bootstrap 稳定疾病特征（M0 vs M1）

### 目标与边界

估计 GSE42568 患者抽样变化对 S1 特征选择的影响，形成与固定原 S1（M0）可并排复现的 Bootstrap 稳定 S1（M1）。Bootstrap 重抽样来自同一队列，衡量内部抽样稳定性，**不是独立外部验证**。

### 预注册设计

1. **冻结 M0**：以原始 GSE42568 表达矩阵、样本注释、归一化/limma 模型、基因 ID 映射、BING 映射和 FDR<.05 规则为不可变输入；记录 SHA-256、软件版本、design/contrast、完整 limma 表、原来的 Top100 UP/DOWN 文件。M0 复现核验通过前不生成 M1。
2. **抽样单位**：患者/样本，不对基因逐个抽样。ER+ tumor 与正常组分别有放回抽样，维持 67/17 组大小；若实际样本有配对/批次结构，先依据原设计确认抽样层级，按患者整体重抽并保留配对关系，不拆样本对。
3. **重复次数**：正式建议 B=2,000；固定并记录随机种子。仅在方案批准后运行。本轮不启动。
4. **每次拟合**：沿用 M0 的表达预处理、limma 设计/对比和 BING 背景；记录各基因 logFC、方向、FDR、方向排名。不得在每次 bootstrap 中更改基因空间或筛选规则。
5. **M1 稳定特征**：以 M0 显著且映射到 BING 的基因为候选母集；分别记录 bootstrap 中同方向概率和进入该方向前 100 名的频率。预注册主门槛：同方向概率≥0.90 且 top100 入选频率≥0.80；不够 100 个就保留实际数量，**不拿不稳定/不显著基因补齐**。门槛敏感性只作预先列出的附表，不挑最优门槛重排。
6. **M0/M1 对照**：M0 和 M1 使用同一份冻结的 5,861 LINCS 签名、同一 QC/剂量/ID 和 WTCS 实现；M1 UP/DOWN 可不等长，必须报告有效基因数、重合与方向一致性。相同 10 μM 规则和 pert_id 聚合。输出 M0/M1 的基因选择稳定率、药物分数差、rank correlation、TopK overlap 与每药 bootstrap-derived rank uncertainty。
7. **不确定性**：外层患者 bootstrap 抽样应重新拟合 S1 并重算对应 WTCS，产生药物分数/排名区间；若只在固定 M1 上重新抽基因或只对已有 WTCS 抽样，不能声称包含 S1 患者不确定性。缺失签名仍记缺失，不插补。

### 成功/失败标准

- 技术成功：M0 文件哈希和复现 WTCS 通过；预注册 bootstrap 次数完成；同 seed 可复现；每次样本组成、收敛/模型失败和 gene mapping 均有日志。
- 科学支持 M1 稳定性的结果：M1 达到预设基因门槛，M0/M1 药物 rank correlation 与 TopK overlap 的 bootstrap 区间满足事先设定的可接受范围，且结论不由单一重抽样/单签名驱动。具体容忍边界须在运行前冻结（建议 rank ρ≥.7 且 Top10 Jaccard 中位数≥.5 作为项目决策门槛，不是领域通用标准）。
- 不支持/不确定：M1 某一方向稳定基因过少、bootstrap 区间宽、M0/M1 排名明显分离，或某个候选在多数 bootstrap 中不入前列。结论写“稳定性不足/结果不确定”，不得填补基因、候选或改阈值直到相似。
- 数据/计算失败：M0 哈希不一致、模型设计错误、样本/对比编码不可复现，先停，不发布 M1。

## 7. Exp014：两条独立改进路线

### Route A：多剂量一致性评价

- 目的：评价一个药物在真实观测剂量上的表达逆转方向是否一致；不是剂量反应/效力曲线，也不是独立重复研究。
- 对每个 pert_id，限定 MCF7、24 h、CC≥.2 的现有真实 Level 5 签名；按 dose 分层，先在同一精确剂量内汇总实际有的签名中位数，保留签名数、实例数、CC/TAS 与系列/板信息。剂量间绝不把同一个药的重复签名伪作独立 N。
- 预注册分类：至少 3 个不同 QC 合格剂量且 ≥2 个剂量 WTCS 中位数为负，报告负向剂量比例、跨剂量中位数/范围与变号；少于 3 剂量为“剂量数据不足”，不是“未通过”；≥3 剂量但负向比例/方向门槛不满足为“有数据但一致性不支持”。不按最佳剂量挑分，不将剂量点当生物学重复计算显著性。
- 如未来要声称剂量效应，需要新独立实验的浓度反应设计、重复批次及细胞毒性窗口；已有 LINCS 浓度点仅用于一致性描述。

### Route B：跨预设分析的共识排序

- 先完成 Exp013，再在固定 LINCS 5,861 签名和相同 10 μM/聚合下计算 M0、M1 × WTCS、Classic KS、Zhang、XSum；Zhang/XSum 明确为 COMPZ 适配实现，不冒称原论文 raw-logFC 复刻。每个药按分析版本计算 percentile rank；预注册中位 percentile rank / Borda 类名次作为**描述性共识排序**，同时公布每个方法/版本排名、有效覆盖数、TopK selection frequency、分歧与名次区间。
- 方法/基因集变化是相关的分析视角，不是独立实验、独立 P 值或重复数；共识 rank 不制造显著性。设置最小覆盖要求（建议至少 6/8 分析组合有真实结果），缺失组合不填 0、不按倒数排名补齐；未达覆盖为“无足够数据”，低共识为“有结果但不支持稳健入选”。
- WTCS 主分析不得被共识排序静默取代；M0 是冻结基线，M1/共识为改进路线，分别出榜，不覆盖原正式 Top10。

## 8. Exp015 与独立验证设计

### Exp015：前瞻、独立 ER+ 细胞验证

- **候选选择**：待 Exp013/014 完成后按预注册规则选稳定共识候选；至少含 2 个模型支持的候选、1 个当前不稳定候选作为负/挑战候选、doxorubicin 已知乳腺癌药作为 assay comparator，不将其当新发现。Fulvestrant 可作 ER 通路 assay control；vehicle 为阴性对照。
- **模型**：至少 3 个 ER+ 乳腺癌细胞模型（如 MCF7、T47D、ZR-75-1，先核验模型身份和培养条件）；ER−/TNBC 模型作亚型对照；MCF10A 等非肿瘤乳腺上皮模型作选择性/毒性对照。至少 3 次独立实验日生物重复，板内随机化，盲化样本标签/分析。
- **剂量与时间**：以预实验确定可溶、覆盖无效至有效的浓度范围；分层剂量曲线、固定时间测 viability/growth；另取不引起明显细胞毒的早期剂量/时间点测 RNA（RNA-seq 或经验证 panel），不得用高细胞死亡时的广泛应激假称逆转。
- **主要终点**：预先指定 ER+ 多模型的浓度-反应 AUC/GR metrics 及相对 MCF10A/TNBC 的选择性对比；其次是非细胞毒窗口的 M1 signature reversal score；靶点 engagement/pathway marker 作为机制终点。
- **成功**：assay controls 通过；独立实验日方向可重复；候选在至少 2/3 ER+ 模型有剂量相关表型，主要效应 CI 排除无效界值；非肿瘤细胞/ER− 对照显示预设的选择性；非细胞毒剂量下表达变化与预测 M1 方向一致且不是单批驱动；若主张机制，还需靶点 engagement/功能依赖支持。
- **失败/不支持**：可评估剂量范围内无可重复剂量反应；仅在泛细胞毒高剂量出现信号；M1 表达逆转在独立重复中方向不一致；ER+ 未较对照显示预注册的选择性；靶点机制与数据相反。阳性/阴性对照失效或药物溶解/暴露失败属于 assay invalid/不可判定，不记作生物学阴性。
- 数值效应界值、主要细胞系、候选名单和多重检验校正规则必须在开实验前按 assay 变异度和预实验冻结；不可事后挑选最有利模型/剂量。

### 独立验证（与训练/选择分离）

1. **患者队列外部复现**：Exp010 的 GSE139038 及其 14 对样本视为已用数据，不能再叫独立验证。预先指定至少两个未用于 M0/M1、参数选取或候选挑选的 ER+ tumor/normal 队列；分别做 cohort-specific normalization/DE，冻结映射与方向规则，再比较签名方向、M1 gene inclusion、M0/M1 drug rank。报告样本数、平台、ER 状态、缺失率与每队列结果，不混合原始平台表达。
2. **盲法锁榜**：冻结 Exp013/014 候选和阈值后才解盲外部队列/Exp015；外部失败不得反向改训练参数后仍称验证通过。记录所有候选，包括未测、化合物身份无法精确匹配、测过但无效三种状态。
3. **总体成功**：队列间方向/效应区间可重复，预注册的药物 shortlist 在外部排序上达到事先指定一致性，且 Exp015 主要表型和表达终点在至少两个 ER+ 模型重复。若外部队列不足样本、结构匹配失败或实验 assay invalid，则结论为不可判定，不算成功也不算失败。

## 9. 产物与执行门槛

本方案只新增准备文档；所有历史结果保持原位、只读。下一步运行 Exp013 前需确认 GSE42568 原始/规范化表达矩阵和样本级注释的实际路径及配对结构；Exp014 需先正式冻结四算法同版本实现/单位和缺失值规则；Exp015 需先批准候选、细胞模型、主要终点与效应阈值。未达到这些门槛前，不启动大规模计算或湿实验，也不更新正式 Top10。

## 10. 关键审计来源

- `experiments/final_results/results/final_data_manifest.json`
- `experiments/final_results/reports/final_top10_selection_report.md`
- `experiments/final_results/final05_scientific_audit/reports/final05_scientific_audit_report.md`
- `experiments/final_results/final05_scientific_audit/results/signature_level_audit.csv`
- `experiments/final_results/final05_scientific_audit/results/historical_permutation_crosswalk.csv`
- `experiments/exp006_ranking_reliability/reports/exp006_final_report.md`
- `experiments/exp007_signature_sensitivity/reports/exp007_report.md`
- `experiments/exp008_scoring_statistics/reports/exp008_report.md`、`results/method_manifest.json`、`results/algorithm_topk_overlap.csv`、`results/method_comparison.csv`
- `experiments/exp009_lincs_quality/reports/exp009_report.md`
- `experiments/exp010_external_s1/reports/exp010_report.md`
- `experiments/exp011_prism_validation/reports/exp011_report.md`
- `experiments/second_round_summary/reports/second_round_master_report.md`
- `experiments/final_results/reports/final_research_report.md`
