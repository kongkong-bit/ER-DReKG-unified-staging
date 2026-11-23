# DiseaseGraph Lab 实施方案完成度审计

审计日期：2026-11-14  
依据：`C:\Users\lai\.codex\attachments\3f1f5621-93bf-4c92-8678-ebfc9944f239\pasted-text-1.txt`；本报告对照当前工程产物和已有实际运行验收记录。

## 阶段状态

| 阶段 | 状态 | 可核对证据 |
|---|---|---|
| Phase A：只读审计与架构设计 | 已完成 | [输入与架构审计](platform_phase_a/phase_a_report.md)、输入清单及哈希、架构/API/数据库/Schema/许可文档 |
| Phase B：受限 OptimusKG 子图 | 已完成 | [真实子图报告](platform_phase_b/phase_b_report.md)、[S1 通路扩展报告](platform_phase_b_pathways/phase_b2_report.md)、映射和关系来源审计 |
| Phase C：Neo4j + FastAPI | 已完成 | [Phase C 报告](platform_phase_c/phase_c_report.md)、[正式 GraphBuild 只读核验](platform_phase_c/formal_graphbuild_verification.md)、GraphBuild/EvidenceRecord/DiseaseContext 版本化记录 |
| Phase D：React 前端 MVP | 已完成核心功能验收 | [前端规划与实现记录](../docs/architecture/frontend_plan.md)、[Phase D 报告](platform_phase_d/phase_d_report.md)、[浏览器上传 E2E](platform_phase_c/browser_upload_e2e_report.md) |
| Phase E：多项目扩展 | 已完成软件隔离验收 | [Phase E 总报告](platform_phase_e_report.md)、[双项目 Neo4j 实测](platform_phase_c/phase_e_neo4j_multi_project_report.md)、[GraphBundle E2E](platform_phase_c/phase_e_graphbundle_e2e_report.md) |
| Phase F：综合候选证据 | 已完成证据矩阵，不产出加权疗效 Top 10 | [Phase F 报告](phase_f_integrated_evidence/phase_f_report.md)、矩阵与输入输出哈希清单 |

## 按方案验收要求核对

- **研究输入保持只读并可校验：通过。** Phase A 清单登记的 S1/S2/Exp006–Exp011 历史文件已有 22/22 哈希一致记录。S1/S2 正式分析结果继续保留在原路径。
- **稳定 ID、映射失败和证据来源：通过。** GraphBundle 报告保留 LINCS perturbagen、化合物 InChIKey、Ensembl、GO/Reactome/MSigDB 稳定 ID 及 unmatched/conflict 审计；正式 GraphBuild 报告记录路径和 evidence ID。
- **Neo4j 幂等导入和项目/版本隔离：通过。** Phase E 双项目实测与正式 GraphBuild 只读核验覆盖共享实体复用、关系来源、GraphBuild 过滤和 API 查询。
- **AnalysisRun 来源链、输入哈希与软件信息：通过。** [来源链审计](platform_phase_e_provenance/run_provenance_audit.md)核验正式 ER 项目的分析运行及 GraphBuild 关联；已保留历史失败运行状态，不将其计作成功。
- **新项目导入门禁：通过。** CSV 上传经 Vite/FastAPI 登记为 `validation_pending`；本轮原生文件选择器实测使用合成表达矩阵，校验要求样本分组信息且没有自动启动分析。
- **API/前端真实联调、边界限制：通过（本机开发模式）。** React 仅通过 FastAPI 查询；图谱查询由固定模板提供，有节点/边/深度上限、项目及 GraphBuild 过滤。OpenAPI 契约说明无任意 Cypher 接口。
- **项目级 S1/S2 可配置管线：已实现并通过软件闭环验证。** 新项目支持预计算 DEG、标准化微阵列 limma、RNA-seq edgeR-voom、通路富集和受限 LINCS S2；新增测试项目运行仅证明软件流程，不代表额外疾病研究结果。
- **候选综合证据矩阵：通过。** Phase F 精确使用 LINCS `pert_id` 联结 819 个候选、正式 S2 条件和 GraphBuild 支持路径；不以未验证权重生成药效总分。历史 240 个项目 S2 条件均保留剂量分层。
- **可复现表格 ETL 依赖：本轮补齐并通过等价性门禁。** `kg/` 现已锁定 DuckDB 1.5.6；GraphBundle 使用列投影读取 OptimusKG 药物、基因和通路节点，避免加载未用的分子图像、文献等字段。单测 11 项通过，正式 GraphBundle 临时重建的 9 个 CSV 全部逐字节一致、计数一致；正式历史目录未被覆盖。
- **原始研究输入完整性：本轮复核通过。** Phase A 清单所列 22 个历史文件重新计算 SHA-256，22/22 匹配。

## 尚未纳入本轮完成声明的事项

1. **生产环境安全加固未完成。** 当前是仅绑定本机回环地址的开发环境；如对外部署，仍需认证、授权、密钥管理和部署安全配置。现有接口不能据此宣称已达到生产安全要求。
2. **独立异步任务队列未实现。** 现有 S1/S2/GraphBundle 任务同步执行；Celery/Redis 和真实进度是在方案中明确延后的功能。
3. **第二个真实疾病队列未做生物医学验证。** Phase E 验证的是两个 `test_only` 项目的软件隔离；方案明确这一步不要求立即下载第二疾病的大型数据集，因此没有把软件夹具说成疾病验证。
4. **没有建立跨条件疗效总排名或最终 Top 10。** 现有结果按剂量/时间保留；Phase F 只整合证据矩阵，不使用未经验证的权重代替疗效证据。
5. **剩余前端改进：** 独立的跨队列汇总/导出界面尚未实现；ECharts 按需加载块仍有体积告警。这些不影响已验收的核心页面与真实 API 流程。

## 本次续验记录

- **2026-11-14 UTC 09:43：本机运行态复核通过。** Docker Compose 中 PostgreSQL 和 Neo4j 均为 healthy，端口只绑定 `127.0.0.1`。FastAPI OpenAPI 返回 HTTP 200；两个已存在的 Vite 页面（5173、5174）均返回 DiseaseGraph Lab 页面，且经各自 `/api/v1/projects` 代理都返回 HTTP 200、4 个项目。新启动的临时 Vite 进程已关闭；本轮启动的 API 仅监听 `127.0.0.1:8000`。这验证本机联调，不代表生产部署或身份认证已完成。
- **正式 ER+ GraphBuild 当前版本复核通过。** 项目默认最新版本为 `GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:a08001496a447f7f`，其 GraphBundle manifest/output 哈希已登记，映射计数为 30,350 条唯一 Ensembl 通路基因链接、1,494 条候选靶点—通路路径、0 条关系冲突；实时 Neo4j 摘要为 6,850 个节点、38,657 条关系。摘要、机制、证据与版本过滤 API 由 Phase D 只读联调脚本实测通过。旧修正版 `a6aabb2147cb5f5e` 仍保留且曾单独验收，但不再标记为默认最新版本。没有重复创建正式 GraphBuild。详情见[正式 GraphBuild 实际验收报告](platform_phase_c/formal_graphbuild_verification.md)和[Phase D 联调报告](platform_phase_d/phase_d_report.md)。
- **前端验收项复核。** 图谱页提供局部子图 JSON 导出、节点和关系筛选、直接靶点/上下文关系筛选及已加载子图内路径高亮；所有浏览器请求走 FastAPI，未发现前端数据库连接或数据库密钥引用。
- 在用户确认后重跑隔离 Phase E GraphBundle 端到端流程：S1、富集、30 条真实 LINCS Signature 的软件 Smoke Test、GraphBundle、Neo4j GraphBuild 和 FastAPI 查询状态完成；随后对正式 ER+ GraphBuild 执行只读核验并得到 PASS。
- Edge 访客窗口实际打开 Windows 原生文件选择器并上传合成表达矩阵至 `test_only` 项目。Dataset 状态为 `validation_pending`，SHA-256 与存储文件匹配，AnalysisRun 数量保持 4。
- 验收报告只把真实执行并核对过的项目标记为 PASS；软件 Smoke Test 以及 `test_only` 图谱结果不视作新的生物医学证据。
