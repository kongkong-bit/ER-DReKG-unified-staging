# 数据来源与许可审计（Phase A）

审计日期：2026-11-13（Asia/Shanghai）。本文件只记录当前确认的信息；每次新增数据源或升级版本时必须重新审计。

| 来源 | 项目中的用途 | 版本/来源记录 | 许可与使用要求 |
|---|---|---|---|
| GSE42568 | S1 微阵列表达与 limma 结果 | GEO accession；本地 limma 文件已计算 SHA-256 | 对外分发前核对 GEO 记录中的数据使用条件；保留原始研究引用及本地文件哈希。 |
| GSE70138 / Broad LINCS | S2 Level 5 COMPZ 及基因、签名、药物和质量元数据 | GSE70138，2017-03-06 发布版本；本地文件哈希记录在实验清单 | 保留 Broad/GEO 引用和版本。不同上游数据组件的许可可能不同，不能假设整个集合使用同一许可；公开分发前核对 README 与各来源条款。 |
| GSE139038 | Exp010 独立患者队列 | GEO accession；版本记录在实验 manifest | 引用 GEO 数据来源与原始研究；与发现队列分析结果分开保存。 |
| Broad/DepMap PRISM Primary | Exp011 细胞存活敏感性 | PRISM Primary；受体亚型注释来自 DepMap Public 24Q4 | 引用 PRISM/DepMap 数据集与发布版本。审计过的本地 README/页面没有单独 LICENSE 文件；不能据此宣称可无限制再分发。 |
| OptimusKG | 拟使用的公共知识图谱底座 | Harvard Dataverse DOI 10.7910/DVN/IYNGEV；本轮 Phase B 固定 release 3.2 | 数据集页面声明 CC BY-NC-SA 4.0。该许可约束图谱数据，和代码仓库许可不同。保留署名、许可、版本、文件哈希及来源断言。Phase B 只下载所需小型 Parquet 子集，没有下载全图。 |
| Ensembl / ChEMBL / MONDO / Reactome / GO | 候选 ID 命名空间与映射来源 | 本轮未单独下载这些源数据库 | 各来源许可和署名要求不同。真正接入前逐个记录版本、许可和文件哈希；不得套用统一许可。 |

OptimusKG 官方文档说明图谱按 Parquet 文件发布，并支持按文件获取。Phase B 已仅下载药物、基因、通路节点和药物—基因、通路—基因关系五个文件；具体 Dataverse 文件 ID、大小、MD5、SHA-256 见 `data/optimuskg/3.2/source_manifest.json`。本轮保留的 OptimusKG 数据必须遵守非商业及相同方式共享要求。

参考：[OptimusKG 官方文档](https://optimuskg.ai/docs)；[Harvard Dataverse 数据集及许可](https://doi.org/10.7910/DVN/IYNGEV)。
