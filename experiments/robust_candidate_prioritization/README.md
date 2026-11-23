# Robust candidate prioritization — v4 主线

用「全部剂量 + 四算法共识 + 剂量重采样 + 方向一致机制链」从 ER+ 乳腺癌疾病签名（GSE42568，肿瘤 67 vs 正常 17）中筛出候选药物。**这是计算优先级与机制假设，不是疗效或临床结论。**

## 流程（v4）

```text
1,471 药物（发现队列，5,861 条修正签名）
   │  280 个无 Classic KS 覆盖
1,191 药物 / 4,761 条四算法齐备签名
   │  539 个剂量数 <3
 652 可做剂量汇总
   │  561 个未过剂量门槛（≥3 剂量、两算法负向比例 ≥0.6、两中位 <0、无强翻转）
  91 过剂量门槛
   │  7 个未达「4 算法中 ≥3 个 ≥0.70」共识
  84 过共识
   │  只有 20 个有方向一致机制链；稳定性 ≥0.70 仅 11 个
  20 有机制链
   │  按 S_disc 取 10（不足时扩展到 Top20 之外）
  10 机制可解释 Top10（A）
```

- 发现分：`S_disc = median(p_WTCS, p_ClassicKS, p_Zhang, p_XSum)`，**无权重**
- 剂量层：每剂量签名中位 → 跨剂量中位 / 负向比例 / IQR / 翻转
- 稳定性：剂量 bootstrap 1,000 次（种子 20261120）
- 机制链：药物 —(精确 InChIKey + 证据)→ 靶点（S1 DEG，方向相反）→ S1 显著通路
- 外部 S1（GSE139038）与 PRISM **只作标签，不参与排序**

## 目录

| 路径 | 内容 |
|---|---|
| `reports/protocol_v4_discovery.md` | 预注册规则（执行前冻结） |
| `reports/v4_report.md` | 结果报告 |
| `reports/top10_selection_pipeline.md` | 完整流程说明（含每步数量与依据） |
| `reports/references.md` | 方法学文献 |
| `scripts/run_v4_discovery.py` | 主流程 |
| `scripts/mechanism.py` | 机制链与打分（唯一实现） |
| `results/v4_*.csv` | 药物级分数、Top20、机制 Top10、C 核心、链明细 |
| `results/v4_manifest.json` | 输入/输出 SHA-256 |
| `results/top10_network_edges.csv` | 机制链图的边表（含完整 evidence_id） |
| `results/v4_top10_local_subgraph.json` | 当前 v4 机制 Top10 的冻结局部知识图谱，含候选精确映射、靶点方向证据及 S1 靶点—通路证据 |
| `results/v4_top10_local_subgraph_manifest.json` | 局部子图源文件、生成脚本和交付文件的 SHA-256 与覆盖计数 |
| `figures/chain_<drug>.png` | 10 个候选的机制链图（药物 → 靶点 → S1 通路） |
| `inputs/graph_bundle_manifest.json` | 图谱来源与哈希 |

前端页面：`/robust-results`（数据来自 `frontend/public/robust-results.json`，由 `results/v4_*.csv` 导出）。

稳健 Top10 局部子图同步到 `frontend/public/robust-top10-subgraph.json`，页面默认展示十个候选的合并图，也可按候选聚焦。子图使用 v4 manifest 引用的固定 GraphBundle；候选映射要求 InChIKey 完全匹配，药物—靶点与靶点—通路边均保留来源证据。没有使用药名模糊匹配或 PPI 扩展。重新生成前会校验 v4 输出和 GraphBundle 输入哈希：

```powershell
& '.\backend\.venv\Scripts\python.exe' experiments\robust_candidate_prioritization\scripts\build_v4_top10_subgraph.py
```

## 结果（三份名单）

| 名单 | 内容 | 数量 |
|---|---|---:|
| 数据 Top20 | 只由 `S_disc` 决定，不看图谱 | 20 |
| 机制可解释 Top10（A） | 有 ≥1 条方向一致链，按 `S_disc` 取 | 10 |
| 高置信核心（C） | 有链且 PRISM 不反 ER+ | 6 |

三者关系：稳定 ≥0.70 且 有链 = 3 个（全部 PRISM 反 ER+）；有链且不反 ER+ = 6 个；**三者同时满足 = 0 个**。

## 复现

```powershell
$py = 'D:\APP\Anaconda\python.exe'
& $py -X utf8 experiments\robust_candidate_prioritization\scripts\run_v4_discovery.py
```

脚本会先校验预注册文件存在，再写出 `v4_*` 与 `v4_manifest.json`。四种算法的签名级分数来自 `experiments/exp008_scoring_statistics/results/method_signature_scores.csv`（本机无原始 GCTX，不能从矩阵重算）。

## 必须与结果一起读的限制

1. **S1 是「肿瘤 vs 正常」，不是 ER+ vs ER−**：签名包含增殖、基质等成分；已知内分泌药（fulvestrant、tamoxifen、raloxifene、letrozole）在该签名下均无法通过剂量门槛。
2. **四算法不独立**：WTCS/KS/Zhang 两两相关 0.85–0.91，XSum 相对独立（0.40–0.52），独立信息约为 2–2.5 个维度。
3. **多数剂量只有一条签名**：3,714 个剂量条件中 3,428 个为单签名，稳定性是弱稳健。
4. **图谱覆盖有偏**：Top20 中 9 个无图谱节点；数据前 10 里有 4 个（CGP-60474、romidepsin、WZ-3105、triptolide）因此无法进入机制名单。
5. **机制链分母很小**：84 个候选只有 20 个可被机制评估，其余是覆盖缺口，不是"无机制"。
6. **无任何细胞、动物或临床验证。**

