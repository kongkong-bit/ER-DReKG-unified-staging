# 前端规划与当前实现

## 已实现

前端使用 React、TypeScript、Vite、Ant Design、Cytoscape.js、ECharts、TanStack Query 和 React Router；所有科研结果均通过 FastAPI 读取，浏览器没有 Neo4j 凭据。

- `/`：项目总览、S1/S2/KG 摘要、数据集校验状态、项目切换和新建项目；显示最近 AnalysisRun 状态并可查单次运行状态。
- `/s1`：limma 摘要、火山图、分页基因表、GO/Reactome/Hallmark 图表，以及新项目的 precomputed DEG、微阵列 limma、RNA-seq edgeR-voom 和通路富集运行入口。正式 ER+ 项目另展示 Exp010/GSE139038 独立配对队列复核指标和剂量/时间分层的外部 S2 排名；读取前校验输出哈希。
- `/s2`：Exp006–Exp011 多来源证据矩阵；项目级 LINCS 条件结果、剂量内排名和跨剂量 Top-N 复现率分别显示，不生成未经验证的疗效总分。
- `/graph`：按 GraphBuild 版本筛选的限量子图；支持 stable ID 搜索、节点/关系筛选、直接药物—靶点/其他疾病通路关系切换、已载入子图最短路径高亮、点击关系查看 evidence ID 来源弹窗、节点属性和子图导出。页面另有 GraphBundle 生成及图谱构建入口。
- `/drugs`：药物详情包括原候选排名、S2 条件级 WTCS/质量、跨剂量排名复现、独立 S1 排名、PRISM ER+/ER− 观测，以及逐条 GraphBuild 机制来源证据。
- `/compare`：选择同一项目中两个已完成的同类型 AnalysisRun，展示运行参数、软件版本、输入哈希、结果摘要差异；S2 按完全相同的条件键与 perturbagen 对齐，不跨剂量/时间汇总；GraphBuild 数量注明是创建时快照。
- 项目创建和数据上传表单会区分正式项目与 `test_only`；新建 Study 并按同一项目关联数据集；上传进入 `validation_pending`，不会自动启动差异分析。

六个页面均按路由动态载入；ECharts 在查看 S1 图表时加载，Cytoscape 在查看图谱时加载。项目创建/上传弹窗仅在打开时加载；导航 shell 不导入 Ant Design。ECharts 使用 `echarts/core`，只注册柱状图、折线图、散点图、网格、图例、提示框和 Canvas renderer。最近一次生产构建的初始静态 JS 依赖块为 313.79 kB（gzip 98.65 kB）；六个页面的最大路由代码块为 20.50 kB。图表分块从 1,145.86 kB 降到 573.89 kB（gzip 195.76 kB），Cytoscape 为 451.17 kB（gzip 144.51 kB）。剩余 >500 kB 告警只来自按需加载的 S1 图表块。

## 已有真实验收证据

- 项目、S1、S2、图摘要、机制和 evidence API 曾通过 Vite `/api` 代理进行真实 HTTP 联调；S1 结果与历史 21,655 个测试基因一致。
- 项目创建和文件上传弹窗按需加载。上传经 Vite/FastAPI 代理的真实 HTTP 测试和隔离数据库测试通过；2026-11-14 又在 Edge 访客窗口中实际打开 Windows 原生文件选择器，上传合成表达矩阵并核验 `validation_pending`、样本注释门禁和 AnalysisRun 未启动，详见 `experiments/platform_phase_c/browser_upload_e2e_report.md`。
- Neo4j 中两个 `test_only` 项目的实体复用、GraphBuild 隔离和 FastAPI 查询已通过数据库级验收；测试夹具不属于第二种疾病的科研证据。
- 正式 ER+ GraphBuild 修正版本的实时摘要、机制、通路、S2 条件和证据 API 已由只读验收脚本复核；当前版本统计为 6,850 个节点、38,657 条关系。
- AnalysisRun 比较 API 和 `/compare` 页面已接入；S2 仅比较两次运行中相同 condition key 与 perturbagen 的 WTCS/条件内排名变化，并报告两版独有条目数。
- 本轮 `npm run build` 和 Vite 页面模块 HTTP 检查通过；初始静态依赖为 313.79 kB，六个页面及项目弹窗均动态载入。Study API 与数据集关联字段已由真实 API 联调验证；原生选择器与提交流程已另行在桌面 Edge 访客窗口实测，未触碰个人 Edge。

## 尚待实现

- 独立异步 Job 队列。当前科研任务由 CLI/API 同步执行；`GET /jobs/{job_id}` 以 AnalysisRun ID 返回同步运行状态，Celery/Redis 与真实百分比仍待异步任务启用后实现。
- Exp010/GSE139038 外部验证目前在 S1 页面内呈现摘要和分页条件排名；跨队列结果专门汇总页面及导出向导尚未实现。
- 更细粒度的按路由拆包，当前动态加载了图表/图谱大依赖，但仍存在大 JS chunk 警告。

所有无数据的新项目显示真实空状态，不填充模拟药物关系。知识图谱路径只表示可追溯的来源断言与项目证据交汇，不证明因果或疗效。
