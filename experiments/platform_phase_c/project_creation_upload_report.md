# 新项目创建与数据登记验收报告

日期：2026-11-14

## 本轮实现

- 新建项目表单增加“项目用途”：正式研究项目或 `test_only` 软件测试项目。默认值仍是正式项目。
- 后端 `ProjectCreate` 将状态限制为 `active` 或 `test_only`，创建时保存所选状态；非法状态会被 Pydantic 拒绝。
- OpenAPI 与 API 契约已同步，明确状态枚举及默认值。

## 实际验收

### 页面创建

在 DiseaseGraph Lab 页面创建了项目“软件测试：新建项目界面验收”，标准疾病 ID 为 `MONDO:0000001`。页面返回新项目 Dashboard，显示 `test_only`、0 个 S1 检验基因、0 个显著差异基因及空数据列表，没有带入 ER+ 历史分析结果。该项目 ID 为 `2b7e1896-d6be-4e1c-b083-db548ef4cb57`。

### 上传与 Vite 代理

Docker Engine 当前未运行，PostgreSQL 容器不可用。为继续本机验证，使用项目内独立临时 SQLite 数据库 `experiments/platform_phase_c/.tmp/ui_smoke.db` 和独立上传目录；未改动正式数据库文件或科研源文件。

通过 Vite 的 `/api` 代理执行真实 HTTP 请求：

- `GET /projects`：HTTP 200。
- 创建 `test_only` 测试项目：返回状态 `test_only`。
- 上传 1 行合成 DEG CSV：HTTP 201，登记类型 `precomputed_deg`，文件名 `ui_test_deg.csv`。
- 上传记录及列表状态均为 `validation_pending`；检测 1 行、4 列；`analysis_started=false`；AnalysisRun 数量仍为 0。
- 输入 SHA-256：`93028558088bc35ce8eb9adb3fd87aa85615f6beeda40bdeff656b7a5d77f08c`。
- SQLite 验收项目 ID：`5dc2105e-b2f6-4e77-9e67-916977742cd0`。

样例仅包含一条合成 ESR1 记录，仅用于软件验收，不代表 S1 实验数据。上传流程没有自动触发分析。

## 验收结果

| 项目 | 结果 | 证据 |
|---|---|---|
| 项目用途字段及默认值 | 通过 | OpenAPI 明确 `active`、`test_only`；未填写时默认 `active` |
| 状态校验 | 通过 | 自动化测试检查 `test_only` 持久化并拒绝非法状态 |
| 前端创建测试项目 | 通过 | 页面创建后显示 `test_only` 且无继承分析结果 |
| Vite 到 FastAPI 代理 | 通过 | 经 `http://127.0.0.1:5173/api/v1` 的项目读取、创建和上传均成功 |
| 数据登记门禁 | 通过 | 上传状态为 `validation_pending`，没有创建 S1 AnalysisRun |
| 后端回归 | 通过 | 后端隔离模式 35 项测试通过；OpenAPI 共 29 条路径 |
| 前端生产构建 | 通过 | `npm run build` 成功；JS bundle 约 2.82 MB，仍有 500 KB 体积提示 |

## 限制与后续

首次执行本报告时 Docker Engine 未运行，因此上传 API 验收使用独立临时 SQLite；该历史限制不代表之后的正式数据库状态。实际文件登记请求通过 Vite 代理和 FastAPI 完成；浏览器原生文件选择器当时未能可靠触发，因此没有声称完成视觉 E2E。

## 2026-11-14 上传控件可访问性补充

- 文件输入框新增明确可见标签、稳定 `id`/`name` 和 `aria-label`，帮助键盘及辅助技术用户识别文件选择控件。
- `npm run build` 通过。当前 Windows 自动化会话发现 Edge 窗口处于最小化/用户输入状态；按恢复流程刷新窗口句柄后仍无法截取状态，因此未实际选择/提交文件，本补充不宣称完成原生文件选择器 E2E。
- Docker Engine 后续恢复并完成正式 PostgreSQL/Neo4j 集成验收，详见 [Phase E 报告](../platform_phase_e_report.md)。
- 随后以独立无头 Edge 通过真实页面完成 test_only 项目的文件输入、数据类型选择、上传提交和待校验状态核验，见[浏览器上传 E2E 报告](browser_upload_e2e_report.md)。该流程通过 DevTools 设置浏览器文件输入，没有打开 Windows 原生选择器窗口；原生对话框仍未验收。
