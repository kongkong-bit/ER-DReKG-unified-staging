# 疾病关联证据报告

基础 Top 10 bundle 有 1 个项目 DiseaseContext 和 1 个 MONDO:0007254 Disease 节点，二者关系来自项目元数据（ABOUT_DISEASE），本身不是药物治疗 ER+ 乳腺癌的文献证据。现在，逐药人工审查记录会在项目级扩展 bundle 中作为 `DiseaseEvidence` 节点保存，并通过 `HAS_DISEASE_CONTEXT_EVIDENCE` 与候选药物、`CONCERNS_DISEASE` 与疾病节点关联。该结构保留研究亚型/模型、证据类型、方向、来源和限制；不会创建无条件的药物—疾病治疗关系。

初始审计时尚未进行逐药文献证据分级；本轮加入的定向检索初审见下节。它不是穷尽式系统综述，也不能将疾病上下文标签解释为疾病特异疗效支持。

## Top 10 文献证据初审（2026-11-21）

已对十个固定候选做定向 PubMed/PMC/ClinicalTrials.gov 及期刊原始研究检索，逐条记录在 `external_disease_evidence.csv`。该表是逐药证据状态档案，不把“没有检索到”编码成生物学阴性关系，也不自动写入 Drug–Disease 图边。

- **ER+ 前临床相关证据：** ponatinib 在 FGFR1 异常的 ER+ MDA-MB-134 模型中被研究（PMID 22238366）；一篇 2026 年 entinostat 为主的研究在补充图中报告 mocetinostat 对 ER+ 内分泌耐药细胞和 WHIM16 PDX 的实验结果（PMID 42464636；DOI 10.1002/1878-0261.70307）。这些仍是前临床结果，不能推出临床疗效；mocetinostat 的具体证据是该论文的补充结果，不应与主药 entinostat 混为一谈。
- **新增 ERα+ 研究：** Ponatinib 另有一项 PubMed 收录的 ERα 阳性乳腺癌细胞研究，摘要报告 ponatinib 与 tamoxifen 联用的细胞生长抑制结果（PMID 33732370）。当前仅作摘要级人工筛查；精确细胞系和实验细节仍需全文复核，且不能证明冻结 LINCS 条件下的靶点命中或临床疗效。
- **混合或反向信号：** doxorubicin 在 MCF-7/T47-D 研究中显示 estrogen 会改变其细胞反应（PMID 22964943）；iniparib 的 TNBC III 期试验未达到预设共同主要终点，另有研究质疑其作为 bona fide PARP inhibitor 的分类（PMID 25349301、24402426）。这些记录是局限/反证，不是 ER+ 药物疗效结论。
- **亚型不可外推：** PHA-767491 的乳腺癌研究来自 TNBC 模型（PMID 31262335）；rebastinib 的 HER2− 转移性乳腺癌 I 期研究包括混合亚型，报告的是联合治疗和药效学结果，没有 ER+ 特异疗效估计（PMID 39531537）。
- **仅有靶点/药理背景：** MK-2461 的 c-MET 抑制研究、PFI-1 的 BET bromodomain 探针研究、JNJ-26481585 的广谱 HDAC 药理不能单独证明 ER+ 疾病关联。
- **仍为证据缺口：** 对 balaglitazone 的本轮定向检索未找到候选药物特异 ER+ 乳腺癌研究。PPARγ 配体类别或其他分子证据不能代替 balaglitazone 本身的证据。

所有结论保留具体模型、临床/前临床层级和亚型边界；详细记录、PMID/DOI、来源链接及局限见 `external_disease_evidence.csv`。本轮尚未进行穷尽式系统综述，因此 gap 表示“当前定向检索未识别到”，不代表不存在文献。

另已从 NCBI PubMed E-utilities 为冻结的 10 个候选执行七组标题/摘要检索，并缓存既有人工记录所引 PMID 的元数据；规范化快照含 1,314 条候选—PMID 记录。七组查询每组最多返回 100 条；manifest 标出 11 个超过上限的候选查询组，因此该召回快照不完整，也不是筛选后的研究集。未人工筛选的命中不得用于升级等级或生成图边。原始响应、截断明细和 SHA 见 `data/top10_kg/evidence/top10_pubmed_search_manifest.json`。疾病证据表当前 11 条人工记录、覆盖 10 个候选；其中 ponatinib 新记录为摘要级审阅，mocetinostat 新增 PMID 映射并完成全文重点段落复核，注明其药物实验位于 entinostat 为主论文的补充结果。

## 逐药机制证据等级（人工定向审阅）

按方案 8.4 的 A/B/C/U 定义，结合候选靶点药理和以上疾病背景证据，人工审阅结果为 A 级 3 种、B 级 6 种、C 级 1 种、U 级 0 种。等级是机制证据完整度判断，不是疗效概率；没有按图边数量评分。每种药物的 rationale、靶点 Evidence ID、来源记录、PMID/DOI、限制条件和输入 SHA 见 `mechanism_evidence_grade.csv` 与 `mechanism_evidence_grade_manifest.json`。构建命令：`python reports/top10_kg/build_mechanism_evidence_grades.py`。等级由人工规则表维护并对源文件哈希绑定，不是自动文献评审，也未替代系统综述。
