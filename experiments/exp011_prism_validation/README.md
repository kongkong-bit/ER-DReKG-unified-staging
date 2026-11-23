# Exp011 — PRISM 外部药物敏感性验证

在当前工作目录运行：

```powershell
.\s2_lincs\.venv\Scripts\python.exe experiments\exp011_prism_validation\scripts\run_exp011.py
```

输入为 PRISM Repurposing Primary 的原始开放文件、DepMap Public 24Q4 `Model.csv`、LINCS `pert_info` 和 Exp006 候选清单。药物映射只接受完全相同的 Broad ID 或由 SMILES 推出的 InChIKey；名字仅留作核对，不用于身份匹配。

PRISM 数据页面：[Broad/DepMap PRISM Repurposing](https://depmap.org/repurposing/)；模型注释下载：[DepMap Public 24Q4 Model.csv](https://ndownloader.figshare.com/files/51065297)。PRISM 下载页和 README 中没有发现单独的 license 文件或逐文件许可说明，报告记录了该限制及引用来源。

PRISM `logfold_change` 越负代表相对 DMSO 细胞存活越低；本工程保存 `sensitivity = -logfold_change`，数值越大代表抑制越强。不同剂量和筛选批次先在单个细胞系、单个 InChIKey 内取中位数。随机对照以 Top50 中结构确认为同一化合物的药物数量为集合大小，固定 seed=20261112，抽取 10,000 个随机化合物集合。

主要产物：`results/candidate_mapping_audit_top50.csv`、`candidate_sensitivity_results.csv`、`s2_prism_rank_correlation.csv`、`candidate_vs_random_test.csv`、`positive_control_sensitivity.csv`、`run_manifest.json` 和 `reports/exp011_report.md`。结果仅是体外细胞系敏感性对照，不是临床疗效结论。
