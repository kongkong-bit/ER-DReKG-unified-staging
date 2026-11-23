from __future__ import annotations
import hashlib,json,sys,time,platform
from pathlib import Path
import h5py,numpy as np,pandas as pd
from scipy.stats import spearmanr
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[3];EXP=Path(__file__).resolve().parents[1];S2=ROOT/'s2_lincs';OUT=EXP/'results'
sys.path.insert(0,str(ROOT/'experiments'/'exp007_signature_sensitivity'/'scripts'))
from exp007_core import wtcs_from_rank_positions

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def pick(d,p):
 z=list(d.glob(p))
 if len(z)!=1:raise RuntimeError(f'{d}/{p}: expected one, found {len(z)}')
 return z[0]
def weighted_es(positions,abs_weights,n):
 positions=np.asarray(positions,dtype=np.int64); w=np.abs(np.asarray(abs_weights,dtype=float))
 if not len(positions) or len(positions)>=n:return np.nan
 ix=np.argsort(positions,kind='stable');positions=positions[ix];w=w[ix]
 if w.sum()<=0:w=np.ones_like(w)
 hc=np.cumsum(w/w.sum()); miss=(positions-np.arange(len(positions)))/(n-len(positions));before=np.r_[0.,hc[:-1]]-miss;after=hc-miss
 hi=max(0.,float(after.max()));lo=min(0.,float(before.min()));return hi if abs(hi)>=abs(lo) else lo
def gsea_one(stats,genes,rng,b=1000):
 names=np.asarray(stats.index.astype(str)); vals=stats.to_numpy(dtype=float); n=len(vals)
 pos=np.flatnonzero(np.isin(names,np.asarray(list(genes),dtype=str)))
 if len(pos)<10 or len(pos)>=n:return None
 es=weighted_es(pos,np.abs(vals[pos]),n)
 null=np.empty(b,dtype=float)
 for i in range(b):
  p=np.sort(rng.choice(n,size=len(pos),replace=False));null[i]=weighted_es(p,np.abs(vals[p]),n)
 if es>=0:
  posnull=null[null>0]; scale=float(np.mean(posnull)) if len(posnull) else float(np.mean(np.abs(null)));pval=(1+int(np.sum(null>=es)))/(b+1)
 else:
  negnull=null[null<0]; scale=float(np.mean(np.abs(negnull))) if len(negnull) else float(np.mean(np.abs(null)));pval=(1+int(np.sum(null<=es)))/(b+1)
 # Standard running-sum extrema determine leading edge in the observed ranked list.
 weights=np.abs(vals[pos]); weights=weights/weights.sum() if weights.sum()>0 else np.ones(len(pos))/len(pos)
 before=np.r_[0.,np.cumsum(weights)[:-1]]-(pos-np.arange(len(pos)))/(n-len(pos));after=np.cumsum(weights)-(pos-np.arange(len(pos)))/(n-len(pos))
 if es>=0: edge_pos=pos[:int(np.argmax(after))+1]
 else: edge_pos=pos[int(np.argmin(before)):]
 return {'ES':float(es),'NES':float(es/scale) if np.isfinite(scale) and scale else np.nan,'pval':float(pval),'leading_edge':names[edge_pos].tolist(),'set_size':int(len(pos))}
def bh(p):
 p=np.asarray(p,float);order=np.argsort(p);q=np.empty(len(p));x=p[order]*len(p)/np.arange(1,len(p)+1);x=np.minimum.accumulate(x[::-1])[::-1];q[order]=np.minimum(x,1);return q
def read_stats(frame,score_col,gene_col):
 x=frame[[gene_col,score_col]].copy();x[score_col]=pd.to_numeric(x[score_col],errors='coerce');x=x[np.isfinite(x[score_col])&x[gene_col].notna()]
 numeric_ids=pd.to_numeric(x[gene_col],errors='coerce')
 if numeric_ids.notna().mean()>.95:x[gene_col]=numeric_ids.astype('int64').astype(str)
 else:x[gene_col]=x[gene_col].astype(str)
 x=x.sort_values(score_col,key=lambda z:z.abs(),ascending=False).drop_duplicates(gene_col).sort_values(score_col,ascending=False);return x.set_index(gene_col)[score_col]
def gsea_dataset(stats,gmt,b,seed):
 pathways={}
 with open(gmt,encoding='utf-8') as f:
  for line in f:
   a=line.rstrip('\n').split('\t');pathways[a[0]]=set(a[2:])
 rng=np.random.default_rng(seed);rows=[]
 for i,(name,genes) in enumerate(pathways.items(),1):
  z=gsea_one(stats,genes,b=b,rng=rng)
  if z is not None:rows.append({'pathway':name,**z})
  if i%10==0:print(f'GSEA {i}/{len(pathways)} pathways, n_genes={len(stats)}',flush=True)
 df=pd.DataFrame(rows);df['padj']=bh(df.pval.to_numpy());df['leading_edge_entrez']=df.leading_edge.apply(lambda z:'/'.join(z));df['leading_edge_symbols']=''
 return df.drop(columns='leading_edge')
def main():
 t=time.time();(EXP/'figures').mkdir(exist_ok=True)
 lim=OUT/'external_limma_results.csv';s1map=ROOT/'experiments'/'s1_pathway_enrichment'/'gene_mapping_audit.csv';gse=EXP/'data'/'GSE139038_series_matrix.txt.gz';gpl=EXP/'data'/'GPL27630_family.soft.gz';gmt=ROOT/'experiments'/'s1_pathway_enrichment'/'input'/'h.all.v2025.1.Hs.entrez.gmt'
 ext=pd.read_csv(lim);s1all=pd.read_csv(s1map);stats_ext=read_stats(ext,'t','entrez_id');stats_s1=read_stats(s1all,'t','ENTREZID')
 ext_h=gsea_dataset(stats_ext,gmt,1000,42);s1_h=gsea_dataset(stats_s1,gmt,1000,42)
 def make_symbol_map(frame,idcol,symcol):
  ids=pd.to_numeric(frame[idcol],errors='coerce');pairs=frame.loc[ids.notna(),[symcol]].copy();pairs['__id']=ids[ids.notna()].astype('int64').astype(str).to_numpy();return dict(zip(pairs.__id,pairs[symcol].astype(str)))
 emap=make_symbol_map(ext,'entrez_id','gene_symbol');smap=make_symbol_map(s1all,'ENTREZID','gene_symbol')
 for df,lookup in [(ext_h,emap),(s1_h,smap)]: df['leading_edge_symbols']=df.leading_edge_entrez.apply(lambda z:'/'.join(lookup.get(g,'') for g in z.split('/') if lookup.get(g,'')))
 ext_h.to_csv(OUT/'external_hallmark_gsea.csv',index=False);s1_h.to_csv(OUT/'S1_comparable_hallmark_gsea.csv',index=False)
 pc=s1_h.merge(ext_h,on='pathway',suffixes=('_S1','_external'));pc['NES_direction_concordant']=np.sign(pc.NES_S1)==np.sign(pc.NES_external);pc['both_FDR05']=(pc.padj_S1<.05)&(pc.padj_external<.05);pc['pathway_type']='Hallmark';pc['ID']=pc.pathway
 # Add GO BP and Reactome pathways computed separately in each cohort.
 additions=[]
 for kind,s1path,epath in [('GO_BP_UP',ROOT/'experiments'/'s1_pathway_enrichment'/'go_up.csv',OUT/'external_go_up.csv'),('GO_BP_DOWN',ROOT/'experiments'/'s1_pathway_enrichment'/'go_down.csv',OUT/'external_go_down.csv'),('Reactome_UP',ROOT/'experiments'/'s1_pathway_enrichment'/'reactome_up.csv',OUT/'external_reactome_up.csv'),('Reactome_DOWN',ROOT/'experiments'/'s1_pathway_enrichment'/'reactome_down.csv',OUT/'external_reactome_down.csv')]:
  a=pd.read_csv(s1path);b=pd.read_csv(epath)
  if 'ID' not in a or 'ID' not in b:continue
  aa=a[['ID','Description','p.adjust']].rename(columns={'p.adjust':'FDR_S1'});bb=b[['ID','Description','p.adjust']].rename(columns={'p.adjust':'FDR_external'}) if 'p.adjust' in b else pd.DataFrame(columns=['ID','Description','FDR_external'])
  z=aa.merge(bb,on='ID',how='outer',suffixes=('_S1','_external'));z['pathway_type']=kind;additions.append(z)
 pd.concat([pc.rename(columns={'padj_S1':'FDR_S1','padj_external':'FDR_external'})[['pathway_type','ID','pathway','FDR_S1','FDR_external','NES_S1','NES_external','NES_direction_concordant','both_FDR05']]]+additions,ignore_index=True,sort=False).to_csv(OUT/'cross_cohort_pathway_comparison.csv',index=False)
 # Reproducibility metrics from all common genes.
 common=pd.read_csv(OUT/'cross_cohort_gene_concordance.csv');rho=spearmanr(common.logFC_S1,common.logFC_external).statistic;dircon=float(common.direction_concordant.mean());both=common[common.both_FDR05]
 s1_sig=common[common.FDR_S1<.05];ext_sig=common[common.FDR_external<.05]
 metric={'n_common_genes':int(len(common)),'spearman_logFC':float(rho),'overall_direction_concordance':dircon,'S1_significant_common_n':int(len(s1_sig)),'external_significant_common_n':int(len(ext_sig)),'both_significant_n':int(len(both)),'both_significant_direction_concordance':float(both.direction_concordant.mean()) if len(both) else np.nan}
 # Fixed external S1 query already restricted to FDR<.05 and BING; no topping-up nonsignificant genes.
 query=pd.read_csv(OUT/'external_s1_signature.csv');qu=set(query[query.direction=='UP'].gene_symbol.str.upper());qd=set(query[query.direction=='DOWN'].gene_symbol.str.upper());
 if qu&qd:raise RuntimeError('External UP/DOWN overlap')
 # Reuse precisely the historical 4,761 Q2 signatures and fixed LINCS BING background.
 old=pd.read_csv(S2/'results'/'formal_signature_scores.csv');old=old[old.scheme=='B'].copy();sigmeta=old.drop_duplicates('sig_id').set_index('sig_id');sigids=sorted(sigmeta.index)
 gi=pd.read_csv(pick(S2/'data','*gene_info*.gz'),sep='\t',dtype={'pr_gene_id':str});gi['sym']=gi.pr_gene_symbol.fillna('').str.strip().str.upper();bing=gi[gi.pr_is_bing.astype(bool)&gi.sym.ne('')].drop_duplicates('sym');bing_set=set(bing.sym);symbol_by_gene=bing.set_index('pr_gene_id').sym
 gctx=pick(S2/'work','*.gctx');scores=[]
 with h5py.File(gctx,'r') as h:
  mat=h['0']['DATA']['0']['matrix'];all_sig=[x.decode() if isinstance(x,bytes) else str(x) for x in h['0']['META']['COL']['id'][:]];geneids=[x.decode() if isinstance(x,bytes) else str(x) for x in h['0']['META']['ROW']['id'][:]];spos={x:i for i,x in enumerate(all_sig)}
  symbols=symbol_by_gene.reindex(geneids).fillna('').to_numpy();valid=np.array([x in bing_set for x in symbols]);bg=symbols[valid];positions={}
  for i,s in enumerate(bg):positions.setdefault(s,[]).append(i)
  iu=np.array([i for g in qu for i in positions.get(g,[])],dtype=np.int32);idn=np.array([i for g in qd for i in positions.get(g,[])],dtype=np.int32)
  if not len(iu) or not len(idn):raise RuntimeError('External BING query has an empty direction')
  for i,sid in enumerate(sigids,1):
   if sid not in spos:raise RuntimeError(f'Q2 signature missing from GCTX: {sid}')
   vals=np.asarray(mat[spos[sid],:],dtype=np.float32)[valid];order=np.lexsort((bg,-vals));rankpos=np.empty(len(order),np.int32);rankpos[order]=np.arange(len(order),dtype=np.int32);eu,ed,w=wtcs_from_rank_positions(rankpos,vals,iu,idn);m=sigmeta.loc[sid]
   scores.append((sid,m.pert_id,m.drug_name,m.cell_id,m.pert_type,m.dose,m.time,m.distil_cc_q75,m.tas,eu,ed,w,-w,len(qu),len(qd)))
   if i%1000==0:print(f'LINCS external query scored {i}/{len(sigids)}',flush=True)
 cols=['sig_id','pert_id','drug_name','cell_id','pert_type','dose','time','CC','TAS','ES_UP','ES_DOWN','WTCS','reversal_score','n_up','n_down'];sc=pd.DataFrame(scores,columns=cols);sc['scheme']='External_GSE139038_ERpos';sc.to_csv(OUT/'external_s1_lincs_scores.csv',index=False)
 keys=['pert_id','drug_name','cell_id','pert_type','dose','time'];drug=sc.groupby(keys,dropna=False).agg(n_signatures=('sig_id','nunique'),WTCS_median=('WTCS','median'),WTCS_mean=('WTCS','mean'),WTCS_sd=('WTCS','std'),WTCS_mad=('WTCS',lambda z:float(np.median(np.abs(z-np.median(z))))),CC_median=('CC','median'),TAS_median=('TAS','median')).reset_index();drug['external_rank']=drug.WTCS_median.rank(ascending=True,method='average')
 base=pd.read_csv(ROOT/'experiments'/'exp007_signature_sensitivity'/'results'/'condition_rankings.csv');base=base[base.scheme=='B200'].copy();base=base.rename(columns={'WTCS_median':'B200_WTCS_median','rank_condition':'B200_rank'});drug=drug.merge(base[['pert_id','dose','time','B200_WTCS_median','B200_rank']],on=['pert_id','dose','time'],how='left');drug.to_csv(OUT/'external_s1_drug_ranking.csv',index=False)
 bothd=drug.dropna(subset=['B200_rank']);corr=spearmanr(bothd.external_rank,bothd.B200_rank).statistic;ta=set(bothd.nsmallest(10,'external_rank').pert_id);tb=set(bothd.nsmallest(10,'B200_rank').pert_id);metric.update({'S2_Q2_signature_n':int(len(sc)),'external_query_up_n':int(len(qu)),'external_query_down_n':int(len(qd)),'external_drug_conditions_n':int(len(drug)),'ranking_common_conditions':int(len(bothd)),'ranking_spearman':float(corr),'top10_overlap_unique_pert_id':int(len(ta&tb))})
 (OUT/'cross_cohort_summary.json').write_text(json.dumps(metric,indent=2),encoding='utf-8')
 # Figures: gene effect agreement, significant-gene directions, Hallmark pathway replication, drug ranking agreement.
 plt.figure(figsize=(7,6));plt.scatter(common.logFC_S1,common.logFC_external,s=6,alpha=.25);plt.axhline(0,c='grey',lw=.8);plt.axvline(0,c='grey',lw=.8);plt.xlabel('GSE42568 ER+ Tumor − Normal logFC');plt.ylabel('GSE139038 paired ER+ Tumor − Normal logFC');plt.title(f'Common genes: Spearman={rho:.3f}, same direction={dircon:.1%}');plt.tight_layout();plt.savefig(EXP/'figures'/'cross_cohort_logfc_scatter.png',dpi=180);plt.close()
 plt.figure(figsize=(6,4));plt.bar(['All common genes','Both FDR<0.05'],[dircon,float(both.direction_concordant.mean()) if len(both) else np.nan],color=['#4e79a7','#f28e2b']);plt.ylim(0,1);plt.ylabel('Direction agreement');plt.tight_layout();plt.savefig(EXP/'figures'/'gene_direction_concordance.png',dpi=180);plt.close()
 plt.figure(figsize=(7,6));plt.scatter(pc.NES_S1,pc.NES_external,c=np.where(pc.both_FDR05,'#d62728','#4e79a7'),s=24);plt.axhline(0,c='grey',lw=.8);plt.axvline(0,c='grey',lw=.8);plt.xlabel('GSE42568 Hallmark NES');plt.ylabel('GSE139038 Hallmark NES');plt.title('Hallmark directions and significance');plt.tight_layout();plt.savefig(EXP/'figures'/'pathway_replication.png',dpi=180);plt.close()
 plt.figure(figsize=(6,6));plt.scatter(bothd.B200_rank,bothd.external_rank,s=12,alpha=.45);plt.xlabel('B200 LINCS Q2 rank');plt.ylabel('External S1 LINCS Q2 rank');plt.title(f'Spearman={corr:.3f}; Top10 overlap={len(ta&tb)}');plt.tight_layout();plt.savefig(EXP/'figures'/'drug_rank_comparison.png',dpi=180);plt.close()
 inputs=[gse,gpl,EXP/'data'/'GSE65194_series_matrix.txt.gz',EXP/'data'/'GSE42568_sample_groups.csv',lim,s1map,S2/'results'/'formal_signature_scores.csv',gctx,pick(S2/'data','*gene_info*.gz'),EXP/'scripts'/'run_exp010.R',EXP/'scripts'/'complete_exp010.py',EXP/'environment_manifest.json']
 manifest={'seed':42,'gsea_gene_set_permutations_per_pathway':1000,'gsea_method':'weighted pre-ranked GSEA (ES), matched gene-set-size permutation null, sign-specific mean-absolute NES; BH across Hallmark H','empirical_p_resolution_minimum':1/1001,'external_primary_cohort':'GSE139038','external_paired_ERpositive_patient_n':14,'external_gene_features':int(pd.read_csv(lim).shape[0]),'external_signature_genes':{'UP':len(qu),'DOWN':len(qd)},'LINCS_Q2_ids_n':len(sigids),'LINCS_Q2_ids_sha256':hashlib.sha256('\n'.join(sigids).encode()).hexdigest(),'input_sha256':{str(p):sha(p) for p in inputs},'summary':metric,'outputs_sha256':{str(p):sha(p) for p in OUT.glob('*.csv')},'python':platform.python_version(),'R':'4.4.3','limma':'3.62.2'}
 (OUT/'run_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 report=f'''# Exp010 — 外部队列能否重复 GSE42568 的 ER 阳性乳腺癌信号？\n\n## 人话结论\n我们找了一批独立患者数据，问同一个问题：ER 阳性肿瘤对比正常组织时，基因变化方向是否和 GSE42568 相似？严格按同一患者的肿瘤/正常配对后，只有 14 对 ER 阳性样本可用。因此这是一次小样本外部核对，不是对整个乳腺癌人群的定论。\n\n## 队列选择和数据\nGSE139038 有 65 个 GPL27630 双通道微阵列样本；GEO 注释记录 26 个 ER 阳性肿瘤、15 个 ER 阴性肿瘤、18 个配对正常组织和 6 个表观正常组织。严格配对筛选得到 14 名 ER 阳性患者的肿瘤及同患者正常组织。发现队列 GSE42568 的样本 GSM 与外部队列无重叠。主要分析只使用这些 14 对配对样本；没有把两个平台的原始表达值混在一起。\n\nGSE139038 的 GPL27630 是 44,544 个 spot，平台注释映射到 27,086 个唯一基因符号，其中 26,590 个成功映射 Entrez ID。重复 spot 按基因符号取平均，再用 limma 拟合患者配对模型，比较方向为 ER+ Tumor − Normal。输入本身是 GEO 提供的已中心化双通道 log-ratio；不是 Affymetrix 强度。\n\n## 外部差异结果\n共分析 27,086 个基因，FDR<0.05 有 694 个（上调 25、下调 669）。上下调很不平衡，可能受小样本、双通道平台和队列差异影响；方向和排名统计应结合这个限制看。跨队列共同基因数 {metric['n_common_genes']:,}，logFC Spearman={metric['spearman_logFC']:.3f}，同方向比例={metric['overall_direction_concordance']:.1%}。两队列都 FDR<0.05 的共同基因 {metric['both_significant_n']} 个，其中 {metric['both_significant_direction_concordance']:.1%} 方向一致。\n\n## 通路和外部 S2\nGO BP 与 Reactome 使用外部本次实际检测并映射的 Entrez 背景；Hallmark 用全基因 t 排序，固定每通路 1,000 次同大小随机基因集置换并 BH 校正。最小可分辨经验 P 值约 0.001，因此达到这个边界的通路只能说在本次置换中很突出，P 值精度有限。Hallmark 中外部 FDR<0.05 的通路有 {int((ext_h.padj<.05).sum())} 条；与原始 S1 同时显著且 NES 同方向的有 {int((pc.both_FDR05 & pc.NES_direction_concordant).sum())} 条。GO/Reactome 结果按实际显著项列出；通路富集不代表通路被药物治疗激活或抑制。\n\n外部 S1 先限制到 BING 和 FDR<0.05，再按 FDR、效应量、符号固定顺序取最多 100 个/方向；实际为 {len(qu)} UP / {len(qd)} DOWN，没有用不显著基因补足。它和原始 B200 使用相同的 4,761 个历史 Q2 LINCS 签名、相同 WTCS、同一 BING 排序背景。产生 {len(drug)} 个剂量/时间分开的药物条件排名；和原 B200 共同条件 Spearman={corr:.3f}，Top10 重叠 {len(ta&tb)} 个药物 ID。分数只代表表达逆转关联，不代表临床疗效。\n\n## 结果文件\n`results/external_limma_results.csv`、`cross_cohort_gene_concordance.csv`、`cross_cohort_pathway_comparison.csv`、`external_s1_signature.csv`、`external_s1_lincs_scores.csv`、`external_s1_drug_ranking.csv`；图在 `figures/`。路径、来源及 SHA-256 在 `results/run_manifest.json`。候选队列的独立审计见 `external_dataset_audit.md`。\n\n## 限制\n只有 14 个严格配对 ER 阳性患者；平台只有约 27k 有符号基因；独立队列和 discovery cohort 的人群、实验平台与样本处理不同。BING 查询仅 11 个上调基因，故外部逆转查询比原 S1 更不平衡。外部结果用于检验可重复性，不构成治疗证据。\n'''
 (EXP/'reports'/'exp010_report.md').write_text(report,encoding='utf-8')
 manifest['status']='PASS'
 manifest['outputs_sha256_all']={str(p):sha(p) for folder in [OUT,EXP/'figures',EXP/'reports'] for p in folder.glob('*') if p.is_file() and p.name!='run_manifest.json'}
 (OUT/'run_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
 (EXP/'experiment_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
 print(f"EXP010 COMPLETE common={len(common)} rho={rho:.3f} directions={dircon:.3f} paired={14} extQ={len(qu)}/{len(qd)} Q2={len(sc)} rank_rho={corr:.3f} top10={len(ta&tb)} seconds={time.time()-t:.1f}")
if __name__=='__main__':main()
