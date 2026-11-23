# 参考文献（按本项目步骤对应）

> 说明：DOI / 链接均已给出，引用前请按你所在学校的数据库再核对一次卷期页。
> 「用在哪」一列对应 `top10_selection_pipeline.md` 的步骤编号。

## A. 数据与平台

| # | 文献 | 用在哪 | 要点 |
| --- | --- | --- | --- |
| A1 | Lamb J, et al. The Connectivity Map: using gene-expression signatures to connect small molecules, genes, and disease. *Science* 2006;313(5795):1929–1935. [doi:10.1126/science.1132939](https://doi.org/10.1126/science.1132939) | 步骤 2–3 的理论来源 | 提出"疾病签名 vs 药物签名"的连接逻辑与加权 KS 型连接分数，是本项目 WTCS 的原型 |
| A2 | Subramanian A, et al. A Next Generation Connectivity Map: L1000 Platform and the First 1,000,000 Profiles. *Cell* 2017;171(6):1437–1452.e17. [doi:10.1016/j.cell.2017.10.049](https://doi.org/10.1016/j.cell.2017.10.049) | 步骤 1–2 | 数据来源（L1000 / LINCS）；本身是**多剂量多时间点**设计，支持"不取单一浓度" |
| A3 | Corsello SM, et al. Discovering the anticancer potential of non-oncology drugs by systematic viability profiling. *Nature Cancer* 2020;1:235–248. [链接](https://golublab.broadinstitute.org/publications/discovering-anti-cancer-potential-non-oncology-drugs-systematic-viability) | 步骤 7 确认层 | PRISM 数据来源；本项目 PRISM ER+/ER− 敏感性比较的依据 |
| A4 | Tsherniak A, et al. Defining a Cancer Dependency Map. *Cell* 2017;170(3):564–576.e16. [doi:10.1016/j.cell.2017.06.010](https://doi.org/10.1016/j.cell.2017.06.010) | 建议的机制升级 | DepMap 给出"哪些基因是 ER+ 细胞系的依赖"；比"有靶点"更接近机制可信度（本项目尚未使用，属缺口） |

## B. 打分算法

| # | 文献 | 用在哪 | 要点 |
| --- | --- | --- | --- |
| B1 | Subramanian A, et al. Gene set enrichment analysis: a knowledge-based approach for interpreting genome-wide expression profiles. *PNAS* 2005;102(43):15545–15550. [doi:10.1073/pnas.0506580102](https://doi.org/10.1073/pnas.0506580102) | 步骤 2 的 KS 基础 | 加权 KS 的运行和与零分布思想来源；也是置换检验的出处 |
| B2 | Zhang SD, Gant TW. A simple and robust method for connecting small-molecule drugs using gene-expression signatures. *BMC Bioinformatics* 2008;9:258. [doi:10.1186/1471-2105-9-258](https://doi.org/10.1186/1471-2105-9-258) | 步骤 4 第三算法 | Zhang signed rank 的原始文献；文中明确讨论了**把不同剂量/细胞系混在一个集合会稀释信号**——支持本项目按剂量分层、并对剂量做 bootstrap |
| B3 | Cheng J, Yang L, Kumar V, Agarwal P. Systematic evaluation of connectivity map for disease indications. *Genome Medicine* 2014;6(12):540. [doi:10.1186/s13073-014-0095-1](https://doi.org/10.1186/s13073-014-0095-1) | 步骤 4 第四算法 | XSum 的来源，并系统比较了不同连接分数对"药物–适应证"富集的影响 |
| B4 | Cheng J, Xie Q, Kumar V, Hurle M, Freudenberg JM, Yang L, Agarwal P. Evaluation of analytical methods for connectivity map data. *Pacific Symposium on Biocomputing* 2013:5–16. [PubMed 23424107](https://pubmed.ncbi.nlm.nih.gov/23424107/) | 步骤 3–4 的必要性 | 同一批 CMap 数据换打分算法，排序会明显不同——直接支持"不要依赖单一评分算法" |

## C. 方法学警示（这几篇会让你的结论更稳，而不是更好看）

| # | 文献 | 用在哪 | 要点 |
| --- | --- | --- | --- |
| C1 | Lim N, Pavlidis P. Evaluation of Connectivity Map shows limited reproducibility in drug repositioning. *bioRxiv* 2019. [预印本](https://www.biorxiv.org/content/10.1101/845693) | 全文讨论 / 稳定性检验 | CMap1 签名去查 CMap2，能优先召回原化合物的成功率只有 **17%**；差异表达本身的复现性差是主因。这正是本项目要加剂量 bootstrap、置换零分布与"稳定核心集"的理由 |
| C2 | Santos R, et al. A comprehensive map of molecular drug targets. *Nature Reviews Drug Discovery* 2017;16(1):19–34. [doi:10.1038/nrd.2016.230](https://doi.org/10.1038/nrd.2016.230) | 步骤 6 机制层 | 明确说明"药物靶点在文献中常被定义不清"；支持把"靶点数量"换成"方向一致链"，也解释了为什么机制分会被注释密度带偏 |
| C3 | Sirota M, et al. Discovery and preclinical validation of drug indications using compendia of public gene expression data. *Science Translational Medicine* 2011;3(96):96ra77. [PMC3502016](https://pmc.ncbi.nlm.nih.gov/articles/PMC3502016/) | 全文讨论 | 表达逆转做重定位的经典先例及其验证方式；可作为"计算候选 → 实验验证"的写法模板 |

## D. 统计与稳健性

| # | 文献 | 用在哪 | 要点 |
| --- | --- | --- | --- |
| D1 | Meinshausen N, Bühlmann P. Stability Selection. *JRSS-B* 2010;72(4):417–473. [doi:10.1111/j.1467-9868.2010.00740.x](https://doi.org/10.1111/j.1467-9868.2010.00740.x) | 步骤 5 稳定性门槛 | 重采样 + 选择频率衡量结果稳定性的标准做法；本项目 1,000 次剂量 bootstrap 与 0.70 门槛的方法学依据 |
| D2 | Breitling R, Armengaud P, Amtmann A, Herzyk P. Rank products: a simple, yet powerful, new method to detect differentially regulated genes in replicated microarray experiments. *FEBS Letters* 2004;573(1–3):83–92. | 步骤 4 秩聚合 | 用秩而不是原始值做多方法聚合的思路来源；本项目四算法取中位秩与之同源 |

## E. 疾病背景

| # | 文献 | 用在哪 | 要点 |
| --- | --- | --- | --- |
| E1 | TCGA Network. Comprehensive molecular portraits of human breast tumours. *Nature* 2012;490(7418):61–70. | 步骤 7 背景 | ER+/HER2 分型与 PAM50 的公共参考 |
| E2 | Curtis C, et al. The genomic and transcriptomic architecture of 2,000 breast tumours reveals novel subgroups. *Nature* 2012;486(7403):346–352. | 建议的外部验证 | METABRIC；若要做真正 held-out 验证，应在这里重建 S1 并事前冻结 |
| E3 | Redefining Breast Cancer Care by Harnessing Computational Drug Repositioning（综述，2025）. [Europe PMC](https://europepmc.org/article/MED/41011031) | 引言 / 讨论 | 近期乳腺癌计算重定位综述，提到 mitoxantrone 等表达逆转候选，可作为对照语境（注意：综述，不是原始验证） |

## F. 本项目的缺口（没有直接先例的部分）

- **"四算法中位秩 + 剂量 bootstrap + 方向一致机制链"这个组合没有现成论文可引**。可分别引 B1–B4、D1、C2 作为组件依据，但要在方法学一节明确写"本文的整合流程为自建，未在独立基准上验证"。
- **ER+ 乳腺癌 + LINCS 多剂量逆转** 的专门先例较少；iLINCS 有 ER 签名逆转的教学用例（[链接](https://www.ilincs.org/help/useCases/Reversing-Estrogen-Receptor-(ER)-signature-profile)），可作为工具层面的对照，不构成方法学验证。
- **机制可信度**若要用文献级证据，需要接 ChEMBL / OpenTargets / PubMed 的自动化检索；本项目第 5 项（文献支持靶点–乳腺癌关系）因此记 0，不是遗漏而是数据缺口。

## 引用建议

- **必引（方法学骨架）**：A1、A2、B1、B4、C1、D1。
- **引以说明算法多样性**：B2、B3。
- **引以说明外部证据**：A3、C3。
- **引以说明局限**：C2、C1。
- **背景**：E1、E3。
