# Top 10 机制图谱建设前基线

## 统计口径

数据来自仓库保存的 manifest、Top 10 机制 CSV 和 2026-11-20 正式 GraphBuild 只读验收转录。本报告不连接实时 PostgreSQL/Neo4j。Top 10 覆盖数字对应旧 GraphBuild `a6aabb2147cb5f5e`；A+ 全量规模对应新 GraphBuild `d570eb8deb3e5eea`，两者不可混算。

## 当前记录的覆盖率

| 指标 | 基线 | 口径/证据 |
|---|---:|---|
| Top 10 药物精确身份映射 | 5/10 | 仅精确 InChIKey；旧构建 `final_neo4j_drug_mapping.csv` |
| Top 10 有直接靶点 | 5/10 | 61 条靶点关系行；旧构建 `final_neo4j_direct_targets.csv` |
| Top 10 有靶点到 S1 通路路径 | 5/10 | 395 条路径行；旧构建 `final_neo4j_s1_pathway_links.csv` |
| 最新 A+ GraphBundle 节点 | 12,899 | `d570eb8…` 全量 bundle |
| 最新 A+ GraphBundle 关系/证据 | 48,729 / 48,729 | `d570eb8…` 全量 bundle/DB 转录 |
| A+ 候选 / S2 条件 / 签名 | 1,032 / 3,943 / 4,385 | 最新 A+ 输入；不等于 Top 10 |
| 新构建 Neo4j 导入器版本 | 原版 | 登记哈希对应 HEAD 原版；改进版未应用 |
| 当前数据库实时连通性 | 未核验 | 本轮未连接 DB；交付验收非实时复核 |

## 节点类型计数（新正式 A+ 构建）

| 类型 | 数量 |
|---|---:|
| Gene | 6,518 |
| S2Condition | 3,943 |
| Candidate | 1,032 |
| Pathway | 709 |
| Drug | 666 |
| GeneSet | 29 |
| DiseaseContext | 1 |
| Disease | 1 |

## 解释

“5/10 无映射”只表示旧图谱中没有精确 InChIKey 对应节点，不等于外部数据库没有该药或其靶点。“有路径”指旧图谱里药物关系与 S1 通路基因关系交汇，不证明药物在 ER+ 乳腺癌中作用于该通路。`Drug` 节点数量不是药物靶点数量；`Gene` 节点数量也不能当作靶点数。

## 尚缺的基线

建设基线专项离线 Top 10 GraphBundle 为 6,639 节点、38,388 关系，计数见 `top10_graph_bundle/3928c54d/bundle_manifest.json` 与 `biocypher_validation.json`。随后 external overlay 扩至 6,643 节点、38,394 关系；本轮又构建项目级 ChEMBL/Reactome 扩展包，6,855 节点、38,868 关系，BioCypher 离线验证通过。扩展包带 AnalysisRun 注册模板，并经隔离 SQLite 验证了应用层注册解析和证据持久化；**尚未登记至主 PostgreSQL，也未导入 Neo4j**，因此新包的实时节点/关系计数、孤立节点及浏览器端 API E2E 仍待真实服务门禁。正式 A+ GraphBundle 与工作区现存文件有差异，因此不能声称工作区当前源数据完全重现了正式 A+ bundle。
