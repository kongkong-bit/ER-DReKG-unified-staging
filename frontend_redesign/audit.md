# DiseaseGraph Lab 前端现状审计

审计日期：2026-11-15  
范围：`frontend/` 只读检查；未修改 API、数据库或科研计算。

## 技术栈

- React 19、TypeScript 5.8、Vite 6、Ant Design 6、React Router 7、TanStack Query 5。
- ECharts 6 + `echarts-for-react`：`src/ChartRenderer.tsx` 按需注册 Bar/Line/Scatter、Canvas renderer、Tooltip、Legend。
- Cytoscape.js 3.33：`src/pages/GraphPage.tsx` 动态加载，按组件生命周期创建/销毁实例。
- API 封装：`src/api.ts` 统一请求 `/api/v1`，项目 ID 作为查询边界；上传和分析运行仍走原有接口。

## 路由与页面

| 路由 | 页面 | 现有真实数据/能力 |
| --- | --- | --- |
| `/` | 项目总览 | 项目、数据集、S1/S2/图谱摘要、分析运行 |
| `/s1` | S1 疾病分析 | 差异基因、火山图、GO/Reactome/Hallmark、外部队列 |
| `/s2` | S2 药物筛选 | 候选证据、WTCS、剂量/时间、稳定性、PRISM、S2 运行 |
| `/graph` | 知识图谱 | GraphBundle/GraphBuild、Cytoscape 子图、筛选、路径和证据 |
| `/drugs` | 机制证据 | 药物详情、机制路径、证据矩阵、KG07 解释 |
| `/compare` | 可靠性分析 | AnalysisRun 比较、Exp006–Exp011 报告 |
| `/final-results` | 最终 Top10 | 冻结排名、Final05 审计、证据矩阵和研究图表 |

## 可复用部分

- `App.tsx` 的布局、项目切换、移动端导航和项目/数据上传入口。
- `src/designTokens.ts` 的颜色集中管理；`src/styles.css` 的全局布局、焦点环、响应式和 reduced-motion。
- Ant Design 的 Button/Card/Table/Modal/Drawer/Form/Alert/Statistic/Tag；`ConfigProvider` 已接入中文 locale 和主题 token。
- `ChartRenderer`、现有 API hooks、数据表分页、项目隔离和真实静态 Final05 研究文件。

## 需要持续关注或重构的部分

- GraphPage 仍然是高复杂度单文件：筛选、GraphBuild 操作、Cytoscape 生命周期、路径和证据详情需要后续拆分为工作区子组件，但不能改变查询边界。
- 部分页面使用内联列定义和内联文案；统一术语继续放在 `src/locales/zh-CN.ts`，不要改 API 字段。
- 图谱在移动端已转单列，但需要人工确认节点详情和关系列表在 375px 上仍可操作。
- 大型 ECharts/Cytoscape chunk 仍有 Vite 500KB 提示；优先按需加载和生命周期复用，不能为了消除提示而删除图表或图谱能力。

## 已发现的文案边界

用户可见状态和导航已通过 `zh-CN.ts` 映射；WTCS、FDR、LINCS、PRISM、GEO、Reactome、基因符号、药物标准名、化合物 ID、GraphBuild 和 Evidence ID 保留标准标识。缺失数据显示“暂无数据”或“—”，不以 0 代替。

## Skill 依据

- React：语义 HTML、谨慎使用 `React.memo`、对 Modal 正确管理焦点。
- Chart：关系图使用 Cytoscape，并提供关系详情/可读回退；排名使用可排序表格和直接数值标签。
- UX：可见焦点环、稳定加载反馈、`prefers-reduced-motion`、响应式断点和不依赖颜色的状态表达。
