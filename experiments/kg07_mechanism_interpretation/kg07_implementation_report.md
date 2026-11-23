# KG07–KG08 实施状态

审计日期：2026-11-15

## 已实现并本地验证

- FastAPI 新增 `POST /api/v1/projects/{project_id}/kg07/interpret/{pert_id}`，支持 `kg_llm`、`direct_llm`、`kg_rule` 三种模式。请求复用 KG06 EvidencePackage，因此项目、GraphBuild、AnalysisRun 隔离规则不变。
- Provider 使用 OpenAI 风格 Chat Completions；模型、Base URL、API key 通过环境配置。API key 放在根目录本地 `.env`（已由 `.gitignore` 排除），没有进入代码、日志或结果文件。
- Prompt 要求结构化 JSON、关系方向标记和临床疗效边界。KG+LLM 的每项结论只保留能在本次 EvidencePackage 中核对的 Evidence ID 或 Path ID；无可核对引用的机制断言会被删除并记入校验问题。方向性与因果断言只有在被引用关系明确支持时才保留，否则降级为关联/未知并加待审核标记。ID 命中不能替代人工判断“引用是否真正支持这句话”。
- 缓存键绑定 EvidencePackage 输入 SHA-256、模型和 Prompt 版本；记录响应模型、token usage、耗时及服务方费用字段（服务方未返回时记为未报告）。
- KG08 药物详情页已增加 KG+AI 生成、规则模板对照、加载/错误/证据不足提示、Path ID 跳转、Evidence ID 原始记录弹窗和 JSON 导出。图谱页按项目与 GraphBuild 重新读取对应 EvidencePackage，将被选 Path ID 的节点和边加入子图并高亮。
- 当前运行版本 v2 EvidencePackage 有 50/50 成功；包含 2,111 条图谱路径及 240 条 S2 条件记录。240/240 个 S2 Evidence ID 已在 Postgres 核验。真实 KG07 规则模板 API 对 ponatinib 返回 HTTP 200；21 条靶点、14 条通路 claim 的 Evidence ID/Path ID 均匹配该候选当前 EvidencePackage。
- `backend/tests/test_kg06.py` 与 `test_kg07.py`：9 项通过；完整后端测试 56 项通过。React TypeScript/Vite production build 通过。

## 真实 20 例本地对照集

- 从 Top50 已审计 EvidencePackage 分层抽取 20 个真实候选，覆盖化合物映射、直接靶点、公共通路和 S1 富集通路的不同组合。
- 已为 20 例生成 KG 规则模板和逐例人工盲审工作表，保留 EvidencePackage 输入哈希。
- Human review 指标列已预留：有依据结论比例、引用精确率、无依据断言、关系方向错误、不确定性准确度、延迟和费用。空值表示尚未评估。
- KG06 → KG07 本机规则模板 Pilot：5/5 真实候选 HTTP 200，5/5 引用 ID/Path ID 对应当前候选的 EvidencePackage，覆盖有多条路径与无可信路径案例；本轮无外部模型调用。
- Exp006/Phase F 的独立验证和 PRISM 数值仍在完整 EvidencePackage 中；当前没有稳定的 EvidenceRecord/Path ID 指向这些源行，因此 KG+LLM prompt 不把它们作为可引用事实。规则报告会显示此限制，候选详情页继续分开显示原始 PRISM/S2 数值。

## 用户授权后的真实模型运行

- 用户于 2026-11-15 明确授权将项目研究证据发送至智谱 API。凭此授权运行 5 案试点、20 案 Direct LLM/KG+LLM 对照及 Top50 解释；结果文件不记录 API key。
- 首次 20 案运行有 9 条 KG+LLM 响应因 JSON 输出截断失败。检查发现单个候选请求包含约 108k 输入 token 的重复边/元数据。随后提示词限制每类最多 3 项，并把模型输入压缩到最多 12 条路径、8 条 S2 条件及关键字段；试点后 20 案重跑及 Top50 均无 API/解析错误。
- 最终 20 案：Direct LLM 20/20、规则模板 20/20、KG+LLM 20/20。KG+LLM 有 51 条未引用声明被丢弃，19 条来源未支持方向的表述降级；最终保留的 101/101 个有引文声明均引用到允许的 EvidencePackage ID/Path ID。全案严格零问题通过为 0/20，不能据此声称语义正确。
- Top50 KG+LLM：50/50 生成，0 调用错误，30 次新请求、20 次缓存；EvidencePackage 50/50 哈希核验有效。全案严格零问题引用校验通过 1/50；其余仍保留逐条引用问题及人工审核标记。
- 费用字段未由服务方返回，保留实际 token 用量与响应时长；不补估费用。
- 人工盲审表包含 60 行（20 候选 × 3 方法），另有 681 行匿名逐声明引用快照；评分仍为空，状态为 `HUMAN_REVIEW_PENDING`。自动引用核验不等于语义蕴含或生物学正确性。

## 复现文件

- `prepare_evaluation.py`：本地分层抽样并生成规则模板。
- `run_evaluation.py`：显式授权后执行 20×2 个模型模式，写入逐例输出、耗时、token 和调用状态。
- `summarize_evaluation.py`：核对 20 案 EvidencePackage 输入哈希，更新逐例表与 manifest，生成三方法盲审表和对照报告。
- `score_human_review.py`：人工盲审表填写完成后验证评分范围/完整性、再揭盲和汇总；空白评分不会被误认为 0。
- `run_top50_explanations.py`：只有 5 案试点与 20 案对照均无 API/解析错误后，才允许在显式外发授权参数下扩展到 Top50；逐候选结果按 SHA-256 核验。
- `audit_top50_coverage.py`：逐包验证 KG06 文件/内部哈希、项目、GraphBuild、候选及输入哈希，再统计模型实际输出覆盖。
- `kg07_evaluation_20_cases.csv`、`kg07_evaluation_manifest.json`：20 例设计与抽样清单。
- `rule_templates/`：本地确定性 KG 模板解释。
- `kg07_implementation_report.md`：本状态报告。
