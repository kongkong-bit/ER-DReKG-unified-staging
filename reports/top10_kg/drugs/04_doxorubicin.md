# 04 doxorubicin (BRD-K92093830)

- Formal rank: 4; WTCS=-0.46716938932002616; LINCS condition MCF7, 10.0 um, 24 h; n_signatures=1.
- Identity: matched_exact_inchikey; OptimusKG drug `CHEMBL53463`.
- Candidate conditions retained: 6 separate condition rows.

## Source-supported target assertions

- TOP2A (`ENSG00000131747`): TARGET / DRUG_BANK, INHIBITOR / OPEN_TARGETS; Evidence `5d997674034af750148403cb1ed2dc913d2b6f0494a2d893b0f755a65e480c89`; source record `OptimusKG 3.2:drug_gene:CHEMBL53463:ENSG00000131747`
- NOLC1 (`ENSG00000166197`): TARGET / DRUG_BANK; Evidence `d7c42225a47d3987c1053c62a9efd375f520a19427471d1804afe8b0ab174207`; source record `OptimusKG 3.2:drug_gene:CHEMBL53463:ENSG00000166197`

## S1 pathway intersections

Route rows: 105; distinct pathway IDs: 88.
- C21-steroid hormone metabolic process
- Cell Cycle, Mitotic
- DNA conformation change
- DNA duplex unwinding
- DNA geometric change
- DNA recombination
- Fatty acid metabolism
- HALLMARK_ADIPOGENESIS
- HALLMARK_E2F_TARGETS
- HALLMARK_ESTROGEN_RESPONSE_LATE
- HALLMARK_G2M_CHECKPOINT
- HALLMARK_MITOTIC_SPINDLE
- HALLMARK_MYC_TARGETS_V1
- HALLMARK_MYC_TARGETS_V2
- HALLMARK_OXIDATIVE_PHOSPHORYLATION
- HALLMARK_REACTIVE_OXYGEN_SPECIES_PATHWAY
- HALLMARK_XENOBIOTIC_METABOLISM
- Metabolism of amino acids and derivatives
- Metabolism of vitamins and cofactors
- Rho protein signal transduction
- SUMO E3 ligases SUMOylate target proteins
- SUMOylation
- SUMOylation of DNA replication proteins
- Signaling by Retinoic Acid
- alcohol metabolic process
- carboxylic acid biosynthetic process
- cellular aldehyde metabolic process
- cellular ketone metabolic process
- cellular lipid catabolic process
- cellular response to ketone
- cellular response to nutrient levels
- chemotaxis
- chromosome condensation
- chromosome segregation
- detoxification
- diterpenoid metabolic process
- fatty acid biosynthetic process
- fatty acid metabolic process
- hormone metabolic process
- isoprenoid metabolic process
- lipid catabolic process
- meiotic cell cycle
- meiotic cell cycle process
- mitochondrial fission
- mitochondrion organization
- monocarboxylic acid biosynthetic process
- negative regulation of chromosome organization
- nitric oxide biosynthetic process
- nitric oxide metabolic process
- nuclear chromosome segregation
- nuclear division
- nucleotide metabolic process
- olefinic compound metabolic process
- organelle fission
- organic acid biosynthetic process
- phosphatidylinositol 3-kinase/protein kinase B signal transduction
- positive regulation of phosphate metabolic process
- positive regulation of phosphatidylinositol 3-kinase/protein kinase B signal transduction
- positive regulation of phosphorus metabolic process
- primary alcohol metabolic process

## Interpretation boundary

A relation is reported using its original assertion type. Enzyme and transporter associations are not silently counted as pharmacologic targets. A target-to-pathway route means the drug-gene and S1 pathway-gene assertions intersect; it does not establish causal modulation, treatment benefit, or ER-positive specificity. WTCS is an expression-reversal ranking signal and is not efficacy evidence.

## ER+ 疾病背景定向文献筛查

- 范围：ER_positive_preclinical；类型：mixed_response；方向：mixed_or_counter_signal。
- 背景：MCF-7 and T47-D with estrogen and doxorubicin
- 整理：Study found estrogen altered molecular responses to doxorubicin in ER-positive cells; low-dose co-treatment showed pro-growth signaling changes and estrogen could modify cytotoxic response.
- 来源：[PMID:22964943](https://pubmed.ncbi.nlm.nih.gov/22964943/)（primary_study）
- 限制：Cell models and specific concentration/schedule; doxorubicin is a cytotoxic comparator, not a novel targeted mechanism or proof of benefit for this candidate ranking.
- 解释边界：这是定向筛查记录，不是系统综述或疗效结论，不据此生成药物—ER+ 疾病图边。
## Exp006–Exp011 历史复核

- Exp006：24 h 合格剂量 6.0 个，历史 WTCS 负向比例 0.8333333333333334；剂量稳定性 `multi_dose_negative`，QC 敏感等级 `low`。
- Exp007：A / B100 / B150 / B200 / B300 / matched125 名次：39.0 / 29.0 / 11.0 / 11.0 / 3.0 / 39.0。
- Exp008：历史 B200 置换经验 P / BH-FDR：0.0004997501249375312 / 0.0039334146486079；Historical Exp008 B200 permutation table (2,000 permutations); NA means this pert_id-condition was not tested there; not recomputed for the corrected 5,861-signature set.
- Exp009 质量阈值复核：available。Exp010 独立 S1：available, rank=352.0, WTCS=-0.42027812726382596。
- Exp011 PRISM：available, ER+ mean=3.1106043918433333, ER− mean=4.002560441606077, ER+−ER−=-0.8919560497627437。
- 限制：这些是已完成的历史分析，不是按本轮冻结签名重算；未匹配或缺少记录不等于阴性结果。PRISM 细胞存活敏感性与 LINCS WTCS 是不同终点。
