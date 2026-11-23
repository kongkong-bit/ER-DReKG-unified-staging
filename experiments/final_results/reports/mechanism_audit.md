# Final03 机制审计

## 审计范围

- Top10 候选数：10；关系查询为只读 Neo4j，限定当前 GraphBuild `GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:a6aabb2147cb5f5e`。
- 药物身份按 LINCS InChIKey 精确匹配；不按名称模糊匹配。10 个药物中 5 个精确映射。
- 5 个候选有当前构建直接靶点；5 个有靶点→S1 通路路径。其余是本构建覆盖缺口，不推论其无已知药理靶点。
- 关系语义保留原始断言 JSON 和来源；`TARGET`、`ENZYME`、`TRANSPORTER` 等不是统一的抑制关系。无方向断言时不推断药物抑制靶点。
- 当前关系类型审计未发现有来源支持的 PPI 关系；未做 PPI 扩展。
- 本轮机制正文由确定性模板生成，未调用 LLM。模型 API、prompt 及 LLM 输出因此不适用。

## 关系/机制风险核查

- Iniparib：当前图谱为 PARP1 一般 TARGET 关系；文献反证不支持将其写作已验证 PARP 抑制剂。
- Balaglitazone：PPARG 激动方向与将“PPARG 下调”简单解释为表达反转并不等价，不能称为已证实逆转。
- Doxorubicin：存在 TOP2A/细胞周期关联，但广谱细胞毒性不构成 ER+ 特异证据。
- LINCS COMPZ 目标基因是转录量描述，不是靶标结合/抑制测量。
- 其余候选外部文献机制是一般药理背景；如果项目图谱无精确节点，明确写作未图谱映射。

## 文件完整性

- `top10_mechanism_paths.csv`：所有能从当前图谱核验的候选靶点-S1 通路路径及 assertion/Evidence ID。
- `top10_evidence_citations.csv`：图谱和外部来源逐项登记。
- `top10_mechanism_reports/`：逐药 EvidencePackage 与限制说明。
