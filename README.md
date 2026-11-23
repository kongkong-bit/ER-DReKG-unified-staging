# ER-DReKG

**基于疾病表达逆转与知识图谱的 ER 阳性乳腺癌药物重定位研究平台**

ER-DReKG 将疾病差异表达（S1）、LINCS 药物扰动表达（S2）和知识图谱证据连接起来，生成可追溯的药物重定位候选与机制假设。当前研究对象为 ER 阳性乳腺癌。计算排名是研究线索，不是药物疗效或临床建议。

## 研究流程与当前结果

1. **S1 疾病签名**：GSE42568，67 个 ER 阳性肿瘤样本与 17 个正常组织样本；limma 对 21,655 个基因分析，FDR < 0.05 的差异基因 7,066 个。另完成 GO、Reactome 和 Hallmark 通路分析。
2. **S2 表达逆转筛选**：LINCS/GSE70138 Level 5 MCF7 化学药物扰动签名；按固定 WTCS 实现评分，并在主实验条件下对 5,861 条签名、1,471 个化合物进行筛选。
3. **可靠性与外部核对**：比较了 S1 基因空间、签名规模、评分、剂量、质量条件，并与独立疾病表达和 PRISM 药物敏感性数据作交叉检查。
4. **知识图谱机制证据**：连接药物、靶点、差异基因、通路与来源证据，形成候选机制解释。
5. **交付平台**：FastAPI 后端、React/TypeScript 前端、PostgreSQL 元数据存储与 Neo4j 图谱查询。

正式初步 Top 10 及其局限见[最终研究报告](experiments/final_results/reports/final_research_report.md)和[项目状态](experiments/final_results/reports/final_project_status.md)。当前主条件下 Top 10 每个候选只有一条合格签名；外部疾病签名 Top 10 重合为 1/10；图谱直接靶点覆盖约 5/10。尚无新的细胞、动物或临床验证，因此结果只能称为**计算候选与机制假设**。

## 目录说明

| 路径 | 内容 |
| --- | --- |
| `backend/` | FastAPI 服务、数据库迁移、分析管线与测试 |
| `frontend/` | React + TypeScript 前端 |
| `kg/` | BioCypher/Neo4j 图谱构建与导入脚本 |
| `s1_初步_gse42568_limma/` | 历史 S1 输入与结果（原始数据可能不纳入 Git） |
| `s2_lincs/` | S2 处理代码、审计、评分与输出；大型 GCTX 不纳入 Git |
| `experiments/` | S1 通路、Exp006–Exp011、Final 与平台阶段报告和结果 |
| `docs/` | 架构、数据许可与项目文档 |
| `data/` | 原始及处理数据；大文件、数据库和本地上传按忽略规则处理 |

## Windows 单项目启动

从本项目根目录启动即可；不要从 `ER-DReKG-KG-delivery-20261120\04_code\backend\app\main.py` 启动整个平台。该嵌套目录是 KG 改动审阅包，按其交付说明刻意只放派生 `main.py` 和相关补丁，不含完整 `app.*` 后端或前端依赖。**可运行的完整后端和前端分别位于根目录 `backend/` 与 `frontend/`。**

首次准备本机环境需要 Docker Desktop、Python 3.12、uv、Node.js/npm：

```powershell
Copy-Item .env.example .env
# 编辑 .env：设置 POSTGRES_PASSWORD、NEO4J_PASSWORD；DATABASE_URL 使用相同的 PostgreSQL 密码。
Set-Location backend
uv sync
Set-Location ..\frontend
npm ci
Set-Location ..
```

之后在根目录用一个命令启动本项目专属的 PostgreSQL、Neo4j、FastAPI 和 Vite：

```powershell
.\scripts\start-project.ps1
```

- 前端：<http://127.0.0.1:15175>
- API：<http://127.0.0.1:18083>
- API 文档：<http://127.0.0.1:18083/docs>

启动脚本会等待数据库健康检查、执行 Alembic 迁移，然后按固定端口启动本目录的服务；端口被其他程序占用时会停止并提示，不会杀掉其他项目。配置 `ZHIPU_API_KEY` 后启用 GLM-5.3-Flash 机制解释。关闭本项目：

```powershell
.\scripts\stop-project.ps1
```

停止脚本只关闭本项目 API、前端和 Compose 数据库容器，保留数据库卷。数据准备和手动复现说明见[运行与复现说明](docs/REPRODUCIBILITY.md)。

## 科研报告入口

- [S1 通路富集](experiments/s1_pathway_enrichment/enrichment_report.md)
- [S2 正式筛选](s2_lincs/reports/formal_s2_screen_report.md)
- [Exp006–Exp011 稳健性与外部核对](experiments/second_round_summary/reports/second_round_master_report.md)
- [Top 10 机制报告](experiments/final_results/reports/final_top10_mechanism_report.md)
- [数据来源与许可审计](docs/audit/source_license_audit.md)
- [运行、数据准备与复现说明](docs/REPRODUCIBILITY.md)

## 数据、许可与安全

公开数据应按各数据源许可和引用要求使用。大型原始数据、LINCS GCTX、数据库、虚拟环境、上传数据及本地密钥不适合直接提交到 GitHub；请按[数据准备说明](docs/REPRODUCIBILITY.md#数据准备)获取或配置。项目结果保留来源、参数与审计报告。禁止提交 `.env`、数据库口令、API Key 或个人数据。

## 贡献与问题

提交代码前请确认变更不覆盖历史实验数据，并检查 `git status` 与暂存文件。复现问题请附操作系统、Python/Node/R 版本、命令和脱敏后的报错日志。详见[贡献指南](CONTRIBUTING.md)。

## 引用

如果使用本项目方法或数据，请同时引用 GSE42568、LINCS/GSE70138 及 README 所链接的具体方法学与数据来源。当前仓库尚未配置正式论文引文元数据（CITATION.cff）。
