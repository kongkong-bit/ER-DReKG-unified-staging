# Exp008：评分算法和随机基因集检验

## 人话版

我们用同一批 4,761 条真实 LINCS 签名，问两件事：换评分公式后，靠前药物还像不像；真实疾病基因名单的 WTCS 是否比随机抽取同样多的 BING 基因更负。

## 随机检验

- 每个随机查询从同一 BING 背景抽取与真实查询等量的 UP/DOWN 行；UP 与 DOWN 不重叠。
- A 是 70 UP + 55 DOWN；B 是 100 UP + 100 DOWN。
- 2,000 个随机查询在全部 signature 间共享。统计单位是同一药物、剂量、时间下 signature WTCS 中位数。
- 单侧经验 P：`(1 + count(null_WTCS <= observed_WTCS)) / 2001`；随后对 A、B 各自全部 3,715 个条件分别做 BH 校正。

| 方案 | 药物剂量条件 | q<0.05 条件 | 最小 q |
|---|---:|---:|---:|
| A | 3715 | 536 | 0.00623 |
| B200 | 3715 | 760 | 0.003933 |

这说明部分真实 WTCS 比当前随机基因集零模型更负。它不代表临床疗效概率，也不等于官方 CMap Tau。

## 算法排名

方法的分数尺度不同，只用排名相关和 TopK 重合比较。B200 中 Classic KS 与 WTCS 的排名相关约 0.878，但 Top10 只重合 1 个；Zhang 适配版与 WTCS 相关约 0.902，Top10 重合 2 个；XSum 适配版相关约 0.577，Top10 重合 4 个。整体排序相关不低也不保证最前面的药物相同。

## 三个容易混淆、但不是一回事的量

- **WTCS** 是单条 LINCS 扰动签名与疾病 UP/DOWN 查询之间的原始表达关联分数。负值表示表达关联方向相反。
- **NCS** 是先有 WTCS 后，按相同细胞系和扰动类型的参考签名分布做标准化；它不是把 WTCS 除以随机基因集的标准差。
- **Tau** 再把观察到的 NCS 和指定参考查询集 Q_ref 比较，表示相对于这批参考查询的连接强度；它不是 WTCS 排名、随机置换 P 值或经验 P 值的另一种写法。
- **本项目的经验 P 值**只回答：从 BING 随机抽取同等大小、上下调不重叠的基因集合时，得到同样或更负 WTCS 的频率。它不需要也不提供官方 NCS/Tau 的参考分布。

CMap 2017 对 WTCS、NCS、Tau 的定义可见 [原文](https://doi.org/10.1016/j.cell.2017.10.049)。当前工程没有可核实的官方 Touchstone 匹配 WTCS 分布和 Q_ref，因此 NCS/Tau 均记为 `NOT_AVAILABLE`，没有代造数值。

## 方法边界

- WTCS 按 Broad CMap 加权双向 GSEA/KS 方向保留原始分数。
- Zhang 与 XSum 的论文输入涉及扰动幅度；本项目手头 Level 5 是 COMPZ 标准化 z 样分数，不是原始 logFC。因此结果标成 COMPZ 输入适配版，不声称完全复刻原始输入。
- NCS 需要匹配细胞系和扰动类型的参考分布，Tau 需要参考查询集。本项目没有合格的参考集合，故标记 `NOT_AVAILABLE`，没有用普通 Z 分数或 WTCS 百分位替代。
- 经验 P 只对当前 BING 随机抽样零模型有效。不同零模型会给不同显著性；显著不等于药物有效。

## 输出与测试

签名级和药物条件级评分在 `method_signature_scores.csv`、`method_condition_scores.csv`。置换结果在 `empirical_pvalues.csv`、`statistical_significance.csv`、`permutation_null_summary.csv`；Top10 B200 候选的完整零分布在 `candidate_null_distribution_top10.csv`。算法审计与置换参数在 `scoring_algorithm_audit.csv`、`permutation_manifest.json`。`tests/test_permutation.py` 检查向量化分数与标量 WTCS 参考实现一致；实验测试日志单独保存。
