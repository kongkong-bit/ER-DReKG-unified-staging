# Top 10 图谱重建与数据库门禁说明

## 可重复生成的本地交付物

从仓库根目录执行：

```powershell
python reports/top10_kg/build_identity_mapping.py
python reports/top10_kg/build_reproducibility_evidence.py
python reports/top10_kg/apply_reproducibility_to_dossiers.py
uv run --with h5py --with numpy --with pandas python reports/top10_kg/extract_top10_expression_reversal.py
python reports/top10_kg/apply_external_evidence_overlay.py
python reports/top10_kg/build_mechanism_evidence_grades.py
python reports/top10_kg/fetch_top10_pubmed_literature.py
kg\.venv\Scripts\python.exe kg\scripts\build_top10_chembl_reactome_bundle.py
```

表达方向交叉脚本读取本地 LINCS GCTX（约 5.8 GB），只提取冻结名单中的十个 `sig_id`。它不会修改 GCTX、S1 结果或正式榜单。疾病背景 CSV 是经人工核对的定向文献整理表；更改来源或记录时，必须同步更新 manifest SHA 和逐药档案，不能从空结果自动生成疾病关系。

复核步骤：

```powershell
git diff --check
Set-Location backend
uv run pytest tests -k "not test_http_project_creation_and_upload_remains_pending"
Set-Location ../kg
uv run --project . --group test pytest tests
Set-Location ../frontend
npm run build
```

后端 HTTP 上传用例在当前受限 Windows 环境卡在 TestClient 建立 Proactor socketpair；它不应被计为通过，需在支持该环境的主机复跑。

构建器为每次构建生成新 run UUID，只写新目录，不修改主数据库；不会覆盖已有 run。当前验收产物输出到项目 `graph_bundle/runs/7e70628f-7c76-4a2e-9dd5-56004e9c8c21`，生成 `analysis_run_registration.json` 注册模板。离线 BioCypher 验证结果为 6,866 节点、38,890 关系和逐边 38,890 EvidenceRecords；包含 9 条 ChEMBL Drug–Target、14 条 Protein–Gene、205 条 Reactome protein–pathway、217 条 pathway hierarchy 关系，以及 11 个人工审查 `DiseaseEvidence` 节点和两类各 11 条的限定语义边。Protein family 保持独立 ChEMBLTarget；疾病证据节点保留模型/亚型、方向、来源和限制，不表示治疗效果。

运行完整测试前先确认使用对应项目环境；新增 `kg/tests/test_top10_mechanism_schema.py` 验证扩展 schema 与 Neo4j importer allowlist，backend 新增隔离 SQLite 集成用例验证 GraphBuild 解析和证据持久化。SQLite 用例不替代 PostgreSQL/Neo4j 验收。

机制等级由 `build_mechanism_evidence_grades.py` 读取冻结名单、ChEMBL 机制记录、source-supported target dossiers 和定向疾病证据，输出 `mechanism_evidence_grade.csv` 与 SHA manifest。当前等级分布 A=3、B=6、C=1、U=0；每次更新来源或十份 target dossier 后都应重建并确认 10 个冻结 ID 完整匹配。等级是人工定向审阅，不按关系条数自动评分，也不代表疗效概率。

PubMed 检索脚本对冻结的 10 个候选分别执行 mechanism、direct target、breast cancer、ER-positive、MCF7、T47D 和 pathway 七组标题/摘要检索，并归档既有人工证据表引用的 PMID 元数据。每个查询组最多返回 100 条；超过上限的组会在 manifest 中列出，因此结果不穷尽。NCBI 原始 ESearch/EFetch 响应及 SHA-256 位于 `data/top10_kg/raw/pubmed/top10_review_v1/`，规范化结果与 manifest 位于 `data/top10_kg/evidence/top10_pubmed_search_results.csv` 和 `top10_pubmed_search_manifest.json`。解析器同时处理期刊文章和 PubMed Bookshelf 条目，并在 manifest 报告题名、摘要与书籍条目覆盖率。重跑默认复用已有响应快照；需要刷新检索时，应先将旧快照归档到新版本目录，再修改脚本 RAW_ROOT/输出版本，避免覆盖已审阅证据。检索命中尚未人工筛选，不自动进入机制等级或生成图关系；需另行记录纳入/排除理由、模型/亚型及限制。

## 隔离数据库验收记录（已执行）

`docker-compose.top10kg-staging.yml` 使用专有 Compose volumes 和本机端口 15432/17474/17687，与默认开发服务的 5432/7474/7687 以及默认命名卷分开。此次验收使用独立 Compose project `top10kg-staging-7e70628f`，确保卷与其他 staging run 隔离；若重跑，先检查该 project 是否已有保留数据，或改用新的 project name。Docker Desktop 可用后，启动隔离服务并检查健康状态：

```powershell
docker compose -p top10kg-staging-7e70628f -f docker-compose.top10kg-staging.yml up -d
docker compose -p top10kg-staging-7e70628f -f docker-compose.top10kg-staging.yml ps
```

首次启动应确认这两个专属 volume 是新建的空环境；复用既有 volume 时须先备份，或换一个全新 Compose project name。导入与回滚演练仅写 staging，不连接默认 5432/7687 服务。

本次独立 Compose 服务已启动并完成验收，project 名为 `top10kg-staging-7e70628f`。复现时容器健康后，在一个 PowerShell 窗口从仓库根目录读取 `.env` 中的本地密码（不打印密码），将 API 指向隔离端口并迁移 schema：

```powershell
$stagingSecrets = @{}
Get-Content .env | ForEach-Object {
  if ($_ -match '^(POSTGRES_PASSWORD|NEO4J_PASSWORD)=(.*)$') { $stagingSecrets[$matches[1]] = $matches[2] }
}
$encodedPgPassword = [uri]::EscapeDataString($stagingSecrets['POSTGRES_PASSWORD'])
$env:DATABASE_URL = "postgresql+psycopg://diseasegraph:$encodedPgPassword@127.0.0.1:15432/diseasegraph"
$env:GRAPH_SOURCE = 'neo4j'
$env:NEO4J_URI = 'bolt://127.0.0.1:17687'
$env:NEO4J_PASSWORD = $stagingSecrets['NEO4J_PASSWORD']
Set-Location backend
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

API 启动会在隔离 PostgreSQL 中补齐历史项目；其确定性 project ID 应为 `3f18f4c1-713d-58c5-8a53-38eca5a5aaf9`。在第二个 PowerShell 窗口从仓库根目录设置同一组数据库环境变量（同样不打印密码），先做只读预检，再显式登记已校验的 AnalysisRun：

```powershell
$stagingSecrets = @{}
Get-Content .env | ForEach-Object {
  if ($_ -match '^(POSTGRES_PASSWORD|NEO4J_PASSWORD)=(.*)$') { $stagingSecrets[$matches[1]] = $matches[2] }
}
$encodedPgPassword = [uri]::EscapeDataString($stagingSecrets['POSTGRES_PASSWORD'])
$env:DATABASE_URL = "postgresql+psycopg://diseasegraph:$encodedPgPassword@127.0.0.1:15432/diseasegraph"
$env:GRAPH_SOURCE = 'neo4j'
$env:NEO4J_URI = 'bolt://127.0.0.1:17687'
$env:NEO4J_PASSWORD = $stagingSecrets['NEO4J_PASSWORD']
Set-Location backend
.\.venv\Scripts\python.exe -m tools.register_analysis_run --registration data/processed/projects/3f18f4c1-713d-58c5-8a53-38eca5a5aaf9/graph_bundle/runs/7e70628f-7c76-4a2e-9dd5-56004e9c8c21/analysis_run_registration.json
.\.venv\Scripts\python.exe -m tools.register_analysis_run --registration data/processed/projects/3f18f4c1-713d-58c5-8a53-38eca5a5aaf9/graph_bundle/runs/7e70628f-7c76-4a2e-9dd5-56004e9c8c21/analysis_run_registration.json --apply
$runId = [uri]::EscapeDataString('ANALYSIS_RUN:KG_GRAPH_BUNDLE:7e70628f-7c76-4a2e-9dd5-56004e9c8c21')
$registered = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/projects/3f18f4c1-713d-58c5-8a53-38eca5a5aaf9/graph-builds?bundle_run_id=$runId"
$graphBuildId = $registered.graph_build_id
```

`register_analysis_run` 会逐项校验 project 路径、bundle manifest、AnalysisRun manifest、全部输出文件及 checksum；默认只读 dry-run。`--apply` 只允许本机 PostgreSQL；非本机目标还要求显式 `--allow-nonlocal`。API 的 POST 才会通过正式 GraphBuild 路径执行 Neo4j 增量导入和 PostgreSQL EvidenceRecord 写入。验证 Neo4j 时回到仓库根目录运行：

```powershell
Set-Location ..
$env:NEO4J_URI = 'bolt://127.0.0.1:17687'
.\kg\.venv\Scripts\python.exe kg\scripts\verify_neo4j_import.py --graph-build-id $graphBuildId --project-id 3f18f4c1-713d-58c5-8a53-38eca5a5aaf9 --bundle-dir 'data/processed/projects/3f18f4c1-713d-58c5-8a53-38eca5a5aaf9/graph_bundle/runs/7e70628f-7c76-4a2e-9dd5-56004e9c8c21'
```

对照精确清单后重复 POST，确认 GraphBuild ID 不变且返回幂等状态。

如需实际演练回滚，先保存验证报告，再在已配置相同本地数据库环境的 PowerShell 窗口执行预览和精确 ID 二次确认：

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m tools.rollback_graph_build --graph-build-id $graphBuildId
.\.venv\Scripts\python.exe -m tools.rollback_graph_build --graph-build-id $graphBuildId --apply --confirm-graph-build-id $graphBuildId
```

该命令只删除该 GraphBuild 成员关系，保留共享 Neo4j 节点和 AnalysisRun；PostgreSQL 中只删除对应 EvidenceRecord、DiseaseContext 和 GraphBuild。Neo4j 先删、PostgreSQL 后删；若第二步失败，保留的 GraphBuild 可供安全重试。默认只允许本机数据库；非本机目标需要 `--allow-nonlocal`。回滚后确认 GraphBuild 清单中已无此 ID，再保留 staging volume 供审计。

完成验收后可停止隔离容器，但保留卷以便审计：

```powershell
docker compose -p top10kg-staging-7e70628f -f docker-compose.top10kg-staging.yml down
```

不要对这组服务执行 `down -v`，除非已确认卷内数据不再需要。真正写入前，仍须分别备份 PostgreSQL 和 Neo4j、保存只读基线计数与 GraphBuild ID，并先完成导入预检。回滚应按新 GraphBuild ID 处理，不能清空数据库或删除其他 build 共享的 Drug/Gene/Pathway 节点。

## 本次 staging 验收结果

项目级扩展 GraphBundle 位于 `data/processed/projects/3f18f4c1-713d-58c5-8a53-38eca5a5aaf9/graph_bundle/runs/7e70628f-7c76-4a2e-9dd5-56004e9c8c21`。它曾通过 AnalysisRun 登记并由 GraphBuild API 导入隔离 staging Neo4j；验收完成后已按方案回滚该 GraphBuild。已回滚的 GraphBuild ID：`GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:5bb1e749e1caa6e2`。当前保留 AnalysisRun 和 GraphBundle 文件，不保留该 GraphBuild 的关系与证据快照。

精确清单核对 PASS；导入时 Neo4j 计数为 6,866 节点和 38,890 关系，逐节点/关系 ID、类型、属性比较差异 0；来源断言/证据 ID 缺失 0，未版本化成员 0，孤立节点 0。Importer 连续执行两次均 PASS，状态一致。报告：`reports/top10_kg/neo4j_import_validation_7e70628f-7c76-4a2e-9dd5-56004e9c8c21.json`。回滚 dry-run 发现 38,890 条关系、38,890 条 EvidenceRecord 和 1 条 DiseaseContext；apply 后均已清除。回查确认 GraphBuild 不存在、AnalysisRun 保留，共享领域节点保留 6,785 个。

以上结论只适用于隔离 staging GraphBuild 导入与回滚；本次未迁移到正式/默认数据库，也未实时复核历史 A+ build。浏览器端运行时 E2E 仍未验收。staging Compose volume 保留供审计，请勿执行 `down -v`。
