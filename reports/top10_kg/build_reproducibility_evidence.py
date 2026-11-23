"""Extract the already-run Exp006–Exp011 robustness evidence for frozen Top 10."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports" / "top10_kg"
RESULT = ROOT / "experiments" / "final_results" / "results"
FROZEN = REPORTS / "02_top10_frozen_manifest.json"
MATRIX = RESULT / "final_top10_evidence_matrix.csv"
EXP009 = ROOT / "experiments" / "exp009_lincs_quality" / "results" / "candidate_quality_comparison.csv"
EXP010 = ROOT / "experiments" / "exp010_external_s1" / "results" / "external_s1_drug_ranking.csv"
EXP011 = ROOT / "experiments" / "exp011_prism_validation" / "results" / "er_specificity_candidate_summary.csv"
OUT = REPORTS / "top10_reproducibility_evidence.csv"
MANIFEST = REPORTS / "top10_reproducibility_evidence_manifest.json"


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    matrix = {row["pert_id"]: row for row in read(MATRIX)}
    exp009 = {row["pert_id"]: row for row in read(EXP009)}
    exp011 = {row["pert_id"]: row for row in read(EXP011)}
    fields = [
        "rank", "pert_id", "drug_name", "main_condition", "WTCS_median", "n_signatures", "CC_median", "TAS_median",
        "exp006_dose_count", "exp006_negative_dose_fraction", "exp006_dose_stability", "exp006_qc_sensitivity_range", "exp006_stability_grade", "exp006_limitations",
        "exp007_rank_A_original", "exp007_rank_B100", "exp007_rank_B150", "exp007_rank_B200", "exp007_rank_B300", "exp007_rank_B_matched125",
        "exp008_empirical_pvalue_B200_historical", "exp008_BH_FDR_B200_historical", "exp008_permutation_count_B200_historical", "exp008_scope",
        "exp009_status", "exp009_rank_CC02", "exp009_rank_CC01", "exp009_rank_CC03", "exp009_rank_CC02_TAS02",
        "exp010_status", "exp010_external_S1_rank", "exp010_external_S1_WTCS",
        "exp011_status", "exp011_ERpos_mean_sensitivity", "exp011_ERpos_median_sensitivity", "exp011_ERpos_cell_lines", "exp011_ERneg_mean_sensitivity", "exp011_ERneg_median_sensitivity", "exp011_ERneg_cell_lines", "exp011_MCF7_sensitivity", "exp011_ERpos_minus_ERneg",
        "interpretation_limits",
    ]
    output = []
    for item in frozen["items"]:
        pid = item["pert_id"]
        row = matrix.get(pid)
        if row is None:
            raise ValueError(f"Consolidated evidence matrix lacks frozen candidate {pid}")
        q = exp009.get(pid)
        prism = exp011.get(pid)
        ext_s1 = row.get("external_S1_same_condition_rank", "")
        output.append({
            "rank": str(item["rank"]), "pert_id": pid, "drug_name": item["pert_iname"],
            "main_condition": row.get("main_condition", ""), "WTCS_median": row.get("WTCS_median", ""),
            "n_signatures": row.get("n_signatures", ""), "CC_median": row.get("CC_median", ""), "TAS_median": row.get("TAS_median", ""),
            "exp006_dose_count": row.get("Exp006_24h_Q2_dose_count", ""), "exp006_negative_dose_fraction": row.get("Exp006_negative_dose_fraction", ""),
            "exp006_dose_stability": row.get("Exp006_dose_stability", ""), "exp006_qc_sensitivity_range": row.get("Exp006_QC_sensitivity_range", ""),
            "exp006_stability_grade": row.get("Exp006_stability_grade", ""), "exp006_limitations": row.get("Exp006_stability_limitations", ""),
            "exp007_rank_A_original": row.get("Exp007_rank_A_original", ""), "exp007_rank_B100": row.get("Exp007_rank_B100", ""),
            "exp007_rank_B150": row.get("Exp007_rank_B150", ""), "exp007_rank_B200": row.get("Exp007_rank_B200", ""),
            "exp007_rank_B300": row.get("Exp007_rank_B300", ""), "exp007_rank_B_matched125": row.get("Exp007_rank_B_matched125", ""),
            "exp008_empirical_pvalue_B200_historical": row.get("empirical_pvalue_B200_historical", ""),
            "exp008_BH_FDR_B200_historical": row.get("BH_FDR_B200_historical", ""),
            "exp008_permutation_count_B200_historical": row.get("permutation_count_B200_historical", ""),
            "exp008_scope": row.get("permutation_statistics_scope", ""),
            "exp009_status": "available" if q else "not_in_exp009_candidate_quality_output",
            "exp009_rank_CC02": q.get("rank_CC02", "") if q else "", "exp009_rank_CC01": q.get("rank_CC01", "") if q else "",
            "exp009_rank_CC03": q.get("rank_CC03", "") if q else "", "exp009_rank_CC02_TAS02": q.get("rank_CC02_TAS02", "") if q else "",
            "exp010_status": "available" if ext_s1 else "not_matched_in_exp010_output",
            "exp010_external_S1_rank": ext_s1, "exp010_external_S1_WTCS": row.get("external_S1_same_condition_WTCS", ""),
            "exp011_status": "available" if prism else "not_matched_in_exp011_prism_output",
            "exp011_ERpos_mean_sensitivity": prism.get("erpos_mean_sensitivity", "") if prism else "",
            "exp011_ERpos_median_sensitivity": prism.get("erpos_median_sensitivity", "") if prism else "",
            "exp011_ERpos_cell_lines": prism.get("n_erpos_lines", "") if prism else "",
            "exp011_ERneg_mean_sensitivity": prism.get("erneg_mean_sensitivity", "") if prism else "",
            "exp011_ERneg_median_sensitivity": prism.get("erneg_median_sensitivity", "") if prism else "",
            "exp011_ERneg_cell_lines": prism.get("n_erneg_lines", "") if prism else "",
            "exp011_MCF7_sensitivity": prism.get("mcf7_sensitivity", "") if prism else "",
            "exp011_ERpos_minus_ERneg": prism.get("erpos_minus_erneg_sensitivity", "") if prism else "",
            "interpretation_limits": "Historical sensitivity analyses are not re-estimates of the frozen primary result. PRISM viability sensitivity is a different endpoint from WTCS; missing candidate rows mean unavailable/unmatched in that experiment output, not a negative result.",
        })
    with OUT.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output)
    sources = [FROZEN, MATRIX, EXP009, EXP010, EXP011]
    manifest = {
        "status": "extracted_from_existing_historical_experiment_outputs",
        "record_count": len(output), "candidate_count": len(output), "frozen_top10_sha256": frozen["source_sha256"],
        "source_hashes": {str(p.relative_to(ROOT)): sha(p) for p in sources},
        "output_sha256": sha(OUT),
        "coverage": {
            "Exp009_candidate_quality_rows": sum(1 for r in output if r["exp009_status"] == "available"),
            "Exp010_external_S1_rows": sum(1 for r in output if r["exp010_status"] == "available"),
            "Exp011_PRISM_rows": sum(1 for r in output if r["exp011_status"] == "available"),
        },
        "limits": [
            "Exp006/Exp007/Exp008 values retain their original historical analysis conditions and are not recomputed on the corrected frozen-signature set.",
            "Exp009/Exp010/Exp011 coverage is incomplete; missing rows are not negative evidence.",
            "PRISM sensitivity is a viability endpoint and is not directly comparable to LINCS WTCS.",
        ],
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
