# KG06–KG08 本轮测试与运行日志

初始本地测试：2026-11-14；真实模型运行补记：2026-11-15（Asia/Shanghai）。

## 自动测试

- `backend/.venv/Scripts/python.exe -m pytest -q tests/test_kg06.py tests/test_kg07.py`：9 passed。
- `backend/.venv/Scripts/python.exe -m pytest -o addopts='' -q`（本机 Docker/Postgres 可访问）：55 passed，0 failed。
- 普通沙箱首次运行时，`test_http_project_creation_and_upload_remains_pending` 在本机数据库生命周期处停滞；切换到已授权的本机数据库访问环境后，该测试单独通过，完整套件随后全部通过。
- `python -m compileall -q app tests`：通过。
- `frontend/npm run build`：TypeScript 检查及 Vite production build 通过；构建工具提示已有大型 chunk 警告，不影响构建完成。

## 实际服务运行

- 已重启项目当前使用的 `127.0.0.1:8000` FastAPI 进程；OpenAPI 检查确认 KG06 与 KG07 路由均已加载。
- 本机 FastAPI 读取本地 Postgres/Neo4j，KG06 EvidencePackage v2：50 请求，50 成功，0 失败。旧目录 `evidence_packages/` 保留；v2 另存，没有改写 S1/S2/GraphBuild。
- v2 中 2,111 条图谱路径；240 条 S2 条件记录对应 240 个 Evidence ID，均在 Postgres EvidenceRecord 中验证。
- KG07 真实本机规则模板 API Pilot：5 个候选 HTTP 200，项目/GraphBuild/候选 ID 对齐；每个输出的 Evidence ID/Path ID 均核对回该候选包（5/5）。Pilot 通过实际前端使用的 8000 端口执行。详见 `rule_pilot/rule_pilot_report.md`。
- 初次本地验收阶段外部 LLM 实际调用为 0；用户于 2026-11-15 明确授权后，运行记录如下。

## 授权后的真实模型调用

- 5 案 Pilot：10/10 API 请求完成，0 错误；输出仍标记人工审核。
- 首次 20 案对照：40 次调用尝试中出现 9 条 KG+LLM JSON 截断，原始 CSV、manifest 和可恢复的 31 个原输出归档在 `evaluation/run_v1_3/`。
- 修复提示词与精简输入后重跑 20 案：20/20 Direct LLM 与 20/20 KG+LLM 成功，错误 0。提示词限制每类最多 3 条；最多输入 12 条路径和 8 条压缩 S2 条件，避免 108k token 重复输入。
- Top50 KG+LLM：50/50 生成、0 错误，其中 30 次未缓存 API 请求、20 次缓存读取。输入包哈希与逐候选输出哈希已复核。
- 本机 FastAPI 重启后 `/health` 返回正常，OpenAPI 登记 38 个路由；对候选 `BRD-K28822270` 调用实际 KG07 POST 路由返回 HTTP 200、KG+LLM `generated`、命中 v1.5 缓存、保留声明引用核验通过。该端到端检查没有新增智谱 API 请求；原始模型输出仍有 3 项校验问题并保留人工审核标记。
- 运行期间服务端未返回费用数据；所有输出保留 prompt/completion token、延迟、模型版本和 EvidencePackage 哈希。
- `backend/.venv/Scripts/python.exe -m pytest -q tests/test_kg06.py tests/test_kg07.py`（cwd=`backend`）：9 passed。
- `backend/.venv/Scripts/python.exe -m pytest -o addopts='' -q`（cwd=`backend`，授权访问本机 Docker 数据库/API）：56 passed，1 条 Starlette/httpx 弃用警告，0 failed。
- 人工语义审核未执行；盲审表 60 行和独立映射表已生成，评分字段为空，不以自动引用 ID 检查代替人工判断。
- `score_human_review.py` 已针对当前盲审表运行，因首个评分单元格为空而按预期拒绝汇总，没有生成人工评分结果。
- 辅助引用快照表有 681 条声明记录：472 条带引用且可在 EvidencePackage 内定位，209 条无引用，0 条带引用但无法定位；ID 定位只供审阅导航，不代替语义核对。

## 安全与解释边界

- `.env` 被 `.gitignore` 排除；key 不在源码、终端输出或结果报告。
- KG+LLM 对无引用的结论会删除；无证据支持的方向/因果关系会降级并标记人工审核。
- `citation_reference_validation_pass` 只证明 ID 属于当前 EvidencePackage，语义蕴含仍需人工审核。代码测试不等于生物学验证。
