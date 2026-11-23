# Phase A：系统输入审计与架构门禁

审计时间：2026-11-14T15:11:35.398584+08:00

## 审计结论

- 当前找到 S1 limma、S2、Exp006–Exp011 和第二轮综合结果的部分核心文件；文件清单及 SHA-256 在 `system_input_inventory.csv`。
- S1 全量 limma 表可读取，共 21,655 行；字段为 `gene_symbol, logFC, AveExpr, t, P.Value, adj.P.Val, B`。`run_limma.R` 明确比较 Tumor − Normal。本次只读检查，没有重跑 limma 或修改结果。
- 找到 S1 通路分析输出：GO BP、Reactome、Hallmark GSEA、基因映射审计和通路基因链接。输出输入 SHA-256 与当前 limma 全量表一致；映射背景为 17649 个 Entrez 基因。显著结果数为 GO UP/DOWN 206/343、Reactome UP/DOWN 135/26、Hallmark 29。原分析报告和参数见 `experiments/s1_pathway_enrichment/`。
- S2 有历史签名级分数；Exp009 审计了稳定 ID 联结与旧显示名称联结差异。平台应以 `sig_id`、LINCS perturbagen ID 等稳定标识关联，并把名称差异留作审计信息。
- 研究目录保持原位。当前工程已有 `backend/`、`frontend/`、`kg/` 平台代码；平台输入清单只读记录历史结果及 SHA-256。
- OptimusKG 作为候选公共知识底座。其数据许可为 CC BY-NC-SA 4.0，必须保留署名和许可信息。本阶段没有下载完整图谱。

## 架构决定

PostgreSQL 保存项目、数据集、分析运行、ID 映射和证据目录；Neo4j 保存标准化实体及带来源的断言。FastAPI 是唯一图谱查询入口，React 不直接访问 Neo4j。大型矩阵和 Parquet 保存在文件层并记录不可变哈希。Celery/Redis 暂缓，先使用可复跑 CLI。

## Phase A 交付物

- `docs/architecture/architecture.md`
- `docs/architecture/tech_stack.md`
- `docs/architecture/database_design.md`
- `docs/architecture/frontend_plan.md`
- `docs/graph_schema/graph_schema.yaml`
- `docs/api/api_contract.yaml`
- `docs/audit/source_license_audit.md`
- `experiments/platform_phase_a/system_input_inventory.csv`
- `experiments/platform_phase_a/phase_a_audit.json`

## 进入 Phase B 前的门禁

架构和接口契约已形成。S1 通路结果已存在并与当前 limma 输入校验值一致。Phase B 使用受限 OptimusKG 子集并完成药物/基因 ID 映射；公共图谱边与 S1 富集结果应分别展示，不把数据库路径视为因果或疗效证据。完整 OptimusKG 未导入。
