# Phase B2：将 S1 富集通路接入疾病子图

运行时间：2026-11-13T10:57:11.273667+00:00

## 输入审计

- S1 富集环境清单记录 limma 输入 SHA-256：`b3dafdae855a0f44cbe80dbc40d17693ed01f4b31d899acbabc60e5485ed21c4`；该值与全量 limma 文件校验值相同。
- 使用显著 GO BP、Reactome、Hallmark 结果及 `pathway_gene_links.csv`；来源文件、OptimusKG 基因表和旧 Phase B 映射表哈希见 `phase_b2_manifest.json`。
- 旧 Phase B 输出不覆盖。它的历史 manifest 曾错误记载通路结果缺失；本版本单独编号并保留旧版文件。

## 抽取与映射

- 新增富集 Pathway/GeneSet 节点：738；新增 Ensembl Gene 节点：95。
- 输入通路基因链接：31,991；唯一映射行：29,441；歧义映射：2,550；未匹配：0。
- 唯一映射规则：使用 OptimusKG primary symbol、symbol_synonyms、obsolete_symbols；只有单一 Ensembl ID 才生成路径。未匹配记录保存在 `pathway_gene_mapping_audit.csv`。
- 项目上下文到富集通路边：738；富集通路到基因边：29,441。同一通路在多个分析中的方向、adjusted P 和 Entrez 保留为独立 assertion。
- 与既有 Phase B 有可靠药物映射的候选/靶点边按 Ensembl ID 精确求交：30 个已映射候选中，22 个存在候选药物→靶点基因→S1 富集通路→疾病上下文的证据路径，共 1,422 条候选-药物-基因-通路组合、涉及 41 个靶基因。输入子图节点表和边表的哈希也记录在 manifest。此结果代表数据库关系的证据交汇，不代表因果或疗效。

## 输出与解释

- `pathway_nodes.csv`、`gene_nodes.csv`、`pathway_edges.csv`、`evidence_records.csv`、`relation_conflicts.csv`、`unmatched_entities.csv`、`pathway_gene_mapping_audit.csv` 和 `phase_b2_manifest.json`。
- 来源证据关系表共 38,331 行，保留 Phase B 与 S1 富集边的原始断言 JSON；未匹配或歧义实体映射共 3,444 行。原始边中显式标记 `relation_conflict=true` 的记录为 0 条；这是对源表冲突标记字段的统计，不表示已经独立核查全部来源库并确认没有冲突。
- Neo4j 实际导入：PASS；重复运行 MERGE 导入两次，节点/边数量前后稳定；数据库实际有 7,314 个节点、37,369 条关系；证据交汇路径 1,422 条。详见 `neo4j_import_validation.json`。
- GO/Reactome UP/DOWN 与 Hallmark NES 正负方向都作为分析属性保存，不将富集关系解释为因果机制、药物疗效或通路激活证明。
- Reactome 与 GO 节点使用标准 pathway ID；Hallmark GeneSet 节点使用 `MSIGDB:` 前缀。连接到相同 Ensembl ID 的公共 Gene 节点，不按项目复制基因实体。

## 限制

- 仅创建当前 ER+ 项目的局部种子子图扩展，没有导入完整 OptimusKG。
- S1 通路富集的统计解释沿用原分析报告；本任务只构建带来源和方向的图连接。
- 若 manifest 中 Neo4j 状态为 PASS，本机 Neo4j 导入及重复运行幂等性已通过；这不代表其他部署环境也已验证。

## 验收

- 本次生成节点、关系、映射审计、来源证据、关系冲突和未匹配实体 CSV；输入和输出 SHA-256 已写入 manifest。
- 后端图仓库/API 自动化测试：11 项通过，其中包含本扩展节点、边及来源追溯检查。
- 若 `neo4j_import_validation.json` 的源文件 SHA-256 与当前 CSV 一致，则数据库导入和重复运行验证引用该报告；若源文件有变化，验证状态会自动标为过期，需重新执行验证脚本。
