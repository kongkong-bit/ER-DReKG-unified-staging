# ER 阳性乳腺癌重定位项目状态

更新（UTC）：2026-11-15T03:33:50.587554+00:00

| 阶段 | 状态 | 说明 |
|---|---|---|
| S1 差异表达与通路 | COMPLETE | GSE42568，limma；7,066 个 FDR<0.05 差异基因，独立通路富集结果已归档。 |
| S2 LINCS 初筛 | COMPLETE | GSE70138 Level 5，stable ID 修正后 5,861 条合格 MCF7 signatures 重算；正式主条件 24 h、10 μM、CC≥0.2。 |
| Exp006–Exp011 可靠性/外部核对 | COMPLETE_WITH_LIMITATIONS | S1 方案/评分法会改变头部；外部 S1 Top10 重合 1/10；PRISM 与 WTCS 排名关联较弱。详见第二轮报告。 |
| Final01 输入与算法审计 | PASS | 历史 ID 联结差异和 Exp009 权重配对 bug 已审计并修复；历史文件只读。 |
| Final02 固定规则 Top10 | PASS | 按 S2 WTCS 生成唯一化合物榜单，不用机制证据事后调排名。 |
| Final03 机制证据 | PARTIAL | 逐药报告、路径和来源均有交付；当前图谱精确覆盖 5/10，机制推断仍需实验验证。 |
| Final04 综合报告和页面 | PASS | React `/final-results` 已接入，候选详情含图谱路径与可点击 Evidence ID；生产构建和数据测试通过。 |
| 药物疗效/因果验证 | NOT_PERFORMED | 未执行新细胞、动物或临床干预实验。Top10 是初步候选，不能称为有效治疗药物。 |

## 当前交付核心

- 正式初步 Top10：`results/final_top10.csv`。
- 总报告：`reports/final_research_report.md`。
- 逐药机制说明：`top10_mechanism_reports/`。
- 路径和引用：`mechanism/top10_mechanism_paths.csv`、`mechanism/top10_evidence_citations.csv`。
- 数据/代码校验清单：`final_results_manifest.json`。

项目最关键的未完成科学工作，是在独立 ER+ 乳腺癌模型中复现候选的表达/生长效应，并检验靶点和机制因果链。
