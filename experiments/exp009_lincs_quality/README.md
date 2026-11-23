# Exp009 — LINCS 质量门槛敏感性

运行入口：

```powershell
.\s2_lincs\.venv\Scripts\python.exe experiments\exp009_lincs_quality\scripts\run_exp009.py
```

本实验比较 LINCS `distil_cc_q75` 阈值和官方 TAS 字段，不重算旧 S2。稳定 ID 用于 Signature 与质量信息连接；剂量和时间仍独立汇总。结果、阈值数量、敏感性图和说明见 `results/`、`figures/`、`reports/`。
