# ER-DReKG 知识图谱改进成果交付包

**交付包名称：** `ER-DReKG-KG-delivery-20261120`  
**整理日期：** 2026-11-20  
**交付范围：** A+ 候选输入 → S2 A+ 运行 → 正式 GraphBundle → 正式 GraphBuild 登记 → 图谱导入/验证代码改进  
**原始项目：** `e:\生物医学信息\ER-DReKG`（数据文件为复制件；main.py 为派生版；README、验收报告与证据文件为新写；原始项目未被修改）

---

## 0. 先读这一页

本包用于交付**知识图谱改进成果**，不是整个平台的完整可运行发行版。

如果目标是启动整个 ER-DReKG 平台，请回到此交付包的上一级 `ER-DReKG-unified-staging` 项目根目录，运行 `.\scripts\start-project.ps1`。完整的 `backend/app/` 源码和 `frontend/package.json` 位于项目根目录；本子包 `04_code/backend/app/main.py` 是供 KG 改动审阅的派生文件，刻意没有复制平台其他模块，因此单独从它启动会报缺少 `app.*` 导入。请不要把这个审阅包当成完整应用，也不要把工作区路径 `E:\生物医学信息\ER-DReKG` 当作当前启动路径。

三个必须先知道的事实：

1. **正式图谱是 `GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:d570eb8deb3e5eea`**，对应 GraphBundle `e0421796-2aff-47e2-9228-d683eab05fa9`，12,899 节点 / 48,729 关系。
2. **正式图谱实际使用的是原版（HEAD）导入器。** 正式记录中的 `neo4j_importer_sha256=72953d3c…`，经实测等于 HEAD 原版导入器 + CRLF；Neo4j 中关系 ID 不含 GraphBuild 后缀、`build_key` 为 `NULL`，与该结论一致。
3. **当前改进版导入器 `9fae6da6…` 是“已完成代码改进，尚未应用于正式图谱”。** 它新增了版本化关系 ID、`build_key`、输入哈希校验、预检/失败关闭、项目锁和导入后复核，但正式图谱**不是**它写入的。不得把它描述为正式图谱的实际导入代码。

**旧报告 `experiments/platform_phase_c/formal_graphbuild_verification.*` 覆盖的是旧构建 `a6aabb2147cb5f5e`，不是本包对象，不得冒充本轮验收报告。**

---

## 1. 目录结构

```text
ER-DReKG-KG-delivery-20261120/
├─ README_交付说明.md                 ← 本文件
├─ MANIFEST.sha256                    ← 包内全部文件（不含自身）的 SHA-256
├─ 01_inputs/
│  ├─ upstream_final_results/          ← 仓库内上游 Final01 结果（3 个 CSV）
│  ├─ aplus_freeze/                    ← A+ 冻结集（候选/条件/链接/lineage/manifest/验证）
│  ├─ aplus_adapted/                   ← 适配为 GraphBuild 契约的输入（15 列）
│  ├─ aplus_signature_scores/          ← A+ 签名派生（4,385 条）
│  └─ s1_and_enrichment/               ← GraphBundle 直接读取的 S1 与富集输入
├─ 02_S2_run/eab2f02a-.../             ← A+ S2 运行（5 个文件）
├─ 03_GraphBundle/e0421796-.../        ← 正式 GraphBundle（14 个文件，约 85 MB）
├─ 04_code/
│  ├─ kg/                              ← 构建器、导入器、验证器、测试、config、lock
│  ├─ backend/app/main.py              ← KG-only 派生版（见第 3 节）
│  ├─ backend/tests/test_api.py        ← 门禁测试
│  ├─ frontend/src/                    ← build 可查询门禁
│  ├─ docs/api/api_contract.yaml       ← GraphBuild 状态枚举
│  ├─ scripts/                         ← A+ dry-run 工具、多项目隔离测试
│  └─ patches/main_collab_removal.diff ← main.py 派生说明（只删 2 行）
└─ 05_evidence/
   ├─ formal_graphbuild_verification_d570eb8deb3e5eea.md / .json
   ├─ postgres_graphbuild_record.txt
   ├─ postgres_counts.txt
   ├─ neo4j_counts.txt
   ├─ bundle_file_hash_verification.tsv
   ├─ bundle_input_hash_verification.tsv
   ├─ environment_hashes.txt
   ├─ git_state_at_delivery.txt
   └─ uvicorn_*.log
```

---

## 2. 正式构建标识与计数

| 项目 | 值 |
|---|---|
| project_id | `3f18f4c1-713d-58c5-8a53-38eca5a5aaf9` |
| S1 运行 | `ANALYSIS_RUN:S1_PRECOMPUTED:9ebd6c43-9342-487e-a052-ae901461b58c` |
| S2 运行 | `ANALYSIS_RUN:S2_LINCS:eab2f02a-2bdf-53c8-833b-fedab03070c5` |
| S1 富集运行 | `ANALYSIS_RUN:S1_ENRICHMENT:eb409567-e846-4422-ae19-0055937871ea` |
| GraphBundle | `ANALYSIS_RUN:KG_GRAPH_BUNDLE:e0421796-2aff-47e2-9228-d683eab05fa9` |
| GraphBuild | `GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:d570eb8deb3e5eea` |
| build_key | `d570eb8deb3e5eea94d4f939e7b4c2cb15ca418b1e1b1a13284322229ba4e3f7` |
| 状态 | `materialized`，`import_status=PASS` |
| 全量节点/关系 | **12,899 / 48,729** |
| 证据记录 | **48,729** |
| DiseaseContext | **1** |
| 接口 2 跳口径 | 12,171 节点 / 44,932 关系（**不同口径，勿混用**） |

> 12,899 / 48,729 是 GraphBundle 全量与按 build 标记的 Neo4j 全量；12,171 / 44,932 是 API 从 `DiseaseContext` 出发 2 跳的实时统计。两者不是同一指标。

---

## 3. `main.py` 的处理方式（必须阅读）

原始工作区 `backend/app/main.py` 是**混合文件**：

- 既有本轮 KG 改动（`_graph_build_queryable`、`_mark_graph_build_failed`、`importing` 状态、导入参数传递等）；
- 又有**无关的协作中心路由**：
  ```python
  from app.routers.collab import router as collab_router
  app.include_router(collab_router)
  ```

按照“不把协作中心文件打包进去、又不能造成项目无法运行”的要求，本包采用如下处理：

- `04_code/backend/app/main.py` 是**派生版**：从工作区原文中**仅删除上述 2 行**，其余内容逐字节保留；
- `04_code/patches/main_collab_removal.diff` 给出精确 diff，可复核“只删了这两行”；
- 派生版已通过 Python `compile()` 语法检查；
- 派生版中不再包含任何 `collab` 引用；
- **原始项目文件未被修改**。

如果接收方要恢复完整应用，应使用原始仓库的 `main.py` 并同时提供协作中心模块；本包只交付 KG 相关代码片段，需与原始仓库其余模块配合运行。

---

## 4. A+ 输入到正式图谱的哈希链

完整清单见 `05_evidence/bundle_input_hash_verification.tsv` 与验收报告第 6 节。关键闭环：

| 环节 | SHA-256 |
|---|---|
| `final_corrected_condition_ranking.csv` | `66e970195564d2945d57c111c57cdfed61b56a136181b59b8acec0a2764fffe8` |
| `final_drug_condition_summary.csv` | `5be0cdb02abbb011314b61927837077c29765f230f3822fcc00e1a650d7ba8f2` |
| `final_signature_scores.csv` | `efd1d5167751160006e6129515ac51db445068a5b1e25b7e1f97b2d9dc758911` |
| `Aplus_candidate_drugs.csv` | `814581b92d01cc48c6a80080c02bd3a3da35fb405d32514aab56d11e056ac106` |
| `Aplus_condition_records.csv` | `c87dfe92648025fd038d32ecc76d32f05d8c65e0a9e0473f7d8663955707b74f` |
| `adapted_input/drug_condition_summary.csv` | `0973fd446e707f1f695cb8a422216ea78a38aeb6cfe67c267c9c7b36e4be7745` |
| S2 `eab2f02a/drug_condition_summary.csv` | `0973fd446e707f1f695cb8a422216ea78a38aeb6cfe67c267c9c7b36e4be7745` |
| A+ `signature_scores.csv` | `bbb9a5b74690420dc30f1cab56d9d8b7270aa28042f66e15c9d531c802b0992e` |
| S2 `eab2f02a/signature_scores.csv` | `bbb9a5b74690420dc30f1cab56d9d8b7270aa28042f66e15c9d531c802b0992e` |
| GraphBundle `bundle_manifest.json` | `c2c9f0f54782af88fabbeb9cd1311d7643a4fa43cdd9aa0f583ba872eb860704` |
| 构建器 `build_project_graph_bundle.py` | `191a506d331e9fa17f7d16af5748b41b929323886ae270f8183b1419f59f0c83` |

规模：1,032 个唯一候选；3,943 条条件；4,385 条签名；668 个精确 InChIKey 映射药物；17,324 条交汇路径；`relation_conflicts=0`。

---

## 5. 代码身份：正式导入器 vs 改进版导入器

见 `05_evidence/environment_hashes.txt`：

| 对象 | SHA-256 |
|---|---|
| HEAD 原版导入器（LF） | `9c4b6609c69810a8e276efd90703db24a148dddfdbddd628880ef0f73801256d` |
| HEAD 原版导入器 + CRLF | `72953d3c3c35d38fda9e23e836ad39b10cbd630084d0de176ba93f2b5ee61cb2` |
| **正式构建记录值** | `72953d3c3c35d38fda9e23e836ad39b10cbd630084d0de176ba93f2b5ee61cb2` |
| 改进版导入器（本包交付） | `9fae6da68bb3309c01ed80345c966937242f5785c9640429c5b91736d4af969d` |

**结论：正式图谱使用原版导入器；改进版导入器尚未应用。**

Neo4j 佐证：关系 ID 形如 `源|关系|目标|source_release`，不含 `|graph_build_id`；样例关系 `build_key=NULL`；版本归属仅存于 `graph_build_ids` 数组。

---

## 6. 未纳入本包的文件（及原因）

| 未纳入项 | 原因 |
|---|---|
| 协作中心后端/迁移/测试/方案文档 | 与 KG 无关；避免交付边界污染 |
| `cloud_migration/er_drekg.dump`、`neo4j.dump` | 数据库导出，可能含敏感数据；与 KG 交付无关 |
| `.env`、任何密钥 | 安全要求 |
| `backend/uv.lock` | 仅 PyPI 镜像与 lock revision 变化，无 KG 依赖变化 |
| `frontend/vite.config.ts` | 仅本地代理端口 `8000→18000` |
| `_original_view/` | 原版对照临时副本，非本轮交付物 |
| 10 个历史 GraphBundle 运行目录 | 初始提交已有，非本轮；避免与正式构建混淆 |
| `experiments/platform_phase_c/formal_graphbuild_verification.*` | 覆盖旧构建 `a6aabb2147cb5f5e`，非本轮 |
| `part3d_graphbundle_evaluation/` | 离线 duckdb 复刻评估，非正式链；避免混淆 |
| OptimusKG parquet、LINCS GCTX/pert_info | 外部许可数据，Git 忽略，体积大；哈希已在输入核对表中 |
| `__pycache__`、`.pytest_cache` | 缓存 |

### 归属仍无法确认、因此暂不纳入

| 项目 | 情况 |
|---|---|
| `data/processed/.../s1_enrichment/eb409567-.../run_manifest.json` 的 revision 2/3 | 仅刷新 `output_hashes`，未改参数；仓库中**找不到**执行该修复的脚本，仅有 manifest 自述 |
| `run_manifest.pre_repair.json`、`run_manifest.r2.json` | 上述修订的备份；归属依赖同一未确认来源 |

这两个/三个文件**未放入 ZIP**。如你确认需要，我可以在你授权后追加，并在 README 中标注“来源由 manifest 自述，脚本未入库”。

---

## 7. 复现与校验说明

### 7.1 校验本包完整性

在本包根目录执行：

```bash
sha256sum -c MANIFEST.sha256
```

Windows 可用 PowerShell 或 Git Bash。`MANIFEST.sha256` 覆盖除自身外的全部文件。

### 7.2 关于 CRLF 哈希

本包的 GraphBundle 输入哈希是在 **Windows 工作区 `core.autocrlf=true`** 下计算的（`i/lf w/crlf`）。因此：

- 在 Linux/macOS 或 `core.autocrlf=false` 环境重新 checkout 同一提交，CSV 字节会不同，哈希不会匹配；
- 如要在其他平台复现，应保留原始字节，或重新生成 manifest；
- 这不是数据差异，而是行尾差异。

### 7.3 外部数据依赖

GraphBundle 的 7 个外部输入未随包提供，但哈希已记录：

- `data/optimuskg/3.2/nodes/{drug,gene,pathway}.parquet`
- `data/optimuskg/3.2/edges/{drug_gene,pathway_gene}.parquet`
- `data/optimuskg/3.2/source_manifest.json`
- `s2_lincs/data/GSE70138_Broad_LINCS_pert_info_2017-03-06.txt.gz`

获取这些数据后，可用 `bundle_input_hash_verification.tsv` 逐项核对。

---

## 8. 已知限制与注意事项

1. **正式图谱未使用改进版导入器**（见第 5 节）。改进代码是下一轮候选，不要在正式图谱上重跑导入。
2. **`candidates` 表仍是旧 PHASEB 的 50 条**；A+ 的 1,032 条存在于 `s2_condition_results`（1,032 个 pert）和 GraphBundle 的 Candidate 节点中。前端 `/s2/candidates` 读 `candidates` 表，因此药物列表页仍显示 50 条。这不是本轮构建错误，但交付说明必须明确。
3. **没有 API 端到端冒烟测试**随本包执行；验收报告只覆盖登记一致性、文件哈希、代码身份和只读计数。
4. **本包不是科学验证**：图谱关系是数据库断言与项目表达证据的交集，不代表疗效、因果或 ER+ 特异性。
5. **旧验收报告不可替代**：`formal_graphbuild_verification.*` 覆盖旧构建 `a6aabb2147cb5f5e`（6,850 / 38,657），与本包 `d570eb8…`（12,899 / 48,729）不是同一对象。

---

## 9. 验收报告入口

- `05_evidence/formal_graphbuild_verification_d570eb8deb3e5eea.md`
- `05_evidence/formal_graphbuild_verification_d570eb8deb3e5eea.json`
- 机器可读核对：`05_evidence/bundle_file_hash_verification.tsv`、`05_evidence/bundle_input_hash_verification.tsv`

---

**交付判定：** 结构、哈希、登记一致性 PASS；正式图谱使用原版导入器；改进版导入器为“已完成代码改进，尚未应用于正式图谱”。
