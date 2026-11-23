# Final02 排名规则冻结

1. 疾病签名：GSE42568 ER+ 肿瘤相对正常组织；BING 空间中 FDR<0.05 的 UP/DOWN 各 Top100。
2. 药物签名：GSE70138 Level 5；MCF7，trt_cp，24 h，distil_cc_q75≥0.2；metadata 仅按 sig_id + pert_id + pert_type 联结。
3. 统一主剂量：经所有 QC 合格 24 h 条件统计，10.0 um 在本数据中覆盖药物最多（1,032 个 perturbagen）；不为每种药物挑最好剂量。完整剂量覆盖见 manifest。
4. WTCS 使用固定 BING 排序背景、 Broad-style 两侧加权 KS，signature-level 得分后按 pert_id / 细胞 / 类型 / 剂量 / 时间组内取 WTCS 中位数。
5. 主排序按主剂量条件 WTCS 升序；同分按 pert_id 字典序。药物 ID 去重。Exp010、PRISM、知识图谱、靶点数、机制路径数不参与排序或 Top10 选择，仅作为独立证据呈现。
6. WTCS<0 仅表示表达方向上的逆关联，不等于药效或临床疗效。单 signature 药物标示重复有限。

本协议在查看最终候选机制证据之前固定。
