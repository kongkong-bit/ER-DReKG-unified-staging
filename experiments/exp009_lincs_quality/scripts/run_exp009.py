from pathlib import Path
import sys,json,time,hashlib,platform
from datetime import datetime,timezone
import numpy as np,pandas as pd,h5py
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[3];EXP=Path(__file__).resolve().parents[1];S2=ROOT/"s2_lincs";DATA=S2/"data"
def pick(d,p):
 x=list(d.glob(p));
 if len(x)!=1:raise RuntimeError(f"Expected one {p}, got {len(x)}")
 return x[0]
def main():
 t=time.time();(EXP/"results").mkdir(exist_ok=True);(EXP/"figures").mkdir(exist_ok=True);(EXP/"reports").mkdir(exist_ok=True);(EXP/"logs").mkdir(exist_ok=True)
 sig=pd.read_csv(pick(DATA,"*sig_info*.gz"),sep="\t",low_memory=False);met=pd.read_csv(pick(DATA,"*sig_metrics*.gz"),sep="\t",low_memory=False)
 # Stable biological identifiers first; report perturbagen display-name disagreements separately.
 x=sig.merge(met[["sig_id","pert_id","pert_iname","pert_type","distil_cc_q75","distil_ss","tas","distil_nsample"]],on=["sig_id","pert_id","pert_type"],how="inner",suffixes=("_sig","_met"))
 for c in ["distil_cc_q75","distil_ss","tas","distil_nsample"]:x[c]=pd.to_numeric(x[c],errors="coerce").replace(-666,np.nan)
 mismatch=x.pert_iname_sig.fillna("").ne(x.pert_iname_met.fillna(""))
 base=x[(x.cell_id=="MCF7")&(x.pert_type=="trt_cp")].copy(); h24=base[base.pert_itime.eq("24 h")].copy()
 quality=[]
 for q in [.1,.2,.3]:
  z=h24[h24.distil_cc_q75.ge(q)]
  quality.append({"metric":"distil_cc_q75","threshold":q,"signatures":z.sig_id.nunique(),"compounds":z.pert_id.nunique(),"dose_strata":z.pert_idose.nunique(),"times":z.pert_itime.nunique()})
 z=h24[h24.tas.ge(.2)];quality.append({"metric":"TAS","threshold":.2,"signatures":z.sig_id.nunique(),"compounds":z.pert_id.nunique(),"dose_strata":z.pert_idose.nunique(),"times":z.pert_itime.nunique()})
 pd.DataFrame(quality).to_csv(EXP/"results"/"quality_threshold_counts.csv",index=False)
 strata=h24.groupby(["pert_itime","pert_idose"],dropna=False).agg(signatures=("sig_id","nunique"),compounds=("pert_id","nunique"),cc_median=("distil_cc_q75","median"),tas_median=("tas","median")).reset_index();strata.to_csv(EXP/"results"/"dose_time_quality_summary.csv",index=False)
 # Reproduce legacy four-key merge count and the display-name join bias.
 strict=sig.merge(met[["sig_id","pert_id","pert_iname","pert_type","distil_cc_q75","tas"]],on=["sig_id","pert_id","pert_iname","pert_type"],how="inner")
 strict24=strict[(strict.cell_id=="MCF7")&(strict.pert_type=="trt_cp")&(strict.pert_itime=="24 h")].copy();strict24["distil_cc_q75"]=pd.to_numeric(strict24.distil_cc_q75,errors="coerce")
 join_audit=pd.DataFrame([{"join":"stable sig_id+pert_id+pert_type","MCF7_trt_cp":len(base),"MCF7_trt_cp_24h":len(h24),"24h_CC_ge_0.2":int(h24.distil_cc_q75.ge(.2).sum()),"name_mismatches":int(mismatch.sum())},{"join":"legacy includes pert_iname","MCF7_trt_cp":int(((strict.cell_id=="MCF7")&(strict.pert_type=="trt_cp")).sum()),"MCF7_trt_cp_24h":len(strict24),"24h_CC_ge_0.2":int(strict24.distil_cc_q75.ge(.2).sum()),"name_mismatches":int(mismatch.sum())}]);join_audit.to_csv(EXP/"results"/"metadata_join_sensitivity.csv",index=False)
 # Audit TAS formula inputs. Official TAS uses sqrt(SS*max(CC,0)/978); distil_ss in this release
 # is a continuous field and is not automatically interchangeable with raw SS.
 both=h24[(h24.distil_cc_q75>0)&h24.tas.notna()&h24.distil_ss.notna()].copy();both["ss_implied_by_TAS"]=both.tas**2*978/both.distil_cc_q75
 formula=pd.DataFrame([{"n_rows":len(both),"frac_implied_SS_near_integer":float(np.mean(np.abs(both.ss_implied_by_TAS-np.round(both.ss_implied_by_TAS))<.02)),"distil_ss_median":float(both.distil_ss.median()),"implied_SS_median":float(both.ss_implied_by_TAS.median()),"correlation_distil_ss_vs_implied_SS":float(both.distil_ss.corr(both.ss_implied_by_TAS))}]);formula.to_csv(EXP/"results"/"tas_field_audit.csv",index=False)
 metric_rows=[]
 for col in ["distil_cc_q75","distil_ss","tas","distil_nsample"]:
  v=pd.to_numeric(h24[col],errors="coerce").dropna()
  metric_rows.append({"field":col,"n_nonmissing":len(v),"n_missing":int(h24[col].isna().sum()),"min":v.min() if len(v) else np.nan,"q25":v.quantile(.25) if len(v) else np.nan,"median":v.median() if len(v) else np.nan,"q75":v.quantile(.75) if len(v) else np.nan,"max":v.max() if len(v) else np.nan,"interpretation":"released LINCS field; distribution summarized without redefining metric"})
 pd.DataFrame(metric_rows).to_csv(EXP/"results"/"lincs_metric_audit.csv",index=False)
 pd.DataFrame([{"audit":"TAS recalculation","status":"NOT_PERFORMED","reason":"Released distil_ss could not be verified as the raw integer signature strength used in the cited TAS formula; supplied TAS retained unchanged.","diagnostic_n":int(formula.iloc[0].n_rows),"distil_ss_median":formula.iloc[0].distil_ss_median,"formula_implied_SS_median":formula.iloc[0].implied_SS_median,"implied_SS_near_integer_fraction":formula.iloc[0].frac_implied_SS_near_integer}]).to_csv(EXP/"results"/"tas_calculation_audit.csv",index=False)
 # Score B200 on the stable-ID 24h cohort once. Each threshold is a nested subset.
 g=pd.read_csv(pick(DATA,"*gene_info*.gz"),sep="\t",dtype={"pr_gene_id":str});g["sym"]=g.pr_gene_symbol.fillna("").str.strip().str.upper();bing=g[g.pr_is_bing.astype(bool)&g.sym.ne("")].drop_duplicates("sym");B=set(bing.sym)
 up=set(pd.read_csv(S2/"s1_bing_top100_up.txt",sep="\t").gene_symbol.str.upper());dn=set(pd.read_csv(S2/"s1_bing_top100_down.txt",sep="\t").gene_symbol.str.upper());gctx=pick(S2/"work","*.gctx");symby=bing.set_index("pr_gene_id").sym
 score=[]
 with h5py.File(gctx,"r") as h:
  mat=h["0"]["DATA"]["0"]["matrix"];ids=[z.decode() if isinstance(z,bytes) else str(z) for z in h["0"]["META"]["COL"]["id"][:]];gids=[z.decode() if isinstance(z,bytes) else str(z) for z in h["0"]["META"]["ROW"]["id"][:]];pos={z:i for i,z in enumerate(ids)}
  symbols=symby.reindex(gids).fillna("").to_numpy();valid=np.array([s in B for s in symbols]);bg=symbols[valid]; maps={}
  for i,s in enumerate(bg):maps.setdefault(s,[]).append(i)
  iu=np.array([i for s in up for i in maps.get(s,[])],np.int32);idn=np.array([i for s in dn for i in maps.get(s,[])],np.int32)
  # local equivalent of weighted KS; profile rank is fixed and no whole matrix is loaded.
  for i,(_,r) in enumerate(h24.iterrows(),1):
   if r.sig_id not in pos:continue
   v=np.asarray(mat[pos[r.sig_id],:],dtype=np.float32)[valid];order=np.lexsort((bg,-v));rp=np.empty(len(order),np.int32);rp[order]=np.arange(len(order));
   def es(ix):
    p=np.sort(rp[ix]);w=np.abs(v[ix]);w=w/w.sum() if w.sum()>0 else np.ones(len(ix))/len(ix);hc=np.cumsum(w);miss=(p-np.arange(len(p)))/(len(v)-len(p));before=np.r_[0.,hc[:-1]]-miss;after=hc-miss;hi=max(0.,float(after.max()));lo=min(0.,float(before.min()));return hi if abs(hi)>=abs(lo) else lo
   eu=es(iu);ed=es(idn);w=0. if np.sign(eu)==np.sign(ed) else (eu-ed)/2
   score.append((r.sig_id,r.pert_id,r.pert_iname_sig,r.pert_idose,r.pert_itime,r.distil_cc_q75,r.tas,eu,ed,w))
   if i%2000==0:print(f"quality scoring {i}/{len(h24)} elapsed={time.time()-t:.1f}s",flush=True)
 scores=pd.DataFrame(score,columns=["sig_id","pert_id","drug_name","dose","time","CC","TAS","ES_UP","ES_DOWN","WTCS"]);scores.to_csv(EXP/"results"/"B200_signature_scores_stable_id.csv",index=False)
 rankrows=[]
 for q in [.1,.2,.3]:
  d=scores[scores.CC.ge(q)].copy();condition=d.groupby(["pert_id","drug_name","dose","time"],dropna=False).agg(n_signatures=("sig_id","nunique"),WTCS_median=("WTCS","median"),WTCS_sd=("WTCS","std"),CC_median=("CC","median"),TAS_median=("TAS","median")).reset_index();condition["CC_threshold"]=q;condition["rank"]=condition.WTCS_median.rank(ascending=True,method="average");rankrows.append(condition)
 d=scores[scores.CC.ge(.2)&scores.TAS.ge(.2)].copy();condition=d.groupby(["pert_id","drug_name","dose","time"],dropna=False).agg(n_signatures=("sig_id","nunique"),WTCS_median=("WTCS","median"),WTCS_sd=("WTCS","std"),CC_median=("CC","median"),TAS_median=("TAS","median")).reset_index();condition["CC_threshold"]=.2;condition["TAS_threshold"]=.2;condition["rank"]=condition.WTCS_median.rank(ascending=True,method="average");rankrows.append(condition)
 allr=pd.concat(rankrows,ignore_index=True,sort=False);allr.to_csv(EXP/"results"/"quality_sensitivity_condition_rankings.csv",index=False)
 condpairs=[];base=allr[allr.CC_threshold.eq(.2)&allr.TAS_threshold.isna()].set_index(["pert_id","dose","time"]).WTCS_median
 for q in [.1,.3]:
  cur=allr[allr.CC_threshold.eq(q)].set_index(["pert_id","dose","time"]).WTCS_median;ix=base.index.intersection(cur.index);condpairs.append({"comparison":f"CC>=0.2 vs CC>={q}","common_conditions":len(ix),"spearman":base.loc[ix].corr(cur.loc[ix],method="spearman"),"top10_overlap":len(set(base.loc[ix].nsmallest(10).index)&set(cur.loc[ix].nsmallest(10).index))})
 cur=allr[allr.CC_threshold.eq(.2)&allr.TAS_threshold.eq(.2)].set_index(["pert_id","dose","time"]).WTCS_median;ix=base.index.intersection(cur.index);condpairs.append({"comparison":"CC>=0.2 vs CC>=0.2 and TAS>=0.2","common_conditions":len(ix),"spearman":base.loc[ix].corr(cur.loc[ix],method="spearman"),"top10_overlap":len(set(base.loc[ix].nsmallest(10).index)&set(cur.loc[ix].nsmallest(10).index))})
 pd.DataFrame(condpairs).to_csv(EXP/"results"/"quality_rank_comparison.csv",index=False)
 pd.DataFrame(quality).to_csv(EXP/"results"/"qc_threshold_comparison.csv",index=False)
 dsum=scores.groupby(["time","dose"],dropna=False).agg(signatures=("sig_id","nunique"),compounds=("pert_id","nunique"),CC_median=("CC","median"),TAS_median=("TAS","median"),WTCS_median=("WTCS","median")).reset_index()
 dsum.to_csv(EXP/"results"/"dose_condition_summary.csv",index=False)
 dose_stab=[];prim=allr[allr.CC_threshold.eq(.2)&allr.TAS_threshold.isna()]
 for tm,gg in prim.groupby("time"):
  doses=sorted(gg.dose.dropna().unique(),key=str)
  for i,a in enumerate(doses):
   for b in doses[i+1:]:
    aa=gg[gg.dose.eq(a)].set_index("pert_id").WTCS_median;bb=gg[gg.dose.eq(b)].set_index("pert_id").WTCS_median;ix=aa.index.intersection(bb.index)
    dose_stab.append({"time":tm,"dose_a":a,"dose_b":b,"shared_compounds":len(ix),"spearman_WTCS":aa.loc[ix].corr(bb.loc[ix],method="spearman") if len(ix)>1 else np.nan,"top10_overlap":len(set(aa.loc[ix].nsmallest(min(10,len(ix))).index)&set(bb.loc[ix].nsmallest(min(10,len(ix))).index)) if len(ix) else 0})
 pd.DataFrame(dose_stab).to_csv(EXP/"results"/"dose_direction_stability.csv",index=False)
 cand_path=ROOT/"experiments"/"exp006_ranking_reliability"/"results"/"candidate_drugs_all.csv"
 if cand_path.exists():
  cands=pd.read_csv(cand_path).rename(columns={"primary_dose":"dose","pert_time":"time"});primary=prim
  cand_cmp=cands.merge(primary[["pert_id","dose","time","WTCS_median","rank"]].rename(columns={"WTCS_median":"WTCS_CC02","rank":"rank_CC02"}),on=["pert_id","dose","time"],how="left",validate="one_to_one")
  for q,label in [(.1,"CC01"),(.3,"CC03")]:
   part=allr[allr.CC_threshold.eq(q)&allr.TAS_threshold.isna()][["pert_id","dose","time","WTCS_median","rank"]].rename(columns={"WTCS_median":f"WTCS_{label}","rank":f"rank_{label}"})
   cand_cmp=cand_cmp.merge(part,on=["pert_id","dose","time"],how="left",validate="one_to_one")
  part=allr[allr.CC_threshold.eq(.2)&allr.TAS_threshold.eq(.2)][["pert_id","dose","time","WTCS_median","rank"]].rename(columns={"WTCS_median":"WTCS_CC02_TAS02","rank":"rank_CC02_TAS02"})
  cand_cmp=cand_cmp.merge(part,on=["pert_id","dose","time"],how="left",validate="one_to_one")
  cand_cmp.to_csv(EXP/"results"/"candidate_quality_comparison.csv",index=False)
 plt.figure(figsize=(8,5));qs=pd.DataFrame(quality);plt.bar(qs.metric+" "+qs.threshold.astype(str),qs.signatures,color=["#4488aa","#337799","#225577","#cc8855"]);plt.xticks(rotation=25,ha="right");plt.ylabel("24 h signatures");plt.tight_layout();plt.savefig(EXP/"figures"/"quality_threshold_counts.png",dpi=180);plt.close()
 fig,ax=plt.subplots(figsize=(8,4.5),dpi=180)
 for col,color in [("distil_cc_q75","#3977a8"),("tas","#d1843b")]:
  v=pd.to_numeric(h24[col],errors="coerce").dropna();ax.hist(v,bins=40,alpha=.45,label=col,color=color)
 ax.set(xlabel="Released metric value",ylabel="24 h signature count",title="LINCS quality metric distributions");ax.legend();fig.tight_layout();fig.savefig(EXP/"figures"/"quality_metric_distributions.png");plt.close(fig)
 heat=prim.pivot_table(index="pert_id",columns="dose",values="WTCS_median",aggfunc="median")
 if not heat.empty:
  heat=heat.loc[heat.median(axis=1).sort_values().head(40).index]
  fig,ax=plt.subplots(figsize=(9,7),dpi=180);im=ax.imshow(heat.to_numpy(),aspect="auto",cmap="coolwarm",vmin=-1,vmax=1);ax.set_yticks(range(len(heat)),heat.index,fontsize=6);ax.set_xticks(range(len(heat.columns)),heat.columns,rotation=35,ha="right",fontsize=7);ax.set_title("Top 40 compound WTCS across doses (24 h, CC≥0.2)");fig.colorbar(im,ax=ax,label="Median WTCS");fig.tight_layout();fig.savefig(EXP/"figures"/"dose_wtcs_heatmap.png");plt.close(fig)
 report=f"""# Exp009 — 数据质量门槛会不会改变药物排名？\n\n## 人话说明\n把 LINCS 签名按重复实验一致性高低筛一遍，比较严格/宽松门槛下的药物排名；也检查官方提供的 TAS 分数。\n\n## 结果\n稳定 ID 合并得到 MCF7 化学扰动 {len(scores)} 条 24 h 可评分签名。主筛选为项目预设的 CC≥0.2；CC≥0.1、0.3 和额外 TAS≥0.2 仅用于敏感性比较。具体签名数/药物数见 `qc_threshold_comparison.csv`，分布见 `lincs_metric_audit.csv` 与图。`metadata_join_sensitivity.csv` 对照了历史把药物显示名称也加入连接条件的做法；显示名称拼写差异会丢掉真实 ID 匹配的签名。\n\n## CC 与 TAS 不是同一个门槛\n`distil_cc_q75` 描述重复签名一致性，CC≥0.2 是本项目选择的 QC 过滤值；它不是普适标准。TAS 是 Broad 的另一种综合活动分数，[CMap 2017 论文](https://doi.org/10.1016/j.cell.2017.10.049)在特定化合物筛选情境使用 TAS≥0.2，不能把该数值解释成 CC 阈值。我们保留 LINCS 发布的 TAS 原值，并只把 TAS≥0.2 作为单独的附加敏感性条件。由于发布字段 `distil_ss` 未能确认等于官方 TAS 公式中的原始 SS，本实验不重算 TAS，审计证据见 `tas_calculation_audit.csv`。\n\n## 剂量与结果边界\n所有结果按剂量与时间分别汇总；药物没有被挑选“最有利”的剂量作为总分。剂量间排序稳定性见 `dose_direction_stability.csv`，药物逐剂量分数热图见 figures。QC 影响排名只能说明筛选敏感性，WTCS 是表达逆转关联，不能证明细胞杀伤或临床有效。\n"""
 (EXP/"reports"/"exp009_report.md").write_text(report,encoding="utf-8")
 def sha(p):
  h=hashlib.sha256()
  with open(p,"rb") as f:
   for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
  return h.hexdigest()
 inputs=[pick(DATA,"*sig_info*.gz"),pick(DATA,"*sig_metrics*.gz"),pick(DATA,"*gene_info*.gz"),gctx,S2/"s1_bing_top100_up.txt",S2/"s1_bing_top100_down.txt"]
 manifest={"experiment":"Exp009 LINCS quality and dose sensitivity","run_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS","seed":42,"primary_cohort":"MCF7 trt_cp 24h; CC thresholds 0.1/0.2/0.3; TAS>=0.2","signature_rows_scored":len(scores),"quality_threshold_counts":quality,"input_sha256":{str(p):sha(p) for p in inputs},"output_sha256":{str(p):sha(p) for folder in [EXP/"results",EXP/"figures",EXP/"reports"] for p in folder.glob("*") if p.is_file() and p.name!="run_manifest.json"},"python":platform.python_version(),"runtime_seconds":round(time.time()-t,2)}
 (EXP/"results"/"run_manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
 (EXP/"experiment_manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
 print("COMPLETE",len(scores),"profile scores; seconds",round(time.time()-t,1))
if __name__=="__main__":main()
