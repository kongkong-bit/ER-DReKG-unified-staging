import importlib.util
from pathlib import Path
import numpy as np

script=Path(__file__).resolve().parents[1]/'scripts'/'complete_exp010.py'
spec=importlib.util.spec_from_file_location('complete_exp010',script); mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

def test_weighted_es_known_extremes():
    assert mod.weighted_es([0,1],[2,1],6)==1.0
    assert mod.weighted_es([4,5],[1,2],6)==-1.0

def test_numeric_entrez_ids_remain_integer_strings():
    import pandas as pd
    s=mod.read_stats(pd.DataFrame({'ENTREZ':[1234.0,np.nan,5678.0],'t':[2.0,3.0,-1.0]}),'t','ENTREZ')
    assert set(s.index)=={'1234','5678'}

def test_gsea_fixed_seed_is_reproducible():
    import pandas as pd
    st=pd.Series(np.arange(100,0,-1,dtype=float),index=[str(i) for i in range(100)])
    genes={str(i) for i in range(10)}
    a=mod.gsea_one(st,genes,np.random.default_rng(42),b=50)
    b=mod.gsea_one(st,genes,np.random.default_rng(42),b=50)
    assert a['ES']>0 and a['NES']>0 and a['pval']==b['pval'] and a['leading_edge']==b['leading_edge']
