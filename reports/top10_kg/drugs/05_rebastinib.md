# 05 rebastinib (BRD-K76694128)

- Formal rank: 5; WTCS=-0.4578457223071144; LINCS condition MCF7, 10.0 um, 24 h; n_signatures=1.
- Identity: matched_exact_inchikey; OptimusKG drug `CHEMBL1738757`.
- Candidate conditions retained: 6 separate condition rows.

## Source-supported target assertions

- ABL1 (`ENSG00000097007`): INHIBITOR / OPEN_TARGETS; Evidence `aeb6a673dcdf95f1e7925487f9faded53cca246ac34bf56acaa28797c7bb31b0`; source record `OptimusKG 3.2:drug_gene:CHEMBL1738757:ENSG00000097007`

## S1 pathway intersections

Route rows: 0; distinct pathway IDs: 0.
No target-to-S1 enriched pathway route in this bundle.

## Interpretation boundary

A relation is reported using its original assertion type. Enzyme and transporter associations are not silently counted as pharmacologic targets. A target-to-pathway route means the drug-gene and S1 pathway-gene assertions intersect; it does not establish causal modulation, treatment benefit, or ER-positive specificity. WTCS is an expression-reversal ranking signal and is not efficacy evidence.

## ER+ 疾病背景定向文献筛查

- 范围：HER2_negative_mixed_subtype_clinical；类型：trial_context；方向：mixed_subtype_clinical_context。
- 背景：Phase Ib rebastinib plus paclitaxel or eribulin in metastatic breast cancer
- 整理：Phase Ib trial enrolled HER2-negative metastatic breast-cancer patients and reported pharmacodynamic evidence consistent with TIE2 inhibition; HR-positive patients could be eligible, while the described individual response was in TNBC.
- 来源：[PMID:39531537](https://pubmed.ncbi.nlm.nih.gov/39531537/)（primary_clinical_study）
- 限制：Combination trial; no ER-positive-specific efficacy estimate or randomized efficacy conclusion.
- 解释边界：这是定向筛查记录，不是系统综述或疗效结论，不据此生成药物—ER+ 疾病图边。
## Exp006–Exp011 历史复核

- Exp006：24 h 合格剂量 未记录 个，历史 WTCS 负向比例 未记录；剂量稳定性 `无候选记录`，QC 敏感等级 `未记录`。
- Exp007：A / B100 / B150 / B200 / B300 / matched125 名次：NA / NA / NA / NA / NA / NA。
- Exp008：历史 B200 置换经验 P / BH-FDR：NA / NA；Historical Exp008 B200 permutation table (2,000 permutations); NA means this pert_id-condition was not tested there; not recomputed for the corrected 5,861-signature set.
- Exp009 质量阈值复核：not_in_exp009_candidate_quality_output。Exp010 独立 S1：not_matched_in_exp010_output。
- Exp011 PRISM：not_matched_in_exp011_prism_output。
- 限制：这些是已完成的历史分析，不是按本轮冻结签名重算；未匹配或缺少记录不等于阴性结果。PRISM 细胞存活敏感性与 LINCS WTCS 是不同终点。
