# 前端构建与视觉验收记录

日期：2026-11-15

## 构建

- 命令：`npm run build`
- 结果：通过（`tsc -b` 与 `vite build` 成功）。
- 构建提示：`index` 主 chunk 约 548 KB、ECharts renderer chunk 约 574 KB，超过 Vite 500 KB 默认提醒阈值；构建未失败。当前改造没有新增依赖。

## 浏览器 Smoke Test

- 环境：本机 Microsoft Edge Headless + Chrome DevTools Protocol；工程未安装 Playwright，所以用 Node 内置 WebSocket 编写轻量检查，没有引入浏览器测试包。
- 前端：`http://127.0.0.1:5175`；API：本机现有 `http://127.0.0.1:8000`，页面经 Vite `/api` 代理请求真实项目接口。
- 选择真实项目 `erpos-gse42568`，仅执行读取操作。
- 检查页面：项目总览、S1、S2、知识图谱、机制证据、可靠性分析、Top10 最终结果。7 个路由均成功选择目标项目，且页面标题断言全部通过。
- 知识图谱：Cytoscape canvas 已生成；桌面工作区为 3 列。
- Final Top10：页面 JSON 与导出 CSV 均为 10 条，`rank + pert_id + drug_name` 顺序逐行一致。
- Exp006–Exp011：6 份静态浏览报告与 `experiments/` 原报告 SHA-256 相同；源文件只读。
- 移动端：390×844 打开导航抽屉；无横向溢出。
- 系统偏好：模拟 `prefers-reduced-motion: reduce`，页面动画时长断言通过。
- 键盘操作：Tab 导航后焦点命中可见控件，`:focus-visible` 焦点环断言通过。
- 截图：`screenshots/`。可复跑脚本：`node scripts/edge_visual_smoke.mjs`（本机需启动前后端并可运行 Edge）。

## 验收范围与限制

- 页面使用当前 API/静态 Final05 文件的真实返回数据；Top10 截图显示冻结排名与真实审计字段。
- Smoke 检查覆盖路由、项目切换、可见标题、Cytoscape 画布存在、三栏布局及移动端溢出；未自动模拟鼠标拖动每个节点或逐项操作所有过滤器。
- 键盘焦点状态与减少动态效果使用 CSS/系统偏好实现；本轮没有完整的屏幕阅读器或人工可访问性评估。
- 本次只针对前端构建与视觉进行验收；没有更改/运行新的 S1/S2 科学计算，也没有对数据库进行写入。
