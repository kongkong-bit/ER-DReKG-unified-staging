# Phase D：前端 MVP 与真实 API 联调验收

验收时间（UTC）：2026-11-14T09:44:09.626187+00:00

## 实际检查

- Vite 首页与 React 开发模块均返回 HTTP 200；最新药物详情代码由 Vite 成功转译。
- 正式 ER+ 项目 S1 查询返回 21,655 个检验基因；候选 API 返回 50 项。
- Study API 返回 HTTP 200（现有研究 1 条）；2 个历史数据集均关联到 GSE42568，列表可读取 Study accession/title。
- Exp010 外部验证 API 返回 GSE139038 的 14 对 ER+ 患者队列、3,715 个剂量/时间条件；摘要和排名文件 SHA-256 均校验通过。
- Exp006–Exp011 综合证据矩阵为 819 项；剂量条件分页完整读取 240 项且 condition key 全部唯一。
- Phase F 候选证据 API 分页读取 819 个唯一 perturbagen；GraphBuild 与结果 SHA-256 和验收清单一致。
- AnalysisRun 比较 API：200；同类型运行可比参数、输入哈希和类型专属结果。
- 运行状态 API：200；当前 job_id 与 AnalysisRun ID 相同；同步执行状态不伪造异步进度。
- S2 跨剂量稳定性返回 50 个候选；正式 GraphBuild 过滤后 6,850 节点、38,657 条关系、DiseaseContext=1。
- EvidenceRecord API/数据库版本验收：正式 GraphBuild 持久化 38,998 条证据，SHA-256 与 GraphBundle 一致；最新与历史 GraphBuild 的证据均按各自版本读取。
- DiseaseContext PostgreSQL 持久化：正式 GraphBuild 保存 1 条项目疾病上下文，来源 `subgraph_nodes.csv` 哈希已登记。
- 机制 API 对 `BRD-A00147595` 返回 82 条版本内路径。
- 以上请求全部通过本机 Vite `/api` 代理读取真实 PostgreSQL/Neo4j 项目数据；不写数据库，不触发实验运行。

## 代码变化

- 药物详情新增分项呈现：Exp006 原排名、B 方案 WTCS、S2 剂量/时间/质量条件、跨剂量 Top 10 复现率、独立 S1 排名、PRISM ER+/ER− 指标，以及带 evidence ID 的机制路径。缺失值保持空值，不按药名补配、不合成疗效总分。
- 新增 `/compare` 运行版本比较页；同类型运行并列显示参数、软件版本、输入哈希和结果摘要，S2 只按精确条件键对齐。
- Dashboard 展示最近 10 个 AnalysisRun 状态，并可按运行 ID 查询同步任务状态。
- S2 详情用分页接口读取所有条件，保留每个剂量/时间独立结果。
- S1 页增加 Exp010/GSE139038 独立配对队列复核和外部 LINCS 条件排名；接口只服务 ER+ 项目，校验实验 manifest 中摘要、数据集清单和排名 CSV 的 SHA-256，其他项目返回明确 unavailable。
- 图谱关系提供全部、直接药物—靶点、其他疾病/通路关系三种筛选；直接关系仅按药物节点与 Gene/ProteinTarget 端点类型判定。
- 点击已加载关系可根据其 evidence ID 打开来源证据弹窗；本次使用正式 GraphBuild 子图中的真实 edge evidence ID 检查证据 API。
- 六个页面已做路由级动态载入，项目/上传弹窗仅在打开时载入；导航 shell 不静态导入 Ant Design。Vite 初始静态 JS 依赖闭包 313.96 kB、最大页面入口块 20.50 kB。ECharts 与 Cytoscape 只在对应页面载入，图表块 573.89 kB、Cytoscape 块 451.17 kB；超过 500 kB 的剩余告警来自按需加载的 S1 图表块。

## 未覆盖范围

本报告不是桌面浏览器视觉验收；没有验证原生文件选择器操作、各屏幕尺寸布局、键盘可访问性或所有按钮交互。通用 Job 页面/队列仍按方案暂缓；生产认证、授权和部署加固未完成。

## 复现

- 命令：`python scripts/verify_phase_d_frontend.py`（在 Vite 5173、FastAPI 8000 及 Docker 数据库服务运行时执行）。
- 机器可读记录：`experiments/platform_phase_d/phase_d_verification.json`。
- JS 构建文件大小与 SHA-256 同记录保存。
