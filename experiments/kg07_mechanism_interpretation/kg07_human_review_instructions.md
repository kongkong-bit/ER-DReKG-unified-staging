# KG07 20 案盲审说明

## 审阅顺序

1. 先只打开 `kg07_human_review_20_cases.csv` 与 `kg07_human_review_evidence.csv`，不要查看 `kg07_human_review_blinding_key.csv`，直到所有案例完成评分。
2. 每行是一名候选的一种解释方法。`claims_json` 仅含实际展示的保留声明；辅助表按 `case + review_code + claim_index` 给出声明引用的证据快照。审阅期间不要打开模型原始结果 JSON，以免从文件名或元数据得知方法。
3. 核对声明时沿 `evidence_ids` 查包中的 `evidence`/`edges.sources`，沿 `path_ids` 查包中的 `paths`。ID 存在不等于它支持文字；需核对来源陈述与关系方向。
4. 完成全部评分后再打开盲审映射表，揭盲并按方法汇总。

## 每个候选的评分口径

- `supported_claim_fraction`：被所引证据直接支持的事实性声明数 / 全部事实性声明数，填 0–1；没有事实性声明填 `NA`。
- `citation_precision`：确实支持对应声明的引用数 / 核查过的引用数，填 0–1；无引用填 `NA`。只核对 ID 是否存在不能算引用正确。
- `unsupported_assertion_count`：按 claim 对象计数；一个 claim 含一条或多条无依据事实时计 1。缺少证据、引用与句子无关、或把相关性说成因果都算无依据，填非负整数。
- `relation_direction_error_count`：按 claim 对象计数；一个 claim 即使同时有多个错误方向也计 1。把结合/抑制/激活/关联方向说错或来源未支持方向都计入，填非负整数。
- `uncertainty_accuracy`：对每一处证据不足/不确定性表述判断是否与实际证据覆盖一致；填“正确的表述数 / 可评估表述数” (0–1)，无可评估表述填 `NA`。
- `review_notes`：简要写出最关键的证据问题，可列 `Path ID` / `Evidence ID`。

延迟与 token 用量已在模型逐例 CSV/JSON 中记录。服务方未返回费用，费用不要估算。建议以案例为单位先算比例，再报告方法间宏平均；断言错误数另报总数。任何结果都不应被写成临床疗效证据。

盲审表中评分单元格为空表示未审阅，不代表 0 分。