# Final05：Top 10 候选药物科研可靠性审计

## 审计结论

正式 Top 10 顺序保持 Final01–04 冻结版本不变。本轮没有重建知识图谱，没有改写 S1/S2 或原始数据。审计确认：主条件下正式纳入每个候选的计分结果均来自一条 Level 5 共识 Signature；其底层通常由 3 个 L1000 实例、3 个检测板整合而成。它们是同一处理条件下的重复表达谱，不是 3 个独立患者队列或独立研究。

原始元数据中 Top 10 主条件共检出 11 条 Level 5 记录：Iniparib 有两条，其中一条的 `distil_cc_q75=0.18`，低于正式门槛 0.2，未进入正式计分；另一条 `distil_cc_q75=0.42` 纳入。其余候选各有一条主条件记录。10 个正式纳入的主条件签名均与冻结分数表的 sig_id、pert_id、WTCS 对齐。

各候选 24 小时可评分剂量条件共 51 个。只有 doxorubicin 5/6、mocetinostat 4/6、JNJ-26481585 6/6 的条件 WTCS 为负；ponatinib 仅 1/5。其余候选也存在符号变化或零分。剂量间变化说明排序依赖处理条件，不构成独立批次重复。对这 10 个扰动药物，GSE70138 MCF7 trt_cp 元数据仅见 24 小时；本轮没有替其他时间重算 WTCS，因此不把时间外推当作支持证据。

## 主条件 Signature 与 QC

主条件：MCF7、`trt_cp`、24 h、10.0 μM；评分输入为现有 BING Top100 UP/DOWN 正式结果。`distil_nsample` 与 `distil_id` 均用于核对底层实例，并与 `inst_info` 中实例/检测板对齐。

| 排名 | 药物 | sig_id | WTCS | CC q75 | TAS | 底层实例 | 平台板数 | 是否通过正式评分 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | ponatinib | LJP009_MCF7_24H:E19 | -0.516654 | 0.63 | 0.54376 | 3 | 3 | 是 |
| 2 | mocetinostat | LJP008_MCF7_24H:I07 | -0.505900 | 0.74 | 0.600766 | 3 | 3 | 是 |
| 3 | MK-2461 | REP.A015_MCF7_24H:D19 | -0.484092 | 0.6 | 0.530655 | 3 | 3 | 是 |
| 4 | doxorubicin | REP.A026_MCF7_24H:L19 | -0.467169 | 0.58 | 0.616557 | 2 | 2 | 是 |
| 5 | rebastinib | LJP007_MCF7_24H:I19 | -0.457846 | 0.77 | 0.73008 | 3 | 3 | 是 |
| 6 | PHA-767491 | LJP007_MCF7_24H:J01 | -0.456419 | 0.69 | 0.639689 | 3 | 3 | 是 |
| 7 | iniparib | LJP008_MCF7_24H:C07 | NA (QC excluded) | 0.18 | 0.129416 | 3 | 3 | 否：CC q75 < 0.2 |
| 7 | iniparib | REP.A005_MCF7_24H:P01 | -0.455273 | 0.42 | 0.529961 | 3 | 3 | 是 |
| 8 | balaglitazone | REP.A012_MCF7_24H:B07 | -0.452738 | 0.28 | 0.219313 | 3 | 3 | 是 |
| 9 | PFI-1 | LJP008_MCF7_24H:G01 | -0.451376 | 0.6 | 0.453345 | 3 | 3 | 是 |
| 10 | JNJ-26481585 | REP.A021_MCF7_24H:J07 | -0.446602 | 0.83 | 0.773507 | 3 | 3 | 是 |

说明：Iniparib 的 QC 未通过记录仍保留在表中，WTCS 留空表示未进入正式评分，并非零分。其余数值只代表表达逆转关联。WTCS 更负不等于临床疗效更强。

## 跨剂量和处理条件支持

| 排名 | 药物 | 24h剂量条件数 | WTCS<0 条件 | 分数范围 |
| --- | --- | --- | --- | --- |
| 1 | ponatinib | 5 | 1/5 | -0.517 to 0.332 |
| 2 | mocetinostat | 6 | 4/6 | -0.506 to 0.429 |
| 3 | MK-2461 | 5 | 2/5 | -0.484 to 0.276 |
| 4 | doxorubicin | 6 | 5/6 | -0.467 to 0.000 |
| 5 | rebastinib | 6 | 3/6 | -0.458 to 0.000 |
| 6 | PHA-767491 | 6 | 1/6 | -0.456 to 0.271 |
| 7 | iniparib | 4 | 3/4 | -0.455 to 0.282 |
| 8 | balaglitazone | 3 | 1/3 | -0.453 to 0.000 |
| 9 | PFI-1 | 4 | 3/4 | -0.451 to 0.000 |
| 10 | JNJ-26481585 | 6 | 6/6 | -0.468 to -0.366 |

没有把不同剂量简单平均，也没有为每个药物挑选最有利剂量。主排名沿用固定统一条件。跨剂量统计是稳定性描述，不是重复实验显著性。原始 24 h 元数据共有 66 条候选签名，其中 53 条进入正式评分，13 条未纳入；6 个药物剂量条件出现多个实验系列记录。多系列记录均来自 Iniparib 的 LJP008 与 REP.A005 两组：0.37 μM 和 3.33 μM 两组均有通过 QC 的 Signature，但 WTCS 方向彼此相反；10.0 μM 中 LJP008 记录因 CC q75=0.18 被排除，REP.A005 记录进入主评分。该批次对照显示其逆转信号并不一致。逐剂量 QC 排除和系列信息见 `results/dose_metadata_qc_audit.csv`；逐条真实签名分数见 `results/all_candidate_signature_audit.csv`。详细逐剂量汇总见 `results/dose_batch_support.csv` 和 `results/time_metadata_coverage.csv`。

## 经验 P 值与多重检验

旧 Exp008 B200 输出进行过 2,000 次置换。本次逐项与当前冻结 WTCS 对齐后，仅 5 个药物的主条件有相同观察分数并可报告其历史经验 P/FDR；其余药物为 NA，不能补造。历史可对齐的 5 项经验 p 均为 0.0005、BH FDR 均为 0.003933，p 值受 2,000 次置换分辨率限制。这些数值来自旧实验文件，不是本轮针对全体最终候选重新计算的统计检验；不能当作对全部 Top 10 的统一显著性证明。

| 排名 | 药物 | empirical p | BH FDR | 范围 |
| --- | --- | --- | --- | --- |
| 1 | ponatinib | 0.00049975 | 0.00393341 | 历史 B200；当前 WTCS 一致 |
| 2 | mocetinostat | 0.00049975 | 0.00393341 | 历史 B200；当前 WTCS 一致 |
| 3 | MK-2461 | NA | NA | 未找到可比历史置换结果 |
| 4 | doxorubicin | 0.00049975 | 0.00393341 | 历史 B200；当前 WTCS 一致 |
| 5 | rebastinib | NA | NA | 未找到可比历史置换结果 |
| 6 | PHA-767491 | NA | NA | 未找到可比历史置换结果 |
| 7 | iniparib | 0.00049975 | 0.00393341 | 历史 B200；当前 WTCS 一致 |
| 8 | balaglitazone | 0.00049975 | 0.00393341 | 历史 B200；当前 WTCS 一致 |
| 9 | PFI-1 | NA | NA | 未找到可比历史置换结果 |
| 10 | JNJ-26481585 | NA | NA | 未找到可比历史置换结果 |

## 五个原图谱未精确映射药物的身份复核

使用 LINCS `pert_id` 对应的原始 `pert_info` InChIKey，与 PubChem 结构记录逐项比较；5/5 InChIKey 精确相同，并记录 PubChem CID、ChEMBL ID 和来源 URL。没有使用模糊名称匹配。这解决的是化合物身份交叉引用，不会自动创建或修改 Neo4j Drug 节点；当前图谱映射仍未覆盖这 5 个实体。

| 药物 | LINCS pert_id | PubChem CID | ChEMBL | InChIKey 精确一致 | 现有 KG 映射 | 外部来源 |
| --- | --- | --- | --- | --- | --- | --- |
| MK-2461 | BRD-K56405753 | 44137946 | CHEMBL1802916 | 是 | no exact InChIKey node in current graph | [PubChem](https://pubchem.ncbi.nlm.nih.gov/summary/summary.cgi?cid=44137946) |
| rebastinib | BRD-K76694128 | 25066467 | CHEMBL1738757 | 是 | no exact InChIKey node in current graph | [PubChem](https://pubchem.ncbi.nlm.nih.gov/compound/25066467) |
| PHA-767491 | BRD-K50000283 | 11715767 | CHEMBL225519 | 是 | no exact InChIKey node in current graph | [PubChem](https://pubchem.ncbi.nlm.nih.gov/compound/11715767) |
| PFI-1 | BRD-K13094524 | 71271629 | CHEMBL2179387 | 是 | no exact InChIKey node in current graph | [PubChem](https://pubchem.ncbi.nlm.nih.gov/summary/summary.cgi?cid=71271629) |
| JNJ-26481585 / quisinostat | BRD-K83837640 | 11538455 | CHEMBL2105763 | 是 | no exact InChIKey node in current graph | [PubChem](https://pubchem.ncbi.nlm.nih.gov/compound/11538455) |

逐项来源链接见 `results/unmapped_drug_identifier_audit.csv`。尤其 MK-2461 PubChem 同义词记录还包含 LINCS BRD 编号，其他候选也以原始 LINCS InChIKey 与 PubChem InChIKey 作结构级核对。

## 药理机制、适应证与反证

| 药物 | 作用类型 | 适应证 / 研究状态 | 本项目解释限制 | 来源 |
| --- | --- | --- | --- | --- |
| ponatinib | Multikinase inhibitor including BCR::ABL1 | FDA-approved for specified Ph+ ALL/CML settings; no breast cancer indication in cited label | Candidate breast cancer mechanism remains hypothetical; label carries serious vascular, cardiac and hepatic warnings | [来源 1](https://www.accessdata.fda.gov/drugsatfda_docs/label/2025/203469s038lbl.pdf) |
| mocetinostat | Class I HDAC1/2/3 inhibitor; exact antitumor mechanism not fully defined | Investigational/clinical study agent; not an approved breast cancer treatment | Epigenetic mechanism is a hypothesis and was not validated in this ER-positive project | [来源 1](https://www.cancer.gov/publications/dictionaries/cancer-drug/def/mocetinostat) |
| MK-2461 | Multikinase inhibitor with preference for activated/phosphorylated c-MET | Investigational compound tested in first-in-human phase I advanced solid tumor studies; no approved breast cancer use | Requires evidence of MET dependence/activation; WTCS cannot establish target dependence | [来源 1](https://ascopubs.org/doi/10.1200/jco.2008.26.15_suppl.14657) [来源 2](https://pubmed.ncbi.nlm.nih.gov/20145145/) |
| doxorubicin | Anthracycline DNA intercalator / topoisomerase II inhibitor | Used in adjuvant and metastatic breast cancer treatment | Expression reversal may reflect broad cytotoxic stress; ranking is not ER-positive-specific efficacy evidence | [来源 1](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=36924f82-6c05-4989-9f41-a398c0ad48e6) |
| rebastinib | Multikinase inhibitor (BCR-ABL, SRC family, TIE2, VEGFR2, among others) | Investigational/development agent; no approved breast cancer indication | Angiogenesis/kinase mechanisms require target and model validation | [来源 1](https://www.cancer.gov/publications/dictionaries/cancer-drug/def/rebastinib-tosylate) |
| PHA-767491 | CDC7 inhibitor with additional CDK9 inhibitory activity | Research/preclinical compound; no approved breast cancer indication | Replication-initiation/transcription mechanism is biologically testable, but current S2 stability is weak | [来源 1](https://pubmed.ncbi.nlm.nih.gov/21768328/) |
| iniparib | Should not be interpreted as a bona fide PARP inhibitor; studies report little/no intact-cell PARP inhibition and possible nonspecific reactivity | Developed and trialed under a PARP inhibitor premise; phase III metastatic TNBC trial did not meet coprimary PFS/OS endpoints | If KG shows a PARP1-drug edge, it does not prove PARP inhibition; mark as mechanistically contradicted/uncertain | [来源 1](https://pubmed.ncbi.nlm.nih.gov/22291137/) [来源 2](https://pubmed.ncbi.nlm.nih.gov/25349301/) |
| balaglitazone | PPAR-gamma partial agonist | Investigational glucose-lowering candidate studied in type 2 diabetes | PPAR-gamma/breast cancer relationship is a testable hypothesis, not validated here | [来源 1](https://pubmed.ncbi.nlm.nih.gov/21328517/) |
| PFI-1 | Selective BET bromodomain chemical probe/inhibitor | Research chemical probe; not an approved anticancer medicine | BET transcriptional regulation is a hypothesis; target engagement and cell dependence remain to be tested | [来源 1](https://pubmed.ncbi.nlm.nih.gov/23576556/) |
| JNJ-26481585 | Pan-HDAC inhibitor (quisinostat) | Investigational/clinical-study agent; PubChem summary lists lymphoma, MDS and other studies | HDAC inhibition and expression reversal do not establish an ER-positive-specific mechanism | [来源 1](https://pubchem.ncbi.nlm.nih.gov/compound/11538455) |

**Doxorubicin** 已有乳腺癌辅助及转移性治疗用途，因此应作为已知治疗药/实验阳性比较对象，不应描述成项目新发现的乳腺癌药物。它的强逆转分数可能包含广谱细胞毒与应激成分，也不提供 ER 阳性特异性证据。

**Iniparib** 不应继续标注成确证的 PARP 抑制剂。研究显示其在完整细胞中对 PARP 活性几乎没有抑制，且高浓度细胞杀伤不支持 PARP 抑制机制。图谱中的 PARP1 关联（如有）只是一条数据库断言，不能自动解释为药物抑制 PARP1。

其余候选的药理类别与来源链接在 CSV 中逐药记录。图谱中的 Drug–Gene 断言不总是抑制关系，数量多也不等同于更强机制证据；路径行数可能来自共享通路/多条证据，不作为独立实验重复计数。

## 分项证据等级（不合并成疗效概率）

| 证据维度 | 本轮判定 |
|---|---|
| 表达逆转 | 主条件有强负 WTCS 的计算信号，但每个药物只有一个纳入的共识签名；剂量稳定性总体有限。 |
| 独立 S1 队列 | Exp010 外部 S1 同条件结果仅 5/10 可用，整体排序 Spearman=0.544，Top10 只重合 1/10；单候选外部也只有一条 Signature。 |
| 独立药物敏感性 | Exp011 PRISM ER+ 结果只覆盖 5/10。已有 Top50 S2–PRISM 秩相关为 rho=0.260，95% CI [-0.105, 0.573]，未显示明确相关；PRISM 是细胞活力观察，不是临床获益。 |
| 已知靶点 | 现有 KG 对 5/10 有精确化合物映射。断言仍需区分抑制、结合、转运或其他关系类型。另 5 个外部化合物身份已精确核实，但未改图谱。 |
| 疾病相关通路 | 5 个已映射药物具有图谱靶点到 S1 通路关联；这属于间接机制线索，不证明因果。 |
| 机制假设 | 全部尚未在 ER+ 乳腺癌实验模型中验证，不构成治疗机制或疗效结论。 |

每个候选的分项描述见 `results/evidence_grade_matrix.csv`。这些维度不相加，不换算成未经验证的“有效概率”。

## 建议后续优先验证

正式 Top10 不变。若进入实验验证，建议将 **mocetinostat** 作为探索性机制验证优先项（仍需靶点占有、剂量重复和 ER+ 模型验证）；**JNJ-26481585 / quisinostat** 可作为表达稳定性追踪候选（观察到的 6/6 个 24 h 剂量条件 WTCS 为负），但缺少当前 KG 与 PRISM 支持，且每条件仍只有一个合格共识签名；**ponatinib** 可作为次级假设，但主条件虽排第 1，只有 1/5 的 24 h 剂量条件 WTCS 为负。**Doxorubicin** 更适合作为已知乳腺癌药物的实验比较/阳性对照，不能作为新重定位发现。此建议是透明的验证顺序，不是重新排名或药效判断。

## 尚缺证据与局限

1. Top10 的正式主条件几乎都是单个 Level 5 共识 Signature；重复实例有助于形成共识质量，但不能代替独立实验批次、独立细胞模型或患者样本重复。
2. 历史置换统计只在部分候选上与当前 WTCS 精确对齐，其他候选没有当前版本统一重算的经验 P/FDR。
3. PRISM 覆盖不足且整体相关性未证明表达逆转分数可以预测细胞敏感性；PRISM 也不等同于乳腺癌患者结局。
4. 对没有精确图谱实体的 5 个候选，身份映射已解决但图谱机制覆盖仍缺失；这轮遵循要求未重建图谱。
5. 没有对候选在 ER+ 乳腺癌模型中做靶点结合、功能扰动、剂量反应、细胞选择性或动物实验。因此 Top10 仍是待验证计算候选，而不是药物推荐。

## 复现与文件

审计脚本：`scripts/run_final05_audit.py`。原始输入与输出 SHA-256、固定条件、来源链接记录在 `final05_manifest.json`。逐签名、逐剂量、身份映射、机制与分项证据 CSV 均保存在 `results/`。正式 `results/final_top10.csv` 未修改。
