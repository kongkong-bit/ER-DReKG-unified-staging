# Exp007 — S1 基因名单大小与选择敏感性

运行重新计算：

```powershell
.\s2_lincs\.venv\Scripts\python.exe experiments\exp007_signature_sensitivity\scripts\run_exp007.py
.\s2_lincs\.venv\Scripts\python.exe experiments\exp007_signature_sensitivity\scripts\verify_historical_reproduction.py
```

固定同一批 4,761 条真实 MCF7 LINCS Signature、BING 背景、WTCS 公式和剂量/时间条件，对照 A、B100、B150、B200、B300 等疾病查询。A/B200 与历史正式分数逐 Signature ID 对照；结果见 `results/historical_reproduction_check.csv`。此实验评价排名敏感性，不证明疗效。
