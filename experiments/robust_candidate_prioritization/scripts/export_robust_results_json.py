"""Export versioned v4 CSV results for the frontend's read-only results page."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = ROOT / "experiments" / "robust_candidate_prioritization"
RESULTS = EXPERIMENT / "results"
OUTPUT = ROOT / "frontend" / "public" / "robust-results.json"


def read_csv(name: str) -> list[dict[str, str]]:
    with (RESULTS / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def number(row: dict[str, str], key: str, cast: type = float) -> Any:
    value = row.get(key, "")
    return None if value == "" else cast(value)


def main() -> None:
    manifest = json.loads((RESULTS / "v4_manifest.json").read_text(encoding="utf-8"))
    top20_rows = read_csv("v4_top20.csv")
    eligible_rows = read_csv("v4_eligible.csv")
    top20 = [{
        "rank": number(row, "rank_v4", int),
        "drug": row["drug_name"],
        "pert_id": row["pert_id"],
        "S_disc": number(row, "S_disc"),
        "stability": number(row, "stability_top20"),
        "doses": number(row, "n_dose_conditions", int),
        "chains": number(row, "n_chains", int),
        "prism": row["prism_status"],
    } for row in top20_rows]
    mechanism_top10 = [{
        "rank": number(row, "rank_mech", int),
        "drug": row["drug_name"],
        "pert_id": row["pert_id"],
        "rank_v4": number(row, "rank_v4", int),
        "S_disc": number(row, "S_disc"),
        "chains": number(row, "n_chains", int),
        "er_chains": number(row, "n_er_chains", int),
        "targets": row["chain_targets"],
        "prism": row["prism_status"],
    } for row in read_csv("v4_mechanism_top10.csv")]
    core_c = [{
        "rank": number(row, "rank_core_c", int),
        "drug": row["drug_name"],
        "pert_id": row["pert_id"],
        "rank_v4": number(row, "rank_v4", int),
        "S_disc": number(row, "S_disc"),
        "chains": number(row, "n_chains", int),
        "prism": row["prism_status"],
    } for row in read_csv("v4_core_c.csv")]
    counts = manifest["counts"]
    payload = {
        "generated_utc": manifest["created_utc"],
        "protocol": manifest["protocol"],
        "manifest_status": manifest["status"],
        "protocol_sha256": manifest["spec_sha256"],
        "input_sha256": manifest.get("input_sha256", {}),
        "funnel": [
            {"step": "发现队列药物", "n": counts["discovery_queue"]},
            {"step": "四算法可评分", "n": counts["four_algorithm_coverage"]},
            {"step": "剂量数 ≥3", "n": counts["structural_pool"]},
            {"step": "过剂量门槛", "n": counts["dose_gates_passed"]},
            {"step": "过 3/4 算法共识", "n": counts["eligible_after_consensus"]},
            {"step": "有方向一致机制链", "n": sum(int(row.get("n_chains") or 0) > 0 for row in eligible_rows)},
            {"step": "机制可解释 Top10", "n": counts["mechanism_top10"]},
        ],
        "top20": top20,
        "mechanism_top10": mechanism_top10,
        "core_c": core_c,
        "caveats": [
            "这是计算优先级与机制假设，不是疗效、适应证或临床结论。",
            "S1 为 GSE42568 肿瘤(67) vs 正常(17)，不是 ER+ vs ER−；签名包含增殖、基质等非 ER 成分。",
            "四算法共享同一排序基因列表：WTCS/KS/Zhang 两两相关 0.85–0.91，XSum 相对独立（0.40–0.52）。",
            "Top20 中 9 个药物无图谱节点；数据前 10 中的 CGP-60474、romidepsin、WZ-3105、triptolide 因此无法进入机制名单。",
            "稳定性 ≥0.70 的只有 11 个；Top20 中 9 个位次在剂量重采样下不稳。",
            "外部 S1 与 PRISM 只作标签，不参与 v4 排序。",
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "output": OUTPUT.relative_to(ROOT).as_posix(), "mechanism_top10": len(mechanism_top10), "protocol_sha256": manifest["spec_sha256"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
