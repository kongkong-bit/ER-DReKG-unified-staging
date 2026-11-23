from __future__ import annotations
import argparse, hashlib, json, sys, time
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy.stats import beta

ROOT=Path(__file__).resolve().parents[3]
EXP=Path(__file__).resolve().parents[1]
S2=ROOT/"s2_lincs"
sys.path.insert(0,str(ROOT/"experiments"/"exp007_signature_sensitivity"/"scripts"))
from exp007_core import weighted_es_from_hits

SEED=8008

def txt(x): return x.decode() if isinstance(x,bytes) else str(x)

def es_batch(pos: np.ndarray, values: np.ndarray, n_genes: int) -> np.ndarray:
    """Weighted KS ES for rows of equally sized random hit sets; matches scalar CMap walk."""
    b,k=pos.shape
    order=np.argsort(pos,axis=1,kind="stable")
    p=np.take_along_axis(pos,order,axis=1)
    w=np.take_along_axis(np.abs(values),order,axis=1)
    totals=w.sum(axis=1,keepdims=True)
    w=np.divide(w,totals,out=np.full_like(w,1.0/k,dtype=np.float64),where=totals>0)
    cum=np.cumsum(w,axis=1)
    miss=(p-np.arange(k)[None,:])/(n_genes-k)
    before=np.concatenate([np.zeros((b,1)),cum[:,:-1]],axis=1)-miss
    after=cum-miss
    hi=np.maximum(0,after.max(axis=1)); lo=np.minimum(0,before.min(axis=1))
    return np.where(np.abs(hi)>=np.abs(lo),hi,lo)

def wtcs_batch(rankpos: np.ndarray, vals: np.ndarray, up: np.ndarray, down: np.ndarray) -> np.ndarray:
    n=len(rankpos)
    eu=es_batch(rankpos[up],vals[up],n)
    ed=es_batch(rankpos[down],vals[down],n)
    return np.where(np.sign(eu)==np.sign(ed),0.0,(eu-ed)/2.0)

def es_multi(rankpos: np.ndarray, values: np.ndarray, qidx: np.ndarray) -> np.ndarray:
    """Return ES for signatures × shared random sets using bounded 3-D chunks."""
    n=rankpos.shape[1]; k=qidx.shape[1]
    pos=rankpos[:,qidx]
    w=np.abs(values[:,qidx])
    order=np.argsort(pos,axis=2,kind="stable")
    p=np.take_along_axis(pos,order,axis=2)
    w=np.take_along_axis(w,order,axis=2)
    totals=w.sum(axis=2,keepdims=True)
    w=np.divide(w,totals,out=np.full_like(w,1.0/k,dtype=np.float64),where=totals>0)
    cum=np.cumsum(w,axis=2)
    miss=(p-np.arange(k)[None,None,:])/(n-k)
    before=np.concatenate([np.zeros((len(rankpos),qidx.shape[0],1)),cum[:,:,:-1]],axis=2)-miss
    after=cum-miss
    hi=np.maximum(0,after.max(axis=2)); lo=np.minimum(0,before.min(axis=2))
    return np.where(np.abs(hi)>=np.abs(lo),hi,lo)

def wtcs_multi(rankpos: np.ndarray, values: np.ndarray, up: np.ndarray, down: np.ndarray) -> np.ndarray:
    eu=es_multi(rankpos,values,up); ed=es_multi(rankpos,values,down)
    return np.where(np.sign(eu)==np.sign(ed),0.0,(eu-ed)/2.0)

def bh(p: np.ndarray) -> np.ndarray:
    p=np.asarray(p,float); n=len(p); order=np.argsort(p); q=np.empty(n,float)
    vals=p[order]*n/(np.arange(n)+1); vals=np.minimum.accumulate(vals[::-1])[::-1]
    q[order]=np.minimum(vals,1.0); return q

def run(n_perm:int, n_sig:int|None, output_suffix:str=""):
    start=time.time(); resdir=EXP/"results"; data=S2/"data"; work=S2/"work"
    outdir=resdir if not output_suffix else resdir/output_suffix
    outdir.mkdir(parents=True,exist_ok=True)
    score7=pd.read_csv(ROOT/"experiments"/"exp007_signature_sensitivity"/"results"/"signature_scores.csv")
    base=score7[score7.scheme.eq("A_original")].drop_duplicates("sig_id").copy()
    if n_sig: base=base.iloc[:n_sig].copy()
    sigids=base.sig_id.astype(str).tolist()
    # Keep the exact S1 symbol sets and use the same BING row background as Exp007's official score.
    queries={"A_original":(set(pd.read_csv(S2/"s1_original_bing_up.txt",sep="\t").gene_symbol.str.upper()),set(pd.read_csv(S2/"s1_original_bing_down.txt",sep="\t").gene_symbol.str.upper())),
             "B200":(set(pd.read_csv(S2/"s1_bing_top100_up.txt",sep="\t").gene_symbol.str.upper()),set(pd.read_csv(S2/"s1_bing_top100_down.txt",sep="\t").gene_symbol.str.upper()))}
    gi=pd.read_csv(next(data.glob("*gene_info*.gz")),sep="\t",dtype={"pr_gene_id":str})
    gi["symbol"]=gi.pr_gene_symbol.fillna("").astype(str).str.strip().str.upper()
    bing=gi[gi.pr_is_bing.astype(bool)&gi.symbol.ne("")].copy()
    symbols=bing.symbol.to_numpy(); geneids=bing.pr_gene_id.astype(str).to_numpy()
    rng=np.random.default_rng(SEED)
    qidx={}
    q_sizes={}
    for scheme,(upset,dnset) in queries.items():
        nu=len(upset); nd=len(dnset); q_sizes[scheme]=(nu,nd)
    gctx=next(work.glob("*.gctx"))
    with h5py.File(gctx,"r") as h:
        mat=h["0"]["DATA"]["0"]["matrix"]
        sig_order=[txt(v) for v in h["0"]["META"]["COL"]["id"][:]]
        gene_order=[txt(v) for v in h["0"]["META"]["ROW"]["id"][:]]
        spos={s:i for i,s in enumerate(sig_order)}
        bing_pos={g:i for i,g in enumerate(geneids)}
        matrix_idx=np.array([bing_pos.get(g,-1) for g in gene_order],dtype=int)
        valid=matrix_idx>=0
        matrix_idx=matrix_idx[valid]
        bg_symbols=symbols[matrix_idx]
        n_bg=len(matrix_idx)
        if n_bg != len(symbols): raise ValueError(f"BING gene_info/GCTX count mismatch: {len(symbols)} vs {n_bg}")
        for scheme,(nu,nd) in q_sizes.items():
            q=np.empty((n_perm,nu+nd),dtype=np.int32)
            # Draw unique BING row positions; UP and DOWN are disjoint by construction.
            for i in range(n_perm): q[i]=rng.permutation(n_bg)[:nu+nd]
            qidx[scheme]=(q[:,:nu],q[:,nu:])
        actual_sig=[]
        null={scheme:np.full((len(sigids),n_perm),np.nan,dtype=np.float32) for scheme in queries}
        actual_sig=list(sigids)
        for start_idx in range(0,len(sigids),8):
            batch_ids=sigids[start_idx:start_idx+8]
            row_ids=np.array([spos[sid] for sid in batch_ids],dtype=int)
            # HDF5 fancy indexing requires monotonically increasing row indices.
            sort_ix=np.argsort(row_ids); sorted_rows=row_ids[sort_ix]
            values_sorted=np.asarray(mat[sorted_rows,:],dtype=np.float32)[:,valid]
            inv=np.argsort(sort_ix); values=values_sorted[inv]
            # Same deterministic descending rank and tie-break used by Exp007.
            symkeys=np.broadcast_to(bg_symbols,(len(values),n_bg))
            order=np.lexsort((symkeys,-values),axis=1)
            rankpos=np.argsort(order,axis=1).astype(np.int32)
            for scheme in queries:
                up_rand,dn_rand=qidx[scheme]
                null[scheme][start_idx:start_idx+len(batch_ids),:]=wtcs_multi(rankpos,values,up_rand,dn_rand).astype(np.float32)
            if (start_idx+len(batch_ids))%100<8: print(f"permuted {min(start_idx+8,len(sigids))}/{len(sigids)} signatures",flush=True)
    meta=base.set_index("sig_id").loc[actual_sig].reset_index()
    all_rows=[]
    summaries=[]
    for scheme in queries:
        # Observed and null statistic are both medians across signatures within compound × dose × time.
        obs=meta.copy()
        score_scheme=score7[(score7.scheme==scheme)&score7.sig_id.isin(actual_sig)].drop_duplicates("sig_id").set_index("sig_id").loc[actual_sig]
        obs["observed_WTCS"]=score_scheme.WTCS.to_numpy()
        group_cols=["pert_id","cell_id","dose","time"]
        for _,g in obs.groupby(group_cols,dropna=False,sort=False):
            ids=g.index.to_numpy()
            row=g.iloc[0]
            observed=float(np.median(g.observed_WTCS))
            null_cond=np.nanmedian(null[scheme][ids,:],axis=0)
            p=(1+int(np.sum(null_cond<=observed)))/(n_perm+1)
            all_rows.append({"scheme":scheme,"pert_id":row.pert_id,"drug_name":row.drug_name,"cell_id":row.cell_id,"dose":row.dose,"time":row.time,"n_signatures":len(g),"observed_WTCS":observed,"empirical_pvalue":p,"permutation_count":n_perm,"null_mean":float(np.mean(null_cond)),"null_sd":float(np.std(null_cond,ddof=1)),"null_q025":float(np.quantile(null_cond,.025)),"null_q50":float(np.quantile(null_cond,.5)),"null_q975":float(np.quantile(null_cond,.975))})
            summaries.append({"scheme":scheme,"pert_id":row.pert_id,"dose":row.dose,"time":row.time,"null_mean":float(np.mean(null_cond)),"null_sd":float(np.std(null_cond,ddof=1)),"null_q025":float(np.quantile(null_cond,.025)),"null_q50":float(np.quantile(null_cond,.5)),"null_q975":float(np.quantile(null_cond,.975)),"permutation_count":n_perm})
    tab=pd.DataFrame(all_rows)
    tab["adjusted_pvalue"]=np.nan
    for scheme,ix in tab.groupby("scheme").groups.items(): tab.loc[ix,"adjusted_pvalue"]=bh(tab.loc[ix,"empirical_pvalue"].to_numpy())
    tab.to_csv(outdir/"empirical_pvalues.csv",index=False)
    tab.to_csv(outdir/"statistical_significance.csv",index=False)
    pd.DataFrame(summaries).to_csv(outdir/"permutation_null_summary.csv",index=False)
    if not n_sig:
        top_b=pd.read_csv(resdir/"method_condition_scores.csv")
        top_b=top_b[(top_b.scheme.eq("B200"))&(top_b.method.eq("WTCS"))].nsmallest(10,"score_median")
        top_keys={(str(x.pert_id),str(x.dose),str(x.time)) for x in top_b.itertuples()}
        selected=[]
        # Re-create the random query statistics for the ten most negative observed B200 conditions
        # from the saved per-condition null moments is impossible; recompute their exact per-query
        # null medians while the signature-level null tensor is still available.
        base_index=meta.reset_index(drop=True)
        for _,g in base_index.groupby(["pert_id","cell_id","dose","time"],dropna=False,sort=False):
            row=g.iloc[0]; key=(str(row.pert_id),str(row.dose),str(row.time))
            if key in top_keys:
                ix=g.index.to_numpy()
                null_cond=np.nanmedian(null["B200"][ix,:],axis=0)
                selected.extend({"pert_id":row.pert_id,"drug_name":row.drug_name,"cell_id":row.cell_id,"dose":row.dose,"time":row.time,"permutation":i+1,"null_WTCS":float(v)} for i,v in enumerate(null_cond))
        pd.DataFrame(selected).to_csv(outdir/"candidate_null_distribution_top10.csv",index=False)
    manifest={"seed":SEED,"permutation_count":n_perm,"signature_count":len(sigids),"status":"PILOT_ONLY" if n_sig else "PASS","gene_background":"all BING GCTX rows in historical Exp007 scoring background","query_counts":{k:{"up_symbols":len(v[0]),"down_symbols":len(v[1])} for k,v in queries.items()},"disjoint_within_query":True,"random_query_shared_across_signatures":True,"statistic":"median WTCS within perturbagen × dose × time; one-sided lower tail","runtime_seconds":round(time.time()-start,2)}
    manifest["input_sha256"]={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [gctx,next(data.glob("*gene_info*.gz")),S2/"s1_original_bing_up.txt",S2/"s1_original_bing_down.txt",S2/"s1_bing_top100_up.txt",S2/"s1_bing_top100_down.txt",ROOT/"experiments"/"exp007_signature_sensitivity"/"results"/"signature_scores.csv"]}
    (outdir/"permutation_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps({"status":manifest["status"],"n_perm":n_perm,"signatures":len(sigids),"conditions":len(tab),"runtime_seconds":manifest["runtime_seconds"]},indent=2))

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--pilot",action="store_true");args=parser.parse_args()
    run(50 if args.pilot else 2000,40 if args.pilot else None,"permutation_pilot" if args.pilot else "")
