# 选出 Top10 候选药物的流程（当前生效版 v4）

- 规则文件：[protocol_v4_discovery.md](protocol_v4_discovery.md)（执行前预注册）
- 执行脚本：`scripts/run_v4_discovery.py`，打分核心 `scripts/mechanism.py`
- 输出：`results/v4_*.csv`、`reports/v4_report.md`
- 本文数字全部来自实际输出，不是估算。
- v2/v3 的历史版本未纳入本仓库，本文只描述当前生效的 v4 流程。

---

## 0. 一图看全流程

```text
上游：S1 = GSE42568 肿瘤(67) vs 正常(17)，BING Top100 UP/DOWN
      S2 = GSE70138 L5，MCF7 / trt_cp / 24 h / CC≥0.2
        │
[1] 分析域：4,761 条签名（WTCS、Classic KS、Zhang、XSum 四算法齐备）
        │  1,191 个药物 / 3,714 个剂量条件；280 个药物无 Classic KS → 标注不补
        ▼
[2] 剂量层：每剂量取签名中位 → 每药跨剂量中位 / 负向比例 / IQR / 翻转
        门槛：≥3 剂量；WTCS 与 KS 负向比例 ≥0.6；两中位 <0；无强翻转
        │  652 可评分 → 91 通过
        ▼
[3] 四算法共识：每种算法在 652 池内转逆转百分位
        门槛：4 个算法中至少 3 个 ≥0.70      → 84 通过
        ▼
[4] 免权重发现分：S_disc = median(四个百分位)
        剂量 bootstrap 1,000 次（种子 20261120）→ stability_top20
        │  稳定性 ≥0.70 仅 11 个 → 预注册阶梯降到"不设门槛"才凑满 20
        ▼
[5] v4 数据驱动 Top20（按 S_disc）
        │  其中只有 5 个有方向一致机制链
        ▼
[6] 机制链门槛：≥1 条「药物→靶点→S1 基因→S1 通路」方向一致链
        │  84 个候选里 20 个有链
        ▼
[7] 取数：
        A 机制可解释 Top10 = 有链者按 S_disc 取 10（可扩展出 Top20）
        C 高置信核心   = 有链 且 PRISM 不反 ER+（全部列出，共 6 个）
        稳定核心       = stability ≥0.70（11 个，不论机制）
```

---

## 1. 步骤 1：分析域

| 项目 | 值 |
|---|---|
| 签名交集 | 5,861 条修正 WTCS ∩ 4,761 条 Classic KS = **4,761** |
| 药物 | **1,191** |
| 剂量条件 | **3,714**（剔除 1 条 `0.0 um` 载体） |
| 无 Classic KS 覆盖 | 280 个药物 → `algorithm_coverage_missing`，不补值 |

四种算法（WTCS / Classic KS / Zhang signed rank / XSum）都已在同一批 4,761 条签名上算过，直接用，不重新定义算法。

---

## 2. 步骤 2：剂量汇总与门槛

**不做的事**：不挑 10 μM、不挑最有利剂量、不把不同剂量平均。

**做的**：
1. 每个 `(pert_id, dose)`：四种算法各取签名中位；
2. 每个药物：每种算法取跨剂量中位；另算负向剂量比例、IQR、MAD、正负翻转标记。

**门槛（任一不过即淘汰，原因逐条保留）**：

```text
n_dose_conditions ≥ 3
WTCS_negative_dose_fraction ≥ 0.6   且   Classic_KS_negative_dose_fraction ≥ 0.6
WTCS_dose_median < 0                且   Classic_KS_dose_median < 0
strong_flip = 0（不同时出现 ≥+0.20 与 ≤−0.20）
```

结果：652 → **91**。主要淘汰原因：WTCS 负向比例不足、中位为正、强翻转。

---

## 3. 步骤 3：四算法共识（免权重）

对每种算法，在 652 个结构池药物内计算逆转百分位 `p_a`（越负越接近 1）：

```text
p_a = 1 − (ascending_rank − 1) / (n − 1)，n = 652，并列取平均秩
共识门槛：四种算法中至少 3 种满足 p_a ≥ 0.70
```

结果：91 → **84**（7 个被共识门槛挡掉）。

这是 v2「双算法各进前 30%」的推广：要求**多数算法一致**，而不是任取两个；同时不再需要给算法分配权重。

---

## 4. 步骤 4：发现分与稳定性

```text
S_disc = median( p_WTCS , p_ClassicKS , p_Zhang , p_XSum )
```

用中位数而非均值：允许一个算法严重偏航而不主导结果，且无需权重。

**剂量 bootstrap**：有放回重抽每个药的剂量，重算四种中位 → 映射到冻结的 652 分布 → 重算 `S_disc` → 在 84 个合格药中重排，记录是否进入前 20；重复 **1,000 次**，种子 **20261120**。

结果：

| 稳定性门槛 | 存活数 |
|---|---:|
| ≥0.70 | 11 |
| ≥0.60 | 15 |
| ≥0.50 | 17 |
| 不设门槛 | 84 |

按预注册阶梯（0.70 → 0.60 → 0.50 → 无门槛），为凑满 Top20 最终使用了**无门槛**一级。**这意味着 v4 Top20 里有 9 个药物的 Top20 位置在重采样下并不稳定** —— 这是必须写进报告的事实。

---

## 5. 步骤 5：v4 数据驱动 Top20

排序：`S_disc` 降序 → `stability_top20` 降序 → `WTCS_dose_median` 升序 → `pert_id` 升序。

Top20 中**只有 5 个有方向一致机制链**（alvocidib、carfilzomib、bortezomib、rucaparib、midostaurin）。

---

## 6. 步骤 6：方向一致机制链（门槛 + 解释）

一条链必须同时满足：

1. 精确 InChIKey 匹配到图谱药物节点，且 drug→gene 边带证据记录；
2. 该靶点是 S1 差异基因（limma FDR<0.05）；
3. **方向相反**：抑制类药靶向 S1 上调基因（logFC>0），或激活类药靶向 S1 下调基因（logFC<0）；
4. 该靶点落在某个 S1 显著通路内（adjusted p<0.05）。

`ER+ 链` 额外要求通路属于雌激素反应程序（HALLMARK_ESTROGEN_RESPONSE_EARLY/LATE 或 Reactome Estrogen-dependent gene expression）。

结果：84 个候选里 **20 个有链**；当前 Top20 里 5 个有链。

---

## 7. 步骤 7：三份名单

### A. 机制可解释 Top10（交付用）

有链者按 `S_disc` 取 10；Top20 内不足时按协议扩展到 Top20 之外，并标注 `rank_v4`。

| # | 药物 | v4 名次 | `S_disc` | 稳定性 | 链靶点 | PRISM |
|---:|---|---:|---:|---:|---|---|
| 1 | alvocidib | 3 | 0.994 | 0.90 | CDK1, CDK9 | 反 ER+ |
| 2 | carfilzomib | 5 | 0.988 | 1.00 | PSMA3/5, PSMB7, PSMD3 | 反 ER+ |
| 3 | bortezomib | 7 | 0.988 | 0.87 | 同上 | 反 ER+ |
| 4 | rucaparib | 8 | 0.986 | 0.64 | PARP1 | 反 ER+ |
| 5 | midostaurin | 19 | 0.955 | 0.33 | PRKCI, PRKCZ | 反 ER+ |
| 6 | mitoxantrone | 21 | 0.952 | 0.38 | TOP2A | 反 ER+ |
| 7 | acetazolamide | 27 | 0.928 | 0.26 | CA12 | 无明确方向 |
| 8 | azacitidine | 30 | 0.916 | 0.12 | DNMT1, DNMT3A | 反 ER+ |
| 9 | pilaralisib | 33 | 0.906 | 0.18 | PIK3R3 | 反 ER+ |
| 10 | AT-7519 | 36 | 0.899 | 0.36 | CDK1/9/10/12/17/20 | 反 ER+ |

### C. 高置信核心（6 个）

有链 **且** PRISM 不反 ER+，全部列出，不补位：

acetazolamide、pindolol、iguratimod、palbociclib、belinostat、quizartinib（v4 名次 27–62，5/6 稳定性 ≥0.84）

### 稳定核心（11 个）

stability ≥0.70：CGP-60474、romidepsin、alvocidib、WZ-3105、carfilzomib、pentobarbital、bortezomib、triptolide、emedastine、dacinostat、lacidipine（其中仅 3 个有链，且 3 个都反 ER+）

### 交集为空

| 条件组合 | 数量 |
|---|---:|
| 稳定 ≥0.70 且 有链 | 3（全部反 ER+） |
| 有链 且 不反 ER+ | 6 |
| **稳定 且 有链 且 不反 ER+** | **0** |

---

## 8. 数值汇总

| 步骤 | 数量 | 主要淘汰原因 |
|---|---:|---|
| 发现队列 | 1,471 | — |
| 双算法分析域 | 1,191 | 280 个无 Classic KS 覆盖 |
| 剂量 ≥3 可评分 | 652 | 539 个剂量数不足 |
| 过剂量门槛 | 91 | 561 个：负向比例 / 方向 / 强翻转 |
| 过 3/4 算法共识 | 84 | 7 个算法间不一致 |
| 稳定性 ≥0.70 | 11 | 73 个重采样不稳 |
| 有方向一致链 | 20 | 64 个无链（知识覆盖或方向不符） |
| **A 名单** | **10** | — |
| **C 核心** | **6** | — |

---

## 9. 复现

```powershell
$py = 'D:\APP\Anaconda\python.exe'
$s  = 'experiments\robust_candidate_prioritization\scripts'
& $py -X utf8 $s\run_v4_discovery.py
```

脚本会校验预注册文件存在，写出 `v4_drug_scores.csv`、`v4_ranked_pool.csv`、`v4_top20.csv`、`v4_mechanism_top10.csv`、`v4_core_c.csv`、`v4_chains.csv` 与 `v4_manifest.json`（含每个输出的 SHA-256）。

---

## 10. 附录：历史版本（已归档）

历史版本（v1–v3）未纳入本仓库；下表仅用于说明版本演进，v4 不依赖它们：

| 版本 | 排序方式 | 机制层 | 现状 |
|---|---|---|---|
| v1 | — | — | 从未执行，无产出 |
| v2 | `S_data = 0.45·S_dose + 0.30·S_algorithm + 0.25·S_external`（加权，先验无实证） | 10 分制，靶点数量驱动 | 归档，主分析溯源 |
| v3 | 同 v2 数据层，机制扩全池、ER+ 设资格、`S_data` 优先 | 同 v2 | 归档，已被 v4 取代 |
| **v4** | **四算法中位秩，免权重**；外部与 PRISM 只作标签 | **方向一致链门槛** | **当前主线** |

v4 相对 v3 的三处改动：① 去掉无依据的权重；② 加入剂量重采样稳定性；③ 机制从"靶点数"改成"方向一致链"。**数据硬门槛（剂量、算法共识）从 v2 到 v4 一致，从未放宽。**



---

## 11. 这套流程不能回答的问题

1. 不能证明药效：没有细胞、动物、临床数据。
2. 机制链的**分母很小**：84 个候选里只有 20 个能被评估，其余是图谱覆盖不足，不是"没有机制"。
3. 稳定性检验显示：Top20 里 9 个位置不稳，说明"第几名"高度依赖剂量抽样；只有 11 个药物真正稳定。
4. S1 是"肿瘤 vs 正常"，不是 ER+ vs ER−，所以"逆转"包含大量非 ER 生物学；ER+ 特异性只能靠 PRISM 与雌激素通路单独评估。
5. 四算法中位秩虽然免权重，但四个算法共享同一份排序基因列表，不是四次独立测量。

