# S1/S2 表达证据整合报告

- S1：沿用交付 GraphBundle 对应的 ER+ 差异表达与通路富集输入；7,066 个显著基因中 6,707 个唯一映射到 Ensembl，359 个歧义/未映射。
- S2：冻结 Top 10 的 10 个 perturbagen 保留所有 A+ 选定剂量/时间条件，共 51 条 `S2Condition`，不合并 WTCS。每个药物主榜单 WTCS、细胞、剂量、处理时长和 QC 已冻结在 `02_top10_frozen_manifest.json`。
- 新 bundle 目前把 S2 候选及条件与 S1/公开知识图谱放入同一版本化图包；未将 S2 响应基因重新建成独立的“直接靶点”关系，也未执行 target engagement 推断。
- 已基于外部证据 overlay 后的 41 条靶点语义关系，从原始 GSE70138 Level 5 GCTX 精确提取冻结 Top 10 `sig_id` 对应向量，按 LINCS gene symbol 的 probes 取中位数；输出见 `top10_graph_bundle/3928c54d_external_v1/08_target_s2_response.csv`，输入/输出哈希见 `08_target_s2_response_manifest.json`。
- 41 个靶点关系中 38 个可匹配到 GCTX 响应；8 个靶点 COMPZ 与显著 S1 DEG 方向相反，6 个同向，其余为未测得/无显著 S1 方向或中性。方向相反只是靶点转录本表现，不代表药物抑制靶蛋白，也不能推出治疗效果。
- 补充全基因 S1/S2 方向交叉：对冻结的 10 个主条件 `sig_id` 分别从原始 GCTX 提取 12,328 个可测基因，不合并剂量/时长。每个签名与 S1 显著差异基因交叉 4,667 个；不同药物观察到 2,579–2,967 个方向相反、1,698–2,086 个同向，其余为零响应或未定向。逐基因结果、逐药汇总及 GCTX/输入/输出 SHA-256 在 `top10_s1_s2_expression_reversal.csv`、`top10_s1_s2_expression_reversal_summary.csv` 和 manifest。
- 全基因方向交叉已接入专项 API 和前端表格，可按基因搜索、按相反/同向/中性过滤。该计数是单条 Level 5 共识签名下的描述性对照，不是独立重复、直接靶点证据或治疗效果。

该结果完成了冻结单签名下的逐靶点 S1/S2 描述性对照；它没有剂量重复统计或独立生物验证，故仍不能宣称完整因果机制或疗效已建立。
