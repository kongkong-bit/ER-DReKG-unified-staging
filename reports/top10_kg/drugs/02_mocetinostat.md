# 02 mocetinostat (BRD-K16485616)

- Formal rank: 2; WTCS=-0.5059000597374851; LINCS condition MCF7, 10.0 um, 24 h; n_signatures=1.
- Identity: matched_exact_inchikey; OptimusKG drug `CHEMBL272980`.
- Candidate conditions retained: 6 separate condition rows.

## Source-supported target assertions

- HDAC1 (`ENSG00000116478`): TARGET / DRUG_BANK, INHIBITOR / OPEN_TARGETS; Evidence `27730fe8fcc8d1fb1d5f67982ee4ce2ad4b2427cf8a2d78e34dd0187495f4c9d`; source record `OptimusKG 3.2:drug_gene:CHEMBL272980:ENSG00000116478`
- HDAC8 (`ENSG00000147099`): INHIBITOR / OPEN_TARGETS; Evidence `3b5ab53e8a33331ae2064f31b55b490d879e8d23e15df515fa253a63222ca9ec`; source record `OptimusKG 3.2:drug_gene:CHEMBL272980:ENSG00000147099`
- HDAC11 (`ENSG00000163517`): INHIBITOR / OPEN_TARGETS; Evidence `9d1ad02de8ffe6b1351484925bcd52c2c18e4fcfcd4036023a06f40361d450a7`; source record `OptimusKG 3.2:drug_gene:CHEMBL272980:ENSG00000163517`
- HDAC3 (`ENSG00000171720`): TARGET / DRUG_BANK, INHIBITOR / OPEN_TARGETS; Evidence `5287e6deb3b2093e54b83c44397c5cbee5ed5ed2eb2c642cccb987decb747fe4`; source record `OptimusKG 3.2:drug_gene:CHEMBL272980:ENSG00000171720`
- HDAC2 (`ENSG00000196591`): TARGET / DRUG_BANK, INHIBITOR / OPEN_TARGETS; Evidence `99bca6f28a0cc98506c69cb3c4ca8fd3913bba5108c408fa429deb210e0aa19c`; source record `OptimusKG 3.2:drug_gene:CHEMBL272980:ENSG00000196591`

## S1 pathway intersections

Route rows: 37; distinct pathway IDs: 37.
- Cell Cycle, Mitotic
- Chromatin modifying enzymes
- Chromatin organization
- Death Receptor Signaling
- ERCC6 (CSB) and EHMT2 (G9a) positively regulate rRNA expression
- ESR-mediated signaling
- Epigenetic regulation of gene expression
- Estrogen-dependent gene expression
- Factors involved in megakaryocyte development and platelet production
- Formation of the beta-catenin:TCF transactivating complex
- HDACs deacetylate histones
- Negative epigenetic regulation of rRNA expression
- NoRC negatively regulates rRNA expression
- Positive epigenetic regulation of rRNA expression
- RNA Polymerase I Promoter Clearance
- RNA Polymerase I Transcription
- RNA Polymerase I Transcription Initiation
- RUNX1 regulates genes involved in megakaryocyte differentiation and platelet function
- Regulation of TP53 Activity
- Regulation of TP53 Activity through Acetylation
- Regulation of endogenous retroelements
- Regulation of endogenous retroelements by KRAB-ZFP proteins
- Regulation of endogenous retroelements by Piwi-interacting RNAs (piRNAs)
- SARS-CoV Infections
- SUMO E3 ligases SUMOylate target proteins
- SUMOylation
- SUMOylation of chromatin organization proteins
- Transcriptional Regulation by TP53
- epigenetic regulation of gene expression
- heterochromatin formation
- negative regulation of gene expression, epigenetic
- p75 NTR receptor-mediated signalling
- positive regulation of stem cell population maintenance
- regulation of stem cell population maintenance
- viral gene expression
- viral process
- viral transcription

## Interpretation boundary

A relation is reported using its original assertion type. Enzyme and transporter associations are not silently counted as pharmacologic targets. A target-to-pathway route means the drug-gene and S1 pathway-gene assertions intersect; it does not establish causal modulation, treatment benefit, or ER-positive specificity. WTCS is an expression-reversal ranking signal and is not efficacy evidence.

## ER+ 疾病背景定向文献筛查

- 范围：ER_positive_preclinical；类型：drug_disease_context；方向：supportive_preclinical。
- 背景：ER-positive endocrine-resistant HCC-1428/LTED and MDA-MB-415/ESR1 cell models; WHIM16 endocrine-resistant PDX; estradiol combination
- 整理：2026 primary study reports mocetinostat-induced H3K27ac in ER-positive models and supplementary growth-suppression results with estradiol; E2 plus mocetinostat also slowed WHIM16 PDX growth relative to E2 alone. The paper's principal analyses focus on entinostat.
- 来源：[DOI:10.1002/1878-0261.70307 / PMID:42464636](https://pubmed.ncbi.nlm.nih.gov/42464636/)（primary_study）
- 限制：Mocetinostat results are supplementary figures in an entinostat-centered paper. Preclinical endocrine-resistant models only; not clinical efficacy or an ER-positive treatment indication.
- 解释边界：这是定向筛查记录，不是系统综述或疗效结论，不据此生成药物—ER+ 疾病图边。
## Exp006–Exp011 历史复核

- Exp006：24 h 合格剂量 6.0 个，历史 WTCS 负向比例 0.6666666666666666；剂量稳定性 `direction_flip`，QC 敏感等级 `low`。
- Exp007：A / B100 / B150 / B200 / B300 / matched125 名次：42.0 / 79.0 / 10.0 / 2.0 / 2.0 / 42.0。
- Exp008：历史 B200 置换经验 P / BH-FDR：0.0004997501249375312 / 0.0039334146486079；Historical Exp008 B200 permutation table (2,000 permutations); NA means this pert_id-condition was not tested there; not recomputed for the corrected 5,861-signature set.
- Exp009 质量阈值复核：available。Exp010 独立 S1：available, rank=26.0, WTCS=-0.5468156446740629。
- Exp011 PRISM：available, ER+ mean=2.1834272844634444, ER− mean=3.081375808303462, ER+−ER−=-0.8979485238400176。
- 限制：这些是已完成的历史分析，不是按本轮冻结签名重算；未匹配或缺少记录不等于阴性结果。PRISM 细胞存活敏感性与 LINCS WTCS 是不同终点。
