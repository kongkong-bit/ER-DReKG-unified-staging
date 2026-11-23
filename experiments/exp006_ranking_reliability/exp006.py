from pathlib import Path
import pandas as pd, numpy as np, json
from scipy.stats import spearmanr, kendalltau
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent; S=R.parents[1]/'s2_lincs'; O=R/'results'; F=R/'figures'; P=R/'reports'; D=S/'data'
sig=pd.read_csv(S/'results'/'formal_signature_scores.csv'); cond=pd.read_csv(S/'results'/'formal_drug_condition_ranking.csv'); qsum=pd.read_csv(S/'results'/'formal_qc_summary.csv'); inv=pd.read_csv(S/'results'/'mcf7_condition_inventory.csv')
# Phase 0 assertions and independent aggregate check
assert sig.sig_id.nunique()==4761 and len(sig)==9522
assert set(sig.scheme)=={'A','B'} and sig.groupby('scheme').sig_id.nunique().eq(4761).all()
keys=['scheme','pert_id','cell_id','dose','time']; assert not cond.duplicated(keys).any()
assert cond.pert_id.notna().all() and cond.drug_name.notna().all()
recalc=sig.groupby(keys,dropna=False).WTCS.median().rename('check').reset_index(); chk=cond.merge(recalc,on=keys); assert np.allclose(chk.WTCS_median,chk.check)
# name consistency
nameconf=sig.groupby('pert_id').drug_name.nunique(); conflicts=nameconf[nameconf>1]
# condition coverage by dose (per scheme)
coverage=cond.groupby(['scheme','time','dose'],dropna=False).agg(condition_rows=('pert_id','size'),unique_drugs=('pert_id','nunique'),signatures=('n_signatures','sum'),median_cc=('quality_cc_median','median')).reset_index(); coverage.to_csv(O/'00_condition_coverage.csv',index=False)
(P/'00_formal_data_audit.md').write_text(f'''# Formal S2 data audit\n\n- Signature-score rows: {len(sig)}; unique signatures: {sig.sig_id.nunique()}; per scheme: {sig.groupby('scheme').sig_id.nunique().to_dict()}.\n- Condition rows: {len(cond)}; by scheme: {cond.groupby('scheme').size().to_dict()}; unique condition key `(scheme, pert_id, cell_id, dose, time)`: {not cond.duplicated(keys).any()}.\n- All perturbagen IDs/names non-empty: {cond.pert_id.notna().all() and cond.drug_name.notna().all()}. IDs with multiple names: {len(conflicts)}.\n- Independent recomputation of condition WTCS median: {'PASS' if np.allclose(chk.WTCS_median,chk.check) else 'FAIL'}.\n- Time records are 24 h. Dose strings retained as exact strata. Source uses one consistent `um` dose unit.\n- WTCS ascending order is inverse-connectivity-first. Source rank_signature is ascending WTCS.\n- Signature rows are already Level 5 replicate-aggregated signatures; their internal replicates are not counted as independent Level 5 records.\n''',encoding='utf-8')
# E01 shared conditions naturally paired
wide=cond.pivot_table(index=['pert_id','cell_id','dose','time'],columns='scheme',values='WTCS_median').dropna().reset_index().rename(columns={'A':'WTCS_median_A','B':'WTCS_median_B'}); wide['rank_A']=wide['WTCS_median_A'].rank(method='average');wide['rank_B']=wide['WTCS_median_B'].rank(method='average');wide['rank_delta']=wide['rank_B']-wide['rank_A'];wide['abs_rank_delta']=wide['rank_delta'].abs();wide.to_csv(O/'E01_AB_rank_comparison.csv',index=False)
metrics=[]
for k in [10,20,50]:
 a=set(wide.nsmallest(k,'WTCS_median_A').pert_id);b=set(wide.nsmallest(k,'WTCS_median_B').pert_id); inter=a&b;union=a|b
 metrics.append({'top_k':k,'overlap_n':len(inter),'overlap_rate_of_k':len(inter)/k,'jaccard':len(inter)/len(union) if union else np.nan})
pd.DataFrame(metrics).to_csv(O/'E01_topk_metrics.csv',index=False)
# Drug-level paired summaries across condition strata, preserving dose condition-level values then median ranks per pert_id for named comparison
bydrug=wide.groupby('pert_id').agg(WTCS_A=('WTCS_median_A','median'),WTCS_B=('WTCS_median_B','median'),conditions=('dose','size')).reset_index();bydrug['rank_A']=bydrug.WTCS_A.rank();bydrug['rank_B']=bydrug.WTCS_B.rank();
from scipy.stats import spearmanr,kendalltau
rho=spearmanr(wide.WTCS_median_A,wide.WTCS_median_B).statistic;tau=kendalltau(wide.WTCS_median_A,wide.WTCS_median_B).statistic
# E02 scheme B dose stability
bcond=cond[cond.scheme=='B'].copy(); dose=bcond.groupby(['pert_id','drug_name','cell_id','time'],dropna=False).agg(n_doses=('dose','nunique'),dose_values=('dose',lambda z:';'.join(sorted(set(z)))),wtcs_median=('WTCS_median','median'),wtcs_min=('WTCS_median','min'),wtcs_max=('WTCS_median','max'),negative_dose_fraction=('WTCS_median',lambda z:float((z<0).mean())),n_signatures=('n_signatures','sum')).reset_index();dose['wtcs_range']=dose.wtcs_max-dose.wtcs_min;dose['direction_flip']=((dose.wtcs_min<0)&(dose.wtcs_max>0));dose.to_csv(O/'E02_dose_stability.csv',index=False)
# choose example drugs with >=3 doses
examples=dose[dose.n_doses>=3].sort_values('n_doses',ascending=False).head(8).pert_id.tolist();bcond[bcond.pert_id.isin(examples)].to_csv(O/'E02_dose_examples.csv',index=False)
# initial figures
plt.figure(figsize=(7,6));plt.scatter(wide.WTCS_median_A,wide.WTCS_median_B,s=10,alpha=.4);plt.xlabel('Scheme A condition median WTCS');plt.ylabel('Scheme B condition median WTCS');plt.title(f'E01 matched conditions Spearman={rho:.3f}');plt.tight_layout();plt.savefig(F/'E01_AB_rank_scatter.png',dpi=160);plt.close()
mm=pd.DataFrame(metrics);plt.figure(figsize=(6,4));plt.bar(mm.top_k.astype(str),mm.overlap_rate_of_k);plt.ylim(0,1);plt.xlabel('Top K');plt.ylabel('Overlap / K');plt.title('A/B candidate overlap');plt.tight_layout();plt.savefig(F/'E01_topk_overlap.png',dpi=160);plt.close()
print({'E01_paired_conditions':len(wide),'rho':rho,'kendall':tau,'topk':metrics,'E02_multi_dose_drugs':int((dose.n_doses>=2).sum()),'flips':int(dose.direction_flip.sum()),'dose_ge3':int((dose.n_doses>=3).sum()),'name_conflicts':len(conflicts)})
