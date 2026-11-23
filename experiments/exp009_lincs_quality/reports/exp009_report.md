# Exp009 — 数据质量门槛会不会改变药物排名？

## 人话说明
把 LINCS 签名按重复实验一致性高低筛一遍，比较严格/宽松门槛下的药物排名；也检查官方提供的 TAS 分数。

## 结果
稳定 ID 合并得到 MCF7 化学扰动 11850 条 24 h 可评分签名。主筛选为项目预设的 CC≥0.2；CC≥0.1、0.3 和额外 TAS≥0.2 仅用于敏感性比较。具体签名数/药物数见 `qc_threshold_comparison.csv`，分布见 `lincs_metric_audit.csv` 与图。`metadata_join_sensitivity.csv` 对照了历史把药物显示名称也加入连接条件的做法；显示名称拼写差异会丢掉真实 ID 匹配的签名。

## CC 与 TAS 不是同一个门槛
`distil_cc_q75` 描述重复签名一致性，CC≥0.2 是本项目选择的 QC 过滤值；它不是普适标准。TAS 是 Broad 的另一种综合活动分数，[CMap 2017 论文](https://doi.org/10.1016/j.cell.2017.10.049)在特定化合物筛选情境使用 TAS≥0.2，不能把该数值解释成 CC 阈值。我们保留 LINCS 发布的 TAS 原值，并只把 TAS≥0.2 作为单独的附加敏感性条件。由于发布字段 `distil_ss` 未能确认等于官方 TAS 公式中的原始 SS，本实验不重算 TAS，审计证据见 `tas_calculation_audit.csv`。

## 剂量与结果边界
所有结果按剂量与时间分别汇总；药物没有被挑选“最有利”的剂量作为总分。剂量间排序稳定性见 `dose_direction_stability.csv`，药物逐剂量分数热图见 figures。QC 影响排名只能说明筛选敏感性，WTCS 是表达逆转关联，不能证明细胞杀伤或临床有效。
