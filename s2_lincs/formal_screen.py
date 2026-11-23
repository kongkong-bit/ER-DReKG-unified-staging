from pathlib import Path
import pandas as pd, numpy as np, h5py, json, time
from smoke import wtcs
R=Path(__file__).resolve().parent; D=R/'data'; OUT=R/'results'; (R/'reports').mkdir(exist_ok=True); (R/'figures').mkdir(exist_ok=True)
sig=pd.read_csv(next(D.glob('*sig_info*.gz')),sep='\t'); met=pd.read_csv(next(D.glob('*sig_metrics*.gz')),sep='\t')
x=sig.merge(met,on=['sig_id','pert_id','pert_iname','pert_type'],how='left',suffixes=('','_m'))
for c in ['distil_cc_q75','distil_ss','tas','distil_nsample']:
 x[c]=pd.to_numeric(x[c],errors='coerce').replace(-666,np.nan)
base=x[(x.cell_id=='MCF7')&(x.pert_type=='trt_cp')].copy(); q=base[(base.pert_itime=='24 h')&base.distil_cc_q75.ge(.2)].copy()
# BING-only mapping and fixed background
G=pd.read_csv(next(D.glob('*gene_info*.gz')),sep='\t',dtype={'pr_gene_id':str});G['sym']=G.pr_gene_symbol.fillna('').str.strip().str.upper();G=G[G.pr_is_bing.astype(bool)&G.sym.ne('')].drop_duplicates('sym')
BING=set(G.sym); Aup=set(pd.read_csv(R/'s1_original_bing_up.txt',sep='\t').gene_symbol.str.upper()); Adn=set(pd.read_csv(R/'s1_original_bing_down.txt',sep='\t').gene_symbol.str.upper()); Bup=set(pd.read_csv(R/'s1_bing_top100_up.txt',sep='\t').gene_symbol.str.upper()); Bdn=set(pd.read_csv(R/'s1_bing_top100_down.txt',sep='\t').gene_symbol.str.upper())
# Confirm reference weighted-KS values using hand-solvable no-miss examples
ref=wtcs(['a','b','c','d','e','f'],dict(zip(['a','b','c','d','e','f'],[6,4,2,-2,-4,-6])),{'a','b'},{'e','f'})
assert np.allclose(ref,(1.,-1.,1.)),ref
assert np.allclose(wtcs(['e','f','d','c','b','a'],dict(zip(['e','f','d','c','b','a'],[6,4,2,-2,-4,-6])),{'a','b'},{'e','f'}),(-1.,1.,-1.))
assert abs(ref[2])<=1
print('GATE reference vectors PASS',ref)
file=next((R/'work').glob('*.gctx')); scores=[]; t0=time.time()
with h5py.File(file,'r') as h:
 mat=h['0']['DATA']['0']['matrix']; ids=[z.decode() for z in h['0']['META']['COL']['id'][:]]; genes=[z.decode() for z in h['0']['META']['ROW']['id'][:]]; pos={z:i for i,z in enumerate(ids)}
 q=q[q.sig_id.isin(pos)].copy(); q=q.sort_values(['pert_id','pert_idose','sig_id']); symbols=G.set_index('pr_gene_id').reindex(genes).sym.to_numpy(); valid=np.array([s in BING for s in symbols]); bg=np.array(symbols)[valid]
 for i,(_,row) in enumerate(q.iterrows()):
  vals=np.asarray(mat[pos[row.sig_id],:],dtype=np.float32)[valid]
  order=np.lexsort((bg,-vals)); ranked=bg[order].tolist(); weight=dict(zip(ranked,vals[order].astype(float)))
  for scheme,up,dn in [('A',Aup,Adn),('B',Bup,Bdn)]:
   eu,ed,w=wtcs(ranked,weight,up,dn); scores.append((row.sig_id,row.pert_id,row.pert_iname,row.cell_id,row.pert_type,row.pert_idose,row.pert_itime,row.distil_cc_q75,row.distil_ss,row.tas,row.distil_nsample,scheme,eu,ed,w,-w,len(up),len(dn)))
  if (i+1)%500==0: print('scored',i+1,'/',len(q),'seconds',round(time.time()-t0,1),flush=True)
cols=['sig_id','pert_id','drug_name','cell_id','pert_type','dose','time','distil_cc_q75','distil_ss','tas','distil_nsample','scheme','ES_UP','ES_DOWN','WTCS','reversal_score','n_up','n_down']; result=pd.DataFrame(scores,columns=cols); result['rank_signature']=result.groupby('scheme').WTCS.rank(method='average',ascending=True);result.to_csv(OUT/'formal_signature_scores.csv',index=False)
# Aggregate within exact drug, dose, time, scheme. Median is robust, prevents best-signature cherry-picking.
keys=['scheme','pert_id','drug_name','cell_id','pert_type','dose','time']; drug=result.groupby(keys,dropna=False).agg(n_signatures=('sig_id','size'),WTCS_median=('WTCS','median'),WTCS_mean=('WTCS','mean'),WTCS_sd=('WTCS','std'),WTCS_mad=('WTCS',lambda z:float(np.median(np.abs(z-np.median(z))))),quality_cc_median=('distil_cc_q75','median'),TAS_median=('tas','median'),replicates_median=('distil_nsample','median')).reset_index();drug['rank_condition']=drug.groupby('scheme').WTCS_median.rank(method='average',ascending=True);drug.to_csv(OUT/'formal_drug_condition_ranking.csv',index=False)
wide=drug.pivot_table(index=['pert_id','dose','time'],columns='scheme',values='WTCS_median').dropna(); from scipy.stats import spearmanr; rho=spearmanr(wide.A,wide.B).statistic
import matplotlib.pyplot as plt
for scheme,d in drug.groupby('scheme'):
 top=d.sort_values('WTCS_median').head(25).copy();top['label']=top.drug_name+' | '+top.dose.astype(str);top.plot.barh(x='label',y='WTCS_median',figsize=(9,8),legend=False,title=f'Formal MCF7 24h BING screen Scheme {scheme}');plt.tight_layout();plt.savefig(R/'figures'/f'formal_top25_{scheme}.png',dpi=160);plt.close()
plt.figure(figsize=(7,5));plt.scatter(wide.A,wide.B,s=12,alpha=.5);plt.xlabel('A median WTCS');plt.ylabel('B median WTCS');plt.title(f'A/B condition WTCS, Spearman={rho:.3f}');plt.tight_layout();plt.savefig(R/'figures'/'formal_AB_comparison.png',dpi=160);plt.close()
print('COMPLETE',len(q),'signatures',q.pert_id.nunique(),'drugs',len(drug),'condition rows; rank rho',rho,'seconds',round(time.time()-t0,1))
