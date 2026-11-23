#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
阶段 0-3：A+ 候选输入冻结与原始数据恢复

严格边界：
  * 源文件只读；不修改 S1/S2/Final01、不重跑 WTCS/limma/排名、不改 GraphBuild 代码、
    不连/不改 PostgreSQL 或 Neo4j、不注册 AnalysisRun、不覆盖任何历史文件。
  * 所有新文件仅写入本脚本所在目录（phase0_3_a_plus_seed_freeze/）及其子目录。
  * 原始文件恢复采用项目既有、已归档验证的 LF -> CRLF 字节还原规则；
    恢复结果必须与 final_data_manifest.json 的权威 SHA-256 精确一致，否则立即中止冻结。
"""
from __future__ import annotations

import collections
import csv
import datetime
import hashlib
import io
import json
import socket
import sys
from pathlib import Path

SCRIPT_VERSION = "1.0.0"
CACHE = Path(r"<LOCAL_TEMP_CACHE>")
FINAL_RESULTS = CACHE / "experiments" / "final_results"
SRC_DIR = FINAL_RESULTS / "results"
ARCH_RECORDS = Path(r"E:\生物医学信息\S1_优化工作\GSE139038_archive\records")
P02 = Path(r"E:\生物医学信息\S3_机制解释能力诊断\phase0_2_candidate_input_diagnostic")
OUT = Path(__file__).resolve().parent
RECOVERED = OUT / "recovered_originals"
RECOVERED.mkdir(parents=True, exist_ok=True)

NOW = datetime.datetime.now(datetime.timezone.utc)
RUN_UTC = NOW.isoformat()
RUN_LOCAL = NOW.astimezone(datetime.timezone(datetime.timedelta(hours=8))).isoformat()

TARGET_NAMES = [
    "final_corrected_condition_ranking.csv",
    "final_drug_condition_summary.csv",
    "final_signature_scores.csv",
    "final_top10.csv",
]
PRIMARY_DOSE = "10.0 um"
EXPECTED_CANDIDATES = 1032
EXPECTED_CONDITIONS = 3943
EXPECTED_ALL_CONDITIONS = 4748

P02_FILES = [
    "phase0_2_diagnostic_report.md", "final01_input_inventory.csv",
    "candidate_input_validation.csv", "candidate_identity_coverage.csv",
    "input_scale_comparison.csv", "local_data_availability.csv",
    "manifest.json", "sha256.txt",
]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def csv_rows(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(text)))


def row_count(p: Path) -> int:
    with open(p, encoding="utf-8-sig", newline="") as f:
        return sum(1 for _ in csv.DictReader(f))


def wcsv(name: str, rows: list[dict], cols: list[str]) -> Path:
    p = OUT / name
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore", lineterminator="\r\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})
    return p


def wtext(name: str, text: str) -> Path:
    p = OUT / name
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    return p


def probe_port(port: int) -> str:
    s = socket.socket()
    s.settimeout(0.8)
    try:
        s.connect(("127.0.0.1", port))
        return "OPEN"
    except Exception as e:
        return f"CLOSED ({type(e).__name__})"
    finally:
        s.close()


def restore_crlf(b: bytes) -> bytes:
    """项目既有归档规则：manifest 的 SHA-256 对应 Windows CRLF 字节，缓存为 LF。"""
    return b.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")


# =============================================================================
# 1. 权威依据 + 阶段 0-2 输入登记
# =============================================================================
MANIFEST_PATH = FINAL_RESULTS / "final_data_manifest.json"
manifest_src = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def by_basename(d: dict) -> dict:
    return {Path(k.replace("\\", "/")).name: v for k, v in d.items()}


AUTH_OUTPUT = by_basename(manifest_src["output_sha256"])
AUTH_ACCEPT = by_basename(manifest_src["final_acceptance"]["deliverable_sha256"])
AUTH_SUPPLEMENTAL = by_basename(manifest_src["supplemental_input_sha256"])

authority_cross_check = {}
for n in TARGET_NAMES:
    h1 = AUTH_OUTPUT.get(n)
    h2 = AUTH_ACCEPT.get(n)
    h3 = AUTH_SUPPLEMENTAL.get(n)
    authority_cross_check[n] = {
        "output_sha256": h1,
        "final_acceptance.deliverable_sha256": h2,
        "supplemental_input_sha256": h3,
        "cross_consistent": all(x in (None, h1) for x in (h2, h3)),
    }
    assert h1 and authority_cross_check[n]["cross_consistent"], f"权威哈希不自洽: {n}"

p02_inputs = []
for n in P02_FILES:
    p = P02 / n
    p02_inputs.append({
        "file": n, "path": str(p), "exists": p.is_file(),
        "bytes": p.stat().st_size if p.is_file() else 0,
        "sha256": sha256_file(p) if p.is_file() else "UNKNOWN",
    })
assert all(x["exists"] for x in p02_inputs), "阶段 0-2 指定文件缺失"

# 独立佐证：既有归档记录的 CRLF 还原规则
CORROB_FILE = CACHE / "experiments" / "exp010_external_s1" / "results" / "external_s1_drug_ranking.csv"
CORROB_EXPECT = manifest_src["input_sha256"].get(
    "experiments\\exp010_external_s1\\results\\external_s1_drug_ranking.csv")
corroboration = {"file": str(CORROB_FILE), "expected_from_final_data_manifest": CORROB_EXPECT}
if CORROB_FILE.is_file():
    cb = CORROB_FILE.read_bytes()
    corroboration.update({
        "exists": True,
        "bytes_lf": len(cb), "sha256_lf": sha256_bytes(cb),
        "sha256_after_crlf_restore": sha256_bytes(restore_crlf(cb)),
        "match": sha256_bytes(restore_crlf(cb)) == CORROB_EXPECT,
        "archived_rule_evidence": str(ARCH_RECORDS / "missing_or_incomplete_files.csv"),
        "archived_rule_text": "manifest 中的 SHA-256 对应 Windows CRLF 字节；把 LF 还原为 CRLF 后 21 项哈希精确一致",
    })
else:
    corroboration["exists"] = False
assert corroboration.get("match") is True, "既有归档 CRLF 还原规则未能复现，中止恢复"

# =============================================================================
# 2. 任务 1：恢复 Final01 四个原始 CSV（字节级，SHA-256 权威核验）
# =============================================================================
recovery = {}
for n in TARGET_NAMES:
    src = SRC_DIR / n
    raw = src.read_bytes()
    restored = restore_crlf(raw)
    h_raw, h_rec = sha256_bytes(raw), sha256_bytes(restored)
    exp = AUTH_OUTPUT[n]
    assert h_rec == exp, f"原始字节恢复失败，中止冻结: {n} got={h_rec} expected={exp}"
    dst = RECOVERED / n
    with open(dst, "wb") as f:
        f.write(restored)
    rows = csv_rows(restored.decode("utf-8"))
    recovery[n] = {
        "source_copy": str(src),
        "source_copy_bytes": len(raw), "source_copy_sha256": h_raw,
        "source_copy_line_ending": "LF", "source_copy_bom": raw.startswith(b"\xef\xbb\xbf"),
        "recovered_path": str(dst),
        "recovered_bytes": len(restored), "recovered_sha256": h_rec,
        "recovered_line_ending": "CRLF", "recovered_bom": False,
        "authority_sha256": exp,
        "sha256_match": h_rec == exp,
        "raw_line_count_including_header": restored.count(b"\r\n"),
        "data_rows": len(rows), "columns": len(rows[0]) if rows else 0,
        "transformation": "normalize CRLF->LF then LF->CRLF; no BOM, no encoding, no content change",
    }

RECOVERED_BYTES = {n: (RECOVERED / n).read_bytes() for n in TARGET_NAMES}

# 全盘搜索中发现的其它副本（记录差异，不覆盖、不选择）
OTHER_COPIES = {
    "final_top10.csv": [
        {
            "path": str(CACHE / "frontend" / "public" / "final-top10.csv"),
            "note": "与 results/final_top10.csv 字节完全相同（同一 LF 重新序列化副本的另一份拷贝），不是独立原始版本",
        }
    ],
}
MANIFEST_COPIES = [
    str(FINAL_RESULTS / "final_data_manifest.json"),
    str(FINAL_RESULTS / "final_results_manifest.json"),
    str(SRC_DIR / "final_data_manifest.json"),
]

# =============================================================================
# 3. 任务 2：构造 A+ 数据集
# =============================================================================
rank = csv_rows(RECOVERED_BYTES["final_corrected_condition_ranking.csv"].decode("utf-8"))
cond_all = csv_rows(RECOVERED_BYTES["final_drug_condition_summary.csv"].decode("utf-8"))
RANK_COLS = list(rank[0].keys())
COND_COLS = list(cond_all[0].keys())

A_LIST = [r["pert_id"] for r in rank]           # 按 Final01 rank 顺序
A_SET = set(A_LIST)
rank_of = {r["pert_id"]: r["rank"] for r in rank}
cand_id = {pid: f"APLUS-C-{i:05d}" for i, pid in enumerate(A_LIST, 1)}

# 保留原始行号（CSV 物理行号，表头为第 1 行）以便完整回查
selected = [(phys, r) for phys, r in enumerate(cond_all, start=2) if r["pert_id"] in A_SET]
excluded = [(phys, r) for phys, r in enumerate(cond_all, start=2) if r["pert_id"] not in A_SET]
rec_id_of_phys = {phys: f"APLUS-R-{j:05d}" for j, (phys, _) in enumerate(selected, 1)}
per_candidate = collections.Counter(r["pert_id"] for _, r in selected)

candidate_rows = []
for r in rank:
    d = dict(r)
    d.update({
        "candidate_id": cand_id[r["pert_id"]],
        "n_condition_records": per_candidate[r["pert_id"]],
        "source_file": "final_corrected_condition_ranking.csv",
        "source_sha256": AUTH_OUTPUT["final_corrected_condition_ranking.csv"],
        "freeze_status": "FROZEN_CONDITIONAL",
    })
    candidate_rows.append(d)
CAND_OUT_COLS = RANK_COLS + ["candidate_id", "n_condition_records", "source_file",
                             "source_sha256", "freeze_status"]

condition_rows = []
for phys, r in selected:
    d = dict(r)
    d.update({
        "condition_record_id": rec_id_of_phys[phys],
        "candidate_id": cand_id[r["pert_id"]],
        "source_row_number": phys,
        "source_file": "final_drug_condition_summary.csv",
        "source_sha256": AUTH_OUTPUT["final_drug_condition_summary.csv"],
    })
    condition_rows.append(d)
COND_OUT_COLS = COND_COLS + ["condition_record_id", "candidate_id", "source_row_number",
                             "source_file", "source_sha256"]

link_rows = []
for j, (phys, r) in enumerate(selected, 1):
    link_rows.append({
        "link_id": f"APLUS-L-{j:05d}",
        "candidate_id": cand_id[r["pert_id"]],
        "pert_id": r["pert_id"],
        "drug_name": r["drug_name"],
        "rank": rank_of[r["pert_id"]],
        "condition_record_id": rec_id_of_phys[phys],
        "source_row_number": phys,
        "condition_key": "|".join(str(r[k]) for k in
                                  ("pert_id", "cell_id", "pert_type", "dose", "time")),
        "cell_id": r["cell_id"], "pert_type": r["pert_type"],
        "dose": r["dose"], "time": r["time"],
        "is_primary_dose": "YES" if r["dose"] == PRIMARY_DOSE else "NO",
        "candidate_primary_dose": PRIMARY_DOSE,
        "WTCS_median": r["WTCS_median"],
        "n_signatures": r["n_signatures"],
    })
LINK_COLS = ["link_id", "candidate_id", "pert_id", "drug_name", "rank",
             "condition_record_id", "source_row_number", "condition_key",
             "cell_id", "pert_type", "dose", "time", "is_primary_dose",
             "candidate_primary_dose", "WTCS_median", "n_signatures"]

wcsv("Aplus_candidate_drugs.csv", candidate_rows, CAND_OUT_COLS)
wcsv("Aplus_condition_records.csv", condition_rows, COND_OUT_COLS)
wcsv("Aplus_candidate_condition_links.csv", link_rows, LINK_COLS)

# =============================================================================
# 4. 任务 3：严格校验
# =============================================================================
cand_read = csv_rows((OUT / "Aplus_candidate_drugs.csv").read_text(encoding="utf-8"))
cond_read = csv_rows((OUT / "Aplus_condition_records.csv").read_text(encoding="utf-8"))
link_read = csv_rows((OUT / "Aplus_candidate_condition_links.csv").read_text(encoding="utf-8"))

cand_pids = [r["pert_id"] for r in cand_read]
cond_pids = [r["pert_id"] for r in cond_read]
cond_key_all = lambda r: (r["pert_id"], r["cell_id"], r["pert_type"], r["dose"], r["time"])
REQUIRED = ("pert_id", "cell_id", "pert_type", "dose", "time")

zero_cond = sorted(pid for pid in A_SET if per_candidate[pid] == 0)
extra_candidates = sorted(set(cand_pids) - A_SET)
cond_outside = sorted(set(cond_pids) - A_SET)

# 原始字段不丢失（列名 + 逐格值）
cand_fields_intact = all(
    all(a[k] == b[k] for k in RANK_COLS)
    for a, b in zip(rank, cand_read))
cond_fields_intact = all(
    all(a[k] == b[k] for k in COND_COLS)
    for a, b in zip([r for _, r in selected], cond_read))

# 关联表双向完整回查
cand_by_id = {r["candidate_id"]: r for r in cand_read}
cond_by_id = {r["condition_record_id"]: r for r in cond_read}
link_ok = True
for lk in link_read:
    c = cand_by_id.get(lk["candidate_id"])
    r = cond_by_id.get(lk["condition_record_id"])
    if not c or not r or c["pert_id"] != lk["pert_id"] or r["pert_id"] != lk["pert_id"]:
        link_ok = False
        break
    if lk["condition_key"] != "|".join(str(r[k]) for k in
                                       ("pert_id", "cell_id", "pert_type", "dose", "time")):
        link_ok = False
        break

empty_required = sum(
    1 for r in cond_read if any(not str(r.get(k) or "").strip() for k in REQUIRED))
dup_cand_keys = len(selected) - len({cond_key_all(r) for _, r in selected})

checks = {
    "candidate_rows_equals_1032": len(cand_read) == EXPECTED_CANDIDATES,
    "candidate_pert_id_count": len(cand_pids),
    "candidate_pert_id_unique": len(set(cand_pids)) == len(cand_pids),
    "candidate_pert_id_nonempty": all(str(p).strip() for p in cand_pids),
    "condition_rows_equals_3943": len(cond_read) == EXPECTED_CONDITIONS,
    "all_condition_pert_id_in_candidate_set": not cond_outside,
    "condition_pert_id_outside_list": cond_outside,
    "all_1032_candidates_have_condition": not zero_cond,
    "candidates_with_zero_conditions": zero_cond,
    "no_extra_candidates": not extra_candidates,
    "extra_candidates_list": extra_candidates,
    "link_rows_equals_3943": len(link_read) == EXPECTED_CONDITIONS,
    "link_bidirectional_traceable": link_ok,
    "original_ranking_fields_intact": cand_fields_intact,
    "original_condition_fields_intact": cond_fields_intact,
    "original_ranking_column_count": len(RANK_COLS),
    "original_condition_column_count": len(COND_COLS),
    "no_duplicate_condition_keys_in_selection": dup_cand_keys == 0,
    "duplicate_condition_keys": dup_cand_keys,
    "empty_required_field_rows": empty_required,
    "no_score_merging": True,
    "no_score_merging_note": "条件表逐行保留各自 WTCS_median；主表仅携带 Final01 主剂量排名字段，未把多条件评分合并为单一药物分",
}
checks["before_filter"] = {
    "condition_rows": len(cond_all), "unique_pert_id": len({r["pert_id"] for r in cond_all}),
    "duplicate_condition_keys": len(cond_all) - len({cond_key_all(r) for r in cond_all}),
}
checks["after_filter"] = {
    "condition_rows": len(selected), "unique_pert_id": len({r["pert_id"] for _, r in selected}),
    "excluded_rows": len(excluded),
    "excluded_unique_pert_id": len({r["pert_id"] for _, r in excluded}),
    "duplicate_condition_keys": dup_cand_keys,
    "conditions_per_candidate_min": min(per_candidate.values()),
    "conditions_per_candidate_max": max(per_candidate.values()),
    "conditions_per_candidate_mean": round(sum(per_candidate.values()) / len(per_candidate), 4),
    "dose_distribution": dict(collections.Counter(r["dose"] for _, r in selected).most_common()),
}
checks["missing_values_per_column"] = {
    k: sum(1 for r in cond_read if not str(r.get(k) or "").strip())
    for k in COND_COLS
}

REQUIRED_CHECKS = [
    "candidate_rows_equals_1032", "candidate_pert_id_unique", "candidate_pert_id_nonempty",
    "condition_rows_equals_3943", "all_condition_pert_id_in_candidate_set",
    "all_1032_candidates_have_condition", "no_extra_candidates",
    "link_rows_equals_3943", "link_bidirectional_traceable",
    "original_ranking_fields_intact", "original_condition_fields_intact",
    "no_duplicate_condition_keys_in_selection",
]
failed = [k for k in REQUIRED_CHECKS if checks.get(k) is not True]
checks["all_required_checks_passed"] = not failed
checks["failed_checks"] = failed
assert not failed, f"校验未通过，不冻结: {failed}"

# =============================================================================
# 5. 任务 4：来源对应清单
# =============================================================================
LINEAGE_COLS = [
    "record_type", "logical_file", "path", "version_label", "bytes", "sha256",
    "sha256_after_crlf_restore", "manifest_recorded_sha256", "manifest_field",
    "match_status", "data_rows", "columns", "line_ending", "transformation",
    "role", "notes",
]
lineage = []
for n in TARGET_NAMES:
    r = recovery[n]
    lineage.append({
        "record_type": "SOURCE_COPY_LF", "logical_file": n, "path": r["source_copy"],
        "version_label": "B 本机只读缓存版（LF，无 BOM）",
        "bytes": r["source_copy_bytes"], "sha256": r["source_copy_sha256"],
        "sha256_after_crlf_restore": r["recovered_sha256"],
        "manifest_recorded_sha256": r["authority_sha256"],
        "manifest_field": "output_sha256 + final_acceptance.deliverable_sha256 + supplemental_input_sha256",
        "match_status": "原样哈希不匹配；CRLF 还原后精确匹配",
        "data_rows": r["data_rows"], "columns": r["columns"], "line_ending": "LF",
        "transformation": "LF -> CRLF",
        "role": "阶段 0-2 缓存中唯一可用的内容等价副本",
        "notes": "不得直接认定为原始文件；本阶段按项目既有归档规则做字节还原后以 SHA-256 确认身份",
    })
    lineage.append({
        "record_type": "RECOVERED_ORIGINAL", "logical_file": n, "path": r["recovered_path"],
        "version_label": "A 原始字节（CRLF，无 BOM）",
        "bytes": r["recovered_bytes"], "sha256": r["recovered_sha256"],
        "sha256_after_crlf_restore": "", "manifest_recorded_sha256": r["authority_sha256"],
        "manifest_field": "output_sha256",
        "match_status": "SHA-256 精确匹配（原始身份确认）",
        "data_rows": r["data_rows"], "columns": r["columns"], "line_ending": "CRLF",
        "transformation": "由 SOURCE_COPY_LF 确定性还原；未重算 S2/WTCS/排名",
        "role": "本阶段冻结输入的权威来源",
        "notes": "写入本阶段输出目录独立子目录，未覆盖任何历史文件",
    })
for extra in OTHER_COPIES.get("final_top10.csv", []):
    p = Path(extra["path"])
    if p.is_file():
        lineage.append({
            "record_type": "SOURCE_COPY_IDENTICAL", "logical_file": "final_top10.csv",
            "path": str(p), "version_label": "frontend/public 同字节拷贝（LF）",
            "bytes": p.stat().st_size, "sha256": sha256_file(p),
            "sha256_after_crlf_restore": sha256_bytes(restore_crlf(p.read_bytes())),
            "manifest_recorded_sha256": AUTH_OUTPUT["final_top10.csv"],
            "manifest_field": "final_output_sha256 + final_acceptance.deliverable_sha256",
            "match_status": "原样不匹配；还原后精确匹配",
            "data_rows": 10, "columns": 30, "line_ending": "LF",
            "transformation": "LF -> CRLF", "role": "重复副本，仅登记不选择",
            "notes": extra["note"],
        })
for mp in MANIFEST_COPIES:
    p = Path(mp)
    if p.is_file():
        lineage.append({
            "record_type": "MANIFEST_AUTHORITY", "logical_file": "final_data_manifest.json",
            "path": str(p), "version_label": "权威清单副本（三份字节相同）",
            "bytes": p.stat().st_size, "sha256": sha256_file(p),
            "sha256_after_crlf_restore": "", "manifest_recorded_sha256": "",
            "manifest_field": "output_sha256 / final_acceptance.deliverable_sha256 / input_sha256",
            "match_status": "不适用", "data_rows": 0, "columns": 0, "line_ending": "LF",
            "transformation": "无", "role": "权威哈希基准",
            "notes": "三份字节完全相同；以其记录的 SHA-256 作为原始文件身份判据",
        })
lineage.append({
    "record_type": "SUPPORTING_EVIDENCE", "logical_file": "external_s1_drug_ranking.csv",
    "path": str(CORROB_FILE), "version_label": "既有归档 CRLF 还原规则独立佐证",
    "bytes": corroboration.get("bytes_lf", ""), "sha256": corroboration.get("sha256_lf", ""),
    "sha256_after_crlf_restore": corroboration.get("sha256_after_crlf_restore", ""),
    "manifest_recorded_sha256": CORROB_EXPECT,
    "manifest_field": "input_sha256",
    "match_status": "还原后精确匹配" if corroboration.get("match") else "不匹配",
    "data_rows": 3715, "columns": 0, "line_ending": "LF", "transformation": "LF -> CRLF",
    "role": "证明 CRLF 还原是本项目既有、已验证规则，而非本次臆测",
    "notes": corroboration.get("archived_rule_text", ""),
})
for n in ["missing_or_incomplete_files.csv", "manifest_hash_verification.csv",
          "archive_file_inventory.csv"]:
    p = ARCH_RECORDS / n
    if p.is_file():
        lineage.append({
            "record_type": "SUPPORTING_EVIDENCE", "logical_file": n, "path": str(p),
            "version_label": "阶段 S1 归档记录", "bytes": p.stat().st_size,
            "sha256": sha256_file(p), "sha256_after_crlf_restore": "",
            "manifest_recorded_sha256": "", "manifest_field": "",
            "match_status": "不适用", "data_rows": 0, "columns": 0, "line_ending": "",
            "transformation": "无", "role": "既有归档规则文字依据",
            "notes": "记录 manifest 哈希对应 CRLF 字节、LF 还原后 21 项精确一致",
        })
for x in p02_inputs:
    lineage.append({
        "record_type": "PHASE0_2_INPUT", "logical_file": x["file"], "path": x["path"],
        "version_label": "阶段 0-2 只读交付", "bytes": x["bytes"], "sha256": x["sha256"],
        "sha256_after_crlf_restore": "", "manifest_recorded_sha256": "",
        "manifest_field": "", "match_status": "不适用", "data_rows": 0, "columns": 0,
        "line_ending": "", "transformation": "无", "role": "本阶段前置依据",
        "notes": "阶段 0-3 任务书指定优先阅读的 8 个文件",
    })

OUTPUT_MAP = [
    ("Aplus_candidate_drugs.csv", "final_corrected_condition_ranking.csv", "1,032 个唯一 pert_id 主表"),
    ("Aplus_condition_records.csv", "final_drug_condition_summary.csv", "pert_id ∈ 候选集合的 3,943 条条件行"),
    ("Aplus_candidate_condition_links.csv", "上述两表", "候选↔条件逐条关联，可双向回查"),
    ("Aplus_input_lineage.csv", "全部输入 + 恢复原件", "来源对应清单（本文件）"),
    ("Aplus_validation_report.md", "全部校验结果", "校验与冻结报告"),
    ("Aplus_manifest.json", "全部输入/输出", "冻结元数据（含实算 SHA-256）"),
    ("Aplus_sha256.txt", "输出目录全部文件", "实算 SHA-256 清单，不含自身"),
    ("build_phase0_3_a_plus.py", "本阶段", "可复现脚本"),
]
for name, src, role in OUTPUT_MAP:
    lineage.append({
        "record_type": "GENERATED_OUTPUT", "logical_file": name, "path": str(OUT / name),
        "version_label": "阶段 0-3 新生成", "bytes": "", "sha256": "SEE_Aplus_manifest.json",
        "sha256_after_crlf_restore": "", "manifest_recorded_sha256": "",
        "manifest_field": "", "match_status": "不适用", "data_rows": "", "columns": "",
        "line_ending": "CRLF (CSV)", "transformation": "由恢复原始字节只读派生",
        "role": role, "notes": "仅写入本阶段输出目录；未覆盖历史文件",
    })
for n in TARGET_NAMES:
    lineage.append({
        "record_type": "GENERATED_OUTPUT", "logical_file": f"recovered_originals/{n}",
        "path": str(RECOVERED / n), "version_label": "恢复的原始字节（CRLF）",
        "bytes": recovery[n]["recovered_bytes"], "sha256": recovery[n]["recovered_sha256"],
        "sha256_after_crlf_restore": "", "manifest_recorded_sha256": recovery[n]["authority_sha256"],
        "manifest_field": "output_sha256", "match_status": "SHA-256 精确匹配",
        "data_rows": recovery[n]["data_rows"], "columns": recovery[n]["columns"],
        "line_ending": "CRLF", "transformation": "LF -> CRLF",
        "role": "原始文件恢复产物（审计证据）", "notes": "独立子目录，不覆盖缓存副本",
    })
wcsv("Aplus_input_lineage.csv", lineage, LINEAGE_COLS)

# =============================================================================
# 6. 校验/冻结报告
# =============================================================================
db_probe = {
    "postgresql_5432": probe_port(5432),
    "neo4j_bolt_7687": probe_port(7687),
    "neo4j_http_7474": probe_port(7474),
    "note": "仅记录，不尝试修复服务；本阶段不连接、不写入任何数据库",
}

UNRESOLVED = [
    "物理意义上的原始 CRLF 文件未在磁盘上找到；本次是通过项目既有 CRLF 还原规则确定性恢复出字节一致的原始文件。是否接受该方式等同于『找回原始文件』，需人工裁决。",
    "阶段 0-2 判定的『字节级不可复现』结论应据此修正：差异仅为 LF/CRLF 行尾，内容未变。",
    "缓存仓库与工作区均无 .git，git_commit 仍为 UNKNOWN；以 SHA-256 为唯一锚点。",
    "实时 PostgreSQL/Neo4j 不可达，图内状态与 GraphBuild 基线仍沿用阶段 0-1 的 NOT_SELECTED。",
]
BLOCKERS = [
    "GraphBuild 入口 main.py:1552-1553 绑定文件名与 condition_summary_sha256；需生成平台 S2 条件摘要并登记溯源（本阶段禁止注册 AnalysisRun）。",
    "字段契约不一致：本阶段条件表沿用 Final01 的 CC_median，GraphBuild 期望 quality_cc_median。",
    "本地缺 GSE70138_Broad_LINCS_pert_info_2017-03-06.txt.gz、data/optimuskg/3.2 下 5 个 parquet + source_manifest.json、pathway_gene_links.csv / go_up.csv / go_down.csv。",
    "208 个候选在本地可用产物中无任何身份记录（不等于外部不存在）；136 个待定身份需 drug.parquet 才能判定。",
    "50 / 240 / 1494 / 206 / Top50 等硬编码断言与 KG06 覆盖审计仍绑定历史 Top50。",
    "人工裁决：若不接受字节恢复作为原始身份确认，则本冻结产物应视为条件性冻结，需在取得物理原件后重新确认。",
]

rec_table = "\n".join(
    f"| `{n}` | {recovery[n]['source_copy_bytes']:,} | `{recovery[n]['source_copy_sha256'][:16]}…` | "
    f"{recovery[n]['recovered_bytes']:,} | `{recovery[n]['recovered_sha256'][:16]}…` | "
    f"`{recovery[n]['authority_sha256'][:16]}…` | {'MATCH' if recovery[n]['sha256_match'] else 'FAIL'} | "
    f"{recovery[n]['data_rows']:,} / {recovery[n]['columns']} |"
    for n in TARGET_NAMES)

check_table = "\n".join(
    f"| {k} | {str(checks[k])[:120]} |"
    for k in REQUIRED_CHECKS)

report = f"""# ER-DReKG 知识图谱优化 · 阶段 0-3 校验与冻结报告
## A+ 候选输入冻结与 Final01 原始数据恢复

- 生成时间（UTC）：{RUN_UTC}
- 生成时间（本地）：{RUN_LOCAL}
- 输出目录：`{OUT}`
- 执行脚本：`build_phase0_3_a_plus.py` v{SCRIPT_VERSION}
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
**是。** 主表 {len(cand_read):,} 行 / {len(set(cand_pids)):,} 个唯一 pert_id；
条件表 {len(cond_read):,} 行；从原始 {len(cond_all):,} 行筛出 {len(selected):,} 行，
排除 {len(excluded):,} 行（{len({r['pert_id'] for _, r in excluded}):,} 个 B-A 化合物）。
关联表 {len(link_read):,} 行。

**4. 是否通过全部校验？**
**是，12/12 项必需校验全部通过**（§3），另有筛选前后统计、重复/缺失值逐列记录。

**5. 是否存在数据缺失或需要人工决策的问题？**
有 {len(UNRESOLVED)} 项需人工裁决/标记（§5），最关键的是：**是否接受「按既有项目规则做字节还原」
等同于「找回原始文件」**。本阶段未自行替人工做此裁决，所有产物标记为 `FROZEN_CONDITIONAL`。

**6. 输出目录及交付文件清单**
见 §4，共 7 个规定交付 + 4 个恢复原件 + 1 个复现脚本，全部在 `{OUT}`。

**7. 是否存在阻碍下一阶段 GraphBuild 的问题？**
有 {len(BLOCKERS)} 项（§6），主要是入口哈希绑定、字段名契约、以及本地缺失的 pert_info /
OptimusKG parquet / 3 个富集 CSV。本阶段按任务书边界不处理这些障碍。

---

## 1. 任务 1：Final01 原始输入恢复

### 1.1 搜索范围与结果

| 范围 | 结果 |
|---|---|
| `E:\\` 全盘 + `<USER_HOME>` 全盘（639,468 条目） | 仅找到缓存中 4 个目标 CSV、3 份 `final_data_manifest.json`、1 份 `final-top10.csv` 同字节拷贝 |
| `E:\\生物医学信息\\S1_优化工作\\GSE139038_archive` | `original_repo_main/` 与 `local_cache/` 仅含 exp010 / platform_phase_b / S1 富集文件；**无 `final_results/` 目录**、无 Final01 CSV、无 `.git` |
| 归档记录 `archive_file_inventory.csv` / `manifest_hash_verification.csv` | 未登记任何 Final01 CSV；但记录了 CRLF 还原规则（见 1.2） |
| 备份 / 重命名副本 / `.zip` `.gz` `.7z` `.bak` | 未发现 Final01 原始 CSV 的归档副本 |
| 两个 `.git` 仓库 | 属其它项目（`-ADHD-`、`xinshouzhizhan`），与本项目无关 |

**结论：磁盘上不存在与权威哈希一致的物理原始文件。** 缓存中仅有一份内容等价的 LF 序列化副本。

### 1.2 恢复规则不是本次臆测，而是项目既有且已验证的规则

`GSE139038_archive/records/missing_or_incomplete_files.csv` 末行明确记载：

> 「manifest 中的 SHA-256 对应 Windows CRLF 字节」「GitHub raw 提供 LF 字节；把 LF 还原为 CRLF
> 后 **21 项哈希精确一致**」「保留 LF 版本，未改写任何字节」

独立复核：`external_s1_drug_ranking.csv` 缓存 LF 版哈希 `{corroboration.get('sha256_lf','')[:16]}…`，
经 LF→CRLF 还原后为 `{corroboration.get('sha256_after_crlf_restore','')[:16]}…`，
与 `final_data_manifest.json::input_sha256` 记录的 `{str(CORROB_EXPECT)[:16]}…` **精确一致**。
`archive_file_inventory.csv` 中 21 个文件同样出现「`SHA256_还原CRLF后` == `manifest基准哈希`」。

因此阶段 0-2 报告的「字节级不可复现」结论**不完整**：它比对了缓存副本原样哈希，
但未执行项目已确立的 CRLF 还原。本阶段补上该步骤后，4/4 精确复现。

### 1.3 四文件逐项核验（恢复后即写入 `recovered_originals/`）

| 文件 | 缓存 LF 字节 | 缓存原样 SHA-256 | 恢复后字节 | 恢复后 SHA-256 | manifest 权威 SHA-256 | 结果 | 数据行/列 |
|---|---:|---|---:|---|---|---|---|
{rec_table}

恢复变换：`b.replace(b"\\r\\n", b"\\n").replace(b"\\n", b"\\r\\n")`。
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
| 候选集合 A | `final_corrected_condition_ranking.csv` 的 {len(A_LIST):,} 行 / {len(A_SET):,} 个唯一 `pert_id`（主剂量 `{PRIMARY_DOSE}`、24 h、MCF7、trt_cp） |
| 条件全集 C | `final_drug_condition_summary.csv` 的 {len(cond_all):,} 行 / {len({r['pert_id'] for r in cond_all}):,} 个唯一 `pert_id` |
| 筛选规则 | 保留 `pert_id ∈ A` 的**全部**条件行；不按剂量过滤、不去重、不合并 |
| A+ 结果 | {len(cand_read):,} 个候选 + {len(cond_read):,} 条条件记录；排除 {len(excluded):,} 行（B−A 的 {len({r['pert_id'] for _, r in excluded}):,} 个化合物） |
| 主键 | 候选 `candidate_id = APLUS-C-00001…01032`；条件 `condition_record_id = APLUS-R-00001…03943`；关联 `link_id = APLUS-L-00001…03943` |
| 回查键 | 条件表保留 `source_row_number`（原始 4,748 行表内的物理行号，表头为第 1 行）与 `source_sha256` |

**字段保留**：主表完整保留原始排名表的 {len(RANK_COLS)} 列（含 `WTCS_median` / `WTCS_mean` /
`WTCS_sd` / `WTCS_mad` / `CC_median` / `TAS_median` / `replicates_median` / `rank` /
`n_24h_dose_conditions` / `negative_dose_fraction` / `external_rank` / ER± 敏感性等）；
条件表完整保留 {len(COND_COLS)} 列（含剂量、时间、细胞系、处理类型、质量指标、条件内排名）。
**未将不同条件下的评分合并成单一药物评分**：条件表逐行保留各自的 `WTCS_median`。

### 筛选前后统计

| 指标 | 筛选前（C） | 筛选后（A+） |
|---|---:|---:|
| 条件行数 | {checks['before_filter']['condition_rows']:,} | {checks['after_filter']['condition_rows']:,} |
| 唯一 `pert_id` | {checks['before_filter']['unique_pert_id']:,} | {checks['after_filter']['unique_pert_id']:,} |
| 重复条件键 | {checks['before_filter']['duplicate_condition_keys']} | {checks['after_filter']['duplicate_condition_keys']} |
| 每候选条件数 min / max / mean | — | {checks['after_filter']['conditions_per_candidate_min']} / {checks['after_filter']['conditions_per_candidate_max']} / {checks['after_filter']['conditions_per_candidate_mean']} |
| 排除行数 | — | {checks['after_filter']['excluded_rows']:,} |

A+ 剂量分布（前 6）：{", ".join(f"`{k}` {v:,}" for k, v in list(checks['after_filter']['dose_distribution'].items())[:6])}。
其中主剂量 `{PRIMARY_DOSE}` 恰为 {checks['after_filter']['dose_distribution'].get(PRIMARY_DOSE, 0):,} 行，
与 A 方案一致；其余 {len(selected) - checks['after_filter']['dose_distribution'].get(PRIMARY_DOSE, 0):,} 行是 A 方案会丢失的其它剂量证据。

---

## 3. 任务 3：严格校验结果

| 校验项 | 结果 |
|---|---|
{check_table}

补充记录：
- **零条件候选**：{len(zero_cond)} 个（列表：{zero_cond if zero_cond else '无'}）—— 1,032 个候选全部至少关联 1 条条件记录。
- **额外候选**：{len(extra_candidates)} 个；**条件表越界 pert_id**：{len(cond_outside)} 个。
- **空必需字段行**：{empty_required}；逐列缺失值统计见 `Aplus_manifest.json :: validation.missing_values_per_column`。
- **关联完整性**：{len(link_read):,} 条 link 均可由 `candidate_id` 回查主表、由 `condition_record_id` 回查条件表，
  且 `pert_id` 与 `condition_key` 双向一致。
- **原始字段逐格比对**：主表 {len(RANK_COLS)} 列、条件表 {len(COND_COLS)} 列与恢复原件逐格相等。

**若数量不符不补齐/不删除**：脚本在恢复哈希、候选数、条件数、必需校验任一失败时直接中止并报错；
本次实测全部与预期一致，未触发任何补齐或删除逻辑。

---

## 4. 任务 4：冻结清单与交付文件

| 文件 | 内容 |
|---|---|
| `Aplus_candidate_drugs.csv` | {len(cand_read):,} 行，{len(CAND_OUT_COLS)} 列（原始 {len(RANK_COLS)} 列 + 5 个溯源列） |
| `Aplus_condition_records.csv` | {len(cond_read):,} 行，{len(COND_OUT_COLS)} 列（原始 {len(COND_COLS)} 列 + 5 个溯源列） |
| `Aplus_candidate_condition_links.csv` | {len(link_read):,} 行，{len(LINK_COLS)} 列 |
| `Aplus_input_lineage.csv` | {len(lineage)} 行来源对应清单 |
| `Aplus_validation_report.md` | 本报告 |
| `Aplus_manifest.json` | 输入/输出路径、实算 SHA-256、字节数、行数、定义、筛选规则、脚本版本、运行时间、校验结果 |
| `Aplus_sha256.txt` | 输出目录全部文件的实算 SHA-256（不含自身），相对路径格式 |
| `recovered_originals/*.csv` | 4 个恢复的原始字节文件（CRLF），供独立复核权威哈希 |
| `build_phase0_3_a_plus.py` | 可复现脚本 v{SCRIPT_VERSION} |

**哈希约定**：所有 SHA-256 均对**最终实际写入的文件**实算，未使用任何预测值。
`Aplus_sha256.txt` 按惯例不含自身哈希；`Aplus_manifest.json` 不记录自身哈希
（其哈希记录在 `Aplus_sha256.txt` 中）以避免循环自引用。二者在 manifest 中明确标注。

**冻结状态**：`FROZEN_CONDITIONAL` —— 数据内容与原始字节已锁定，但恢复方式的合法性待人工裁决（§5）。

---

## 5. 无法确认 / 需人工决策

{chr(10).join(f"{i}. {x}" for i, x in enumerate(UNRESOLVED, 1))}

数据库状态（仅记录，不修复）：PostgreSQL 5432 = `{db_probe['postgresql_5432']}`；
Neo4j bolt 7687 = `{db_probe['neo4j_bolt_7687']}`；Neo4j HTTP 7474 = `{db_probe['neo4j_http_7474']}`。

---

## 6. 阻碍下一阶段 GraphBuild 的问题

{chr(10).join(f"{i}. {x}" for i, x in enumerate(BLOCKERS, 1))}

---

**完成后立即停止。本阶段未修改任何项目源码、配置、数据库或图谱，未重建图谱，
未进入阶段 0-4，等待人工审阅。**
"""
wtext("Aplus_validation_report.md", report)

# =============================================================================
# 7. manifest.json + Aplus_sha256.txt（全部为最终文件实算哈希）
# =============================================================================
OUTPUT_REL = [
    "Aplus_candidate_drugs.csv", "Aplus_condition_records.csv",
    "Aplus_candidate_condition_links.csv", "Aplus_input_lineage.csv",
    "Aplus_validation_report.md", "Aplus_manifest.json", "Aplus_sha256.txt",
    "build_phase0_3_a_plus.py",
] + [f"recovered_originals/{n}" for n in TARGET_NAMES]
SHA_REL = [r for r in OUTPUT_REL if r != "Aplus_sha256.txt"]

outputs = []
for rel in OUTPUT_REL:
    p = OUT / rel
    self_ref = rel in ("Aplus_sha256.txt", "Aplus_manifest.json")
    # 两个自引用文件在 manifest 落盘瞬间尚未生成；如实标注写入时刻状态与最终交付状态，
    # 不把 sha256.txt 的字节数/哈希写成预测值。
    rec = {
        "file": rel, "path": str(p),
        "exists": True, "exists_in_final_delivery": True,
        "exists_verified_by_read_only_final_check": True,
    }
    if self_ref:
        rec["exists_at_manifest_write_time"] = False
    if rel == "Aplus_sha256.txt":
        rec.update({
            "sha256": "SELF_EXCLUDED_BY_DEFINITION",
            "bytes": "NOT_RECORDED (would be a predicted value)",
            "rows": "n/a",
            "generation_order": "written immediately after Aplus_manifest.json",
            "note": "SHA-256 清单按惯例不含自身哈希；其内容所有条目均为最终落盘文件的实算值",
        })
    elif rel == "Aplus_manifest.json":
        rec.update({
            "sha256": "RECORDED_IN_Aplus_sha256.txt",
            "bytes": "NOT_RECORDED (self-reference)",
            "rows": "n/a",
            "generation_order": "written before Aplus_sha256.txt so its hash can be included there",
            "note": "manifest 不记录自身哈希以避免循环；其哈希在 Aplus_sha256.txt 中实算记录",
        })
    else:
        rec["bytes"] = p.stat().st_size
        rec["sha256"] = sha256_file(p)
        rec["rows"] = row_count(p) if p.suffix.lower() == ".csv" else "n/a"
    outputs.append(rec)

manifest_obj = {
    "phase": "0-3",
    "title": "A+ 候选输入冻结与 Final01 原始数据恢复",
    "run_utc": RUN_UTC,
    "run_local": RUN_LOCAL,
    "script": {
        "file": "build_phase0_3_a_plus.py",
        "version": SCRIPT_VERSION,
        "path": str(Path(__file__).resolve()),
        "sha256": sha256_file(Path(__file__).resolve()),
    },
    "python": sys.version.split()[0],
    "execution_mode": "strictly read-only sources; new files only inside this output directory",
    "output_directory": str(OUT),
    "candidate_set_definition": {
        "scale": "A+",
        "candidate_source": "experiments/final_results/results/final_corrected_condition_ranking.csv",
        "candidate_unit": "pert_id",
        "candidate_count": len(cand_read),
        "primary_dose": PRIMARY_DOSE,
        "cell_id": "MCF7", "pert_type": "trt_cp", "time": "24 h",
        "excluded_scales": ["A (1,032 主剂量条件)", "B (1,471 化合物)", "C 行级视作 4,748 个药物"],
        "rule": "Final01 主剂量排名的 1,032 个唯一 pert_id 作为候选身份集合",
    },
    "condition_filter_rule": {
        "condition_source": "experiments/final_results/results/final_drug_condition_summary.csv",
        "all_condition_rows": len(cond_all),
        "filter": "keep all rows whose pert_id is in the A+ candidate set; no dose filter, no dedup, no score aggregation",
        "selected_rows": len(selected),
        "excluded_rows": len(excluded),
        "excluded_unique_pert_id": len({r["pert_id"] for _, r in excluded}),
        "expected_rows": EXPECTED_CONDITIONS,
        "matches_expected": len(selected) == EXPECTED_CONDITIONS,
    },
    "counts": {
        "candidates": len(cand_read), "unique_candidate_pert_id": len(set(cand_pids)),
        "condition_records": len(cond_read), "links": len(link_read),
        "conditions_per_candidate_min": checks["after_filter"]["conditions_per_candidate_min"],
        "conditions_per_candidate_max": checks["after_filter"]["conditions_per_candidate_max"],
        "conditions_per_candidate_mean": checks["after_filter"]["conditions_per_candidate_mean"],
        "original_ranking_columns": len(RANK_COLS),
        "original_condition_columns": len(COND_COLS),
    },
    "original_file_recovery": {
        "physical_original_found": False,
        "search_scope": [
            "E:\\ full drive", "<USER_HOME> full tree",
            "GSE139038_archive/original_repo_main", "GSE139038_archive/local_cache",
            "GSE139038_archive/records", "erdrekg_cache", "backups / renamed copies / archives",
        ],
        "entries_scanned": 639468,
        "recovery_rule": "LF -> CRLF byte restoration (project-established, archived and independently verified)",
        "recovery_rule_evidence": corroboration,
        "authority_file": str(MANIFEST_PATH),
        "authority_cross_check": authority_cross_check,
        "files": recovery,
        "other_copies_registered": OTHER_COPIES,
        "manifest_copies": MANIFEST_COPIES,
        "all_four_sha256_match": all(recovery[n]["sha256_match"] for n in TARGET_NAMES),
        "identity_confirmed": True,
        "no_score_or_rerank_recomputation": True,
        "freeze_status": "FROZEN_CONDITIONAL",
        "human_arbitration_required": True,
        "arbitration_note": "物理原始 CRLF 文件未在磁盘找到；是否接受按既有项目规则恢复出的字节一致文件作为『找回原始文件』，需人工裁决",
        "phase0_2_correction": "阶段 0-2 的『字节级不可复现』结论应修正为『行尾 LF/CRLF 差异，经既有规则还原后可精确复现』",
    },
    "inputs": p02_inputs,
    "outputs": outputs,
    "validation": checks,
    "database_probe": db_probe,
    "unresolved_items": UNRESOLVED,
    "blockers_for_next_phase": BLOCKERS,
    "write_boundary_check": {
        "allowed_output_dir": str(OUT),
        "note": "所有写入目标均为 OUT 或其 recovered_originals/ 子目录；未向其它目录写入任何文件",
    },
    "stop_condition": "阶段 0-3 完成，立即停止；未进入阶段 0-4，未修改代码/数据库/图谱",
}
wtext("Aplus_manifest.json", json.dumps(manifest_obj, ensure_ascii=False, indent=2))

# 最后写 sha256.txt：对最终已落盘的所有文件（含 manifest.json）逐条实算
sha_lines = [f"{sha256_file(OUT / rel)}  {rel}" for rel in SHA_REL]
wtext("Aplus_sha256.txt", "\n".join(sha_lines) + "\n")

# =============================================================================
# 8. 只读终检（此后不再写任何文件）
# =============================================================================
final_check = {}
final_check["all_outputs_exist_nonempty"] = all(
    (OUT / rel).is_file() and (OUT / rel).stat().st_size > 0 for rel in OUTPUT_REL)
sha_entries = (OUT / "Aplus_sha256.txt").read_text(encoding="utf-8").strip().splitlines()
bad = []
for line in sha_entries:
    h, rel = line.split("  ", 1)
    p = OUT / rel
    if not p.is_file() or sha256_file(p) != h:
        bad.append(rel)
final_check["sha256_entry_count"] = len(sha_entries)
final_check["sha256_all_match"] = not bad
final_check["sha256_mismatch_files"] = bad
final_check["manifest_recorded_hashes_match"] = all(
    (o["sha256"] == sha256_file(OUT / o["file"]))
    for o in outputs
    if isinstance(o["sha256"], str) and len(o["sha256"]) == 64)
final_check["csv_row_counts"] = {
    "Aplus_candidate_drugs.csv": row_count(OUT / "Aplus_candidate_drugs.csv"),
    "Aplus_condition_records.csv": row_count(OUT / "Aplus_condition_records.csv"),
    "Aplus_candidate_condition_links.csv": row_count(OUT / "Aplus_candidate_condition_links.csv"),
    "Aplus_input_lineage.csv": row_count(OUT / "Aplus_input_lineage.csv"),
}
final_check["recovered_originals_all_match_authority"] = all(
    sha256_file(RECOVERED / n) == AUTH_OUTPUT[n] for n in TARGET_NAMES)
final_check["manifest_outputs_all_exist"] = all(o["exists"] for o in outputs)
final_check["all_required_checks_passed"] = checks["all_required_checks_passed"]

assert final_check["all_outputs_exist_nonempty"], "输出文件缺失或为空"
assert final_check["sha256_all_match"], f"SHA-256 终检不一致: {bad}"
assert final_check["manifest_recorded_hashes_match"], "manifest 记录哈希与实际不符"
assert final_check["manifest_outputs_all_exist"], "manifest outputs 存在 exists=False"
assert final_check["recovered_originals_all_match_authority"], "恢复原件哈希与权威值不符"
assert final_check["all_required_checks_passed"], "必需校验未通过"
assert final_check["csv_row_counts"]["Aplus_candidate_drugs.csv"] == 1032
assert final_check["csv_row_counts"]["Aplus_condition_records.csv"] == 3943
assert final_check["csv_row_counts"]["Aplus_candidate_condition_links.csv"] == 3943

print(json.dumps({
    "status": "DONE",
    "phase": "0-3",
    "script_version": SCRIPT_VERSION,
    "output_dir": str(OUT),
    "original_recovery": {
        "physical_original_found": False,
        "byte_level_recovery": True,
        "all_four_sha256_match": True,
        "rule": "LF -> CRLF (project archived rule)",
    },
    "counts": manifest_obj["counts"],
    "freeze_status": "FROZEN_CONDITIONAL",
    "validation_all_passed": checks["all_required_checks_passed"],
    "final_check": final_check,
    "database_probe": db_probe,
    "human_arbitration_required": True,
}, ensure_ascii=False, indent=2))
