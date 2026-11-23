# KG07 20 案解释对照与 Top50 生成报告

## 实际运行

- 20 个真实候选均来自分层抽样集；每个案例使用同一 EvidencePackage 输入哈希。
- 智谱模型：`glm-5.3-flash`；KG+LLM 提示词版本：`kg07-evidence-interpretation-v1.5`。20 案 direct baseline 与 20 案 KG+LLM 均完成，API/解析错误为 0。
- Direct LLM：20/20 完成，平均响应 13.31 秒，输出 148 条声明；提示词输入/输出 token 共 19024/18550。该基线不接收图谱路径；模型产生的无效引用会被移除，剩余文字标记未验证，不能视为证据引用通过。
- KG 规则模板：20/20 本地生成，20/20 的引用 ID/Path ID 可回到对应 EvidencePackage；它是按字段填充的模板，不是语义正确性证明。
- KG+LLM：20/20 完成，平均响应 8.94 秒，保留 156 条声明；提示词输入/输出 token 共 52142/12899。校验共记录 70 个问题：51 条未引用模型声明被丢弃、19 条方向表述被降级。保留的有引文声明中 101/101 个 ID 属于该候选允许的 EvidencePackage 子集。
- 服务方没有返回费用字段；token 用量已记录。缓存命中：direct 20/20，KG+LLM 1/20。

## Top50 解释

- Top50 LLM 结果：50/50，调用错误 0，其中未缓存的真实 API 调用 30 次、缓存复用 20 次。
- 累计 token 156519，平均响应 8.16 秒；保留结论的引用 ID/Path ID 可核验：50/50；原始模型输出无降级/丢弃问题：1/50。引用 ID 命中只证明来源可定位，不证明语义蕴含。
- KG06 输入包的本轮审计：50/50 文件与哈希有效，28/50 有图谱路径，30/50 有精确化合物映射。对没有路径或映射的候选不补造关系。

## 人工审核状态与解释边界

- 20 案盲审表已生成，60 行；逐声明证据快照表有 681 行，其中 472 行带有包内可定位的 Evidence/Path ID、209 行没有引用、带引用但包内无法定位为 0 行。评分列仍为空，等待人工逐项判断句子是否真的受引用支持。评分规则见 `kg07_human_review_instructions.md`；盲审代码对应关系单独保存在 `kg07_human_review_blinding_key.csv`。
- 本次没有给出“模型更正确”或生物学正确率结论。自动程序只检查输出能否解析、引用 ID 是否属于当前 EvidencePackage、方向表述是否需要降级；语义支持、机制合理性及不确定性准确度必须由人工审阅。
- WTCS/PRISM、关联路径和数据库靶点记录均不等同于临床疗效证据。

## 可复现文件

- 逐案模型结果：`evaluation/kg07_evaluation_cases.csv`；原始运行记录：`evaluation/kg07_evaluation_manifest.json`。
- 20 案审阅表：`kg07_human_review_20_cases.csv`；引用快照：`kg07_human_review_evidence.csv`；盲审映射：`kg07_human_review_blinding_key.csv`。
- 审阅评分说明：`kg07_human_review_instructions.md`；填写完成后运行 `score_human_review.py`，脚本会先做完整性与范围校验，当前空表会被拒绝，不生成评分结果。
- Top50 结果：`top50_llm/kg07_top50_llm_results.csv` 与逐候选 JSON；覆盖审计：`kg07_top50_explanation_coverage_report.md`。
- 首次因长输出出现的 9 个 JSON 截断错误记录保存在 `evaluation/run_v1_3/`；压缩到 12 条摘要路径和 8 条精简 S2 条件后，后续 20 案及 Top50 均完成。
