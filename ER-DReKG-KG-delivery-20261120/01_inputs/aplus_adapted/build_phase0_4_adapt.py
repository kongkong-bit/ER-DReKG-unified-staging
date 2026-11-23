# -*- coding: utf-8 -*-
"""阶段 0-4 第二部分：A+ 输入格式适配（只做数据转换，不改任何源码/数据库）。

将 A+ 三个 CSV 适配为 GraphBuild 能读取的输入格式：
  - 候选主集合 = 1,032 个唯一 pert_id
  - 条件记录 = 3,943 条（全部保留，不合并剂量/时间/细胞系/处理类型）
  - 唯一字段名变化：Final01 的 CC_median -> GraphBuild 契约的 quality_cc_median

严格只读源文件；输出仅写入本目录（adapted_input/）。
不修改 A+ 原始文件、不覆盖仓库文件、不连接数据库、不注册 AnalysisRun/GraphBuild。
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

PHASE0_3 = Path(r"e:/生物医学信息/S3_机制解释能力诊断/phase0_3_a_plus_seed_freeze")
OUT = Path(__file__).resolve().parent

SRC_CONDITIONS = PHASE0_3 / "Aplus_condition_records.csv"
SRC_CANDIDATES = PHASE0_3 / "Aplus_candidate_drugs.csv"
SRC_LINKS = PHASE0_3 / "Aplus_candidate_condition_links.csv"

# GraphBuild 契约的 15 列（platform S2 drug_condition_summary.csv）
CONTRACT_COLUMNS = [
    "pert_id", "drug_name", "cell_id", "pert_type", "dose", "time", "n_signatures",
    "WTCS_median", "WTCS_mean", "WTCS_sd", "WTCS_mad", "quality_cc_median",
    "TAS_median", "replicates_median", "rank_within_condition",
]

PROVENANCE_COLUMNS = ["condition_record_id", "candidate_id", "source_row_number", "source_file", "source_sha256"]


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="raise")
        w.writeheader()
        w.writerows(rows)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for c in iter(lambda: f.read(1024 * 1024), b""):
            h.update(c)
    return h.hexdigest()


def fail(msg: str) -> None:
    raise SystemExit(f"[ABORT] {msg}")


def main() -> None:
    started = datetime.now(timezone.utc).isoformat()

    # ---- 读取源文件（只读） ----
    cond = read_csv(SRC_CONDITIONS)
    cand = read_csv(SRC_CANDIDATES)
    links = read_csv(SRC_LINKS)

    # ---- 源文件完整性核对 ----
    if len(cond) != 3943:
        fail(f"条件记录行数 != 3943，实际 {len(cond)}")
    if len(cand) != 1032:
        fail(f"候选药物行数 != 1032，实际 {len(cand)}")
    if len(links) != 3943:
        fail(f"关联表行数 != 3943，实际 {len(links)}")

    cond_columns = list(cond[0].keys())
    cand_columns = list(cand[0].keys())

    # 条件表必须含 15 个原始字段 + 5 个溯源字段（共 20 列）
    for col in CONTRACT_COLUMNS:
        if col not in cond_columns and col != "quality_cc_median":
            # contract 中除 quality_cc_median 外，其余应等于 Final01 原始列名
            if col not in cond_columns:
                fail(f"条件表缺列 {col}")
    if "CC_median" not in cond_columns:
        fail("条件表缺 CC_median 列")
    if "quality_cc_median" in cond_columns:
        fail("条件表不应已有 quality_cc_median 列")
    for col in PROVENANCE_COLUMNS:
        if col not in cond_columns:
            fail(f"条件表缺溯源列 {col}")

    # 候选唯一性核对
    pert_ids = [r["pert_id"] for r in cond]
    unique_pert = sorted(set(pert_ids))
    if len(unique_pert) != 1032:
        fail(f"条件表唯一 pert_id 数 != 1032，实际 {len(unique_pert)}")
    if len(set(r["pert_id"] for r in cand)) != 1032:
        fail(f"候选表唯一 pert_id 数 != 1032")

    # 候选表与条件表的 pert_id 集合一致
    if set(r["pert_id"] for r in cand) != set(pert_ids):
        fail("候选表 pert_id 集合与条件表不一致")

    # 条件记录唯一键核对
    cond_ids = [r["condition_record_id"] for r in cond]
    if len(set(cond_ids)) != 3943:
        fail("condition_record_id 不唯一")
    cand_ids = [r["candidate_id"] for r in cand]
    if len(set(cand_ids)) != 1032:
        fail("candidate_id 不唯一")

    # rank_within_condition 必须为正有限数值（GraphBuild 契约要求）
    for r in cond:
        try:
            rk = float(r["rank_within_condition"])
        except (TypeError, ValueError):
            fail(f"rank_within_condition 非数值：{r.get('pert_id')} {r.get('rank_within_condition')}")
        if not (rk > 0 and rk < float("inf")):
            fail(f"rank_within_condition 非正有限值：{r.get('pert_id')} {rk}")

    # 每条条件记录都能映射到唯一候选（candidate_id 回查）
    cand_by_id = {r["candidate_id"]: r for r in cand}
    for r in cond:
        if r["candidate_id"] not in cand_by_id:
            fail(f"条件记录 {r['condition_record_id']} 的 candidate_id 不在候选表")

    # ---- 转换：CC_median -> quality_cc_median（值不变） ----
    seed_rows = []
    for i, r in enumerate(cond, start=1):
        seed = {c: r[c] for c in CONTRACT_COLUMNS if c != "quality_cc_median"}
        seed["quality_cc_median"] = r["CC_median"]  # 纯重命名，值原样保留
        # 按契约列顺序重排
        seed = {c: seed[c] for c in CONTRACT_COLUMNS}
        seed["__seed_row"] = i  # 临时行号，用于溯源
        seed_rows.append(seed)

    # 值不变校验：CC_median == quality_cc_median 逐格
    for orig, s in zip(cond, seed_rows):
        if orig["CC_median"] != s["quality_cc_median"]:
            fail(f"CC_median 值在重命名后发生变化：{orig['pert_id']}")

    # ---- 写出 seed（15 契约列，去掉临时行号） ----
    seed_out = [ {c: r[c] for c in CONTRACT_COLUMNS} for r in seed_rows ]
    write_csv(OUT / "drug_condition_summary.csv", seed_out, CONTRACT_COLUMNS)

    # ---- 溯源 sidecar（每行对应 seed 一行，双向回查） ----
    prov_rows = []
    for i, r in enumerate(cond, start=1):
        prov_rows.append({
            "seed_row_number": i,
            "pert_id": r["pert_id"],
            "condition_record_id": r["condition_record_id"],
            "candidate_id": r["candidate_id"],
            "source_row_number": r["source_row_number"],
            "source_file": r["source_file"],
            "source_sha256": r["source_sha256"],
        })
    PROV_COLUMNS = ["seed_row_number", "pert_id", "condition_record_id", "candidate_id", "source_row_number", "source_file", "source_sha256"]
    write_csv(OUT / "seed_provenance.csv", prov_rows, PROV_COLUMNS)

    # ---- 候选主表（1,032，派生校验物，非 GraphBuild 输入） ----
    # 保留原始 30 列 + 溯源列（A+ 候选表原样，仅确认 pert_id 与条件表一致）
    write_csv(OUT / "candidate_master.csv", cand, cand_columns)

    # ---- 字段映射表 ----
    mapping = []
    for c in CONTRACT_COLUMNS:
        if c == "quality_cc_median":
            mapping.append({"aplus_field": "CC_median", "adapted_field": "quality_cc_median", "transform": "RENAME (value unchanged)", "destination": "drug_condition_summary.csv"})
        else:
            mapping.append({"aplus_field": c, "adapted_field": c, "transform": "UNCHANGED", "destination": "drug_condition_summary.csv"})
    for c in ["condition_record_id", "candidate_id", "source_row_number", "source_file", "source_sha256"]:
        mapping.append({"aplus_field": c, "adapted_field": c, "transform": "PRESERVED", "destination": "seed_provenance.csv"})
    MAP_COLUMNS = ["aplus_field", "adapted_field", "transform", "destination"]
    write_csv(OUT / "field_mapping.csv", mapping, MAP_COLUMNS)

    # ---- SHA-256 清单 ----
    outputs = ["drug_condition_summary.csv", "seed_provenance.csv", "candidate_master.csv", "field_mapping.csv"]
    sha_lines = []
    for name in outputs:
        p = OUT / name
        sha_lines.append(f"{sha256(p)}  {name}")
    sha256_txt = OUT / "sha256.txt"
    sha256_txt.write_text("\n".join(sha_lines) + "\n", encoding="utf-8")

    # ---- 校验报告数据 ----
    seed_unique_pert = len(set(r["pert_id"] for r in seed_out))
    report = {
        "generated": started,
        "inputs": {
            "Aplus_condition_records.csv": {"rows": len(cond), "columns": cond_columns},
            "Aplus_candidate_drugs.csv": {"rows": len(cand), "columns": cand_columns},
            "Aplus_candidate_condition_links.csv": {"rows": len(links)},
        },
        "outputs": {
            "drug_condition_summary.csv": {"rows": len(seed_out), "columns": CONTRACT_COLUMNS, "unique_pert_id": seed_unique_pert},
            "seed_provenance.csv": {"rows": len(prov_rows), "columns": PROV_COLUMNS},
            "candidate_master.csv": {"rows": len(cand), "unique_pert_id": len(set(r["pert_id"] for r in cand))},
            "field_mapping.csv": {"rows": len(mapping)},
        },
        "checks": {
            "condition_rows_equals_3943": len(cond) == 3943,
            "candidate_rows_equals_1032": len(cand) == 1032,
            "unique_pert_id_equals_1032": seed_unique_pert == 1032,
            "condition_record_id_unique": len(set(cond_ids)) == 3943,
            "candidate_id_unique": len(set(cand_ids)) == 1032,
            "candidate_pert_id_set_matches_condition": set(r["pert_id"] for r in cand) == set(pert_ids),
            "cc_median_renamed_value_unchanged": True,
            "no_condition_merged": len(seed_out) == len(cond),
            "rank_within_condition_all_positive_finite": True,
        },
        "sha256": {name: sha256(OUT / name) for name in outputs},
    }
    report_path = OUT / "validation_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("\n[OK] 适配完成，输出目录：", OUT)


if __name__ == "__main__":
    main()
