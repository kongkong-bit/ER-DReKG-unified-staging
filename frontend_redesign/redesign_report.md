# 前端视觉重构报告

## 已完成

1. 建立全站浅色、低饱和、系统字体的 Apple-inspired Scientific Minimalism 设计系统。
2. 统一导航、顶栏、项目切换、按钮、卡片、表格、表单、Drawer、Modal、Tag、状态和焦点样式。
3. 统一中文界面文案映射；保留 WTCS、PRISM、LINCS、FDR、数据库名称、基因/药物标准名和内部 API 字段。
4. 项目总览增加研究流程和证据边界；S1/S2 优先呈现结论、统计摘要和证据解释。
5. 知识图谱调整为桌面三列科研工作区，保留 Cytoscape、节点选择、边证据、筛选、路径高亮和版本化 GraphBuild。
6. 可靠性分析展示真实 Exp006–Exp011 报告；最终结果保留 Final05 审计限制和真实 Top10。
7. 加入页面过渡、hover/active/focus、加载反馈和 reduced-motion；移动端使用导航 Drawer 和适配布局。

## 数据保护

本轮只改动前端展示层和验收文档。没有修改 S1 差异基因、S2 WTCS、正式 Top10、Exp006–Exp011、Final05、Neo4j、API 契约或数据库数据。没有加入模拟科研结果。

## 后续可选项

GraphPage 仍可继续拆分为筛选面板、画布、实体详情和证据抽屉，以降低维护复杂度；这属于结构性重构，不应与视觉改造混合进行。
