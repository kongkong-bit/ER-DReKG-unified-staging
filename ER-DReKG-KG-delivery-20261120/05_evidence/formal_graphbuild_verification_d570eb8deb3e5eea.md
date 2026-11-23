# 正式 GraphBuild 只读验收报告

**GraphBuild ID：** `GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:d570eb8deb3e5eea`  
**报告生成时间（UTC）：** 2026-11-20T04:47:41Z  
**报告性质：** 只读验收。未重新构建 GraphBundle，未重新导入 Neo4j，未写入 PostgreSQL/Neo4j。  
**适用范围：** 仅覆盖本报告列出的 GraphBuild `d570eb8deb3e5eea`。  
**重要声明：** `experiments/platform_phase_c/formal_graphbuild_verification.*` 覆盖的是旧构建 `a6aabb2147cb5f5e`，**不是本报告对象**，不得替代或冒充本报告。

---

## 1. 标识与关联

| 项目 | 值 |
|---|---|
| project_id | `3f18f4c1-713d-58c5-8a53-38eca5a5aaf9` |
| project_slug | `erpos-gse42568` |
| S1 运行 | `ANALYSIS_RUN:S1_PRECOMPUTED:9ebd6c43-9342-487e-a052-ae901461b58c` |
| S2 运行 | `ANALYSIS_RUN:S2_LINCS:eab2f02a-2bdf-53c8-833b-fedab03070c5` |
| S1 富集运行 | `ANALYSIS_RUN:S1_ENRICHMENT:eb409567-e846-4422-ae19-0055937871ea` |
| GraphBundle 运行 | `ANALYSIS_RUN:KG_GRAPH_BUNDLE:e0421796-2aff-47e2-9228-d683eab05fa9` |
| GraphBuild | `GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:d570eb8deb3e5eea` |
| build_key | `d570eb8deb3e5eea94d4f939e7b4c2cb15ca418b1e1b1a13284322229ba4e3f7` |
| 状态 | `materialized` |
| 图来源 | `neo4j` |
| 登记时间（DB 记录） | `2026-11-19 10:44:37.228794+00` |

---

## 2. 验收方法与证据边界

本次验收使用以下只读证据：

1. **GraphBundle 文件哈希**：`bundle_checksums.json`、`analysis_run_manifest.json`、`bundle_manifest.json`。
2. **PostgreSQL 只读结果**：`graph_builds`、`analysis_runs`、`evidence_records`、`disease_contexts`、`s2_condition_results`、`candidates`。
3. **Neo4j 只读结果**：节点标签计数、按 GraphBuild 标记的关系计数、样例关系属性。
4. **服务日志**：`uvicorn_graphbuild.log`、`uvicorn_graphbundle.log`、`uvicorn_part3_step5.log`。
5. **代码身份哈希**：HEAD、工作区与正式构建记录中的导入器/构建器 SHA-256。

**证据边界（必须明确）：**

- PostgreSQL/Neo4j 数值来自**本次审计阶段已执行的只读查询结果转录**（见 `postgres_*.txt`、`neo4j_counts.txt`）。交付包制作阶段**没有再次连接数据库**。
- 本报告不是 API 端到端冒烟测试报告；它验证的是**登记一致性、文件完整性、哈希闭包和代码身份**。
- 本报告不是科学或临床验证。图谱关系是数据库断言与项目表达证据的交汇，不证明因果、疗效或 ER+ 特异性。

---

## 3. 验收结论

| 检查项 | 结果 | 证据 |
|---|---|---|
| GraphBundle 清单状态 | **PASS** | `bundle_manifest.json`: `status=validated`，`project_id` 匹配，`s2_analysis_run_id=eab2f02a` |
| BioCypher 结构验证 | **PASS** | `biocypher_validation.json`: `status=PASS`，`node_count=12899`，`edge_count=48729` |
| Bundle 文件哈希 | **PASS** | 14/14 文件与 `bundle_checksums.json` 或 DB `input_hashes` 一致（`bundle_file_hash_verification.tsv`） |
| Bundle 输入哈希（包内可核部分） | **PASS** | 14/14 可核输入 MATCH；7 项外部许可数据未纳入（`bundle_input_hash_verification.tsv`） |
| PostgreSQL 登记 | **PASS** | `graph_builds.status=materialized`，`import_status=PASS`，`evidence_record_count=48729` |
| 证据持久化 | **PASS** | `evidence_records` 中该 build 共 48,729 行；`disease_contexts` 1 行 |
| Neo4j 内容 | **PASS** | 该 build 标记关系 48,729 条；节点标签合计 12,899 |
| 导入链路日志 | **PASS** | `POST /graph-bundles` 200；`POST /graph-builds?bundle_run_id=…e0421796…` 200 |
| 正式图谱使用的导入器 | **已确认（见第 5 节）** | 记录值 `72953d3c…` = HEAD 原版导入器 + CRLF |

---

## 4. 计数（两种口径必须区分）

### 4.1 全量 GraphBundle / 全量 build 标记内容

| 指标 | 值 |
|---|---:|
| 节点 | **12,899** |
| 关系 | **48,729** |
| 证据记录 | **48,729** |
| DiseaseContext | **1** |

节点类型：Gene 6,518；S2Condition 3,943；Candidate 1,032；Pathway 709；Drug 666；GeneSet 29；DiseaseContext 1；Disease 1。

### 4.2 接口实时 2 跳口径（`graph_builds.summary_json`）

| 指标 | 值 |
|---|---:|
| 节点 | **12,171** |
| 关系 | **44,932** |

节点类型：DiseaseContext 1；Pathway 709；Gene 5,790；GeneSet 29；Drug 666；Candidate 1,032；S2Condition 3,943；Disease 1。

> **不要把 12,171 / 44,932 与 12,899 / 48,729 混用。** 前者是 API 从 `DiseaseContext` 出发 2 跳范围内的实时统计；后者是 GraphBundle 全量与按 build 标记的 Neo4j 全量。

---

## 5. 导入器溯源（关键结论）

正式 GraphBuild 的 `summary_json` 记录：

```text
neo4j_importer_sha256 = 72953d3c3c35d38fda9e23e836ad39b10cbd630084d0de176ba93f2b5ee61cb2
```

实测哈希关系：

| 对象 | SHA-256 |
|---|---|
| HEAD 原版导入器（LF 原始 blob） | `9c4b6609c69810a8e276efd90703db24a148dddfdbddd628880ef0f73801256d` |
| HEAD 原版导入器 + CRLF | `72953d3c3c35d38fda9e23e836ad39b10cbd630084d0de176ba93f2b5ee61cb2` |
| **正式构建记录值** | `72953d3c3c35d38fda9e23e836ad39b10cbd630084d0de176ba93f2b5ee61cb2` |
| 当前工作区改进版导入器 | `9fae6da68bb3309c01ed80345c966937242f5785c9640429c5b91736d4af969d` |
| 当前工作区改进版（LF 归一化） | `7e90b016c31edc3c26b29f3b70575994d253d893cef4cc3ef9b6537f2a59d275` |

**结论：正式图谱 d570eb8deb3e5eea 实际使用的是原版（HEAD）导入器，而不是当前改进版导入器。**

Neo4j 侧进一步印证：

- 关系 ID 形如 `源|关系|目标|source_release`，**不含 GraphBuild 后缀**；
- 样例关系的 `build_key` 为 `NULL`；
- 关系仅通过 `graph_build_ids` 数组标记所属版本。

当前改进版导入器（交付包内 `04_code/kg/scripts/import_phase_b_to_neo4j.py`）新增了：

- 关系身份加入 GraphBuild：`源|关系|目标|source_release|graph_build_id`；
- 每条关系写入 `build_key` 与 `input_sha256`；
- 导入前节点/关系预检与失败关闭；
- 输入哈希校验、项目级导入锁、`ON CREATE SET` 节点写入策略；
- 导入后关系复核。

**因此：**

> **改进版导入器状态 = 已完成代码改进，尚未应用于正式图谱。**  
> 不得把改进版导入器描述为“正式图谱的实际导入代码”。

---

## 6. A+ 输入到正式图谱的哈希链

| 环节 | 文件 | SHA-256 |
|---|---|---|
| 上游候选 | `final_corrected_condition_ranking.csv` | `66e970195564d2945d57c111c57cdfed61b56a136181b59b8acec0a2764fffe8` |
| 上游条件 | `final_drug_condition_summary.csv` | `5be0cdb02abbb011314b61927837077c29765f230f3822fcc00e1a650d7ba8f2` |
| 上游签名 | `final_signature_scores.csv` | `efd1d5167751160006e6129515ac51db445068a5b1e25b7e1f97b2d9dc758911` |
| A+ 候选 | `Aplus_candidate_drugs.csv` | `814581b92d01cc48c6a80080c02bd3a3da35fb405d32514aab56d11e056ac106` |
| A+ 条件 | `Aplus_condition_records.csv` | `c87dfe92648025fd038d32ecc76d32f05d8c65e0a9e0473f7d8663955707b74f` |
| A+ 适配条件 | `adapted_input/drug_condition_summary.csv` | `0973fd446e707f1f695cb8a422216ea78a38aeb6cfe67c267c9c7b36e4be7745` |
| S2 条件（实际 bundle 输入） | `s2/eab2f02a/drug_condition_summary.csv` | `0973fd446e707f1f695cb8a422216ea78a38aeb6cfe67c267c9c7b36e4be7745` |
| A+ 签名 | `aplus_signature_scores/signature_scores.csv` | `bbb9a5b74690420dc30f1cab56d9d8b7270aa28042f66e15c9d531c802b0992e` |
| S2 签名 | `s2/eab2f02a/signature_scores.csv` | `bbb9a5b74690420dc30f1cab56d9d8b7270aa28042f66e15c9d531c802b0992e` |
| GraphBundle 节点 | `subgraph_nodes.csv` | `0e20f5cca9daa945b168e8452e96a3465bcf1d786fc2272a830cbd18b70423ee` |
| GraphBundle 关系 | `subgraph_edges.csv` | `10a345da91c9e462c8f561d439162194f306575f6d9ee514fe57c2c1049938f8` |
| GraphBundle 证据 | `evidence_records.csv` | `72ca7079a096c88628f8648dd423ce15bdb0cf70ded3061bc0359a3170b80a70` |
| GraphBundle 清单 | `bundle_manifest.json` | `c2c9f0f54782af88fabbeb9cd1311d7643a4fa43cdd9aa0f583ba872eb860704` |
| 构建器 | `kg/scripts/build_project_graph_bundle.py` | `191a506d331e9fa17f7d16af5748b41b929323886ae270f8183b1419f59f0c83` |

**A+ 规模：** 1,032 个唯一 `pert_id`；3,943 条条件；4,385 条签名。  
**映射结果：** 668 个候选有精确 InChIKey 对应的 Drug 节点；17,324 条候选靶点—通路交汇路径；`relation_conflicts=0`。

---

## 7. 未执行事项（明确边界）

本次**没有**执行：

1. 没有重新构建 GraphBundle；
2. 没有重新导入 Neo4j；
3. 没有清库、删库或修改 GraphBuild 记录；
4. 没有写入 PostgreSQL/Neo4j；
5. 没有重跑 S1/S2、没有重算 WTCS；
6. 没有调用机器学习的机制解释或 LLM 接口；
7. 没有把改进版导入器应用到正式图谱。

---

## 8. 解释限制

- 知识图谱关系表示可追溯的数据库断言与项目表达证据的交集，**不代表药物疗效、临床建议或因果机制**。
- 靶点—通路路径是“靶点在 S1 富集通路中”的共现关系，不是作用方向、活性强弱或实验验证。
- 候选排名只基于计算评分；A+ 集合扩大了覆盖面，不等于单药解释质量提升。
- 本报告只验证结构与哈希一致性，不验证生物学正确性。

---

## 9. 附件索引

| 附件 | 内容 |
|---|---|
| `postgres_graphbuild_record.txt` | `graph_builds` 完整记录（只读转录） |
| `postgres_counts.txt` | 分析运行与各表计数 |
| `neo4j_counts.txt` | Neo4j 标签、关系与 2 跳口径计数 |
| `bundle_file_hash_verification.tsv` | Bundle 14 个文件逐一哈希核对 |
| `bundle_input_hash_verification.tsv` | Bundle 21 个输入哈希核对（14 MATCH，7 EXTERNAL） |
| `environment_hashes.txt` | 导入器/构建器代码身份哈希 |
| `git_state_at_delivery.txt` | 交付准备时的 Git 状态 |
| `uvicorn_*.log` | 三个登记接口的实际调用日志 |

---

**报告判定：结构与登记一致性 PASS；科学解释仍为计算候选与机制假设。**
