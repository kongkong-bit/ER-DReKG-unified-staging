from pathlib import Path
import pandas as pd,numpy as np
R=Path(__file__).resolve().parent;S=R.parent.parent/'s2_lincs';D=S/'data';O=R/'results';
s=pd.read_csv(next(D.glob('*sig_info*.gz')),sep='\t');m=pd.read_csv(next(D.glob('*sig_metrics*.gz')),sep='\t');x=s.merge(m,on=['sig_id','pert_id','pert_iname','pert_type'],how='left');x['distil_cc_q75']=pd.to_numeric(x.distil_cc_q75,errors='coerce').replace(-666,np.nan);x=x[(x.cell_id=='MCF7')&(x.pert_type=='trt_cp')&(x.pert_itime=='24 h')&x.distil_cc_q75.ge(.1)]
meta=x[['sig_id','pert_id','pert_iname','cell_id','pert_type','pert_idose','pert_itime','distil_cc_q75','distil_ss','tas','distil_nsample']].drop_duplicates('sig_id')
formal=pd.read_csv(S/'results'/'formal_signature_scores.csv');formal=formal[formal.scheme=='B'][['sig_id','WTCS']].merge(meta,on='sig_id').rename(columns={'pert_iname':'drug_name','pert_idose':'dose','pert_itime':'time'})
inc=pd.read_csv(O/'E03_q1_incremental_scores.csv')[['sig_id','WTCS']].merge(meta,on='sig_id').rename(columns={'pert_iname':'drug_name','pert_idose':'dose','pert_itime':'time'})
q1=pd.concat([formal,inc],ignore_index=True,sort=False);q2=formal[formal.distil_cc_q75.ge(.2)];q3=formal[formal.distil_cc_q75.ge(.3)]
rows=[]
for th,z in {0.1:q1,0.2:q2,0.3:q3}.items():
 z=z.copy(); agg=z.groupby(['pert_id','cell_id','dose','time']).agg(wtcs_median=('WTCS','median'),n_signatures=('sig_id','nunique'),drug_name=('drug_name','first')).reset_index();agg['threshold']=th;rows.append(agg)
allc=pd.concat(rows,ignore_index=True);allc.to_csv(O/'E03_qc_sensitivity.csv',index=False)
for th,z in allc.groupby('threshold'):print(th,z.n_signatures.sum(),z.pert_id.nunique(),len(z))

