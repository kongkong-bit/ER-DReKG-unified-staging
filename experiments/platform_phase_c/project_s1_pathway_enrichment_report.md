# 项目级 S1 通路富集功能实施与审计报告

日期：2026-11-13

## 本次实现

- 新增 `POST /api/v1/projects/{project_id}/s1/pathway-enrichment`，输入必须是本项目已完成的 S1 AnalysisRun；S1 文件存在性和 SHA-256 会先核对。
- 新增独立 R 管线，使用 `org.Hs.eg.db` 将 Symbol、Entrez 或 Ensembl ID 映射到 Entrez。映射审计保留未匹配和一对多情况，不修改输入 S1 表。
- GO Biological Process 使用 `clusterProfiler::enrichGO`；Reactome 使用 `ReactomePA::enrichPathway`；两项 ORA 均以该 S1 实际检验且成功映射的 Entrez 集合作为 universe，采用 BH 校正。
- Hallmark 使用 Broad MSigDB 2025.1.Hs Entrez GMT 和全部可映射、有限的 limma t 统计量进行 `fgseaMultilevel` 排序富集，固定 seed=42、单进程、minSize=10、maxSize=500、eps=1e-10。重复 Entrez 在 ORA 中按最低 adj.P.Val 决定保留行；GSEA 独立按最大绝对 t 统计量决定保留行。
- 每次执行生成独立 `AnalysisRun`、输入/脚本/GMT 哈希、R 与包版本、输出文件哈希、JSON 清单和中文报告。输出包括映射审计、上下调输入基因、GO/Reactome/Hallmark 全量表、通路-基因链接及图表。
- `GET /api/v1/projects/{project_id}/s1/pathways` 支持读取该项目最近一次、且对应当前最新 S1 的富集结果；可以用 `analysis_run_id` 查询指定历史富集运行。若 S1 已更新但尚未重新富集，接口不会将旧富集冒充新 S1 结果。历史 ER+ 项目继续使用原有静态结果。
- 非 ER 项目的 S1 页面新增富集运行控件；结果按现有路径图组件显示。历史科研结果与 Exp006–Exp011 未被重写。

## 真实数据验证

通过上述同一 R runner，在临时输出目录中使用现有完整 GSE42568 limma 表验证 21,655 个检验基因；临时输出在验证后清理，历史源文件未修改。该验证不是 API 创建的持久化 ER AnalysisRun。

| 指标 | 实际结果 |
|---|---:|
| 成功映射的 Entrez 背景 | 17,649 |
| 映射后的上调 / 下调输入 | 2,991 / 3,164 |
| GO BP 显著通路（上调 / 下调） | 206 / 343 |
| Reactome 显著通路（上调 / 下调） | 135 / 26 |
| Hallmark 显著基因集 | 29 |
| 实际生成图表 | 12 张 |

显著数量与已有 GSE42568 富集报告一致。图表包括 GO/Reactome 气泡图、Hallmark GSEA 总览、6 张显著 Hallmark 富集曲线及通路-命中基因图。

验证输入：

- limma 表 SHA-256：`b3dafdae855a0f44cbe80dbc40d17693ed01f4b31d899acbabc60e5485ed21c4`
- Hallmark GMT SHA-256：`fcf3a5471f973874f3c37996dc93a45a9c84edf7d7828bba54a7eb95af53bc45`
- R 管线 SHA-256：`c76cb0bd00a6fb328aee959a7ab2d59b4ae2218414b8dc5297644b0ad3471eb3`
- R 4.4.3；clusterProfiler 4.14.6；ReactomePA 1.50.0；org.Hs.eg.db 3.20.0；fgsea 1.32.4；ggplot2 4.0.3。

## 软件验收

- 新增 API 编排测试验证项目/S1 归属、AnalysisRun provenance、输出校验、路径越界保护、摘要更新及通路结果查询。
- 后端隔离 CSV 模式完整测试：31 项通过。根目录 `.env` 配置的是 Neo4j，故测试进程显式使用临时 `GRAPH_SOURCE=csv`；没有改写 `.env`。
- Python `compileall` 通过；API 契约 YAML 与运行时 OpenAPI 均包含 28 条路径，新富集端点一致存在。
- 前端 `npm run build` 通过；仍有约 2.82 MB 主 bundle 的拆包提示。
- 真实 R 管线验证使用真实完整 S1 输入；API 编排验收使用隔离的模拟输出。没有声称在真实完整 GSE42568 上通过 API 创建持久化运行。

## 限制

- 新项目必须选择正确的 `identifier_type`；页面暂未自动推断/验证用户标注的 ID 类型。映射审计是每次运行的输出，不改变上游 S1。
- ORA/GSEA 的显著性只表示基因集统计关联，不代表通路因果激活、ER+ 特异机制或药物疗效。
- 新项目的通路结果可以查询和展示，但从这些富集结果自动创建带关系冲突审计的通用 GraphBundle 仍未完成。
- 本机开发环境需保留项目 R 环境及 Broad GMT 文件；R 运行超时上限为 30 分钟，尚未迁移到后台 Job 队列。
