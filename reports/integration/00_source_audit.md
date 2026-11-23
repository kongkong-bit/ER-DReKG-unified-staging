# 四工程来源审计（Phase 0）

审计日期：2026-11-22（Asia/Shanghai）。本轮只读检查来源；创建独立 staging 时仅复制 syh 到新目录，未改动来源。

## 仓库与状态

| 来源 | Git / 状态 | 可核实结构 |
|---|---|---|
| `D:\CLASS\syh` | Git `main`，HEAD `be7f857`，比 `origin/main` ahead 1；存在大量已修改和未跟踪文件（审计时 63 项 status 行） | FastAPI 单入口、React/Vite、PostgreSQL/Alembic、Neo4j/BioCypher、S1/S2、实验与历史数据；Python >=3.12 |
| `D:\CLASS\wd\ER-DReKG-main` | 未发现 `.git` 元数据 | 架构与 syh 高度相似；backend/app 39 文件、tests 18、frontend pages 7、KG scripts 8；另有丰富实验与 KG07 评估资料 |
| `D:\CLASS\ER-DReKG-KG-delivery-20261120` | 未发现 `.git` 元数据 | 有 manifest、冻结 A+ 输入、正式 S2/GraphBundle、实现代码和运行证据；README 明确正式构建使用旧版导入器，改进导入器未应用 |
| `D:\CLASS\zq` | 未发现 `.git` 元数据；`rg --files` 未返回文件 | 当前可见状态为空；无法认定有可迁移代码 |

## 可核实功能差异

- syh 与 wd 的 Python 和前端依赖声明基本一致（FastAPI/SQLAlchemy/Neo4j；React/TypeScript/Vite）。两者不是可并行拼接的不同技术栈。
- syh 当前代码已具有 S1、S2、候选证据、KG06/KG07、Top10 mechanism/report、GraphBundle/GraphBuild 端点；未提交文件包含进一步 Top10 机制页面、KG enrichment 和 Neo4j 构建改动。这些属于应保留的主线成果。
- wd 有更广的实验/验证资料、KG07 评估脚本和部分后端测试。需要按文件内容、manifest 与 syh 结果比对，不能仅凭文件数量认定是新增功能。
- 交付包提供正式 GraphBuild `d570eb8deb3e5eea`、build_key、GraphBundle、正式 S2 run ID 及 PostgreSQL/Neo4j 数量证据。包内说明明确：正式 Neo4j 导入来自原版导入器；改进导入器只是交付候选，不能声称已用于正式图谱。
- 交付 A+ S2 与 syh README 所述主 S2 结果有独立 lineage。必须并行保留版本及输入哈希，除非逐项复核后确认可替代；目前不替换 syh 正式 Top10。
- GLM provider 是否已真正实现、AI 报告是否持久化以及无密钥/超时行为尚未通过运行验证；API 路由和 wd 的离线评估脚本本身不足以证明在线链路成功。

## 当前版本、数据库与运行事实

审计只确认了配置声明与交付包自带证据，未连接数据库或启动容器，因此当前运行实例、真实服务健康、migration head 与应用记录的对应关系仍待隔离验证。正式数据有目录和 README 线索，但大体积输入受 Git ignore/外部许可约束。`syh/.env` 存在且未被复制；交付副本使用 `.env.example`，应为其配置独立凭据。

## 暂不迁移 / 淘汰

- 不迁移空 `zq`。
- 不引入第二套 FastAPI、React 前端、数据访问层或数据库 schema。
- 不直接采用交付包的派生 `main.py`（它移除了协作路由，作为 KG-only 包装而非完整主应用）。
- 不把 A+ lineage 覆盖到 syh 正式 S2 结果。
- 不采用未验证的导入器改进作为已生产代码；先针对隔离图谱审查与测试。
