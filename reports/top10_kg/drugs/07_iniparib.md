# 07 iniparib (BRD-K11153516)

- Formal rank: 7; WTCS=-0.4552728740394625; LINCS condition MCF7, 10.0 um, 24 h; n_signatures=1.
- Identity: matched_exact_inchikey; OptimusKG drug `CHEMBL1170047`.
- Candidate conditions retained: 4 separate condition rows.

## Source-supported target assertions

- PARP1 (`ENSG00000143799`): TARGET / DRUG_BANK; Evidence `a432a020e64f0128551066b50f61682f0b9f900003e8c51b22b90f1b671e8385`; source record `OptimusKG 3.2:drug_gene:CHEMBL1170047:ENSG00000143799`

## S1 pathway intersections

Route rows: 40; distinct pathway IDs: 40.
- Base Excision Repair
- DNA Double-Strand Break Repair
- DNA Repair
- DNA recombination
- DNA replication
- DNA-templated DNA replication
- DNA-templated DNA replication maintenance of fidelity
- DNA-templated transcription elongation
- Homology Directed Repair
- Resolution of AP sites via the multiple-nucleotide patch replacement pathway
- Resolution of Abasic Sites (AP sites)
- SUMO E3 ligases SUMOylate target proteins
- SUMOylation
- base-excision repair
- cellular response to UV
- double-strand break repair
- double-strand break repair via homologous recombination
- negative regulation of DNA-templated transcription, elongation
- negative regulation of chromosome organization
- negative regulation of transcription elongation by RNA polymerase II
- positive regulation of DNA metabolic process
- positive regulation of DNA recombination
- positive regulation of DNA repair
- positive regulation of DNA-templated transcription, elongation
- positive regulation of double-strand break repair
- positive regulation of double-strand break repair via homologous recombination
- protein localization to chromosome
- recombinational repair
- regulation of DNA metabolic process
- regulation of DNA repair
- regulation of DNA-templated transcription elongation
- regulation of cellular response to stress
- regulation of chromosome organization
- regulation of double-strand break repair
- regulation of double-strand break repair via homologous recombination
- regulation of transcription elongation by RNA polymerase II
- replication fork processing
- telomere maintenance
- telomere organization
- transcription elongation by RNA polymerase II

## Interpretation boundary

A relation is reported using its original assertion type. Enzyme and transporter associations are not silently counted as pharmacologic targets. A target-to-pathway route means the drug-gene and S1 pathway-gene assertions intersect; it does not establish causal modulation, treatment benefit, or ER-positive specificity. WTCS is an expression-reversal ranking signal and is not efficacy evidence.

## ER+ 疾病背景定向文献筛查

- 范围：triple_negative_phase3_negative；类型：negative_clinical_and_mechanism；方向：counter_signal_and_mechanism_revision。
- 背景：Metastatic TNBC randomized phase III plus PARP mechanism re-evaluation
- 整理：Phase III missed its prespecified coprimary OS/PFS criteria in the intention-to-treat population; separate mechanistic work disputes classification as a bona fide PARP inhibitor.
- 来源：[PMID:25349301; PMID:24402426](https://pubmed.ncbi.nlm.nih.gov/25349301/; https://pubmed.ncbi.nlm.nih.gov/24402426/)（primary_clinical_and_mechanistic_studies）
- 限制：TNBC only; exploratory subgroup findings do not replace failed primary endpoints; not ER-positive evidence.
- 解释边界：这是定向筛查记录，不是系统综述或疗效结论，不据此生成药物—ER+ 疾病图边。
## Exp006–Exp011 历史复核

- Exp006：24 h 合格剂量 4.0 个，历史 WTCS 负向比例 0.75；剂量稳定性 `direction_flip`，QC 敏感等级 `low`。
- Exp007：A / B100 / B150 / B200 / B300 / matched125 名次：243.0 / 416.0 / 100.0 / 16.0 / 28.0 / 243.0。
- Exp008：历史 B200 置换经验 P / BH-FDR：0.0004997501249375312 / 0.0039334146486079；Historical Exp008 B200 permutation table (2,000 permutations); NA means this pert_id-condition was not tested there; not recomputed for the corrected 5,861-signature set.
- Exp009 质量阈值复核：available。Exp010 独立 S1：available, rank=155.0, WTCS=-0.47371818467967297。
- Exp011 PRISM：available, ER+ mean=0.2234544371641, ER− mean=0.2331990767706308, ER+−ER−=-0.009744639606530797。
- 限制：这些是已完成的历史分析，不是按本轮冻结签名重算；未匹配或缺少记录不等于阴性结果。PRISM 细胞存活敏感性与 LINCS WTCS 是不同终点。
