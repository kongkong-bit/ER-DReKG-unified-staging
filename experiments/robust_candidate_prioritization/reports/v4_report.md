# v4 发现版结果

- 预注册规则：`protocol_v4_discovery.md`（SHA-256 `ffa4fe9bfcf0d920…`）。
- 结构池 652 个药物；过剂量门槛 91 个；再过「3/4 算法 ≥0.70」共识门槛 **84** 个。
- 免权重发现分：`S_disc = median(p_WTCS, p_ClassicKS, p_Zhang, p_XSum)`。
- 剂量 bootstrap（1000 次，种子 20261120）后，稳定性门槛使用 **no_gate**；各级存活数：{'0.70': 11, '0.60': 15, '0.50': 17, 'no_gate': 84}。
- 稳定性分布：≥0.70 的 11 个、0.50–0.70 的 6 个、<0.50 的 67 个。
- v4 Top20 中**有方向一致机制链的只有 5 个**。
- 机制可解释 Top10（A 方案）输出 **10** 个（其中 5 个来自 Top20，5 个为按协议扩展自 Top20 之外）；高置信核心集（C 方案）**6** 个。

## 四算法一致性

- 四种算法的药物级中位数两两 Spearman：见 `v4_drug_scores.csv`；`S_disc` 与 WTCS 单独排序的秩相关 = 0.926。
- 共识门槛（≥3/4 算法前 30%）淘汰了 7 个已过剂量门槛的药物。

## v4 Top20

| # | 药物 | `S_disc` | 稳定性 | 链数 | ER+ 链 | PRISM |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 1 | CGP-60474 | 0.998 | 1.00 | 0 | 0 | missing |
| 2 | romidepsin | 0.997 | 1.00 | 0 | 0 | missing |
| 3 | alvocidib | 0.994 | 0.90 | 2 | 1 | anti_er_positive |
| 4 | WZ-3105 | 0.988 | 1.00 | 0 | 0 | missing |
| 5 | carfilzomib | 0.988 | 1.00 | 4 | 0 | anti_er_positive |
| 6 | pentobarbital | 0.988 | 0.87 | 0 | 0 | no_clear_direction |
| 7 | bortezomib | 0.988 | 0.86 | 4 | 0 | anti_er_positive |
| 8 | rucaparib | 0.986 | 0.64 | 1 | 0 | anti_er_positive |
| 9 | triptolide | 0.985 | 0.94 | 0 | 0 | missing |
| 10 | emedastine | 0.984 | 1.00 | 0 | 0 | anti_er_positive |
| 11 | TPCA-1 | 0.980 | 0.64 | 0 | 0 | anti_er_positive |
| 12 | dacinostat | 0.979 | 0.83 | 0 | 0 | anti_er_positive |
| 13 | lacidipine | 0.974 | 0.81 | 0 | 0 | support |
| 14 | tioconazole | 0.974 | 0.67 | 0 | 0 | no_clear_direction |
| 15 | RG-108 | 0.968 | 0.63 | 0 | 0 | missing |
| 16 | doxepin | 0.965 | 0.59 | 0 | 0 | support |
| 17 | GDC-0879 | 0.964 | 0.58 | 0 | 0 | no_clear_direction |
| 18 | lestaurtinib | 0.957 | 0.36 | 0 | 0 | anti_er_positive |
| 19 | midostaurin | 0.955 | 0.33 | 2 | 0 | anti_er_positive |
| 20 | HG-5-113-01 | 0.953 | 0.39 | 0 | 0 | missing |

## 机制可解释 Top10（A 方案）

| # | 药物 | v4 名次 | `S_disc` | 链数 | ER+ 链 | PRISM 方向 | 链靶点 |
| ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| 1 | alvocidib | 3 | 0.994 | 2 | 1 | anti_er_positive | CDK1; CDK9 |
| 2 | carfilzomib | 5 | 0.988 | 4 | 0 | anti_er_positive | PSMA3; PSMA5; PSMB7; PSMD3 |
| 3 | bortezomib | 7 | 0.988 | 4 | 0 | anti_er_positive | PSMA3; PSMA5; PSMB7; PSMD3 |
| 4 | rucaparib | 8 | 0.986 | 1 | 0 | anti_er_positive | PARP1 |
| 5 | midostaurin | 19 | 0.955 | 2 | 0 | anti_er_positive | PRKCI; PRKCZ |
| 6 | mitoxantrone | 21 | 0.952 | 1 | 1 | anti_er_positive | TOP2A |
| 7 | acetazolamide | 27 | 0.928 | 1 | 1 | no_clear_direction | CA12 |
| 8 | azacitidine | 30 | 0.916 | 2 | 0 | anti_er_positive | DNMT1; DNMT3A |
| 9 | pilaralisib | 33 | 0.906 | 1 | 0 | anti_er_positive | PIK3R3 |
| 10 | AT-7519 | 36 | 0.899 | 6 | 1 | anti_er_positive | CDK1; CDK10; CDK12; CDK17; CDK20; CDK9 |

## 高置信核心集（C 方案）

| # | 药物 | v4 名次 | `S_disc` | 链数 | ER+ 链 | PRISM 差值 |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | acetazolamide | 27 | 0.928 | 1 | 1 | -0.069 |
| 2 | pindolol | 38 | 0.896 | 2 | 0 | 0.001 |
| 3 | iguratimod | 45 | 0.876 | 1 | 0 | 0.029 |
| 4 | palbociclib | 50 | 0.865 | 1 | 1 | 0.633 |
| 5 | belinostat | 59 | 0.846 | 2 | 1 | 0.655 |
| 6 | quizartinib | 62 | 0.838 | 1 | 1 | -0.034 |

## 与 v3 交付版的关系

- v4 不使用外部 S1 与 PRISM 排序，因此这两项在 v4 中只是标签；v3 用它们做过资格门槛。
- v4 的机制层是「方向一致链」门槛，不是注释密度打分；因此机制 Top10 与 v3 的名单会明显不同。
- 所有结果仍是计算优先级，不是疗效或临床结论；没有链的候选是知识覆盖不足，不是无效。