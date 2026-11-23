# 药物身份映射报告

本次对冻结 Top 10 的 LINCS `pert_id` 读取 `pert_info` InChIKey，并与 OptimusKG 3.2 Drug 节点作精确 InChIKey 匹配。未使用名称模糊匹配。

- OptimusKG 3.2 本地五文件节点映射：8/10 精确匹配；2 个没有本地图节点（PHA-767491、PFI-1）。
- 身份核查：10/10 均有 InChIKey；本地缺失的两种药可由外部权威记录按完全相同 InChIKey 解析：PHA-767491 → PubChem CID 11715767 / ChEMBL CHEMBL225519；PFI-1 → ChEMBL CHEMBL2179387。外部核对记录见 `external_identity_and_mechanism_evidence.csv`。身份被解析不代表已经加进图数据库。
- 旧 Top 10 Neo4j 查询文件曾记录 5/10 映射；本次离线重建为 8/10。新增精确映射：MK-2461 → CHEMBL1822792；rebastinib → CHEMBL1738757；JNJ-26481585 → CHEMBL2105763。结果仅说明在 OptimusKG 3.2 这五个公开文件中存在精确结构键对应。
- 冻结榜单与排名未因映射覆盖变化。
- 外部 overlay 在保留 OptimusKG 原始 8/10 精确节点映射的基础上，以外部来源和相同 InChIKey 补入 PHA-767491、PFI-1，因此专项 overlay 身份解析为 10/10。该补充不得表述为 OptimusKG 原始覆盖率。
- 外部 overlay 版本在保持 Opt imusKG 的 8 个精确节点映射基础上，将 PHA-767491 与 PFI-1 以外部来源和同一 InChIKey 加入独立补充层，因此专项 overlay 的身份解析为 10/10；本地底图原始映射率仍是 8/10。对比不得把外部补充说成 OptimusKG 原始覆盖率。
- 冻结清单缺失的 `sig_id` 已从正式 `final_signature_scores.csv` 以完全相同的 pert_id、细胞、处理类型、剂量、时长精确匹配回填；10/10 唯一匹配，WTCS 与 Top 10 记录误差小于 `1e-12`。回填依据和状态写在 `02_top10_frozen_manifest.json`。
- 逐药映射见 `top10_graph_bundle/3928c54d/candidate_mapping_audit.csv`。

## 未映射

PHA-767491（BRD-K50000283）和 PFI-1（BRD-K13094524）在本地 LINCS PertInfo 提供的结构键，未命中 OptimusKG 3.2 Drug 节点；外部 ID 已补核但尚未并入当前 KG。准确来源与证据等级在补充 CSV 中记录。

## 可复现身份交付

`data/top10_kg/identity/top10_identity_mapping.csv` 逐候选保存 LINCS ID、名称/别名、InChIKey、ChEMBL/PubChem ID、来源图谱匹配状态和剂量条件行数；`identity_mapping_manifest.json` 固定输入/输出 SHA-256。精确解析为 10/10，其中原始 OptimusKG 节点 8/10、外部精确 InChIKey overlay 另补 2/10。`unresolved_identity_candidates.csv` 当前只有表头，表示在本专项核查范围内无未解决项；不表示每个来源均提供了所有交叉引用字段。
