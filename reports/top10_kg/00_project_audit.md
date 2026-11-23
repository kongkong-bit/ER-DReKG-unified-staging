# Top 10 知识图谱专项：项目与图谱审计

审计基于当前仓库文件及 `ER-DReKG-KG-delivery-20261120` 的只读交付证据；本次没有连接或写入 PostgreSQL/Neo4j。所有构建数字均标注其适用的 GraphBuild，不能视为实时数据库状态。

## 主工程与工作区

- 主工程：当前仓库 `D:/CLASS/syh`，项目 README 标识为 ER-DReKG。
- Git：分支 `main`，相对 `origin/main` ahead 1；工作区存在多处已修改和未跟踪文件（包括 `backend/`、`kg/`、`frontend/`、实验输出和交付包）。本专项审计未覆盖、重置或改写这些既有修改。
- 技术栈：FastAPI + SQLite/PostgreSQL 元数据路径（仓库同时含本地 SQLite DB）+ Neo4j 图查询；React/TypeScript 前端；BioCypher bundle 校验和 Neo4j 导入脚本。
- 关键代码：`kg/scripts/build_project_graph_bundle.py` 构建项目 GraphBundle；`backend/app/main.py` 注册 bundle 与 GraphBuild API 并调用导入器；`kg/scripts/import_phase_b_to_neo4j.py` 导入关系和节点。

## 图谱与正式构建

- 公共底图来源为 OptimusKG 3.2，许可记录为 CC BY-NC-SA 4.0；`data/optimuskg/3.2/source_manifest.json` 列出 5 个必要 Parquet 文件及 SHA-256，且这 5 个文件当前均存在，可作为后续补证输入。
- 交付包登记正式 GraphBuild `GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:d570eb8deb3e5eea`，GraphBundle `e0421796-2aff-47e2-9228-d683eab05fa9`，S1 run `9ebd6c43-9342-487e-a052-ae901461b58c`、S2 run `eab2f02a-2bdf-53c8-833b-fedab03070c5`、富集 run `eb409567-e846-4422-ae19-0055937871ea`。
- 该构建是 A+ 扩展候选集图谱，输入 1,032 个候选、3,943 条条件、4,385 条签名；全量 12,899 节点、48,729 关系/证据。它不是 Top 10 专项子图。
- 正式构建验收记录的 Neo4j 全量是 12,899/48,729；API DiseaseContext 两跳口径是 12,171/44,932。它们是不同统计范围。
- 交付报告确认正式图谱使用 HEAD 原版导入器哈希 `72953d3c…`；交付包的改进版导入器 `9fae6da6…` 未应用到正式 GraphBuild。
- 2026-11-20 报告使用当时执行的只读数据库查询转录，并没有在打包时重新连接数据库。当前服务/DB 是否仍与报告一致，尚未验证。

## Top 10 现有证据基线

- 正式榜单文件：`experiments/final_results/results/final_top10.csv`，10 行；哈希记录见 `experiments/final_results/results/final_results_manifest.json`（SHA-256 `c1f414d20e98923471a461e1ce6c3bf5b59002d4e5309cadf89be22492c08baf`）。名单不因图谱覆盖而调整。
- 现存 Top 10 机制映射、靶点和路径查询指向旧 GraphBuild `a6aabb2147cb5f5e`，不是上述最新正式 A+ GraphBuild。
- 旧构建审计：10 个药物精确 InChIKey 映射 5 个；有直接靶点 5 个（61 条靶点关系行）；有靶点→S1 通路路径 5 个（395 行）。这些是旧构建的文件证据，不代表当前 Neo4j 实时状态或新构建 Top 10 覆盖率。
- 作用语义保留原始关系（TARGET、ENZYME、TRANSPORTER 等），不统一推断为抑制/激活；路径表示来源关系与项目表达的交汇，不是因果或疗效证明。

## 当前缺口和阶段结论

1. 当前正式 A+ GraphBuild 与专项冻结 Top 10 范围不同；已在 `top10_graph_bundle/3928c54d` 单独生成 Top 10 离线 GraphBundle，未写 Neo4j。
2. Top 10 新 bundle 的实体映射、靶点语义和 S1 通路交汇覆盖已单独重算，见 `05_identity_mapping_report.md`、`06_top10_bundle_coverage.csv` 和 `08_mechanism_path_report.md`。
3. 交付包内正式 GraphBundle 与工作区当前文件存在若干哈希差异；本专项明确以交付包快照作为本次构建输入，不混用工作区路径下的不同版本。
4. 十份旧药物档案位于 `experiments/final_results/top10_mechanism_reports/`；本轮另生成了十份绑定新 Top 10 bundle 的档案，不能把旧档案误报为缺失或新证据。
5. Neo4j 改进导入器尚未正式应用；本专项未做数据库写入或当前 API/Neo4j 实时验收。

P0 的代码/数据溯源、名单冻结和离线基线已交付；实时数据库关系类型与孤立节点审计仍未完成。Top 10 离线图包是可审计的专项增量产物，不是已物化到 Neo4j 的正式 GraphBuild。
