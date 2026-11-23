# Top 10 离线子图提取

输入为 `reports\top10_kg\top10_graph_bundle\3928c54d_external_v1`，manifest SHA-256 `30ae77db16435419ea5aa9c4d4e4c9bb224e79d4cd9c15927668b6b183cb1821`。

为冻结的 10 个候选各生成了独立 JSON。新增 SIGNOR Oct2026 与 OmniPath academic-filtered core signed assertions，经精确 UniProt→OptimusKG gene crosswalk 映射并按出度阈值过滤；路径仅由有向 REGULATES 边搜索，路径边 Evidence ID 可回溯至来源断言。候选路径形成离线 BioCypher 扩展包（297 个节点、461 条关系，其中 328 条调控断言和 133 条映射边）；该层已按 GraphBuild 导入隔离 staging。Reactome current-2026-10 的 gene-pathway membership 映射至机制路径的 S1 终点基因，生成 17,504 条离线通路注释记录；独立于调控边，不传播符号。Reactome 当前版 gene-pathway/hierarchy 和 PrimeKG 精确 Top10 子集也已通过第二个 GraphBuild 增量导入 staging；PrimeKG 1,026 条候选关系中 978 条通过唯一标识映射，48 条边及 44 个未映射/歧义节点留在拒绝报告。PrimeKG 不进入 signed path search 或候选评分。未知或上下文不明确的冲突符号保留为 unknown。ChEMBL→UniProt→Reactome98 routes 仍是非因果上下文注释。
