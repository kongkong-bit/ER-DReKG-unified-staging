# A+ 输入格式适配 · 验证报告（阶段 0-4 第二部分）

- 生成时间（UTC）：2026-11-18T11:47:27+00:00
- 执行脚本：`build_phase0_4_adapt.py`
- 输出目录：`phase0_4_a_plus_freeze_and_adapt/adapted_input/`
- 执行性质：**只读源文件，仅写本目录；未修改 A+ 原始文件、未覆盖仓库文件、未连接数据库、未注册 AnalysisRun / GraphBuild。**

---

## 1. 做了什么 / 没做什么

**做了**：把 A+ 三个 CSV 适配为 GraphBuild 能读取的输入格式（纯数据转换）。

**没做**（严格禁止项，均未触碰）：
- 未修改 GraphBuild 源码、S1/S2 原始结果。
- 未连接 / 写入 PostgreSQL、Neo4j。
- 未注册 AnalysisRun 或 GraphBuild。
- 未删除 / 覆盖任何历史版本。
- 未改变候选集合（1,032 唯一 pert_id）或任何评分。

---

## 2. 唯一的数据契约变化

GraphBuild 消费端（`kg/scripts/build_project_graph_bundle.py:367,387`）读的字段名是
`quality_cc_median`，而 Final01 / A+ 原始字段名是 `CC_median`。二者是**同一个字段**，仅是命名差异。

| A+ 原始字段 | GraphBuild 契约字段 | 转换 | 说明 |
|---|---|---|---|
| CC_median | quality_cc_median | **重命名（值原样保留）** | 逐格校验 3,943 行 0 不一致 |

其余 14 个契约字段（`pert_id`、`drug_name`、`cell_id`、`pert_type`、`dose`、`time`、
`n_signatures`、`WTCS_median/mean/sd/mad`、`TAS_median`、`replicates_median`、`rank_within_condition`）
均同名，未做任何改动。

---

## 3. 输入核对

| 输入文件 | 行数 | 唯一 pert_id | 关键列 |
|---|---:|---:|---|
| Aplus_condition_records.csv | 3,943 | 1,032 | 15 原始字段 + 5 溯源字段（20 列） |
| Aplus_candidate_drugs.csv | 1,032 | 1,032 | 30 原始字段 + 5 溯源字段（35 列） |
| Aplus_candidate_condition_links.csv | 3,943 | — | link_id / candidate_id / condition_record_id 双向回查 |

---

## 4. 输出文件清单

| 文件 | 行数 | 列数 | 说明 |
|---|---:|---:|---|
| `drug_condition_summary.csv` | 3,943 | 15 | **GraphBuild seed 输入**，15 契约列，`quality_cc_median` 已就位 |
| `seed_provenance.csv` | 3,943 | 7 | 溯源 sidecar：每行对应 seed 一行，含 candidate_id / condition_record_id / source_row_number / source_file / source_sha256 |
| `candidate_master.csv` | 1,032 | 35 | 候选主集合（1,032 唯一 pert_id），派生校验物，**非 GraphBuild 输入** |
| `field_mapping.csv` | 20 | 4 | 转换前后字段映射表 |
| `validation_report.json` | — | — | 机器可读校验结果 |
| `sha256.txt` | — | — | 全部输出文件的 SHA-256 |

**设计说明**：seed 文件严格保持 15 个契约列，不附加额外列；溯源信息（候选 ID、条件 ID、来源）放在
`seed_provenance.csv`，通过 `seed_row_number` 与 seed 行一一对应、双向回查。这样既满足
「按实际 GraphBuild 输入契约处理字段名与文件格式」，又「保留候选 ID / 条件 ID / 来源追溯信息」。

---

## 5. 校验结果（9/9 通过）

| 校验项 | 结果 |
|---|---|
| 条件记录行数 = 3,943 | ✅ |
| 候选药物行数 = 1,032 | ✅ |
| 唯一 pert_id = 1,032 | ✅ |
| condition_record_id 唯一 | ✅ |
| candidate_id 唯一 | ✅ |
| 候选表 pert_id 集合 == 条件表 pert_id 集合 | ✅ |
| CC_median → quality_cc_median 值逐格不变 | ✅ |
| 未合并任何剂量/时间/细胞系/处理类型评分（3,943 行全保留） | ✅ |
| rank_within_condition 全部为正有限数值 | ✅ |

---

## 6. SHA-256 清单

| 文件 | SHA-256 |
|---|---|
| drug_condition_summary.csv | `0973fd446e707f1f695cb8a422216ea78a38aeb6cfe67c267c9c7b36e4be7745` |
| seed_provenance.csv | `af58be45ed7f3260008db3505f9c11567d4729f08ca7c3cda9a8cd502ce0a083` |
| candidate_master.csv | `d425cdb9ee01435474736b1a35bf757faa872a67145a6acac3f6b47b256d154e` |
| field_mapping.csv | `f529aaa943eb76354aab40e0f870bcf13bd264791169fdf7fa9f80588b0e1cef` |

---

## 7. 本阶段边界与遗留（供下一阶段）

本阶段只产出**数据**层面的契约适配。以下属于**代码/流程层**改造，不在本阶段范围内，留待下一阶段：

1. GraphBuild 入口 `backend/app/main.py:1552-1553` 仍硬编码 seed 文件名 `drug_condition_summary.csv`
   并绑定平台 S2 AnalysisRun 的 `condition_summary_sha256`——需在代码层改为显式接收 A+ seed 并登记其 SHA-256。
2. `50 / 240 / 1494 / 206 / Top50` 等历史规模硬编码断言（注册 / 验收脚本）需在新构建版本中移除或改判。
3. 新 `graph_build_id` 的登记与证据追溯。

本阶段未做上述任何代码修改，符合「只做数据转换，不改源码」的指令。

---

**完成后已停止，等待人工审阅。**
