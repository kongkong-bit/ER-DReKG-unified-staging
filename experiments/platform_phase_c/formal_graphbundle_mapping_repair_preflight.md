# 正式 ER+ GraphBundle 基因映射修复预检报告

日期：2026-11-14

## 当前结论

本地 R 富集和 GraphBundle 映射预检通过；随后修复版正式数据库运行也已登记并通过实际 API 验收。旧的两个正式 GraphBuild 仍保留在数据库中供审计，不作为当前修正版。

## 发现的问题

第一次历史结果导入后，正式 GraphBundle 结构构建成功，但其输入的旧 `pathway_gene_links.csv` 不含 Ensembl 映射列。实际结果为 31,991 条通路基因链接中唯一映射 0 条、药物靶点到通路交汇路径 0 条。旧版本 ID 为 `GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:92ccf8669de7c697`。该版本保留作为审计记录，不应当作修复后的图谱使用。

## 已完成的本地验证

- 已通过项目隔离 R 环境加载 R 4.4.3、clusterProfiler 4.14.6、ReactomePA 1.50.0、org.Hs.eg.db 3.20.0、fgsea 1.32.4 和 ggplot2 4.0.3。
- 对项目内 S1 标准化副本实际重跑了 S1 通路富集及 Entrez—Ensembl 映射；没有重跑 limma。输入 21,653 个唯一基因，得到 17,649 个映射 Entrez 背景；Ensembl 映射审计记录 15,977 个唯一映射、1,148 个歧义映射、4,531 个未映射基因。GO、Reactome、Hallmark 显著项数量分别为 206、343、135、26、29。
- 使用真实 S1、项目级 50 个 Exp006 Top 候选的 240 个 scheme B 剂量条件以及本地 OptimusKG 数据，独立运行 GraphBundle 构建器。31,991 条通路—基因链接中 30,350 条唯一映射到 Ensembl；50 个候选中 30 个以精确 InChIKey 映射公共药物，得到 1,494 条候选靶点—通路交汇路径。剂量仍逐层保留，没有合并成单一药物分数。
- 已在 GraphBundle 构建器增加失败关闭门禁：存在通路—基因链接但唯一 Ensembl 映射为 0 时，拒绝生成 `validated` 图包。新增回归用例覆盖旧输入缺少 Ensembl crosswalk 的情形；`kg/tests` 全部 7 项通过。
- Phase A 历史输入清单 22 个文件再次逐一核对，22/22 SHA-256 匹配。

本地验证输出分别位于 `data/processed/projects/3f18f4c1-713d-58c5-8a53-38eca5a5aaf9/s1_enrichment/repair-preflight-50ae049d-52a3-4edf-9659-e64ce1d2f686/` 和 `experiments/platform_phase_c/.tmp/formal_bundle_mapping_50c300c1-7ffd-42cf-8554-47cae399ee79/`。这些是本地预检产物，尚未以正式新 AnalysisRun/GraphBuild 写入 PostgreSQL/Neo4j。

## 阻塞状态

第一次重提数据库审批请求曾返回 `Bad Request`，没有执行数据库写入。用户确认重试后，正式通路富集运行、GraphBundle 和 Neo4j GraphBuild 已成功登记。最终版本 `GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:a6aabb2147cb5f5e` 的 Neo4j 图摘要为 6,853 节点、38,657 条关系；机制 API 返回 82 条抽查路径，证据 API 返回 HTTP 200。详细端到端核验见[正式 GraphBuild 实际验收报告](formal_graphbuild_verification.md)。

## 解释边界

这些通路和关系只表示统计富集及来源数据库支持的关系交汇；不是因果机制、药物疗效或 ER 阳性特异性治疗证据。详细机器可读计数见同目录 `formal_graphbundle_mapping_repair_preflight.json`。
