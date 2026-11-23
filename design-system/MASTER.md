# DiseaseGraph Lab — Master Design System

版本：2026-11-15  
方向：Apple-inspired Scientific Minimalism

## 设计决策来源

本规范基于 UI/UX Pro Max 的 Design System、React、Chart 与 UX 查询结果，并结合现有 React 19 + Ant Design 6 + ECharts 6 + Cytoscape.js 工程约束确定。Skill 的科学分析查询命中了 Data-Dense Dashboard；其中通用字体和企业后台建议被项目约束覆盖，继续使用系统字体和科研工作区布局。

## 视觉原则

- 先呈现研究结论，再展开原始数据、方法和证据边界。
- 明亮、低饱和、少装饰；白色内容面板置于接近 Apple 浅色系统背景之上。
- 品牌蓝只用于主动作、当前导航、链接和图表强调；不使用荧光色堆叠。
- 不把所有内容塞进卡片；图谱、表格和证据路径保留足够连续空间。
- 科研限制必须可见，视觉层级不能掩盖数据缺失或证据不足。

## Tokens

| Token | Value | Use |
| --- | --- | --- |
| `--page` | `#F5F5F7` | 全局背景 |
| `--surface` | `#FFFFFF` | 卡片和工作区 |
| `--ink` | `#1D1D1F` | 主文字 |
| `--muted` | `#6E6E73` | 辅助文字 |
| `--accent` | `#2878D0` | 主动作和选中 |
| `--success` | `#39856D` | 已验证/已完成 |
| `--warning` | `#B87928` | 注意/边界 |
| `--danger` | `#BD4C4C` | 错误/失败 |
| `--line` | `#E8E8ED` | 边框和分隔线 |
| `--radius-card` | `16px` | 普通卡片 |
| `--radius-panel` | `22px` | 大型面板/抽屉 |
| `--motion` | `180ms` | 默认过渡，范围 150–250ms |

图表和图谱颜色统一由 `frontend/src/designTokens.ts` 管理；组件内不得新增散落的品牌色。

## Typography

使用系统字体：`-apple-system`、`PingFang SC`、`Microsoft YaHei`、`Noto Sans CJK SC`、`Segoe UI`。正文保持 12–14px、行高约 1.5；标题 25–32px；数字使用 tabular figures。科研标识、数据库名称、基因符号、药物通用名和 ID 保留原始值。

## Layout

- 桌面：252px 固定导航 + 最大 1700px 内容区。
- 1180px 以下：减少侧栏和内容留白，指标改为两列。
- 900px 以下：侧栏改为可访问 Drawer；图谱工作区转单列。
- 600px 以下：保留表格横向滚动，不压缩科学字段到不可读。
- 图谱桌面工作区：左侧筛选 / 中央 Cytoscape 画布 / 右侧实体详情。

## Interaction and accessibility

- 所有可交互控件具有语义元素、可见 hover/active/focus 状态和至少 44px 的可操作高度。
- Drawer、Modal 和详情面板提供可关闭路径；图谱详情支持 Escape。
- 加载使用稳定的 loading/skeleton 状态并保留布局空间；缺失值显示“暂无数据”。
- 支持 `prefers-reduced-motion: reduce`，禁用非必要动效。
- 图谱不只依靠颜色区分节点类型；同时使用标签、形状和证据摘要，并保留可读的关系详情。

## Data integrity

UI 只映射真实 API 或版本化静态研究文件。WTCS、PRISM、外部 S1、Final05、Exp006–Exp011 和 GraphBuild 只做展示层转换，不修改数值、排名、字段名或 API 契约。
