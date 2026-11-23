from __future__ import annotations
import numpy as np
from exp007_core import weighted_es_from_hits

def classic_ks(ranked_symbols, up, down):
    """Unweighted one-sided KS pair; positive is concordant, negative reversal."""
    idx={}
    for i,g in enumerate(ranked_symbols): idx.setdefault(g,[]).append(i)
    n=len(ranked_symbols)
    pu=np.array([i for g in up for i in idx.get(g,[])],dtype=int)
    pd=np.array([i for g in down for i in idx.get(g,[])],dtype=int)
    eu=weighted_es_from_hits(pu,np.ones(len(pu)),n); ed=weighted_es_from_hits(pd,np.ones(len(pd)),n)
    return eu,ed,(eu-ed if np.sign(eu)!=np.sign(ed) else 0.0)

def zhang_rank_score(symbols, values, up, down):
    """Signed absolute-rank dot product normalized to [-1,1]. Ties are stable."""
    order=np.lexsort((np.asarray(symbols),-np.abs(values)))
    rank=np.empty(len(order),dtype=float); rank[order]=np.arange(len(order),0,-1,dtype=float)
    signed=rank*np.sign(values)
    idx={}
    for i,g in enumerate(symbols): idx.setdefault(g,[]).append(i)
    upi=[i for g in up for i in idx.get(g,[])]; dni=[i for g in down for i in idx.get(g,[])]
    denom=sum(sorted(rank,reverse=True)[:len(upi)+len(dni)])
    if not denom:return float('nan')
    return float((signed[upi].sum()-signed[dni].sum())/denom)

def xsum_score(symbols, values, up, down, top_n=150):
    """XSum-style signed sum over top-|profile score| genes (z-score adaptation)."""
    order=np.lexsort((np.asarray(symbols),-np.abs(values)))[:min(top_n,len(values))]
    selected=set(order.tolist()); idx={}
    for i,g in enumerate(symbols): idx.setdefault(g,[]).append(i)
    upi=[i for g in up for i in idx.get(g,[]) if i in selected]
    dni=[i for g in down for i in idx.get(g,[]) if i in selected]
    return float(np.sum(values[upi])-np.sum(values[dni]))

def bh_adjust(p):
    p=np.asarray(p,dtype=float); n=len(p); order=np.argsort(p); q=np.empty(n); ranked=p[order]*n/np.arange(1,n+1); ranked=np.minimum.accumulate(ranked[::-1])[::-1];q[order]=np.minimum(ranked,1.0);return q
