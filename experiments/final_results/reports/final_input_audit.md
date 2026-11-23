# Final01 输入与 ID 审计

审计与重算时间（UTC）：2026-11-15T03:03:12.434674+00:00。

## 核验结论

- GSE70138 的 sig_info / sig_metrics 用 sig_id + pert_id + pert_type 联结；两表显示名不作为键。实际发现 25,327 行 pert_iname 不同。
- 24 h MCF7 / trt_cp、CC≥0.2 的 stable ID 合并共有 5,861 条签名、1,471 个化合物；全部签名 ID 均在 GCTX 中。
- 历史四字段连接（额外要求 pert_iname 一致）仅留下 4,761 条签名；stable ID 口径为 5,861 条，漏失 1,100 条。这个差异会改变有效实验集合，故历史排行榜不能直接作为最终 Top10。
- 本次从 GCTX 重算 5,861 条 stable ID 签名，沿用已通过历史复现的 WTCS 算法；对与旧正式结果重叠的 4,761 个 BING Top100 签名，ES_UP、ES_DOWN、WTCS 最大绝对差分别为 1.3e-13、1.02e-13、6.65e-14。门禁通过。
- Exp009 的 stable-ID 分数文件虽补齐了签名，但该文件与本次正确排序权重配对的重算结果有 3,870/4,761 条不一致，最大 WTCS 差 0.4719；根因是其命中权重未随命中位置排序。本次不采用该旧分数文件。
- S1 输入为既有 BING Top100 UP/DOWN 文件；未修改 limma、S1 清单、LINCS 原始文件或历史 Smoke Test。全部来源 SHA-256 见 `results/final_data_manifest.json`。
