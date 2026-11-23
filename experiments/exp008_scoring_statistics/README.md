# Exp008 — WTCS、算法排名和随机基因集检验

在 `D:\CLASS\syh` 运行：

```powershell
.\s2_lincs\.venv\Scripts\python.exe experiments\exp008_scoring_statistics\scripts\run_exp008.py
.\s2_lincs\.venv\Scripts\python.exe experiments\exp008_scoring_statistics\scripts\run_exp008_permutation.py
.\s2_lincs\.venv\Scripts\python.exe experiments\exp008_scoring_statistics\scripts\finalize_exp008.py
```

第一步使用 4,761 条真实 MCF7/24h Q2 signatures 比较 WTCS、Classic KS、Zhang 和 XSum；第二步固定 seed=8008，对 A/B 两种 S1 查询分别执行 2,000 次共享随机 BING 查询置换，以药物剂量时间条件的中位 WTCS 为统计量，并分方案 BH 校正。Zhang/XSum 使用 COMPZ 输入适配，NCS/Tau 因缺少官方参考查询而 NOT_AVAILABLE。
