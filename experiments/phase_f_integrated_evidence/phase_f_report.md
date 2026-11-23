# Phase F：Exp006–Exp011 与项目 GraphBuild 候选证据整合

生成时间（UTC）：2026-11-14T04:34:13.972865+00:00

## 整合规则

以 LINCS perturbagen ID 精确联结第二轮综合证据矩阵与项目 GraphBundle。化合物只接受已审计的精确 InChIKey 映射；名称仅作展示，不参与匹配。当前图谱种子来自 Exp006 Top50，因此未进入该种子的候选标为‘未评估图谱’，不能误作映射失败。

不将 S2 WTCS、Exp007–010 稳定性/外部 S1 和 Exp011 PRISM 合成加权分数，也不据此生成疗效 Top10。图谱交汇数只表示在所用 OptimusKG 版本和 S1 通路数据中存在可溯源关系。

## 实际整合计数

- 第二轮候选行：819；LINCS perturbagen ID 唯一性校验通过。
- 纳入图谱候选种子：50；其中精确 InChIKey 映射 30。
- 有支持路径的精确映射候选：24；未映射种子 20；映射成功但无交汇路径 6。
- 候选—靶点—S1 通路交汇行：1,494。每行候选保留关联靶点、稳定通路 ID 和对应来源 evidence ID。

- 项目级 S2 剂量条件：240 行，全部与历史正式 scheme B 条件表逐条件匹配；覆盖 50 个 perturbagen。WTCS 恰为 0 的 39 行按原始数据保留，不做改写或插补。

## 解释限制

公共知识图谱路径是数据库来源断言与本项目差异表达/富集结果的交汇，不证明直接因果、药物作用方向、ER 阳性特异性或疗效。PRISM 是体外细胞存活终点，与 LINCS 表达逆转不是同一实验结果。Exp008 仍为 PARTIAL，保持原方法学限制。

## 可复现文件

- 整合矩阵：`experiments/phase_f_integrated_evidence/candidate_evidence_with_kg.csv`
- 输入/输出哈希与运行清单：`experiments/phase_f_integrated_evidence/phase_f_manifest.json`
- 构建代码：`scripts/build_phase_f_candidate_evidence.py`
