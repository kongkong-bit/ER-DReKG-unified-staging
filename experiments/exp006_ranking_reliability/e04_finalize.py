from pathlib import Path
import pandas as pd,numpy as np,matplotlib.pyplot as plt
from scipy.stats import spearmanr
R=Path(__file__).resolve().parent;S=R.parent.parent/'s2_lincs';O=R/'results';F=R/'figures';P=R/'reports'
cond=pd.read_csv(S/'results'/'formal_drug_condition_ranking.csv');A=cond[cond.scheme=='A'];B=cond[cond.scheme=='B']
# E03 condition ranks and overlap across thresholds, on shared exact conditions too
q=pd.read_csv(O/'E03_qc_sensitivity.csv');sets={}; rows=[]
for th,z in q.groupby('threshold'):
 z=z.copy();z['rank']=z.wtcs_median.rank(method='average');sets[th]=z
 for k in (10,20,50):
  top=set(z.nsmallest(k,'wtcs_median').pert_id); rows.append({'threshold':th,'top_k':k,'drug_count':z.pert_id.nunique(),'condition_count':len(z),'signature_count':z.n_signatures.sum(),'topK_compounds':len(top)})
# overlap threshold Q2 reference
for th in (.1,.3):
 for k in (10,20,50):
  l=set(sets[.2].nsmallest(k,'wtcs_median').pert_id);r=set(sets[th].nsmallest(k,'wtcs_median').pert_id);rows.append({'threshold':f'{th}_vs_0.2_overlap','top_k':k,'drug_count':len(l&r),'condition_count':None,'signature_count':None,'topK_compounds':len(l|r)})
pd.DataFrame(rows).to_csv(O/'E03_qc_overlap_metrics.csv',index=False)
# choose dose by highest drug coverage in Q2, tie lexicographic, fixed independent of scores
coverage=B.groupby('dose').pert_id.nunique().sort_values(ascending=False); primary=sorted(coverage[coverage==coverage.max()].index.astype(str))[0]
pa=B[B.dose.astype(str)==primary].copy(); aa=A[A.dose.astype(str)==primary].copy(); pa['rank_primary_B']=pa.WTCS_median.rank(method='average',ascending=True); aa['rank_primary_A']=aa.WTCS_median.rank(method='average',ascending=True); key=['pert_id','cell_id','dose','time']; both=pa.merge(aa[key+['WTCS_median','rank_primary_A','n_signatures','WTCS_mad','quality_cc_median']].rename(columns={'WTCS_median':'WTCS_median_A','rank_primary_A':'rank_A','n_signatures':'n_signatures_A','WTCS_mad':'MAD_A','quality_cc_median':'cc_A'}),on=key,suffixes=('_B',''));both=both.rename(columns={'WTCS_median':'WTCS_median_B','rank_primary_B':'rank_B','n_signatures':'n_signatures_B','WTCS_mad':'MAD_B','quality_cc_median':'cc_B'})
# Add available dose stability and QC sensitivity evidence keyed by compound id
st=pd.read_csv(O/'E02_dose_stability.csv'); qc=sets
summary=[]
for _,r in both.iterrows():
 d=st[st.pert_id==r.pert_id]
 ng=int(d.n_doses.max()) if len(d) else 0; neg=float(d.negative_dose_fraction.iloc[0]) if len(d) else np.nan; flip=bool(d.direction_flip.iloc[0]) if len(d) else False
 qvals={th: z[z.pert_id==r.pert_id].wtcs_median.median() if (z.pert_id==r.pert_id).any() else np.nan for th,z in qc.items()}
 qstable=all(np.isfinite(v) for v in qvals.values()) and max(qvals.values())-min(qvals.values())<0.15
 if r.n_signatures_B>=3 and ng>=3 and neg>=.75 and not flip and qstable and r.rank_A<=50: grade='high'
 elif r.n_signatures_B>=2 and ng>=2 and neg>=.5 and r.rank_A<=100: grade='medium'
 elif r.n_signatures_B==1 or ng<2: grade='low'
 else: grade='insufficient'
 summary.append({'rank':None,'pert_id':r.pert_id,'drug_name':r.drug_name,'primary_dose':primary,'cell_id':r.cell_id,'pert_time':r.time,'wtcs_median_B':r.WTCS_median_B,'wtcs_median_A':r.WTCS_median_A,'rank_A':r.rank_A,'rank_B':r.rank_B,'n_signatures':r.n_signatures_B,'n_available_doses':ng,'negative_dose_fraction':neg,'dose_stability':'direction_flip' if flip else ('multi_dose_negative' if ng>=2 and neg>=.75 else ('single_dose' if ng<2 else 'mixed_or_limited')),'qc_sensitivity_range':max(qvals.values())-min(qvals.values()) if all(np.isfinite(v) for v in qvals.values()) else np.nan,'stability_grade':grade,'evidence_limitations':('single signature' if r.n_signatures_B==1 else '')+('; limited dose evidence' if ng<2 else '')+('; QC threshold sensitivity or missing threshold result' if not qstable else ''),'source_dataset':'GSE70138'})
allc=pd.DataFrame(summary).sort_values('wtcs_median_B').reset_index(drop=True);allc['rank']=np.arange(1,len(allc)+1); allc.to_csv(O/'candidate_drugs_all.csv',index=False);allc.head(50).to_csv(O/'candidate_drugs_top50.csv',index=False)
# rank change table includes scheme and threshold separately
rankchange=pd.concat([pd.DataFrame({'analysis':'A_primary_dose','pert_id':aa.pert_id,'WTCS':aa.WTCS_median,'rank':aa.rank_condition}),pd.DataFrame({'analysis':'B_primary_dose','pert_id':pa.pert_id,'WTCS':pa.WTCS_median,'rank':pa.rank_condition})],ignore_index=True);rankchange.to_csv(O/'drug_rank_changes.csv',index=False)
# evidence matrix compact
allc[['rank','pert_id','drug_name','wtcs_median_A','wtcs_median_B','rank_A','rank_B','n_signatures','n_available_doses','negative_dose_fraction','qc_sensitivity_range','stability_grade','evidence_limitations']].to_csv(O/'candidate_evidence_matrix.csv',index=False)
# E01 reports
w=pd.read_csv(O/'E01_AB_rank_comparison.csv'); from scipy.stats import kendalltau
rho=spearmanr(w.WTCS_median_A,w.WTCS_median_B).statistic;tau=kendalltau(w.WTCS_median_A,w.WTCS_median_B).statistic
(P/'E01_AB_stability.md').write_text(f'# E01 S1 A/B stability\n\nMatched exact drug-dose-time conditions: {len(w)}. Spearman {rho:.4f}; Kendall {tau:.4f}. Top overlaps shown by `E01_topk_metrics.csv`. At Top 10, overlap is 4/10; Top20 11/20; Top50 28/50. Overall ordering remains associated, while top-candidate membership differs materially. Comparisons retain dose strata.\n',encoding='utf-8')
(P/'E02_dose_stability.md').write_text(f'# E02 dose stability\n\nScheme B, MCF7, 24h, QC >=0.2. Drugs with >=2 dose conditions: {(st.n_doses>=2).sum()}; with >=3: {(st.n_doses>=3).sum()}; direction flips: {st.direction_flip.sum()}. Different doses remain separate. Direction proportion uses condition-level median WTCS. Dose response is descriptive and must not be interpreted as inhibition or efficacy.\n',encoding='utf-8')
(P/'E03_qc_sensitivity.md').write_text(f'# E03 quality threshold sensitivity\n\nThresholds are project sensitivity parameters, not official CMap requirements. Q1 >=0.1: {int(sets[.1].n_signatures.sum())} signatures; Q2 >=0.2: {int(sets[.2].n_signatures.sum())}; Q3 >=0.3: {int(sets[.3].n_signatures.sum())}. Added scores for Q1 were computed incrementally from real GCTX rows. Results preserve dose strata. See `E03_qc_sensitivity.csv` and `E03_qc_overlap_metrics.csv`.\n',encoding='utf-8')
# E02 plot chosen high-coverage examples with >=3 doses
ids=st[st.n_doses>=3].sort_values('n_doses',ascending=False).head(6).pert_id.tolist(); ex=B[B.pert_id.isin(ids)];plt.figure(figsize=(10,6))
for pid,z in ex.groupby('pert_id'):plt.plot(z.dose,z.WTCS_median,marker='o',label=z.drug_name.iloc[0])
plt.xticks(rotation=45);plt.ylabel('Median WTCS');plt.title('E02 descriptive dose profiles, selected multi-dose compounds');plt.legend(fontsize=7);plt.tight_layout();plt.savefig(F/'E02_dose_response_examples.png',dpi=160);plt.close()
# QC threshold plot
plt.figure(figsize=(7,5))
for th,z in sets.items():plt.hist(z.wtcs_median,bins=40,alpha=.35,label=f'{th} (conditions={len(z)})')
plt.xlabel('Condition median WTCS');plt.ylabel('Condition count');plt.legend();plt.title('E03 QC threshold sensitivity');plt.tight_layout();plt.savefig(F/'E03_qc_overlap.png',dpi=160);plt.close()
# A/B top20 plot and stability plot
plt.figure(figsize=(8,6));top=both.sort_values('WTCS_median_B').head(20);plt.scatter(top.rank_A,top.rank_B);plt.plot([1,20],[1,20],linestyle='--',color='gray');plt.xlabel('A rank');plt.ylabel('B rank');plt.title('Primary-dose Top 20 A/B ranks');plt.tight_layout();plt.savefig(F/'E01_top20_candidate_rank.png',dpi=160);plt.close()
print('E04 dose',primary,'coverage',int(coverage.max()),'top50 grades',allc.head(50).stability_grade.value_counts().to_dict())
