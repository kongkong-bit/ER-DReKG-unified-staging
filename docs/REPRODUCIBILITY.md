# 运行与复现说明

本文说明代码环境和本地数据配置。所有路径均相对于仓库根目录。

## 软件环境

- Windows 10/11（当前维护环境）
- Python 3.12；后端依赖和锁文件：`backend/pyproject.toml`、`backend/uv.lock`
- Node.js/npm；前端依赖和锁文件：`frontend/package.json`、`frontend/package-lock.json`
- Docker Desktop；PostgreSQL 17、Neo4j 5 Community（见 `docker-compose.yml`）
- S1/R 富集分析需 R 与 Bioconductor 依赖，具体版本记录在 `experiments/s1_pathway_enrichment/environment_manifest.json`

## 配置与启动

本目录是完整可运行项目根目录。请不要从嵌套的 `ER-DReKG-KG-delivery-20261120/04_code/backend/app/main.py` 启动整个平台；那是只交付 KG 改动的派生审阅包，缺少完整后端模块和前端 package manifest 是该子包的设计边界，不代表本项目根目录源码缺失。完整应用入口位于 `backend/app/`，前端依赖清单位于 `frontend/package.json`。

1. 复制根目录 `.env.example` 为 `.env`，设置 `POSTGRES_PASSWORD` 与 `NEO4J_PASSWORD`，并让 `DATABASE_URL` 中的 PostgreSQL 密码与 `POSTGRES_PASSWORD` 一致。AI 机制解释另需本机 `ZHIPU_API_KEY`。`.env` 已被忽略，不能提交。
2. 首次安装依赖：在 `backend/` 执行 `uv sync`；在 `frontend/` 执行 `npm ci`。
3. 从项目根目录运行 `.\scripts\start-project.ps1`。脚本按 `er-drekg-unified-staging` Compose 项目名启动本项目 PostgreSQL/Neo4j、执行 Alembic 迁移，然后启动 API `127.0.0.1:18083` 和 Vite `127.0.0.1:15175`。
4. 打开前端 `http://127.0.0.1:15175`；API 文档为 `http://127.0.0.1:18083/docs`。脚本检查端口占用并等待两个 HTTP 服务就绪。
5. 关闭本项目使用 `.\scripts\stop-project.ps1`。它只停止本项目 API、前端和 Compose 数据库容器，保留 PostgreSQL/Neo4j 持久卷。

手动开发时，后端应使用根 `.env` 和端口 18083，前端 Vite 端口 15175；前端 `/api` 代理默认指向 `http://127.0.0.1:18083`。CSV 离线模式与研究流水线的环境要求另见下文和 `kg/scripts/`。

## 数据准备

代码仓库不保证包含所有原始数据。开始复现实验前，依据各阶段报告的数据清单准备对应输入：

- S1：GSE42568 表达/limma 输入。报告及既有结果位于 `s1_初步_gse42568_limma/` 和 `experiments/s1_pathway_enrichment/`。
- S2：GSE70138 Level 5 GCTX 和签名、基因、扰动、质量元数据。GCTX 体积数 GB，需从 GEO 获取；文件名、字段和筛选条件见 `s2_lincs/reports/00_data_audit.md` 与 `s2_lincs/reports/formal_s2_screen_report.md`。
- 外部验证：按 Exp010/Exp011 报告中的数据来源和清单获取输入。不得将本机缓存或下载文件误认为代码仓库提供的数据。

请遵循 `docs/audit/source_license_audit.md` 和原数据集的引用、许可要求。忽略规则排除了大型输入、上传数据和本地缓存；小型审计报告、脚本及精选结果可纳入版本控制。

## 运行分析与验证

- S2 评分与单元测试脚本、参数和数据依赖说明位于 `s2_lincs/`。
- S1 通路分析脚本、R 环境清单、输入与报告位于 `experiments/s1_pathway_enrichment/`。
- 平台 API 测试位于 `backend/tests/`；用 `cd backend; uv run pytest` 运行。
- 前端构建可在 `frontend/` 使用 `npm ci`、`npm run build`。

阶段结果与局限以对应报告为准。当前正式候选仍是计算初筛结果，尚无新增实验验证。
