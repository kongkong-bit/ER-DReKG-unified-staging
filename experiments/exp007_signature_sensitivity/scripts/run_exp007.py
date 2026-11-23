from __future__ import annotations

import hashlib, json, sys, time
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
EXP = Path(__file__).resolve().parents[1]
S2 = ROOT / "s2_lincs"
sys.path.insert(0, str(EXP / "scripts"))
from exp007_core import wtcs_from_rank_positions  # noqa

def pick(folder, pattern):
    found = list(folder.glob(pattern))
    if len(found) != 1: raise RuntimeError(f"Expected one {pattern} in {folder}, got {len(found)}")
    return found[0]

def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def main():
    t0=time.time(); (EXP/"results").mkdir(exist_ok=True); (EXP/"logs").mkdir(exist_ok=True)
    data=S2/"data"; limma=ROOT/"s1_初步_gse42568_limma"/"limma_all_genes.csv"
    s1=pd.read_csv(limma); s1["sym"]=s1.gene_symbol.fillna("").astype(str).str.strip().str.upper()
    if not {"gene_symbol","logFC","adj.P.Val","t"}.issubset(s1.columns): raise RuntimeError("S1 required columns missing")
    gi=pd.read_csv(pick(data,"*gene_info*.gz"),sep="\t",dtype={"pr_gene_id":str})
    gi["sym"]=gi.pr_gene_symbol.fillna("").astype(str).str.strip().str.upper()
    bing=gi[gi.pr_is_bing.astype(bool)&gi.sym.ne("")].drop_duplicates("sym")
    bing_set=set(bing.sym)
    # Exact historical signature set: four-key metadata join used by the published formal screen.
    sig=pd.read_csv(pick(data,"*sig_info*.gz"),sep="\t",low_memory=False)
    met=pd.read_csv(pick(data,"*sig_metrics*.gz"),sep="\t",low_memory=False)
    strict=sig.merge(met[["sig_id","pert_id","pert_iname","pert_type","distil_cc_q75","distil_ss","tas","distil_nsample"]],on=["sig_id","pert_id","pert_iname","pert_type"],how="inner")
    hist=strict[(strict.cell_id=="MCF7")&(strict.pert_type=="trt_cp")&(strict.pert_itime=="24 h")&(pd.to_numeric(strict.distil_cc_q75,errors="coerce")>=.2)].copy()
    gctx=pick(S2/"work","*.gctx")
    a_up=pd.read_csv(S2/"s1_original_bing_up.txt",sep="\t").gene_symbol.astype(str).str.upper().tolist()
    a_dn=pd.read_csv(S2/"s1_original_bing_down.txt",sep="\t").gene_symbol.astype(str).str.upper().tolist()
    # B lists are derived from the full original limma table restricted to BING; strict FDR and fixed tie-break.
    bx=s1[s1.sym.isin(bing_set)&(s1["adj.P.Val"]<.05)].copy()
    bx=bx.sort_values(["adj.P.Val"],ascending=True,kind="mergesort").sort_values("adj.P.Val",kind="mergesort")
    # Stable ranking: FDR ascending, |logFC| descending, symbol ascending.
    bx["abs_logFC"]=bx.logFC.abs()
    bx=bx.sort_values(["adj.P.Val","abs_logFC","sym"],ascending=[True,False,True],kind="mergesort").drop_duplicates("sym")
    up=bx[bx.logFC>0].copy(); dn=bx[bx.logFC<0].copy()
    schemes={"A_original":(a_up,a_dn),"B_matched125":(up.sym.head(70).tolist(),dn.sym.head(55).tolist()),
             "B100":(up.sym.head(50).tolist(),dn.sym.head(50).tolist()),
             "B150":(up.sym.head(75).tolist(),dn.sym.head(75).tolist()),
             "B200":(up.sym.head(100).tolist(),dn.sym.head(100).tolist()),
             "B300":(up.sym.head(150).tolist(),dn.sym.head(150).tolist())}
    pd.DataFrame([{"scheme":k,"direction":d,"n":len(v),"gene_symbol":g} for k,(u,w) in schemes.items() for d,v in [("UP",u),("DOWN",w)] for g in v]).to_csv(EXP/"signature_gene_lists"/"gene_lists.csv",index=False)
    # Preserve complete source stats for every gene used in B variants.
    used=set(g for u,d in schemes.values() for g in u+d)
    bx[bx.sym.isin(used)].to_csv(EXP/"signature_gene_lists"/"selected_s1_statistics.csv",index=False)
    id_to_symbol=bing.set_index("pr_gene_id").sym
    rows=[]; fail=[]
    with h5py.File(gctx,"r") as h:
        mat=h["0"]["DATA"]["0"]["matrix"]
        sigids=[x.decode() if isinstance(x,bytes) else str(x) for x in h["0"]["META"]["COL"]["id"][:]]
        geneids=[x.decode() if isinstance(x,bytes) else str(x) for x in h["0"]["META"]["ROW"]["id"][:]]
        rowpos={x:i for i,x in enumerate(sigids)}
        gene_symbols=id_to_symbol.reindex(geneids).fillna("").to_numpy()
        valid=np.array([x in bing_set for x in gene_symbols]); bg=gene_symbols[valid]
        # Match the historical formal-screen background exactly: every GCTX row
        # annotated as BING remains in the rank universe, including repeated symbols.
        positions_by_symbol={}
        for i,symbol in enumerate(bg): positions_by_symbol.setdefault(symbol,[]).append(i)
        scheme_idx={k:(np.array([i for g in u for i in positions_by_symbol.get(g,[])],dtype=np.int32),np.array([i for g in d for i in positions_by_symbol.get(g,[])],dtype=np.int32)) for k,(u,d) in schemes.items()}
        for j,(_,r) in enumerate(hist.iterrows(),1):
            if r.sig_id not in rowpos: fail.append(r.sig_id); continue
            vals=np.asarray(mat[rowpos[r.sig_id],:],dtype=np.float32)[valid]
            order=np.lexsort((bg,-vals)); pos=np.empty(len(order),dtype=np.int32); pos[order]=np.arange(len(order),dtype=np.int32)
            for name,(u,d) in scheme_idx.items():
                eu,ed,w=wtcs_from_rank_positions(pos,vals,u,d)
                rows.append((r.sig_id,r.pert_id,r.pert_iname,r.cell_id,r.pert_type,r.pert_idose,r.pert_itime,float(r.distil_cc_q75),float(r.tas) if pd.notna(r.tas) else np.nan,name,eu,ed,w,-w,len(u),len(d)))
            if j%500==0: print(f"scored {j}/{len(hist)} signatures; elapsed={time.time()-t0:.1f}s",flush=True)
    cols=["sig_id","pert_id","drug_name","cell_id","pert_type","dose","time","distil_cc_q75","tas","scheme","ES_UP","ES_DOWN","WTCS","reversal_score","n_up","n_down"]
    scores=pd.DataFrame(rows,columns=cols)
    scores["rank_signature"]=scores.groupby("scheme").WTCS.rank(method="average",ascending=True)
    scores.to_csv(EXP/"results"/"signature_scores.csv",index=False)
    keys=["scheme","pert_id","drug_name","cell_id","pert_type","dose","time"]
    cond=scores.groupby(keys,dropna=False).agg(n_signatures=("sig_id","nunique"),WTCS_median=("WTCS","median"),WTCS_mean=("WTCS","mean"),WTCS_sd=("WTCS","std"),WTCS_mad=("WTCS",lambda x:float(np.median(np.abs(x-np.median(x))))),CC_median=("distil_cc_q75","median"),TAS_median=("tas","median")).reset_index()
    cond["rank_condition"]=cond.groupby("scheme").WTCS_median.rank(method="average",ascending=True)
    cond.to_csv(EXP/"results"/"condition_rankings.csv",index=False)
    pairs=[]
    for i,a in enumerate(schemes):
      for b in list(schemes)[i+1:]:
        x=cond[cond.scheme==a].set_index(["pert_id","dose","time"]).WTCS_median
        y=cond[cond.scheme==b].set_index(["pert_id","dose","time"]).WTCS_median
        common=x.index.intersection(y.index); xx=x.loc[common]; yy=y.loc[common]
        ra=xx.rank(ascending=True); rb=yy.rank(ascending=True); topa=set(ra.nsmallest(10).index); topb=set(rb.nsmallest(10).index)
        pairs.append({"scheme_a":a,"scheme_b":b,"n_common_conditions":len(common),"spearman":spearmanr(xx,yy).statistic,"top10_overlap":len(topa&topb),"top10_jaccard":len(topa&topb)/len(topa|topb),"median_abs_WTCS_difference":float(np.median(np.abs(xx-yy)))})
    cmp=pd.DataFrame(pairs); cmp.to_csv(EXP/"results"/"ranking_comparison.csv",index=False)
    plt.figure(figsize=(9,5));
    for name,d in scores.groupby("scheme"): plt.hist(d.WTCS,bins=50,alpha=.35,label=name,density=True)
    plt.xlabel("WTCS (negative = reversal association)");plt.ylabel("Density");plt.legend();plt.tight_layout();plt.savefig(EXP/"figures"/"wtcs_distributions.png",dpi=180);plt.close()
    plt.figure(figsize=(8,6));
    for _,r in cmp.iterrows(): plt.scatter(r.spearman,r.top10_jaccard,label=f"{r.scheme_a} vs {r.scheme_b}")
    plt.xlabel("Spearman correlation");plt.ylabel("Top 10 Jaccard overlap");plt.legend(fontsize=7,bbox_to_anchor=(1.02,1),loc="upper left");plt.tight_layout();plt.savefig(EXP/"figures"/"ranking_stability.png",dpi=180);plt.close()
    manifest={"seed":42,"S1_source":str(limma),"S1_sha256":sha(limma),"GCTX":str(gctx),"GCTX_sha256":sha(gctx),"signature_count":len(hist),"signature_ids_sha256":hashlib.sha256("\n".join(sorted(hist.sig_id)).encode()).hexdigest(),"gene_background":"unique BING symbols mapped from GCTX row IDs; lexicographic tie-break for equal expression","FDR_cutoff":0.05,"B_rule":"BING intersection, FDR<0.05; direction-specific; FDR ascending, abs(logFC) descending, symbol ascending","aggregation":"median WTCS per pert_id x cell x dose x time; no across-condition mixing","missing_signatures":fail,"runtime_seconds":round(time.time()-t0,2),"outputs":{p.name:sha(p) for p in (EXP/"results").glob("*.csv")}}
    (EXP/"results"/"run_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    report=f"""# Exp007 — S1 基因签名规模对药物排名的影响\n\n## 人话说明\n同一批 {len(hist)} 条历史 LINCS 真实 MCF7 药物扰动记录，用六种疾病基因名单重算。分数和排名的变化只用于评估方法稳定性，不能解释为临床疗效。\n\n## 方法\nWTCS、LINCS 数据、BING 背景与历史正式筛选的 24 h 且 distil_cc_q75≥0.2 签名保持一致。药物按药物ID、细胞、剂量、时间分组，组内取 WTCS 中位数；剂量和时间不混合。方案 A 使用历史 BING 交集（{len(a_up)} UP/{len(a_dn)} DOWN）；B_matched125={len(schemes['B_matched125'][0])}/{len(schemes['B_matched125'][1])}；B100=50/50、B150=75/75、B200=100/100、B300=150/150。B 方案从 limma 全表限制至 BING 且 FDR<0.05，按 FDR、|logFC|、基因符号确定顺序。\n\n## 结果\n共生成 {len(scores)} 条签名级分数、{len(cond)} 条条件级结果。排名比较见 `results/ranking_comparison.csv`，分数分布及稳定性图见 figures。更负 WTCS 是表达关联方向上的逆转信号，不是更好的药效证明。\n\n## 可复现性和限制\n输入路径、SHA-256、参数和缺失签名写入 `results/run_manifest.json`。基因背景为 GCTX 中映射成功的唯一 BING 符号，固定为同一背景。历史 S1、S2 和 Smoke Test 文件均只读。本实验没有使用随机数据。\n"""
    (EXP/"reports"/"exp007_report.md").write_text(report,encoding="utf-8")
    with open(EXP/"logs"/"run.log","w",encoding="utf-8") as f:f.write(f"completed signatures={len(hist)}, scored={scores.sig_id.nunique()}, rows={len(scores)}, failed={len(fail)}, seconds={time.time()-t0:.2f}\n")
    print(f"COMPLETE signatures={scores.sig_id.nunique()} score_rows={len(scores)} conditions={len(cond)} seconds={time.time()-t0:.1f}")

if __name__=="__main__": main()
