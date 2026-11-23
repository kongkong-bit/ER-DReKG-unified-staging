# DiseaseGraph Lab Design System

## 设计原则

以低对比度灰白背景、清楚的信息层级和克制的蓝色强调科研动作。优先阅读真实数据、实验条件和证据局限，不用装饰性数字替代结果。

## 全局 Token

| Token | 值 | 用法 |
| --- | --- | --- |
| 页面背景 | `#F5F5F7` | 全局工作区 |
| 卡片背景 | `#FFFFFF` | 内容面板 |
| 主文字 | `#1D1D1F` | 标题与主要内容 |
| 次文字 | `#6E6E73` | 解释、辅助标签 |
| 品牌蓝 | `#2878D0` | 主按钮、当前导航、链接 |
| 成功/警告/错误 | `#39856D` / `#B87928` / `#BD4C4C` | 低饱和状态反馈 |
| 边框 | `#E8E8ED` | 表格、卡片、输入边界 |
| 卡片圆角 | `16px` | 普通卡片 |
| 大面板圆角 | `22px` | 抽屉/大面板 |
| 交互过渡 | `180ms` | hover、焦点和页面进入 |

CSS Token 定义在 `src/styles.css`；共享图表/图谱颜色在 `src/designTokens.ts`；Ant Design Token 在 `src/main.tsx`。

## 字体和排版

采用系统字体：`-apple-system`、`PingFang SC`、`Microsoft YaHei`、`Noto Sans CJK SC`、`Segoe UI`。不请求外部字体服务。页面主标题 25–32px，卡片标题约 14px，正文/表格约 12–14px；指标使用 tabular figures。

## 响应式与交互

- 桌面：固定 252px 导航，内容最大宽 1700px。
- 1180px 以下：收窄侧栏与留白；卡片指标改为两列。
- 900px 以下：侧栏改为 Ant Design Drawer，顶栏菜单始终可操作；图谱工作区转为单列。
- 600px 以下：卡片/统计缩紧，表格保持横向滚动，不强行压缩字段。
- `:focus-visible` 为按钮、链接和表单控件提供可见焦点环。
- 页面过渡、按钮和卡片交互使用短时轻动效；`prefers-reduced-motion: reduce` 会收敛动画。

## 图表和图谱

ECharts 包装器设置统一低饱和配色、系统字形、深色 Tooltip 和约 220ms 动画。原始序列、坐标含义和科学数据不变。知识图谱工作区采用桌面三列：左侧检索/筛选，中间 Cytoscape 画布，右侧节点详情；窄屏按控件、画布、详情顺序纵向排列。

## 文案规则

`src/locales/zh-CN.ts` 集中维护导航、通用状态、分析运行类型和图谱类型显示名。只在 UI 渲染层映射可见标签，不改请求/响应枚举或 ID。LINCS、WTCS、FDR、MCF7、PRISM、GEO、Reactome、ChEMBL、基因符号、化合物名和可审计标识保留原值；对缺失值使用“暂无数据/无可比结果”，而不是把它当成 0。
