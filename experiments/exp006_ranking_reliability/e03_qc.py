from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'s2_lincs'))
import pandas as pd,numpy as np,h5py,time
from smoke import wtcs
R=Path(__file__).resolve().parent; S=R.parent.parent/'s2_lincs';D=S/'data';O=R/'results'; G=pd.read_csv(next(D.glob('*gene_info*.gz')),sep='\t',dtype={'pr_gene_id':str});G['sym']=G.pr_gene_symbol.fillna('').str.strip().str.upper();G['bing']=G.pr_is_bing.astype(bool);G=G[G.pr_is_bing.astype(bool)&G.sym.ne('')].drop_duplicates('sym');bing=set(G.sym)
u=set(pd.read_csv(S/'s1_bing_top100_up.txt',sep='\t').gene_symbol.str.upper());d=set(pd.read_csv(S/'s1_bing_top100_down.txt',sep='\t').gene_symbol.str.upper())
s=pd.read_csv(next(D.glob('*sig_info*.gz')),sep='\t');m=pd.read_csv(next(D.glob('*sig_metrics*.gz')),sep='\t');x=s.merge(m,on=['sig_id','pert_id','pert_iname','pert_type'],how='left');x['distil_cc_q75']=pd.to_numeric(x.distil_cc_q75,errors='coerce').replace(-666,np.nan);x=x[(x.cell_id=='MCF7')&(x.pert_type=='trt_cp')&(x.pert_itime=='24 h')&x.distil_cc_q75.ge(.1)]
existing=pd.read_csv(S/'results'/'formal_signature_scores.csv'); existing=existing[existing.scheme=='B']; have=set(existing.sig_id); todo=x[~x.sig_id.isin(have)].copy(); print('Q1 candidates',len(x),'new',len(todo),flush=True)
path=next((S/'work').glob('*.gctx')); add=[];t=time.time()
with h5py.File(path,'r') as h:
 mat=h['0']['DATA']['0']['matrix']; ids=[v.decode() for v in h['0']['META']['COL']['id'][:]]; genes=[v.decode() for v in h['0']['META']['ROW']['id'][:]]; ix={v:i for i,v in enumerate(ids)}; gm=G.set_index('pr_gene_id').reindex(genes); sy=gm.sym.to_numpy(); keep=gm.bing.fillna(False).to_numpy(dtype=bool)&(sy!=''); bg=sy[keep]
 todo=todo[todo.sig_id.isin(ix)]
 for j,(_,r) in enumerate(todo.iterrows()):
  vals=np.asarray(mat[ix[r.sig_id],:],float)[keep]; order=np.lexsort((bg,-vals)); ranked=bg[order].tolist(); w=dict(zip(ranked,vals[order])); eu,ed,wt=wtcs(ranked,w,u,d)
  add.append({'sig_id':r.sig_id,'pert_id':r.pert_id,'drug_name':r.pert_iname,'cell_id':r.cell_id,'pert_type':r.pert_type,'dose':r.pert_idose,'time':r.pert_itime,'distil_cc_q75':r.distil_cc_q75,'distil_ss':r.distil_ss,'tas':r.tas,'distil_nsample':r.distil_nsample,'ES_UP':eu,'ES_DOWN':ed,'WTCS':wt})
  if (j+1)%500==0:print('added',j+1,'/',len(todo),'sec',round(time.time()-t),flush=True)
new=pd.DataFrame(add);new.to_csv(O/'E03_q1_incremental_scores.csv',index=False)
# combine exact real signature scores and threshold-filtered condition aggregates
# Reuse the just-written incremental scores; attach metadata without duplicate columns.
meta=x[['sig_id','pert_id','pert_iname','cell_id','pert_type','pert_idose','pert_itime','distil_cc_q75','distil_ss','tas','distil_nsample']].drop_duplicates('sig_id')
formal=pd.read_csv(S/'results'/'formal_signature_scores.csv'); formal=formal[formal.scheme=='B'].merge(meta,on='sig_id',suffixes=('_score',''))
formal=formal.rename(columns={'pert_iname':'drug_name','pert_idose':'dose','pert_itime':'time'})
new=new.merge(meta,on='sig_id',suffixes=('_score',''))
new=new.rename(columns={'pert_iname':'drug_name','pert_idose':'dose','pert_itime':'time'})
q1=pd.concat([formal,new],ignore_index=True,sort=False); q2=formal[formal.distil_cc_q75.ge(.2)]; q3=formal[formal.distil_cc_q75.ge(.3)]
rows=[]
for threshold,z in {0.1:q1,0.2:q2,0.3:q3}.items():
 z=z.copy();keys=['pert_id','cell_id','dose','time'];agg=z.groupby(keys).agg(wtcs_median=('WTCS','median'),n_signatures=('sig_id','nunique'),drug_name=('drug_name','first')).reset_index();agg['threshold']=threshold;rows.append(agg)
allc=pd.concat(rows,ignore_index=True);allc.to_csv(O/'E03_qc_sensitivity.csv',index=False)
for threshold,z in allc.groupby('threshold'): print('threshold',threshold,'signatures',z.n_signatures.sum(),'drugs',z.pert_id.nunique(),'conditions',len(z))
