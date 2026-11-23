# KG07 Top50 解释输入覆盖审计

审计范围：当前正式 GraphBuild 下、Exp006 Top50 的 50 个 KG06 EvidencePackage。报告统计的是解释输入可用性，不代表模型解释已生成或机制结论正确。

## 真实覆盖

- EvidencePackage：50/50。
- EvidencePackage 文件哈希、内部 package 哈希、项目/GraphBuild/候选 ID 与 evidence input hash：50/50 全部核对通过。
- 精确 InChIKey 化合物映射：30/50。
- 至少一条真实路径（直接靶点、公共通路或 S1 交汇）：28/50。
- 至少一条路径且路径证据在 PostgreSQL 可验证：28/50。
- S2 条件及其 Evidence ID：50/50 有条件记录；逐例数量见 CSV。
- 当前 KG+LLM 解释：50/50；以逐候选输出文件及 manifest hash 核验后的结果计数，不把未生成或失败案例算作覆盖。其间 50/50 个候选的保留声明通过引用 ID 核验，语义仍需人工审核。

## 边界

没有路径的候选保留为证据不足；没有精确化合物映射的候选不补造映射。Evidence ID 可验证只证明该 ID 属于本项目 GraphBuild 的证据记录，不证明它语义上支持某个具体句子。路径也不构成因果或临床疗效证据。

## 复现

- 输入索引 SHA-256：`548ea5a4421bc3764375b6b2ab1cc2795e9dedf65cf25b4e369ea36704a687f4`。
- 逐候选明细：`kg07_top50_explanation_coverage.csv`。
- LLM 调用状态：`PASS`；模型输出数量为 50/50，实际未缓存 API 调用 30 次。费用以服务方回传为准；未回传的项目记为未报告。
