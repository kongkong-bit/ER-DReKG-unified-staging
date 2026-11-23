# v4 发现版协议（执行前预注册）

- 立文时间：2026-11-20 19:2x (+08:00)，**在计算 v4 结果之前**
- 执行脚本：`scripts/run_v4_discovery.py`
- 与旧版本关系：v2（`selection_protocol.json`）与 v3（`reports/protocol_v3_deliverable.md`）结果保留，不被本协议改写；v4 结果并列报告。

## 1. v4 要修的两件事

1. **权重无依据**：v2/v3 的 `S_data = 0.45·S_dose + 0.30·S_algorithm + 0.25·S_external` 是先验权重，双算法项在合格候选内几乎无区分度。v4 改用**四算法免权重秩聚合**。
2. **机制分=注释密度**：v2/v3 的机制分与靶点注释数 Spearman 0.899。v4 改用**方向一致机制链**作为门槛，ER+ 方向与外部数据只作标签，不参与排序。

## 2. 分析域

- 与 v2 相同：修正 WTCS 与 Classic KS 的签名交集 **4,761 条**，MCF7 / trt_cp / 24 h / `distil_cc_q75 ≥ 0.2`，剔除 `0.0 um` 载体。
- 结构池（百分位分母）：剂量数 ≥3 的 **652** 个药物。

## 3. 第 1 层：发现（只使用 LINCS + S1，不使用任何外部数据）

### 3.1 四种评分算法

| 算法 | 来源 | 说明 |
| --- | --- | --- |
| WTCS | 最终修正结果 | Broad 风格双侧加权 KS |
| Classic_KS | exp008 方案 B200 | 非加权 KS |
| Zhang_signed_rank | exp008 方案 B200 | 绝对秩点积，符号保留 |
| XSum_zscore_adaptation | exp008 方案 B200 | 前 150 个高 |z| 基因的符号和 |

四者均已在同一 4,761 条签名上算过，**不重新定义算法**。

### 3.2 剂量层与药物层

- 每个 `(pert_id, dose)`：对四种算法分别取签名中位数。
- 每个药物：对四种算法分别取**跨剂量中位数**（不挑剂量、不按剂量加权、不用 10 μM）。

### 3.3 剂量门槛（与 v2 完全一致，不放宽）

```text
n_dose_conditions ≥ 3
WTCS_negative_dose_fraction ≥ 0.6  且  Classic_KS_negative_dose_fraction ≥ 0.6
WTCS_dose_median < 0              且  Classic_KS_dose_median < 0
strong_flip = 0（不同时出现 ≥+0.20 与 ≤−0.20）
```

### 3.4 百分位

对每种算法，在 652 个结构池药物上计算**逆转百分位** `p_a`（值越负、`p_a` 越接近 1）：

```text
p_a = 1 − (ascending_rank(x) − 1) / (n − 1)，n = 652，并列取平均秩
```

### 3.5 发现分（免权重）

```text
S_disc = median( p_WTCS , p_ClassicKS , p_Zhang , p_XSum )
```

用中位数而不是均值：允许一个算法严重偏离而不主导结果，也不需要任何权重。

### 3.6 算法共识门槛

```text
四种算法中至少 3 种满足 p_a ≥ 0.70
```

这是 v2「双算法各进前 30%」的免权重推广，且要求多数算法一致，而不是任取两个。

### 3.7 剂量 bootstrap 稳定性

- 对每个合格药物，有放回重抽它的剂量（抽 `n_dose` 次），重算四种药物的跨剂量中位数 → 各自映射到**冻结的原始 652 分布**得到 `p_a` → 重算 `S_disc`。
- 每次重抽后，把全部合格药物按 `S_disc` 重排，记录每个药物是否进入前 20。
- 重复 **1,000 次**，`stability_top20` = 进入前 20 的比例。
- 随机种子固定为 **20261120**。

## 4. 第 2 层：机制链（门槛 + 解释，不参与排序）

### 4.1 方向映射（预注册）

| 关系类型 | 方向 |
| --- | --- |
| INHIBITOR / ANTAGONIST / BLOCKER / INVERSE_AGONIST / NEGATIVE_ALLOSTERIC_MODULATOR | 抑制（−） |
| AGONIST / ACTIVATOR / PARTIAL_AGONIST / POSITIVE_ALLOSTERIC_MODULATOR / OPENER / POSITIVE_MODULATOR | 激活（+） |
| TARGET / ENZYME / TRANSPORTER / CARRIER / MODULATOR / SUBSTRATE | **无方向，不进入链检验** |

### 4.2 一条「方向一致机制链」需同时满足

1. 药物与靶点之间存在**带证据记录**的 drug→gene 边（精确 InChIKey 匹配药物节点，禁止药名匹配）；
2. 该靶点是 S1 差异基因（limma FDR < 0.05）；
3. **方向相反**：抑制类药物靶向 S1 上调基因（logFC > 0），或激活类药物靶向 S1 下调基因（logFC < 0）；
4. 该靶点落在某个 S1 显著通路内（`pathway_gene_links` adjusted p < 0.05）。

`ER+ 链` 额外要求该通路属于雌激素反应程序（`HALLMARK_ESTROGEN_RESPONSE_EARLY` / `_LATE` / Reactome `Estrogen-dependent gene expression`）。

### 4.3 链门槛

- 进入「机制可解释」名单的候选必须 **≥1 条方向一致链**。
- 没有链的候选不判为无效，标 `knowledge_coverage_missing`。

## 5. 排序与取数

### 5.1 v4 数据驱动 Top20

```text
按 S_disc 降序 → stability_top20 降序 → WTCS_dose_median 升序 → pert_id 升序
仅纳入 stability_top20 ≥ 0.70 的药物
```

- 若稳定 ≥0.70 的药物不足 20 个，按预注册阶梯依次降到 0.60、0.50、不设门槛，记录使用的那一级。
- 不补位、不手工挑药。

### 5.2 机制可解释 Top10（A 方案）

```text
在 v4 Top20 中取「≥1 条方向一致链」者，按 S_disc 降序取 10
不足 10 时：扩展到 Top20 之外的有链候选，仍按 S_disc 降序补足，并在表中标注 rank_v4 > 20
仍不足 10 就输出更少
```

### 5.3 高置信核心集（C 方案）

```text
在全部 v4 合格候选中，同时满足「≥1 条方向一致链」且「PRISM 方向不为反 ER+」者，全部列出
不论数量，不补位
```

## 6. 标签（不参与排序）

- `PRISM ER+ vs ER−`：差值 ≥+0.1 记 support，|差值| <0.1 记 no_clear_direction，≤−0.1 记 anti_er_positive。
- 外部 S1（GSE139038）：仅作复现标签，**完全不参与 v4 排序**。
- ER+ 链：单独标记。

## 7. 输出

- `results/v4_drug_scores.csv`（652 个药物：四算法百分位、S_disc、共识、门槛）
- `results/v4_eligible.csv`
- `results/v4_stability.csv`
- `results/v4_top20.csv`
- `results/v4_mechanism_top10.csv`
- `results/v4_core_c.csv`
- `results/v4_chains.csv`（每条链的详细记录：药物、靶点、关系、logFC、通路、adjust p、evidence 键）
- `reports/v4_report.md`

## 8. 纪律

- 本文件写定后，四算法集合、中位秩聚合、共识阈值 3/4、bootstrap 次数与种子、稳定性门槛、方向映射、链定义均不可改。
- 如需调整，必须发 v5 并说明理由，同时并列报告 v4。
- v4 结果仍然只是计算优先级，不是疗效、适应证或临床结论。
