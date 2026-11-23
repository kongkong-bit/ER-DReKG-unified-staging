from __future__ import annotations
import json,sys,time,hashlib
from pathlib import Path
import h5py,numpy as np,pandas as pd
from scipy.stats import spearmanr
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[3]; EXP=Path(__file__).resolve().parents[1]; S2=ROOT/"s2_lincs"
sys.path[:0]=[str(ROOT/"experiments"/"exp007_signature_sensitivity"/"scripts"),str(EXP/"scripts")]
from exp007_core import wtcs_from_rank_positions
from methods import classic_ks,zhang_rank_score,xsum_score
def pick(d,p):
 x=list(d.glob(p));
 if len(x)!=1:raise RuntimeError(f"{d} {p}: {len(x)} files")
 return x[0]
def main():
 t=time.time(); out=EXP/"results";out.mkdir(exist_ok=True); data=S2/"data"
 scores7=pd.read_csv(ROOT/"experiments"/"exp007_signature_sensitivity"/"results"/"signature_scores.csv")
 ids=sorted(scores7[scores7.scheme=="A_original"].sig_id.unique())
 gi=pd.read_csv(pick(data,"*gene_info*.gz"),sep="\t",dtype={"pr_gene_id":str});gi["sym"]=gi.pr_gene_symbol.fillna("").astype(str).str.strip().str.upper(); bing=gi[gi.pr_is_bing.astype(bool)&gi.sym.ne("")].drop_duplicates("sym"); B=set(bing.sym)
 aup=set(pd.read_csv(S2/"s1_original_bing_up.txt",sep="\t").gene_symbol.str.upper());adn=set(pd.read_csv(S2/"s1_original_bing_down.txt",sep="\t").gene_symbol.str.upper());bup=set(pd.read_csv(S2/"s1_bing_top100_up.txt",sep="\t").gene_symbol.str.upper());bdn=set(pd.read_csv(S2/"s1_bing_top100_down.txt",sep="\t").gene_symbol.str.upper())
 queries={"A_original":(aup,adn),"B200":(bup,bdn)}
 sig=pd.read_csv(pick(data,"*sig_info*.gz"),sep="\t",low_memory=False);met=pd.read_csv(pick(data,"*sig_metrics*.gz"),sep="\t",low_memory=False)
 meta=sig.merge(met[["sig_id","pert_id","pert_iname","pert_type","distil_cc_q75","tas"]],on=["sig_id","pert_id","pert_iname","pert_type"],how="inner").set_index("sig_id").loc[ids].reset_index()
 gctx=pick(S2/"work","*.gctx"); symbol_by_gene=bing.set_index("pr_gene_id").sym
 rr=[]
 with h5py.File(gctx,"r") as h:
  mat=h["0"]["DATA"]["0"]["matrix"]; sids=[x.decode() if isinstance(x,bytes) else str(x) for x in h["0"]["META"]["COL"]["id"][:]]; gids=[x.decode() if isinstance(x,bytes) else str(x) for x in h["0"]["META"]["ROW"]["id"][:]]; spos={s:i for i,s in enumerate(sids)}
  syms=symbol_by_gene.reindex(gids).fillna("").to_numpy(); valid=np.array([s in B for s in syms]); bg=syms[valid]
  for n,(_,m) in enumerate(meta.iterrows(),1):
   vals=np.asarray(mat[spos[m.sig_id],:],dtype=np.float32)[valid]; order=np.lexsort((bg,-vals)); rankpos=np.empty(len(order),dtype=np.int32);rankpos[order]=np.arange(len(order)); ranked=bg[order].tolist(); ranked_vals=vals[order]
   for scheme,(up,dn) in queries.items():
    iu=np.array([i for i,g in enumerate(bg) if g in up],dtype=np.int32); idn=np.array([i for i,g in enumerate(bg) if g in dn],dtype=np.int32)
    eu,ed,wt=wtcs_from_rank_positions(rankpos,vals,iu,idn)
    ku,kd,ks=classic_ks(ranked,up,dn)
    z=zhang_rank_score(bg,vals,up,dn); xs=xsum_score(bg,vals,up,dn,150)
    for method,value,esup,esdn in [("WTCS",wt,eu,ed),("Classic_KS",ks,ku,kd),("Zhang_signed_rank",z,np.nan,np.nan),("XSum_zscore_adaptation",xs,np.nan,np.nan)]:
     rr.append((m.sig_id,m.pert_id,m.pert_iname,m.pert_idose,m.pert_itime,float(m.distil_cc_q75),float(m.tas) if pd.notna(m.tas) else np.nan,scheme,method,esup,esdn,value,-value))
   if n%500==0:print(f"scored {n}/{len(meta)} signatures, {time.time()-t:.1f}s",flush=True)
 cols=["sig_id","pert_id","drug_name","dose","time","CC","TAS","scheme","method","ES_UP","ES_DOWN","score","reversal_score"]
 res=pd.DataFrame(rr,columns=cols);res.to_csv(out/"method_signature_scores.csv",index=False)
 keys=["scheme","method","pert_id","dose","time"]
 cond=res.groupby(keys,dropna=False).agg(n_signatures=("sig_id","nunique"),score_median=("score","median"),score_mean=("score","mean"),score_sd=("score","std")).reset_index();cond["rank"]=cond.groupby(["scheme","method"]).score_median.rank(ascending=True,method="average");cond.to_csv(out/"method_condition_scores.csv",index=False)
 cmp=[]
 for scheme in queries:
  p=cond[cond.scheme==scheme].pivot_table(index=["pert_id","dose","time"],columns="method",values="score_median")
  names=list(p.columns)
  for i,a in enumerate(names):
   for b in names[i+1:]:
    q=p[[a,b]].dropna();ta=set(q[a].nsmallest(10).index);tb=set(q[b].nsmallest(10).index)
    cmp.append({"scheme":scheme,"method_a":a,"method_b":b,"n_conditions":len(q),"spearman_score":spearmanr(q[a],q[b]).statistic,"top10_overlap":len(ta&tb),"top10_jaccard":len(ta&tb)/len(ta|tb),"median_abs_score_diff":float(np.median(np.abs(q[a]-q[b])))})
 pd.DataFrame(cmp).to_csv(out/"method_comparison.csv",index=False)
 plt.figure(figsize=(9,5));
 for m,d in cond[(cond.scheme=="B200")].groupby("method"):plt.hist(d.score_median,bins=45,alpha=.38,density=True,label=m)
 plt.xlabel("Condition median score (negative = reversal)");plt.ylabel("Density");plt.legend(fontsize=8);plt.tight_layout();plt.savefig(EXP/"figures"/"method_score_distributions.png",dpi=180);plt.close()
 manifest={"seed":42,"signature_ids":len(ids),"scheme_list_counts":{k:[len(x[0]),len(x[1])] for k,x in queries.items()},"source_format":"GSE70138 Level 5 COMPZ (normalized z-like scores), not raw log fold changes","WTCS":"Broad weighted KS; official-style raw WTCS retained","Classic_KS":"unweighted KS pair with zero if same-signed ES; signed score=ES_UP-ES_DOWN","Zhang":"signed absolute-rank dot product divided by max possible sum; rank-based adaptation to COMPZ","XSum":"top 150 absolute COMPZ values, signed sum; adaptation because input is COMPZ rather than original differential logFC","Tau":"not calculated: no independent disease-query reference collection Q_ref","ncs":"not calculated here; separate Exp008 gate required compatible matched reference cohort","runtime_seconds":round(time.time()-t,2)}
 (out/"method_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
 report=f"""# Exp008 — 换一把打分尺子，排名会不会变？\n\n## 人话说明\n同一批 {len(ids)} 条真实扰动签名分别用 WTCS、经典 KS、Zhang 排名分和 XSum 变体评分。负分代表与疾病方向相反的表达关联；不代表临床疗效。\n\n## 方法口径\nWTCS 使用 LINCS 官方加权 KS 定义。经典 KS 使用无权重 KS。Zhang 按基因扰动幅度绝对值排序后作带符号秩和。XSum 使用排名最靠前的 150 个基因做带符号求和。注意 GSE70138 Level 5 是 COMPZ 标准化 z 样分值，不是原论文使用的原始 logFC，因此 Zhang 和 XSum 在本项目中是明确标记的输入适配版本，不能声称逐字复刻原论文数据输入。\n\n## 结果与边界\n签名级和药物条件级结果见 results。所有方法使用同一批签名与同一 BING 基因背景；药物按剂量和时间分别汇总。没有把不同条件混在一起。Tau 未计算，因为没有独立的疾病查询参考集合；NCS 需额外确认匹配参考签名分布后另行计算。\n\n## 实验状态\n本报告完成方法对照；随机基因置换经验 P 值另作为独立步骤，不与 WTCS/NCS/Tau 混称。\n"""
 (EXP/"reports"/"exp008_report.md").write_text(report,encoding="utf-8");print(f"COMPLETE rows={len(res)} cond={len(cond)} seconds={time.time()-t:.1f}")
if __name__=="__main__":main()
