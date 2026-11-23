import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"exp007_signature_sensitivity"/"scripts"))
from methods import classic_ks,zhang_rank_score,xsum_score,bh_adjust

def test_classic_ks_orientation_and_same_direction_zero():
    ranked=["d1","d2","x","u1","u2"]
    assert classic_ks(ranked,{"u1","u2"},{"d1","d2"})[2] < 0
    assert classic_ks(["u1","d1","u2","d2"]+[f"x{i}" for i in range(6)],{"u1","u2"},{"d1","d2"})[2] == 0

def test_zhang_signed_rank_orientation():
    symbols=["u1","u2","d1","d2"]
    values=np.array([-4.,-3.,2.,1.])
    assert zhang_rank_score(symbols,values,{"u1","u2"},{"d1","d2"}) < 0
    assert zhang_rank_score(symbols,-values,{"u1","u2"},{"d1","d2"}) > 0

def test_xsum_orientation_and_bh():
    syms=["u","d","a","b"]; vals=np.array([-4.,4.,1.,-1.])
    assert xsum_score(syms,vals,{"u"},{"d"},top_n=2) < 0
    assert np.allclose(bh_adjust([.01,.04,.03]),[.03,.04,.04])
