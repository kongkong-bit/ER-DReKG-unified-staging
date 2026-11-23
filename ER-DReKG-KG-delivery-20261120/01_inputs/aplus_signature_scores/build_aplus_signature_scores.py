# -*- coding: utf-8 -*-
"""Part 3-C 任务A：生成 A+ signature_scores.csv（纯过滤，不重算 WTCS）。

规则确认（只读调查结论）：
  - 历史 signature_scores.csv 由 formal_screen.py 从 GCTX 表达矩阵实时计算 WTCS 生成；
    但 Final01 的 final_signature_scores.csv 已经是 scheme-B 的最终签名级结果
    （n_up=100/n_down=100 与历史 scheme B 一致，无需 GCTX 重算）。
  - A+ 条件记录（drug_condition_summary.csv）来自 Final01，与 final_signature_scores.csv
    的关联键为 (pert_id, cell_id, pert_type, dose, time)。
  - 本脚本仅按关联键过滤 final_signature_scores.csv，得到 A+ 候选对应的签名级记录。
  - /s2/import 只要求 signature_scores.csv 存在且哈希匹配，不解析其内容（main.py:693）。

严格只读源文件；输出仅写本目录；不覆盖任何历史文件；不改 S1/S2 原始数据。
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ADAPTED = Path(r"e:/生物医学信息/S3_机制解释能力诊断/phase0_4_a_plus_freeze_and_adapt/adapted_input")
FINAL01_SIG = Path(r"e:/生物医学信息/ER-DReKG/experiments/final_results/results/final_signature_scores.csv")
OUT = Path(__file__).resolve().parent

COND_KEYS = ["pert_id", "cell_id", "pert_type", "dose", "time"]


def read_csv(path: Path):
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


def key(r: dict) -> tuple:
    return tuple(str(r[c]).strip() for c in COND_KEYS)


def main() -> None:
    started = datetime.now(timezone.utc).isoformat()
    cond = read_csv(ADAPTED / "drug_condition_summary.csv")
    prov = read_csv(ADAPTED / "seed_provenance.csv")
    sig = read_csv(FINAL01_SIG)

    sig_cols = list(sig[0].keys())
    cond_keys = {key(r): r for r in cond}
    # provenance: seed_row_number -> {condition_record_id, candidate_id, source_row_number}
    prov_by_row = {int(r["seed_row_number"]): r for r in prov}

    cond_key_to_prov = {}
    for i, c in enumerate(cond, start=1):
        cond_key_to_prov[key(c)] = prov_by_row[i]

    # 过滤：只保留 A+ 条件键对应的签名行
    filtered = [r for r in sig if key(r) in cond_keys]
    if len(filtered) != 4385:
        raise SystemExit(f"[ABORT] 期望 4,385 行，实际 {len(filtered)}")

    # 值逐格保留，仅按原列顺序写出
    write_csv(OUT / "signature_scores.csv", filtered, sig_cols)

    # 溯源 sidecar：sig_id -> condition_record_id / candidate_id / source_row_number / pert_id
    prov_rows = []
    for r in filtered:
        k = key(r)
        c = cond_keys[k]
        p = cond_key_to_prov[k]
        prov_rows.append({
            "sig_id": r["sig_id"],
            "pert_id": r["pert_id"],
            "condition_record_id": p["condition_record_id"],
            "candidate_id": p["candidate_id"],
            "source_row_number": p["source_row_number"],
            "cell_id": r["cell_id"], "pert_type": r["pert_type"], "dose": r["dose"], "time": r["time"],
        })
    PROV_COLS = ["sig_id", "pert_id", "condition_record_id", "candidate_id", "source_row_number", "cell_id", "pert_type", "dose", "time"]
    write_csv(OUT / "signature_provenance.csv", prov_rows, PROV_COLS)

    # 校验：候选覆盖 / 条件覆盖 / 唯一键 / 空值 / 数值范围
    sig_ids = [r["sig_id"] for r in filtered]
    numeric_fields = ["distil_cc_q75", "distil_ss", "tas", "distil_nsample", "ES_UP", "ES_DOWN", "WTCS", "reversal_score", "effective_background_genes", "n_up", "n_down"]
    nulls = {f: sum(1 for r in filtered if r.get(f) in (None, "", "NA", "NaN")) for f in numeric_fields}
    def finite(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None
    ranges = {f: (min((finite(r[f]) for r in filtered if finite(r[f]) is not None), default=None),
                  max((finite(r[f]) for r in filtered if finite(r[f]) is not None), default=None)) for f in numeric_fields}

    report = {
        "generated": started,
        "rule": "按 (pert_id, cell_id, pert_type, dose, time) 过滤 Final01 final_signature_scores.csv，不重算 WTCS",
        "source": str(FINAL01_SIG),
        "source_sha256": sha256(FINAL01_SIG),
        "source_schema": sig_cols,
        "output_schema_equals_source": sig_cols,
        "counts": {
            "aplus_conditions": len(cond),
            "aplus_unique_condition_keys": len(cond_keys),
            "final01_signature_rows": len(sig),
            "filtered_signature_rows": len(filtered),
            "unique_sig_id": len(set(sig_ids)),
            "covered_candidates": len({r["pert_id"] for r in filtered}),
            "covered_conditions": len({key(r) for r in filtered}),
        },
        "checks": {
            "filtered_rows_equals_4385": len(filtered) == 4385,
            "all_condition_keys_have_signature": all(key(c) in {key(r) for r in filtered} for c in cond),
            "n_signatures_sum_matches": sum(int(c["n_signatures"]) for c in cond) == len(filtered),
            "sig_id_unique": len(sig_ids) == len(set(sig_ids)),
            "candidate_coverage_1032": len({r["pert_id"] for r in filtered}) == 1032,
        },
        "nulls": nulls,
        "numeric_ranges": ranges,
        "outputs": {},
    }
    for name in ["signature_scores.csv", "signature_provenance.csv"]:
        report["outputs"][name] = {"rows": len(filtered) if name == "signature_scores.csv" else len(prov_rows),
                                   "sha256": sha256(OUT / name)}
    report_path = OUT / "build_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT / "sha256.txt").write_text("\n".join(f"{v['sha256']}  {k}" for k, v in report["outputs"].items()) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
