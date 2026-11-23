from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
RES=ROOT/"experiments"/"exp009_lincs_quality"/"results"


def test_quality_threshold_counts_are_monotone():
    x=pd.read_csv(RES/"quality_threshold_counts.csv")
    cc=x[x.metric.eq("distil_cc_q75")].sort_values("threshold")
    assert cc.threshold.tolist()==[0.1,0.2,0.3]
    assert cc.signatures.is_monotonic_decreasing
    assert cc.compounds.is_monotonic_decreasing


def test_quality_rank_comparison_has_full_top10_overlap():
    x=pd.read_csv(RES/"quality_rank_comparison.csv")
    assert len(x)==3
    assert (x.top10_overlap==10).all()
    assert (x.spearman.between(-1,1)).all()


def test_qc_and_tas_are_reported_as_separate_filters():
    x=pd.read_csv(RES/"qc_threshold_comparison.csv")
    assert set(x.metric)=={"distil_cc_q75","TAS"}
    assert len(x[x.metric.eq("distil_cc_q75")])==3
    audit=pd.read_csv(RES/"tas_calculation_audit.csv").iloc[0]
    assert audit.status=="NOT_PERFORMED"


def test_dose_and_candidate_sensitivity_outputs_are_complete():
    cand=pd.read_csv(RES/"candidate_quality_comparison.csv")
    assert len(cand)==819
    assert {"rank_CC02","rank_CC01","rank_CC03","rank_CC02_TAS02"}.issubset(cand.columns)
    dose=pd.read_csv(RES/"dose_direction_stability.csv")
    assert len(dose)>0
    comparable=dose[dose.shared_compounds.gt(1)]
    assert len(comparable)>0 and comparable.spearman_WTCS.between(-1,1).all()
    for name in ["lincs_metric_audit.csv","dose_condition_summary.csv"]:
        assert (RES/name).is_file()
