# 08 balaglitazone (BRD-A00147595)

- Formal rank: 8; WTCS=-0.45273824135333623; LINCS condition MCF7, 10.0 um, 24 h; n_signatures=1.
- Identity: matched_exact_inchikey; OptimusKG drug `CHEMBL2103991`.
- Candidate conditions retained: 3 separate condition rows.

## Source-supported target assertions

- PPARG (`ENSG00000132170`): PARTIAL_AGONIST / OPEN_TARGETS; Evidence `fba4167f822b4d3a96da791edea42fdeae960c2cf5e85eb5a6c1f31018fbe6ff`; source record `OptimusKG 3.2:drug_gene:CHEMBL2103991:ENSG00000132170`

## S1 pathway intersections

Route rows: 82; distinct pathway IDs: 82.
- BMP signaling pathway
- HALLMARK_ADIPOGENESIS
- HALLMARK_CHOLESTEROL_HOMEOSTASIS
- HALLMARK_UV_RESPONSE_DN
- SMAD protein signal transduction
- adipose tissue development
- blood circulation
- blood vessel endothelial cell migration
- cell surface receptor protein serine/threonine kinase signaling pathway
- cellular ketone metabolic process
- cellular response to BMP stimulus
- cellular response to insulin stimulus
- cellular response to peptide hormone stimulus
- cellular response to transforming growth factor beta stimulus
- cholesterol efflux
- connective tissue development
- endothelial cell migration
- endothelial cell proliferation
- epithelial cell proliferation
- fat cell differentiation
- fatty acid metabolic process
- lipid homeostasis
- lipid storage
- macrophage derived foam cell differentiation
- mitochondrial fission
- mitochondrion organization
- muscle cell proliferation
- myeloid cell differentiation
- myeloid leukocyte differentiation
- negative regulation of angiogenesis
- negative regulation of blood vessel morphogenesis
- negative regulation of cell migration
- negative regulation of cell motility
- negative regulation of endothelial cell migration
- negative regulation of locomotion
- negative regulation of response to external stimulus
- negative regulation of smooth muscle cell proliferation
- negative regulation of vascular associated smooth muscle cell proliferation
- negative regulation of vasculature development
- ossification
- osteoblast differentiation
- positive regulation of cholesterol transport
- positive regulation of fat cell differentiation
- positive regulation of lipid localization
- positive regulation of lipid metabolic process
- positive regulation of lipid transport
- positive regulation of small molecule metabolic process
- positive regulation of sterol transport
- regulation of BMP signaling pathway
- regulation of angiogenesis
- regulation of blood pressure
- regulation of blood vessel endothelial cell migration
- regulation of cellular ketone metabolic process
- regulation of cellular response to growth factor stimulus
- regulation of endothelial cell migration
- regulation of fat cell differentiation
- regulation of fatty acid metabolic process
- regulation of lipid localization
- regulation of lipid metabolic process
- regulation of lipid storage

## Interpretation boundary

A relation is reported using its original assertion type. Enzyme and transporter associations are not silently counted as pharmacologic targets. A target-to-pathway route means the drug-gene and S1 pathway-gene assertions intersect; it does not establish causal modulation, treatment benefit, or ER-positive specificity. WTCS is an expression-reversal ranking signal and is not efficacy evidence.

## ER+ 疾病背景定向文献筛查

- 范围：focused_search_gap；类型：unresolved_disease_link；方向：unknown_no_claim。
- 背景：ER-positive breast cancer
- 整理：Focused search did not identify a compound-specific ER-positive breast-cancer study; evidence for other PPAR-gamma ligands cannot be transferred to balaglitazone.
- 来源：[Search audit 2026-11-21]()（search_audit）
- 限制：Search was focused rather than systematic; this is an evidence gap, not proof that no such study exists.
- 解释边界：这是定向筛查记录，不是系统综述或疗效结论，不据此生成药物—ER+ 疾病图边。
## Exp006–Exp011 历史复核

- Exp006：24 h 合格剂量 3.0 个，历史 WTCS 负向比例 0.3333333333333333；剂量稳定性 `mixed_or_limited`，QC 敏感等级 `low`。
- Exp007：A / B100 / B150 / B200 / B300 / matched125 名次：20.0 / 18.0 / 19.0 / 17.0 / 71.0 / 20.0。
- Exp008：历史 B200 置换经验 P / BH-FDR：0.0004997501249375312 / 0.0039334146486079；Historical Exp008 B200 permutation table (2,000 permutations); NA means this pert_id-condition was not tested there; not recomputed for the corrected 5,861-signature set.
- Exp009 质量阈值复核：available。Exp010 独立 S1：available, rank=40.0, WTCS=-0.5270782698981555。
- Exp011 PRISM：available, ER+ mean=0.11547362867406667, ER− mean=-0.06336096053913078, ER+−ER−=0.17883458921319745。
- 限制：这些是已完成的历史分析，不是按本轮冻结签名重算；未匹配或缺少记录不等于阴性结果。PRISM 细胞存活敏感性与 LINCS WTCS 是不同终点。
