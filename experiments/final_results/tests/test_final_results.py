from pathlib import Path
import json

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "experiments" / "final_results"


def test_corrected_signature_scores_are_complete_and_unique():
    scores = pd.read_csv(OUT / "results" / "final_signature_scores.csv")
    assert len(scores) == 5861
    assert scores["sig_id"].is_unique
    assert scores["WTCS"].notna().all()
    assert scores["pert_id"].notna().all()


def test_historical_overlap_reproduces_corrected_wtcs():
    manifest = json.loads((OUT / "final_data_manifest.json").read_text(encoding="utf-8"))
    validation = manifest["validation"]
    counts = manifest["counts"]
    assert validation["historical_match_tolerance"] == 1e-9
    assert max(validation["historical_max_abs_difference"].values()) < 1e-9
    assert counts["historical_common_ids_reproduced"] == 4761
    assert counts["exp009_wtcs_values_mismatching_corrected"] == 3870


def test_primary_top10_follows_fixed_condition_and_rank():
    top = pd.read_csv(OUT / "results" / "final_top10.csv")
    assert len(top) == 10
    assert top["rank"].tolist() == list(range(1, 11))
    assert top["pert_id"].is_unique
    assert set(top["cell_id"]) == {"MCF7"}
    assert set(top["pert_type"]) == {"trt_cp"}
    assert set(top["time"]) == {"24 h"}
    assert set(top["dose"]) == {"10.0 um"}
    assert (top["n_signatures"] >= 1).all()
    assert (top["WTCS_median"].diff().dropna() >= -1e-12).all()


def test_evidence_does_not_change_the_s2_ranking():
    top = pd.read_csv(OUT / "results" / "final_top10.csv")
    evidence = pd.read_csv(OUT / "results" / "final_top10_evidence_matrix.csv")
    assert top[["rank", "pert_id"]].equals(evidence[["rank", "pert_id"]])
    assert (evidence["n_signatures"] == 1).all()


def test_frontend_artifacts_match_final_results():
    page = json.loads((ROOT / "frontend" / "public" / "final-results.json").read_text(encoding="utf-8"))
    top = pd.read_csv(OUT / "results" / "final_top10.csv")
    assert page["status"] == "PASS"
    assert len(page["candidates"]) == len(top) == 10
    assert [item["pert_id"] for item in page["candidates"]] == top["pert_id"].tolist()
    assert all("mechanism_paths" in item for item in page["candidates"])


def test_mechanism_packages_and_citations_are_complete_and_traceable():
    reports = OUT / "top10_mechanism_reports"
    paths = pd.read_csv(OUT / "mechanism" / "top10_mechanism_paths.csv")
    citations = pd.read_csv(OUT / "mechanism" / "top10_evidence_citations.csv")
    assert len(list(reports.glob("*.md"))) == 10
    assert len(paths) == 395
    assert len(citations) >= len(paths)
    graph_rows = citations[citations["evidence_type"].isin(["drug_target_relation", "target_to_S1_pathway", "disease_context_pathway"])]
    assert graph_rows["evidence_id"].notna().all()


def test_missing_empirical_statistics_remain_missing_and_scoped():
    matrix = pd.read_csv(OUT / "results" / "final_top10_evidence_matrix.csv")
    assert matrix["empirical_pvalue_B200_historical"].notna().sum() == 5
    assert matrix["BH_FDR_B200_historical"].notna().sum() == 5
    assert matrix["permutation_statistics_scope"].str.contains("Historical Exp008 B200").all()


def test_final_status_and_manifest_alias_exist():
    assert (OUT / "reports" / "final_project_status.md").is_file()
    alias = json.loads((OUT / "final_results_manifest.json").read_text(encoding="utf-8"))
    assert alias["requested_final_artifacts"]["frontend_route"] == "/final-results"
    fallback = json.loads((ROOT / "frontend" / "public" / "final-evidence-records.json").read_text(encoding="utf-8"))
    assert fallback
    assert all(record.get("source_assertion") for record in fallback.values())
