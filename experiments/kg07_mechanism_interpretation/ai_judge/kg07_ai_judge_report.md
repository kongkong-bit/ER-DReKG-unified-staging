# KG07 20 案 AI 自动盲审结果

> **这是智谱 GLM-5.3-Flash 的 AI-as-judge 结果，不是人工审阅结果。它不能满足原方案要求的独立人工证据审核，也不能作为临床疗效证据。**

评审样本：20 个候选 × 3 种解释，共 60 条；模型：`glm-5.3-flash`；评分 Prompt：`kg07-blinded-ai-judge-v1.0`。
评分 CSV SHA-256：`1bcbb6fb1b7b3246951407b113f4688bdcb4a783797f49e32b08a92280aeffc8`。人工盲审仍为待完成；原人工评分表没有被修改。

## 方法汇总

比例指标先按每条解释计算，再对每种方法的 20 条解释取宏平均；错误计数按声明对象汇总。

| 方法 | 案例数 | 有依据声明比例（可评分数） | 引用支持准确率（可评分数） | 无依据断言数 / 率 | 方向错误数 / 率 | 不确定性准确率（可评分数） | 方法平均耗时（秒） | 方法输出 tokens | 方法费用 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Direct LLM | 20 | 53.7% (20/20) | NA (0/20) | 40 / 47.1% | 0 / NA | 60.4% (20/20) | 13.3 | 37574 | 未返回 |
| KG 规则模板 | 20 | 100.0% (20/20) | 100.0% (20/20) | 0 / 0.0% | 0 / 0.0% | 100.0% (6/20) | 0.0 | 0 | 未返回 |
| KG + LLM | 20 | 96.7% (20/20) | 93.1% (20/20) | 5 / 5.1% | 0 / 0.0% | 95.0% (20/20) | 8.9 | 65041 | 未返回 |

## 配对分数差异

正值表示左侧方法的比例分数较高；该比较是描述性汇总，不是显著性检验。

| 对比 | 指标 | 配对数 | 平均差值 |
|---|---|---:|---:|
| KG 规则模板 minus Direct LLM | supported_claim_fraction | 20 | 0.463 |
| KG 规则模板 minus Direct LLM | citation_precision | 0 | NA |
| KG 规则模板 minus Direct LLM | uncertainty_accuracy | 6 | 0.000 |
| KG + LLM minus Direct LLM | supported_claim_fraction | 20 | 0.430 |
| KG + LLM minus Direct LLM | citation_precision | 0 | NA |
| KG + LLM minus Direct LLM | uncertainty_accuracy | 20 | 0.346 |
| KG + LLM minus KG 规则模板 | supported_claim_fraction | 20 | -0.033 |
| KG + LLM minus KG 规则模板 | citation_precision | 20 | -0.069 |
| KG + LLM minus KG 规则模板 | uncertainty_accuracy | 6 | 0.000 |

## 解释边界与审计限制

- 评审模型只依据盲化输出、引用快照和 EvidencePackage 覆盖摘要打分；A/B/C 在评分结束后才通过独立映射表揭盲。
- 这是单一模型的自动评审，且生成器与评审器都使用同一智谱模型系列，存在自我偏好和系统性误差风险。结果不能替代专业人员逐条核对原始来源。
- `supported_claim_fraction` 的分母为事实性 claim 数；`citation_precision` 按每个被引用的 Evidence ID / Path ID 逐个计；无可评估项为 NA。无依据断言率以事实性 claim 总数为分母；方向错误率以含方向性表述的事实 claim 总数为分母。
- 方法耗时与生成 tokens 来自原始 Direct LLM / KG 规则 / KG+LLM 运行输出；它们与下面 AI 评审自身的 API 耗时/token 分开统计。
- 评审使用外部 API，证据与解释文本已按授权发送给智谱。服务方没有返回费用，不做估算。已保留成功评分记录报告的 AI 评审 token 用量为 1,523,971 prompt / 98,466 completion，平均评审延迟 22.1 秒；此前 10 次失败/重试请求没有完整记录逐次 token，故 token 数不是总账单用量。
- 所有分数只描述这 20 个案例的自动审阅结果，不证明药物机制正确性或临床疗效，也不能据此声称某方案被人工验证为优越。
