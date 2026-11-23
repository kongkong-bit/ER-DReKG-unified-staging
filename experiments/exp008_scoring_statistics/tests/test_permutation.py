import sys
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"experiments"/"exp008_scoring_statistics"/"scripts"))
sys.path.insert(0,str(ROOT/"experiments"/"exp007_signature_sensitivity"/"scripts"))
from run_exp008_permutation import es_multi, wtcs_multi
from exp007_core import wtcs_from_rank_positions


def test_batched_es_matches_scalar_reference():
    rng=np.random.default_rng(71)
    n_sig,n_gene,n_perm=3,90,17
    values=rng.normal(size=(n_sig,n_gene)).astype(np.float32)
    rankpos=np.vstack([np.argsort(np.argsort(-v,kind="stable"),kind="stable") for v in values]).astype(np.int32)
    q=np.stack([rng.permutation(n_gene)[:12] for _ in range(n_perm)])
    got=es_multi(rankpos,values,q[:,:6])
    for s in range(n_sig):
        for p in range(n_perm):
            expected=wtcs_from_rank_positions(rankpos[s],values[s],q[p,:6],q[p,6:])[0]
            assert np.isclose(got[s,p],expected,atol=1e-7)


def test_batched_wtcs_direction_and_disjoint_random_queries():
    rng=np.random.default_rng(19)
    values=np.array([[4,3,2,1,-1,-2,-3,-4]],dtype=np.float32)
    rankpos=np.array([[6,7,4,5,2,3,0,1]],dtype=np.int32)
    up=np.array([[0,1],[1,2]],dtype=np.int32)
    down=np.array([[6,7],[5,7]],dtype=np.int32)
    score=wtcs_multi(rankpos,values,up,down)
    assert score.shape==(1,2)
    assert np.all(score<0)  # Disease UP genes are at the bottom; disease DOWN genes are at the top.
    assert all(set(a).isdisjoint(b) for a,b in zip(up,down))


def test_fixed_seed_random_query_generation_is_reproducible():
    def queries():
        rng=np.random.default_rng(8008)
        return np.stack([rng.permutation(250)[:200] for _ in range(25)])
    assert np.array_equal(queries(),queries())
    assert all(len(set(q[:100]).intersection(q[100:]))==0 for q in queries())
