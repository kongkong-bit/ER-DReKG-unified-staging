# DiseaseGraph Lab 前端现状审计

审计时间：2026-11-15。此文档记录本次视觉改造开始时的代码结构与功能边界。

## 技术结构

- React 19、TypeScript、Vite 6、Ant Design 6、TanStack Query 5。
- 路由由 React Router 提供；网络请求集中在 `src/api.ts`，统一访问 `/api/v1`。
- Cytoscape.js 在 `src/pages/GraphPage.tsx` 中按需加载，节点/边、筛选、搜索、路径高亮、证据弹窗和 GraphBuild 操作均使用项目真实 API 数据。
- Apache ECharts 通过 `src/ChartRenderer.tsx` 加载；S1 火山图与 GO/Reactome/Hallmark 图使用后端/真实项目输出。
- 项目状态由 `ActiveProjectContext` 和顶栏项目选择器管理；每个 API 查询继续带原 project ID。

## 当前路由与页面

| 路由 | 页面 | 主要真实数据/操作 |
| --- | --- | --- |
| `/` | 项目总览 | 项目、数据集、S1/S2/图谱摘要、AnalysisRun |
| `/s1` | S1 疾病表达特征 | 差异基因、火山图、富集、外部队列；其他项目可登记并运行 S1 |
| `/s2` | S2 药物筛选 | 候选证据、剂量/时间、稳定性、PRISM、项目级 S2 操作 |
| `/graph` | 知识图谱探索 | 版本化 GraphBuild、GraphBundle、Cytoscape 子图、过滤和证据详情 |
| `/drugs` | 机制证据与药物详情 | 候选、条件结果、路径证据、KG07 解释和引用记录 |
| `/compare` | 原 AnalysisRun 版本比较 | 同项目同类型运行的参数、来源哈希及条件匹配结果比较 |
| `/final-results` | Final01–05 Top10 | 冻结排名、Final05 审计、证据矩阵与图表 |

没有独立的数据集管理页、用户系统或设置页；数据集登记/上传存在于现有顶栏对话框。本次没有创建虚假路由或新数据操作。

## 改造前观察

- 原视觉变量偏向深蓝后台，组件间距和圆角不一致，并从 Google Fonts 外链加载字体。
- 移动端把侧栏缩到窄图标栏，导航文字不可见，没有抽屉菜单。
- 多个页面把 `completed`、`validated`、`kg_mapping_status`、运行类型等后端枚举直接显示；组件文案已有部分中文，但缺少统一术语表。
- 图谱控件以宽工具栏堆在画布上方；画布和详情是两栏，画布可用面积受限。
- `/compare` 原本只提供运行版本比较，已有 Exp006–Exp011 的实验报告未在该页面形成实验索引。
- S1/S2/最终结果页面包含不少应保留的专业缩写与 ID，如 WTCS、LINCS、FDR、MCF7、PRISM、Entrez ID、GraphBuild、Evidence ID；这些不是普通界面译文。

## 数据安全边界

本次改动限于 `frontend/`：全局样式、前端文案、展示标签、可靠性报告静态副本、视觉测试脚本和截图。未修改 `src/api.ts` 的接口契约、S1/S2 计算、WTCS、药物排名、Neo4j 数据或既有实验结果。报告副本来自 `experiments/exp006...exp011` 原报告，供浏览器打开；源报告保留不动。
