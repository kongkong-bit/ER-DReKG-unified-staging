# ER-DReKG 知识图谱优化 · 阶段 0-3 校验与冻结报告
## A+ 候选输入冻结与 Final01 原始数据恢复

- 生成时间（UTC）：2026-11-18T10:06:43.983652+00:00
- 生成时间（本地）：2026-11-18T18:06:43.983652+08:00
- 输出目录：`E:\生物医学信息\S3_机制解释能力诊断\phase0_3_a_plus_seed_freeze`
- 执行脚本：`build_phase0_3_a_plus.py` v1.0.0
- 执行性质：源文件严格只读；所有新文件仅写入本阶段输出目录；未修改 S1/S2/Final01、未重跑 limma/WTCS/排名、
  未改 GraphBuild 代码或 Neo4j Schema、未导入 Neo4j、未写 PostgreSQL、未注册 AnalysisRun、
  未覆盖历史文件、未进入阶段 0-4。

---

## 汇报摘要（任务书 §八 七问）

**1. 是否找回了原始 Final01 四个 CSV？**
**物理原始文件：未找到；原始字节：已确定性恢复。** 全盘搜索 639,468 个文件条目 +
归档目录（`GSE139038_archive/original_repo_main`、`local_cache`、`records`）+
历史工作区 / 备份 / 个人目录，均未发现与权威哈希一致的 CRLF 原始文件；只找到一份 LF 重新序列化副本
（及 `frontend/public/final-top10.csv` 这一份同字节拷贝）。但该副本经项目**既有归档规则**
（LF → CRLF）还原后，四个文件的 SHA-256 全部精确命中 `final_data_manifest.json` 权威值。
SHA-256 一致即字节一致，因此原始输入的字节身份已被密码学确认。

**2. 原始 SHA-256 是否全部匹配？**
**是，4/4 精确匹配**（`output_sha256`、`final_acceptance.deliverable_sha256`、
`supplemental_input_sha256` 三处记录交叉自洽）。逐文件见 §1.3。
缓存副本原样哈希 **4/4 不匹配** —— 差异仅为行尾 LF↔CRLF，无 BOM、无编码、无内容变化。

**3. 是否成功构造 1,032 个候选药物和 3,943 条条件记录？**
**是。** 主表 1,032 行 / 1,032 个唯一 pert_id；
条件表 3,943 行；从原始 4,748 行筛出 3,943 行，
排除 805 行（439 个 B-A 化合物）。
关联表 3,943 行。

**4. 是否通过全部校验？**
**是，12/12 项必需校验全部通过**（§3），另有筛选前后统计、重复/缺失值逐列记录。

**5. 是否存在数据缺失或需要人工决策的问题？**
有 4 项需人工裁决/标记（§5），最关键的是：**是否接受「按既有项目规则做字节还原」
等同于「找回原始文件」**。本阶段未自行替人工做此裁决，所有产物标记为 `FROZEN_CONDITIONAL`。

**6. 输出目录及交付文件清单**
见 §4，共 7 个规定交付 + 4 个恢复原件 + 1 个复现脚本，全部在 `E:\生物医学信息\S3_机制解释能力诊断\phase0_3_a_plus_seed_freeze`。

**7. 是否存在阻碍下一阶段 GraphBuild 的问题？**
有 6 项（§6），主要是入口哈希绑定、字段名契约、以及本地缺失的 pert_info /
OptimusKG parquet / 3 个富集 CSV。本阶段按任务书边界不处理这些障碍。

---

## 1. 任务 1：Final01 原始输入恢复

### 1.1 搜索范围与结果

| 范围 | 结果 |
|---|---|
| `E:\` 全盘 + `<USER_HOME>` 全盘（639,468 条目） | 仅找到缓存中 4 个目标 CSV、3 份 `final_data_manifest.json`、1 份 `final-top10.csv` 同字节拷贝 |
| `E:\生物医学信息\S1_优化工作\GSE139038_archive` | `original_repo_main/` 与 `local_cache/` 仅含 exp010 / platform_phase_b / S1 富集文件；**无 `final_results/` 目录**、无 Final01 CSV、无 `.git` |
| 归档记录 `archive_file_inventory.csv` / `manifest_hash_verification.csv` | 未登记任何 Final01 CSV；但记录了 CRLF 还原规则（见 1.2） |
| 备份 / 重命名副本 / `.zip` `.gz` `.7z` `.bak` | 未发现 Final01 原始 CSV 的归档副本 |
| 两个 `.git` 仓库 | 属其它项目（`-ADHD-`、`xinshouzhizhan`），与本项目无关 |

**结论：磁盘上不存在与权威哈希一致的物理原始文件。** 缓存中仅有一份内容等价的 LF 序列化副本。

### 1.2 恢复规则不是本次臆测，而是项目既有且已验证的规则

`GSE139038_archive/records/missing_or_incomplete_files.csv` 末行明确记载：

> 「manifest 中的 SHA-256 对应 Windows CRLF 字节」「GitHub raw 提供 LF 字节；把 LF 还原为 CRLF
> 后 **21 项哈希精确一致**」「保留 LF 版本，未改写任何字节」

独立复核：`external_s1_drug_ranking.csv` 缓存 LF 版哈希 `75e87b10fd7ae83b…`，
经 LF→CRLF 还原后为 `4a7ce1bc4fc72298…`，
与 `final_data_manifest.json::input_sha256` 记录的 `4a7ce1bc4fc72298…` **精确一致**。
`archive_file_inventory.csv` 中 21 个文件同样出现「`SHA256_还原CRLF后` == `manifest基准哈希`」。

因此阶段 0-2 报告的「字节级不可复现」结论**不完整**：它比对了缓存副本原样哈希，
但未执行项目已确立的 CRLF 还原。本阶段补上该步骤后，4/4 精确复现。

### 1.3 四文件逐项核验（恢复后即写入 `recovered_originals/`）

| 文件 | 缓存 LF 字节 | 缓存原样 SHA-256 | 恢复后字节 | 恢复后 SHA-256 | manifest 权威 SHA-256 | 结果 | 数据行/列 |
|---|---:|---|---:|---|---|---|---|
| `final_corrected_condition_ranking.csv` | 309,794 | `a71dc5dbbfdbbdc7…` | 310,827 | `66e970195564d294…` | `66e970195564d294…` | MATCH | 1,032 / 30 |
| `final_drug_condition_summary.csv` | 536,889 | `d82e868129525419…` | 541,638 | `5be0cdb02abbb011…` | `5be0cdb02abbb011…` | MATCH | 4,748 / 15 |
| `final_signature_scores.csv` | 1,052,130 | `6d9e7decdf8b1790…` | 1,057,992 | `efd1d51677511600…` | `efd1d51677511600…` | MATCH | 5,861 / 18 |
| `final_top10.csv` | 3,330 | `44c2c2ed369e6557…` | 3,341 | `c1f414d20e989234…` | `c1f414d20e989234…` | MATCH | 10 / 30 |

恢复变换：`b.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")`。
四个文件前 4 字节分别为 `pert` / `pert` / `sig_` / `pert`，**均无 BOM**；
变换不涉及编码、字段、数值或行内容，仅行尾字节。两条独立路径（纯字节变换、
`csv` 标准 `QUOTE_MINIMAL` + CRLF 重序列化）命中同一哈希，排除巧合。

### 1.4 多版本处理

按任务书要求「不自行覆盖或选择」，全部登记在 `Aplus_input_lineage.csv`：
- 4 份 `SOURCE_COPY_LF`（缓存原样，哈希不匹配）
- 4 份 `RECOVERED_ORIGINAL`（写入 `recovered_originals/`，哈希精确匹配）
- 1 份 `SOURCE_COPY_IDENTICAL`（`frontend/public/final-top10.csv`，与 `results/final_top10.csv` 字节相同）
- 3 份 `MANIFEST_AUTHORITY`（三份 `final_data_manifest.json` 字节相同）
- 佐证文件、阶段 0-2 八个输入、全部生成输出

恢复产物写入**新目录的独立子目录**，缓存副本与其它历史文件**一个字节都未改动**。
本次未重新计算 S2、未重跑 WTCS、未重新生成排名，也未伪造任何哈希。

---

## 2. 任务 2：A+ 输入数据集构造

| 项 | 定义 |
|---|---|
| 候选集合 A | `final_corrected_condition_ranking.csv` 的 1,032 行 / 1,032 个唯一 `pert_id`（主剂量 `10.0 um`、24 h、MCF7、trt_cp） |
| 条件全集 C | `final_drug_condition_summary.csv` 的 4,748 行 / 1,471 个唯一 `pert_id` |
| 筛选规则 | 保留 `pert_id ∈ A` 的**全部**条件行；不按剂量过滤、不去重、不合并 |
| A+ 结果 | 1,032 个候选 + 3,943 条条件记录；排除 805 行（B−A 的 439 个化合物） |
| 主键 | 候选 `candidate_id = APLUS-C-00001…01032`；条件 `condition_record_id = APLUS-R-00001…03943`；关联 `link_id = APLUS-L-00001…03943` |
| 回查键 | 条件表保留 `source_row_number`（原始 4,748 行表内的物理行号，表头为第 1 行）与 `source_sha256` |

**字段保留**：主表完整保留原始排名表的 30 列（含 `WTCS_median` / `WTCS_mean` /
`WTCS_sd` / `WTCS_mad` / `CC_median` / `TAS_median` / `replicates_median` / `rank` /
`n_24h_dose_conditions` / `negative_dose_fraction` / `external_rank` / ER± 敏感性等）；
条件表完整保留 15 列（含剂量、时间、细胞系、处理类型、质量指标、条件内排名）。
**未将不同条件下的评分合并成单一药物评分**：条件表逐行保留各自的 `WTCS_median`。

### 筛选前后统计

| 指标 | 筛选前（C） | 筛选后（A+） |
|---|---:|---:|
| 条件行数 | 4,748 | 3,943 |
| 唯一 `pert_id` | 1,471 | 1,032 |
| 重复条件键 | 0 | 0 |
| 每候选条件数 min / max / mean | — | 1 / 6 / 3.8207 |
| 排除行数 | — | 805 |

A+ 剂量分布（前 6）：`10.0 um` 1,032, `3.33 um` 681, `1.11 um` 611, `0.37 um` 550, `0.12 um` 549, `0.04 um` 520。
其中主剂量 `10.0 um` 恰为 1,032 行，
与 A 方案一致；其余 2,911 行是 A 方案会丢失的其它剂量证据。

---

## 3. 任务 3：严格校验结果

| 校验项 | 结果 |
|---|---|
| candidate_rows_equals_1032 | True |
| candidate_pert_id_unique | True |
| candidate_pert_id_nonempty | True |
| condition_rows_equals_3943 | True |
| all_condition_pert_id_in_candidate_set | True |
| all_1032_candidates_have_condition | True |
| no_extra_candidates | True |
| link_rows_equals_3943 | True |
| link_bidirectional_traceable | True |
| original_ranking_fields_intact | True |
| original_condition_fields_intact | True |
| no_duplicate_condition_keys_in_selection | True |

补充记录：
- **零条件候选**：0 个（列表：无）—— 1,032 个候选全部至少关联 1 条条件记录。
- **额外候选**：0 个；**条件表越界 pert_id**：0 个。
- **空必需字段行**：0；逐列缺失值统计见 `Aplus_manifest.json :: validation.missing_values_per_column`。
- **关联完整性**：3,943 条 link 均可由 `candidate_id` 回查主表、由 `condition_record_id` 回查条件表，
  且 `pert_id` 与 `condition_key` 双向一致。
- **原始字段逐格比对**：主表 30 列、条件表 15 列与恢复原件逐格相等。

**若数量不符不补齐/不删除**：脚本在恢复哈希、候选数、条件数、必需校验任一失败时直接中止并报错；
本次实测全部与预期一致，未触发任何补齐或删除逻辑。

---

## 4. 任务 4：冻结清单与交付文件

| 文件 | 内容 |
|---|---|
| `Aplus_candidate_drugs.csv` | 1,032 行，35 列（原始 30 列 + 5 个溯源列） |
| `Aplus_condition_records.csv` | 3,943 行，20 列（原始 15 列 + 5 个溯源列） |
| `Aplus_candidate_condition_links.csv` | 3,943 行，16 列 |
| `Aplus_input_lineage.csv` | 36 行来源对应清单 |
| `Aplus_validation_report.md` | 本报告 |
| `Aplus_manifest.json` | 输入/输出路径、实算 SHA-256、字节数、行数、定义、筛选规则、脚本版本、运行时间、校验结果 |
| `Aplus_sha256.txt` | 输出目录全部文件的实算 SHA-256（不含自身），相对路径格式 |
| `recovered_originals/*.csv` | 4 个恢复的原始字节文件（CRLF），供独立复核权威哈希 |
| `build_phase0_3_a_plus.py` | 可复现脚本 v1.0.0 |

**哈希约定**：所有 SHA-256 均对**最终实际写入的文件**实算，未使用任何预测值。
`Aplus_sha256.txt` 按惯例不含自身哈希；`Aplus_manifest.json` 不记录自身哈希
（其哈希记录在 `Aplus_sha256.txt` 中）以避免循环自引用。二者在 manifest 中明确标注。

**冻结状态**：`FROZEN_CONDITIONAL` —— 数据内容与原始字节已锁定，但恢复方式的合法性待人工裁决（§5）。

---

## 5. 无法确认 / 需人工决策

1. 物理意义上的原始 CRLF 文件未在磁盘上找到；本次是通过项目既有 CRLF 还原规则确定性恢复出字节一致的原始文件。是否接受该方式等同于『找回原始文件』，需人工裁决。
2. 阶段 0-2 判定的『字节级不可复现』结论应据此修正：差异仅为 LF/CRLF 行尾，内容未变。
3. 缓存仓库与工作区均无 .git，git_commit 仍为 UNKNOWN；以 SHA-256 为唯一锚点。
4. 实时 PostgreSQL/Neo4j 不可达，图内状态与 GraphBuild 基线仍沿用阶段 0-1 的 NOT_SELECTED。

数据库状态（仅记录，不修复）：PostgreSQL 5432 = `CLOSED (TimeoutError)`；
Neo4j bolt 7687 = `CLOSED (TimeoutError)`；Neo4j HTTP 7474 = `CLOSED (TimeoutError)`。

---

## 6. 阻碍下一阶段 GraphBuild 的问题

1. GraphBuild 入口 main.py:1552-1553 绑定文件名与 condition_summary_sha256；需生成平台 S2 条件摘要并登记溯源（本阶段禁止注册 AnalysisRun）。
2. 字段契约不一致：本阶段条件表沿用 Final01 的 CC_median，GraphBuild 期望 quality_cc_median。
3. 本地缺 GSE70138_Broad_LINCS_pert_info_2017-03-06.txt.gz、data/optimuskg/3.2 下 5 个 parquet + source_manifest.json、pathway_gene_links.csv / go_up.csv / go_down.csv。
4. 208 个候选在本地可用产物中无任何身份记录（不等于外部不存在）；136 个待定身份需 drug.parquet 才能判定。
5. 50 / 240 / 1494 / 206 / Top50 等硬编码断言与 KG06 覆盖审计仍绑定历史 Top50。
6. 人工裁决：若不接受字节恢复作为原始身份确认，则本冻结产物应视为条件性冻结，需在取得物理原件后重新确认。

---

**完成后立即停止。本阶段未修改任何项目源码、配置、数据库或图谱，未重建图谱，
未进入阶段 0-4，等待人工审阅。**
