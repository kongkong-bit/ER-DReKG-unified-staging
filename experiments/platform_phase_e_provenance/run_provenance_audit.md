# 正式项目 AnalysisRun 来源链审计

审计时间：2026-11-14 08:37 UTC  
方式：只读 PostgreSQL 查询；脚本 `scripts/audit_project_run_provenance.py`

## 结果

- 项目 `erpos-gse42568` 登记 2 个 Dataset、14 个 AnalysisRun、9 个 GraphBuild。
- 13 个正式管线运行（S1、S2、富集、GraphBundle）均保存参数、软件版本和输入哈希；Dataset 参数指向同项目数据集且 SHA-256 一致；上游 S1/S2/富集运行引用均能解析到同一项目。9 个 GraphBuild 的 AnalysisRun 引用均有效。
- 13 个正式运行都具备完整来源链字段；其中 12 个运行状态为 `completed`，1 个较早的 GraphBundle 运行状态为 `failed`。该失败记录保留，不当作成功实验；运行参数、软件与输入哈希仍可追溯。
- 1 个早期 Phase B `knowledge_graph_seed_subgraph` 是非分析管线历史运行，没有原始输入哈希，单独标记为 legacy exempt，不计入 S1/S2/富集/GraphBundle 门禁。
- 来源链完整性验收：**PASS**；缺失/跨项目 Dataset、上游运行或 GraphBuild 链接：0。

机器可读明细见 `3f18f4c1-713d-58c5-8a53-38eca5a5aaf9_run_provenance.json`。
