# 靶点—通路交汇报告

S1 通路由正式项目富集输出的 GO、Reactome、Hallmark 结果（校正 P < 0.05）与通路—基因映射生成；药物候选路径要求药物—基因来源边与 S1 富集通路—基因边共享同一 gene ID。

2026-11-21 按 ChEMBL mechanism target 的 UniProt protein component，调用 Reactome Content Service（release 98）查询 Homo sapiens pathway 映射，并针对映射的 101 个 pathway 获取 event ancestors。14 个唯一 UniProt accession 对应 19 条 ChEMBL target-component 记录，得到 316 条 component–pathway 映射、101 个不同 pathway 和 217 条父子层级关系，API 错误为 0。规范化结果及原始响应分别见 `data/top10_kg/evidence/reactome_protein_pathways.csv`、`reactome_pathway_hierarchy.csv`、`top10_reactome_manifest.json` 与 `data/top10_kg/raw/reactome/`。

这些是蛋白组件参与/映射，不代表通路激活或抑制，也不代表 ER+ 特异性。ChEMBL `PROTEIN FAMILY` target 的组件继续标注为 family component；不会把家族整体作用擅自拆成对每个亚基的直接药物靶向主张。单药 API/页面已独立展示这些 Reactome 记录，和靶点—S1 富集交汇路径分开展示。

- GraphBundle 路径交汇总数：471。
- 有至少一条交汇路径的 Top 10 药物：6/10。
- 路径是来源记录与 S1 富集集合的交叉，不代表药物使通路上调/下调，也不代表 ER+ 特异机制。
- 每药路径数和 ID 见 `06_top10_bundle_coverage.csv` 与逐药档案；具体节点/关系 Evidence ID 见 `evidence_records.csv`。

新增的 ChEMBL/Reactome 图路径以 `Drug -[HAS_DIRECT_TARGET]-> ChEMBLTarget -[HAS_COMPONENT]-> Protein -[PARTICIPATES_IN]-> Pathway -[SUBPATHWAY_OF]-> Pathway` 保存。共有 205 条唯一 Protein–Reactome `PARTICIPATES_IN` 边、217 条 Reactome pathway 层级边；10 个候选的 S1 富集交汇路径仍独立保持 528 行/8 个候选的原始基线口径，不将蛋白参与映射直接混成候选—疾病通路证据。新图包含 232 个 Reactome Pathway 节点，并通过 BioCypher 离线校验。
