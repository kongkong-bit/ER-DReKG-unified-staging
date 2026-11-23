# 直接作用靶点证据报告

来源为 OptimusKG 3.2 drug-gene 边的原始关系断言；只把 `TARGET`、`INHIBITOR`、`AGONIST`、`ANTAGONIST`、`PARTIAL_AGONIST`、`BLOCKER`、`ACTIVATOR`、`INVERSE_AGONIST`、`BINDER` 计入靶点语义。`ENZYME`、`TRANSPORTER` 等保留为药物—基因关联，不称作靶点。

- 8/10 候选精确映射；这 8 个药物在该来源有至少一个上述靶点关系。
- 全量导入 74 条 drug-gene 断言；不是所有断言都属靶点。
- 具体基因、关系类型、来源记录和 Evidence ID 在各药物档案及 `top10_graph_bundle/3928c54d/evidence_records.csv`。
- 两个未映射候选的图中靶点覆盖记为未知/未连接，不能解释为无已知靶点。

原始 OptimusKG 靶点语义关系覆盖为 8/10；独立 overlay 添加两药四条明确来源的关系后，专项图中达到 10/10。PHA-767491 的 CDC7 抑制有原始生化/细胞研究支持，CDK9 主张来自不同研究上下文；PFI-1 的 SGC 探针页面给出 BRD2/BRD4 体外数据。overlay 关系仍与原始公开 KG 关系区分，详见 `external_identity_and_mechanism_evidence.csv` 和 overlay `evidence_records.csv`。

本地图数据库断言的来源证据类型和实验强度未在所有关系上统一到 assay 级，因此不夸大为结合实验或临床验证。

## ChEMBL / DGIdb 独立源快照（2026-11-21）

按冻结候选的精确 LINCS ID → ChEMBL molecule ID 映射，从官方 ChEMBL REST API 获取机制与活性记录，并按候选名称查询 DGIdb GraphQL。原始响应保存在 `data/top10_kg/raw/`，规范化记录、请求状态与 SHA-256 在 `data/top10_kg/evidence/`。复算命令：`python kg/scripts/fetch_top10_drug_evidence.py`（有缓存时读取原始响应），随后运行 `python kg/scripts/summarize_top10_source_evidence.py`。

- ChEMBL 返回机制记录 10 条、活性记录 4,852 条；机制靶点组件展开为 19 行，靶点均注释为人类 SINGLE PROTEIN 或 PROTEIN FAMILY。ChEMBL mechanism 端点未返回记录不表示无靶点知识。
- 活性端点对每药最多保留 1,000 条；ponatinib、doxorubicin、rebastinib 的查询达到上限，分别为 1,536、15,388、1,420 条总记录，清楚标记为部分结果。其他候选按端点查询返回完整，但仍不是对药物直接靶点关系的自动认定。
- DGIdb 返回 278 条互动记录；只有 8/10 候选出现精确药名节点。其余 178 条来自未能按精确药物实体映射的变体名称（例如盐型/制剂名称），没有归到冻结候选。精确命中的记录也保留 DGIdb 源库、互动类型、文献和属性，不自动升级为直接靶点；其中包含计算推断的表达/生物标志物关联。
- 逐候选记录数与截断状态见 `top10_source_evidence_summary.csv`。ChEMBL curated mechanism target subset 已按 source/evidence 规则进入新的项目 GraphBundle；完整 ChEMBL activity 和 DGIdb 仍作为可审计证据表/原始快照，不自动升级为直接靶点。新的项目图包尚未登记进 PostgreSQL 或写入 Neo4j。

## ChEMBL mechanism 已进入项目 GraphBundle

新增项目图包 run `ANALYSIS_RUN:KG_GRAPH_BUNDLE:66108369-35fe-44a4-bd44-5c8d97be5a11` 将 ChEMBL mechanism endpoint 中有 target ID 且 `direct_interaction=1` 的记录以 `Drug → ChEMBLTarget` 表示。共 9 条关系，覆盖 5/10 候选；方向、target 类型、source record ID、引用和解释限制保存在边断言中。没有把无 target ID 的 iniparib 记录虚构成基因靶点边。

ChEMBL `PROTEIN FAMILY` 目标保持 `ChEMBLTarget` 家族实体，通过 `HAS_COMPONENT` 连到 14 个唯一 UniProt 蛋白组件；14 个组件均通过唯一 canonical GENE_SYMBOL 连到项目 Gene 节点。Protein–Gene 与 Protein–Reactome 关系、层级关系也独立携带来源 EvidenceRecord。该数据图包离线 BioCypher 验证通过，但还没有登记进 PostgreSQL 或写入 Neo4j。
