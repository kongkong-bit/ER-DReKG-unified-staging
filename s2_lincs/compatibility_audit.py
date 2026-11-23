from pathlib import Path
import numpy as np, pandas as pd, h5py
from scipy.stats import spearmanr
from smoke import wtcs
R=Path(__file__).resolve().parent; D=R/'data'; O=R/'results'; O.mkdir(exist_ok=True)
g=pd.read_csv(next(D.glob('*gene_info*.gz')),sep='\t',dtype={'pr_gene_id':str}); g['sym']=g.pr_gene_symbol.fillna('').str.strip().str.upper(); g['bing']=g.pr_is_bing.astype(bool); g['lm']=g.pr_is_lm.astype(bool)
s=pd.read_csv(R.parent/'s1_初步_gse42568_limma'/'limma_all_genes.csv'); s['gene_symbol']=s.gene_symbol.str.upper()
up=pd.read_csv(R/'s1'/'s1_100_up.txt',sep='\t'); dn=pd.read_csv(R/'s1'/'s1_100_down.txt',sep='\t'); up.gene_symbol=up.gene_symbol.str.upper(); dn.gene_symbol=dn.gene_symbol.str.upper()
lookup=g[g.sym.ne('')].drop_duplicates('sym').set_index('sym'); audit=[]
for direction,df in [('UP',up),('DOWN',dn)]:
 for _,r in df.iterrows():
  x=lookup.loc[r.gene_symbol] if r.gene_symbol in lookup.index else None
  audit.append({'direction':direction,'gene_symbol':r.gene_symbol,'entrez_id':x.pr_gene_id if x is not None else '', 'match_type':'exact_symbol' if x is not None else 'unmatched','reason':'exact symbol' if x is not None else 'no exact symbol; LINCS gene_info has no alias field','LM':bool(x.lm) if x is not None else False,'BING':bool(x.bing) if x is not None else False,'AIG':not bool(x.bing) if x is not None else False,'logFC':r.logFC,'t':r.t,'adj.P.Val':r['adj.P.Val']})
a=pd.DataFrame(audit); a.to_csv(O/'gene_mapping_audit.csv',index=False)
spaces=[]
for name,mask in [('LM',g.lm),('BING',g.bing),('AIG_nonBING',~g.bing),('all_L1000',g.index==g.index)]:
 symbols=set(g.loc[mask,'sym'])
 for d,df in [('UP',up),('DOWN',dn)]:
  hit=set(df.gene_symbol)&symbols; spaces.append({'gene_space':name,'direction':d,'query_n':len(df),'matched_n':len(hit),'coverage':len(hit)/len(df),'matched_symbols':';'.join(sorted(hit))})
pd.DataFrame(spaces).to_csv(O/'gene_space_coverage.csv',index=False)
bing=set(g.loc[g.bing,'sym']); au=set(up.gene_symbol)&bing; ad=set(dn.gene_symbol)&bing
s=s[s.gene_symbol.isin(bing)&(s['adj.P.Val']<.05)]
bu=set(s[s.logFC>0].sort_values(['adj.P.Val','logFC'],ascending=[True,False]).head(100).gene_symbol); bd=set(s[s.logFC<0].sort_values(['adj.P.Val','logFC'],ascending=[True,True]).head(100).gene_symbol)
for stem,sets in [('s1_original_bing',(au,ad)),('s1_bing_top100',(bu,bd))]:
 for label,ss in zip(('up','down'),sets):
  src=pd.read_csv(R.parent/'s1_初步_gse42568_limma'/'limma_all_genes.csv'); src=src[src.gene_symbol.str.upper().isin(ss)][['gene_symbol','logFC','t','adj.P.Val']]; src.to_csv(R/f'{stem}_{label}.txt',sep='\t',index=False)
sig=pd.read_csv(R/'metadata'/'smoke_selected_signatures.csv'); gp=next((R/'work').glob('*.gctx')); scores=[]
with h5py.File(gp,'r') as h:
 m=h['0']['DATA']['0']['matrix']; ids=[z.decode() for z in h['0']['META']['COL']['id'][:]]; gids=[z.decode() for z in h['0']['META']['ROW']['id'][:]]; gm=g.set_index('pr_gene_id').reindex(gids); sy=gm.sym.to_numpy(); keep=gm.bing.fillna(False).to_numpy()&(sy!=''); bg=sy[keep]; ix={z:i for i,z in enumerate(ids)}
 for sid in sig.sig_id:
  vec=np.asarray(m[ix[sid],:],float)[keep]; f=pd.DataFrame({'gene':bg,'v':vec}).groupby('gene',as_index=False).v.mean().sort_values(['v','gene'],ascending=[False,True]); rank=f.gene.tolist(); w=dict(zip(f.gene,f.v))
  for scheme,u,d in [('A',au,ad),('B',bu,bd)]:
   eu,ed,wt=wtcs(rank,w,u,d); scores.append({'sig_id':sid,'scheme':scheme,'n_up':len(u),'n_down':len(d),'ES_UP':eu,'ES_DOWN':ed,'WTCS':wt,'reversal_score':-wt})
x=pd.DataFrame(scores); x['rank']=x.groupby('scheme').WTCS.rank(method='average'); x.to_csv(O/'wtcs_method_comparison.csv',index=False); p=x.pivot(index='sig_id',columns='scheme',values='WTCS'); rr=x.pivot(index='sig_id',columns='scheme',values='rank'); rho=spearmanr(rr.A,rr.B).statistic; top=set(rr[rr.A<=10].index)&set(rr[rr.B<=10].index)
report=f'''# S1 BING compatibility and WTCS comparison\n\n## Method provenance\nCMap WTCS follows Subramanian et al. 2017: weighted KS enrichment of UP and DOWN lists, combined as (ES_UP - ES_DOWN)/2 when signs differ and zero otherwise. Lim & Pavlidis 2021 describe BING-only queries and 10–150 genes per direction. Both here are literature methods. Project-specific settings are A=original Top 100 clipped to BING and B=FDR<0.05 full limma list restricted to BING then separately ranked by adjusted P ascending and absolute logFC descending.\n\n## Mapping\nExact official symbol matches {int((a.match_type=='exact_symbol').sum())}/200. Supplied gene_info contains Entrez, symbol, title, LM, BING but no alias/synonym field, so unmatched symbols cannot be alias-resolved from supplied annotations. LINCS counts: LM {int(g.lm.sum())}, BING {int(g.bing.sum())}, AIG/non-BING {int((~g.bing).sum())}.\n\nA sizes UP/DOWN {len(au)}/{len(ad)}. B sizes {len(bu)}/{len(bd)}.\n\n## Comparison\nSame {len(sig)} signatures, same BING ranked background ({len(bg)} unique genes), same score vectors and WTCS implementation. Spearman rank correlation {rho:.4f}; Top-10 overlap {len(top)}/10; mean absolute WTCS difference {np.mean(np.abs(p.A-p.B)):.4f}; maximum {np.max(np.abs(p.A-p.B)):.4f}. Changes come from query membership and list sizes. This 30-signature smoke test does not show B is superior. More negative WTCS is inverse connectivity, not evidence of efficacy.\n'''
(R/'reports'/'s1_bing_comparison_report.md').write_text(report,encoding='utf-8'); print({'mapped':int((a.match_type=='exact_symbol').sum()),'A':(len(au),len(ad)),'B':(len(bu),len(bd)),'signatures':len(sig),'rho':rho,'top10':len(top),'background':len(bg)})
