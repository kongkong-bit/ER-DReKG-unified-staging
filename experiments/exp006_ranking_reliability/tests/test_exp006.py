import pandas as pd
from pathlib import Path
R=Path(__file__).resolve().parent

def test_formal_score_pairing_and_condition_uniqueness():
    p=R.parents[2]/'s2_lincs'/'results'/'formal_signature_scores.csv'
    x=pd.read_csv(p)
    assert x.sig_id.nunique()==4761 and len(x)==9522
    assert x.groupby('sig_id').scheme.nunique().eq(2).all()
    c=pd.read_csv(R.parent/'results'/'E01_AB_rank_comparison.csv')
    assert not c.duplicated(['pert_id','cell_id','dose','time']).any()

def test_condition_medians_recompute():
    s=pd.read_csv(R.parents[2]/'s2_lincs'/'results'/'formal_signature_scores.csv')
    c=pd.read_csv(R.parents[2]/'s2_lincs'/'results'/'formal_drug_condition_ranking.csv')
    keys=['scheme','pert_id','cell_id','dose','time']
    med=s.groupby(keys).WTCS.median().reset_index(name='recomputed')
    z=c.merge(med,on=keys)
    assert (abs(z.WTCS_median-z.recomputed)<1e-12).all()

def test_qc_thresholds_nested_and_signatures_real():
    x=pd.read_csv(R.parent/'results'/'E03_qc_sensitivity.csv')
    n={t:int(g.n_signatures.sum()) for t,g in x.groupby('threshold')}
    assert n[0.1] >= n[0.2] >= n[0.3]
    assert n[0.1]==7768 and n[0.2]==4761 and n[0.3]==2973

def test_single_signature_stability_is_not_fabricated():
    x=pd.read_csv(R.parent/'results'/'candidate_drugs_top50.csv')
    assert (x.loc[x.n_signatures.eq(1),'stability_grade']=='low').all()
    assert x.primary_dose.nunique()==1

