from app.s2_stability import summarize_condition_stability


def test_stability_counts_top_n_recurrence_without_combining_scores():
    rows = [
        {"pert_id": "DRUG-A", "drug_name": "Drug A", "cell_id": "MCF7", "pert_type": "trt_cp", "time": "24 h", "dose": "1 uM", "rank_within_condition": "2", "WTCS_median": "-0.8"},
        {"pert_id": "DRUG-A", "drug_name": "Drug A", "cell_id": "MCF7", "pert_type": "trt_cp", "time": "24 h", "dose": "10 uM", "rank_within_condition": "15", "WTCS_median": "-0.1"},
        {"pert_id": "DRUG-A", "drug_name": "Drug A", "cell_id": "MCF7", "pert_type": "trt_cp", "time": "6 h", "dose": "1 uM", "rank_within_condition": "1", "WTCS_median": "-0.9"},
        {"pert_id": "DRUG-B", "drug_name": "Drug B", "cell_id": "MCF7", "pert_type": "trt_cp", "time": "24 h", "dose": "1 uM", "rank_within_condition": "1", "WTCS_median": "-0.7"},
        {"pert_id": "", "rank_within_condition": "1"},
    ]

    result = summarize_condition_stability(rows, top_n=10)
    a_24h = next(row for row in result if row["pert_id"] == "DRUG-A" and row["time"] == "24 h")
    a_6h = next(row for row in result if row["pert_id"] == "DRUG-A" and row["time"] == "6 h")

    assert a_24h["dose_count"] == a_24h["condition_count"] == 2
    assert a_24h["top_n_condition_count"] == 1
    assert a_24h["top_n_condition_fraction"] == 0.5
    assert a_24h["rank_range_across_conditions"] == 13
    assert a_6h["condition_count"] == 1
    assert "不合并 WTCS" in a_24h["interpretation"]


def test_stability_rejects_nonpositive_top_n():
    try:
        summarize_condition_stability([], top_n=0)
    except ValueError as error:
        assert "positive" in str(error)
    else:
        raise AssertionError("top_n=0 should fail")
