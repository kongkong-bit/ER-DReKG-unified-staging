# 前端视觉验收报告

日期：2026-11-15

## 已有验证

- `npm run build`：已通过 TypeScript 构建和 Vite 打包。
- Edge DevTools smoke：覆盖 `/`、`/s1`、`/s2`、`/graph`、`/drugs`、`/compare`、`/final-results`，项目选择、标题断言、Cytoscape canvas 和图谱三列布局已通过。
- 移动端：390×844 导航 Drawer 打开，无横向溢出。
- 可访问性：`prefers-reduced-motion` 和键盘可见焦点检查已通过。
- 数据核验：Final Top10 的 JSON/CSV 顺序一致；Exp006–Exp011 报告副本与源文件 SHA-256 一致。
- 截图：已生成 9 张交付截图，覆盖总览、S1、S2、图谱页面与工作区、机制证据、可靠性、Top10 和移动端导航；验收脚本在每个路由截图前回到顶部。

## 当前限制

- 未安装 Playwright，因此浏览器验收使用现有 Edge CDP 脚本 `frontend/scripts/edge_visual_smoke.mjs`。
- 尚未自动覆盖每一个图谱节点拖动、每个筛选器和完整屏幕阅读器流程，需要人工验收。
- 构建仍有 ECharts/Cytoscape chunk 超过 500KB 的提示；不影响构建成功，后续可继续做按路由拆包。
