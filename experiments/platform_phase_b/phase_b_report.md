# Phase B：基于真实数据的候选药物子图原型

## 人话摘要

从 Exp006 Top50 候选开始，用化学结构 InChIKey 精确匹配 OptimusKG 药物；再把 S1 显著基因映射到 Ensembl，查找图谱中已有的药物—基因靶点关系和通路—基因关系。只有实际存在、带来源的关系才进入结果。

## 数据来源与范围

- OptimusKG Harvard Dataverse 发布版 **3.2**，许可 **CC BY-NC-SA 4.0**。
- 仅下载 5 个 Parquet 表，共 76,907,347 字节；完整图谱没有下载。
- 每个源文件的 Dataverse 文件 ID、MD5、SHA-256 见 `data/optimuskg/3.2/source_manifest.json`。

## 映射和路径结果

- Exp006 候选药物：50 个；精确 InChIKey 映射成功 30 个。
- S1 FDR<0.05 基因：7066 个；唯一 Symbol/别名映射到 Ensembl 6192 个；歧义或未匹配 874 个。
- 子图包含 1801 条候选药物→靶基因→通路路径，30 个药物节点、6188 个 S1 基因节点、233 个通路节点。
- 当前缺少本地 S1 GO/Reactome/Hallmark 富集结果；这些路径仅表示公共知识图谱中的靶点与通路关系和 S1 差异基因重合，不代表通路已被本项目富集验证，更不代表 ER+ 特异性或疗效证据。

## 可追溯文件

- `candidate_mapping_audit.csv`：Top50 每个 LINCS 药物的精确结构匹配状态。
- `s1_gene_mapping_audit.csv`：S1 基因映射、方向及 limma 原始统计量。
- `unmatched_entities.csv`：未匹配及有歧义条目。
- `subgraph_nodes.csv`、`subgraph_edges.csv`：局部子图。边的 `properties_json` 保留原始 relation、数据源和冲突字段。
- `candidate_target_pathway_routes.csv`：路径和两条源关系断言。
- `phase_b_manifest.json`：输入/输出哈希、运行 ID、许可、计数。

## 限制

OptimusKG 汇总了多个来源；一条图边不能替代源数据库原始证据审查。药物映射仅使用完全相同 InChIKey；不同盐型和立体异构体不会自动合并。当前未加载 Neo4j，因此结果是可导入、可复跑的子图原型，还不是在线图数据库服务。
