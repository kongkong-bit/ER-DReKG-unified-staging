# 项目级 S2 运行配置与执行报告

日期：2026-11-13

## 新增能力

- 新项目的 S2 页面可选择本项目已完成的预计算 DEG、microarray limma 或 RNA-seq edgeR-voom S1 运行。
- 可配置 ID 类型、FDR、每方向 Top N、细胞、扰动类型、时间及 `distil_cc_q75` 质量阈值。默认参数为 BING symbol、FDR 0.05、每方向 100 个、MCF7、`trt_cp`、24 h、CC Q75 ≥ 0.2。
- 后端通过 `POST /api/v1/projects/{project_id}/s2/run` 调用 `s2_lincs/.venv` 中的 CLI，并向 CLI 传递预分配的 S2 AnalysisRun ID。
- `test_only` 项目必须设置 Signature 数上限，默认 5，避免误启全量。普通项目不能限制 Signature 数；页面要求用户确认后才启动完整筛选。
- 每次运行先登记 `running` AnalysisRun。完成后校验 manifest、S1 项目归属与输出 SHA-256，再导入分剂量/分时间条件结果。失败和超时记录状态、错误与独立日志；最大运行时间为 2 小时。
- 日志、CLI 输出和参数写入项目独立目录；WTCS 保留原始符号，剂量时间条件不合并。

## 验证

- S2 CLI 小型 GCTX 单元测试继续验证真实矩阵行提取、预分配运行 ID、方向评分和剂量分层。
- 新增 API 编排测试使用 `test_only` 项目与隔离数据库，模拟子进程返回并真实执行 manifest/文件哈希门禁、S2 条件入库和日志留存。合成子进程输出仅作为软件测试数据，不是科研结果。
- 后端完整测试、S2 工程测试和 Vite 生产构建的最终状态见 [Phase C 主报告](phase_c_report.md)。

### 真实数据 Smoke Test

- 使用本机已有的 GSE42568 S1 结果和 LINCS Level 5 GCTX，运行了 `test_only` 项目的 5 条 Signature Smoke Test；没有下载新数据，也没有改写历史 S1 或既有 Smoke Test 文件。
- 新运行 ID：`ANALYSIS_RUN:S2_LINCS:ec3830fe-d10f-4d10-9d94-1fc36ad31462`；来源 S1 运行 ID：`ANALYSIS_RUN:S1_LIMMA:9b9000e2-b35d-42de-82d7-1451ed69db84`。
- 实际完成 5 条 LINCS Signature 评分并形成 5 条分时间/剂量条件记录。数据库只读核验结果为：运行状态 `completed`、类型 `s2_lincs`、条件结果 5 行。
- 运行日志：`data/processed/projects/89aa18d8-e1ca-4eb4-8046-634cd2911207/s2_logs/ec3830fe-d10f-4d10-9d94-1fc36ad31462.log`；SHA-256：`767e2c7d7420fb01993491741e1e23a49e59498aa9188a4950d078565c28c0fd`。
- 这是软件链路的真实数据 Smoke Test，不是全量筛选或正式候选药物排名；5 条记录不足以支持药效结论。

## 执行限制

- 本轮没有启动完整 S2 药物筛选，没有生成正式候选药物排名。上述 5 条结果仅用于验证真实数据读取、评分与条件结果入库。
- 完整任务通过同步 API 运行，连接会保持到结束，最多 2 小时；生产部署前应改成后台 Job/队列并提供进度轮询。
- 该功能不产生跨剂量药物总排名；条件级结果可审计，但要写入通用 Candidate 表仍需单独预设跨条件汇总规则。
- 本轮前端生产构建已通过；Windows 浏览器内实际选择 S1 并提交 Smoke 的交互尚未完成验收。
