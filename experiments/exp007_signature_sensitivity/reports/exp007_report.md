# Exp007 — S1 基因签名规模对药物排名的影响

## 人话说明
同一批 4761 条历史 LINCS 真实 MCF7 药物扰动记录，用六种疾病基因名单重算。分数和排名的变化只用于评估方法稳定性，不能解释为临床疗效。

## 方法
WTCS、LINCS 数据、BING 背景与历史正式筛选的 24 h 且 distil_cc_q75≥0.2 签名保持一致。药物按药物ID、细胞、剂量、时间分组，组内取 WTCS 中位数；剂量和时间不混合。方案 A 使用历史 BING 交集（70 UP/55 DOWN）；B_matched125=70/55；B100=50/50、B150=75/75、B200=100/100、B300=150/150。B 方案从 limma 全表限制至 BING 且 FDR<0.05，按 FDR、|logFC|、基因符号确定顺序。

## 结果
共生成 28566 条签名级分数、22290 条条件级结果。排名比较见 `results/ranking_comparison.csv`，分数分布及稳定性图见 figures。更负 WTCS 是表达关联方向上的逆转信号，不是更好的药效证明。

复现核验将 4,761 条历史 A 方案与新算 A_original 按 Signature ID 逐条比较，WTCS 最大绝对差为 5.82×10⁻¹⁴；历史 B 与新算 B200 最大绝对差为 6.65×10⁻¹⁴，ID 全部匹配且没有差异超过 1×10⁻¹⁰。明细见 `results/historical_reproduction_check.csv`。

## 可复现性和限制
输入路径、SHA-256、参数和缺失签名写入 `results/run_manifest.json`。基因背景为 GCTX 中映射成功的唯一 BING 符号，固定为同一背景。历史 S1、S2 和 Smoke Test 文件均只读。本实验没有使用随机数据。
