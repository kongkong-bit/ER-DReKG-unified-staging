# A+ 冻结裁决记录（Final Freeze Ruling）

- 生成时间（UTC）：2026-11-18T11:50:00+00:00
- 裁决性质：人工已下达裁决指令，本文档为证据核对后的裁决落档。未修改任何源码/数据/数据库，未注册 AnalysisRun 或 GraphBuild。

---

## 0. 裁决结论（v2，2026-11-18 更新）

| 字段 | 值 | 含义 |
|---|---|---|
| **decision** | **ACCEPT** | 接受字节级身份确认 |
| **physical_original_found** | **false** | 原始工作机上的物理文件**未找回** |
| **repository_copy_found** | **true** | 完整仓库中的 Final01 四个文件已找到 |
| **repository_copy_byte_identical** | **true** | 仓库副本与权威 SHA-256 逐字节一致 |
| **byte_identity_verified** | **true** | 字节身份已确认 |
| **recovery_method** | **LF_to_CRLF** | 恢复件经 LF→CRLF 还原命中权威哈希 |
| **freeze_status** | **FROZEN** | 候选集合与原始字节已锁定 |

裁决要点（v2 明确）：
1. **原始工作机上的物理文件没有找回**（`physical_original_found=false`）。
2. **完整仓库中的 Final01 四个文件与权威 SHA-256 逐字节一致**（`repository_copy_found=true`、`repository_copy_byte_identical=true`）。
3. **LF→CRLF 恢复件也与权威哈希一致**（`recovery_method=LF_to_CRLF`、`byte_identity_verified=true`）。
4. **不要把仓库副本的发现描述成「原始工作机物理文件找回」**——二者是不同的事实：前者是"原始工作机上的物理原件未找回"，后者是"仓库提交版本身即为 CRLF 且字节一致"。仓库副本的来源必须标注为 `GIT_COMMITTED`，恢复件标注为 `RECOVERED_ORIGINAL`，均不得描述为物理原件。

---

## 1. 权威哈希来源确认

权威 manifest 已确认存在，且两份副本字节一致（同一 SHA-256），来源可信：

| 文件 | 状态 |
|---|---|
| `experiments/final_results/final_data_manifest.json` | 存在 |
| `experiments/final_results/results/final_data_manifest.json` | 存在，与上者字节一致 |

- 两份 manifest 的 SHA-256 均为 `960223ef52703f14698200105a729543ec1595ae689d3946254def66c1d4141f`。
- 其中的 `output_sha256` 含四个 Final01 文件的权威哈希，与 `supplemental_input_sha256`、`final_acceptance.deliverable_sha256` 交叉自洽（对同一文件记录值一致）。

四个权威哈希：

| 文件 | 权威 SHA-256（output_sha256） |
|---|---|
| final_signature_scores.csv | `efd1d5167751160006e6129515ac51db445068a5b1e25b7e1f97b2d9dc758911` |
| final_drug_condition_summary.csv | `5be0cdb02abbb011314b61927837077c29765f230f3822fcc00e1a650d7ba8f2` |
| final_corrected_condition_ranking.csv | `66e970195564d2945d57c111c57cdfed61b56a136181b59b8acec0a2764fffe8` |
| final_top10.csv | `c1f414d20e98923471a461e1ce6c3bf5b59002d4e5309cadf89be22492c08baf` |

---

## 2. 归档记录中的 CRLF 还原规则确认

规则不是本次臆测，而是项目既有、已独立记载的规则：

- `GSE139038_archive/records/missing_or_incomplete_files.csv` 第 11 行记载：
  > 「manifest 中的 SHA-256 对应 Windows CRLF 字节」「GitHub raw 提供 LF 字节；把 LF 还原为 CRLF 后 21 项哈希精确一致」。
- `GSE139038_archive/records/manifest_hash_verification.csv` 多行以「已恢复：内容一致（LF→CRLF 后哈希一致）」记录了同一条规则的实际应用。

结论：CRLF 还原规则有既有归档记录背书，恢复方法合法。

---

## 3. 三方哈希比对结果

| 文件 | 权威 | 恢复件 | 恢复件命中 | 仓库内文件 | 仓库命中 | 仓库行尾 |
|---|---:|---|---:|---|---|---|
| final_signature_scores.csv | efd1d516… | efd1d516… | ✅ | efd1d516… | ✅ | CRLF |
| final_drug_condition_summary.csv | 5be0cdb0… | 5be0cdb0… | ✅ | 5be0cdb0… | ✅ | CRLF |
| final_corrected_condition_ranking.csv | 66e97019… | 66e97019… | ✅ | 66e97019… | ✅ | CRLF |
| final_top10.csv | c1f414d2… | c1f414d2… | ✅ | c1f414d2… | ✅ | CRLF |

**4/4 恢复件精确命中权威哈希；4/4 仓库内文件精确命中权威哈希。**

---

## 4. 重要补充发现（不改变裁决，但强化证据）

克隆完整仓库后，`experiments/final_results/results/` 下的四个 Final01 CSV **本身就是 CRLF 行尾，且与权威哈希逐字节一致**（`repo_matches=true`，`repo_line_ending=CRLF`）。

这意味着存在**第二条独立确认路径**：
1. 恢复件路径：缓存 LF 副本 → LF→CRLF 还原 → 命中权威哈希（recovery_method=LF_to_CRLF）。
2. 仓库路径：Git 提交的原始文件 → 直接 CRLF → 命中权威哈希（非恢复，直接字节一致）。

两条路径指向同一字节序列，字节身份确认的强度高于单一恢复路径。

**说明（v2 字段化）**：`physical_original_found=false` 与 `repository_copy_found=true` / `repository_copy_byte_identical=true` 三者并列、互不矛盾：
- `physical_original_found=false`：原始工作机上的物理原件**未找回**。
- `repository_copy_found=true`：完整仓库（Git 提交版）中找到了 Final01 四个文件。
- `repository_copy_byte_identical=true`：仓库副本与权威 SHA-256 逐字节一致（CRLF）。

仓库副本的发现**不改变** `physical_original_found=false`，也**不得**被描述成物理原件找回；仓库副本来源标注为 `GIT_COMMITTED`。

---

## 5. 最终状态

- `freeze_status = FROZEN`
- A+ 候选集合（1,032 候选 / 3,943 条件）数据内容与原始字节已锁定。
- 冻结产物的来源标注：`RECOVERED_ORIGINAL`（恢复件）；仓库提交文件为 `GIT_COMMITTED`（字节一致）。

---

## 6. 修改记录（Changelog）

| 版本 | 时间（UTC） | 变更 |
|---|---|---|
| v1 | 2026-11-18T11:50 | 初始裁决：`decision=ACCEPT`、`physical_original_found=false`、`byte_identity_verified=true`、`recovery_method=LF_to_CRLF`、`freeze_status=FROZEN`。§4 记录"仓库副本字节一致"作为补充发现，但未字段化。 |
| v2 | 2026-11-18 | 依据最新发现新增字段 `repository_copy_found=true`、`repository_copy_byte_identical=true`；明确四条澄清（物理原件未找回 / 仓库副本字节一致 / 恢复件字节一致 / 不混淆二者）。**证据与原始哈希均未改动**，仅补充字段与措辞。 |

本记录完成。
