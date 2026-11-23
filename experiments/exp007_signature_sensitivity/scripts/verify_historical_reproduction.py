from __future__ import annotations
import hashlib, json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
HIST=ROOT/"s2_lincs"/"results"/"formal_signature_scores.csv"
NEW=ROOT/"experiments"/"exp007_signature_sensitivity"/"results"/"signature_scores.csv"
OUT=ROOT/"experiments"/"exp007_signature_sensitivity"/"results"/"historical_reproduction_check.csv"

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for x in iter(lambda:f.read(1024*1024),b""):h.update(x)
    return h.hexdigest()

def main():
    h=pd.read_csv(HIST);n=pd.read_csv(NEW)
    pairs=[("A","A_original"),("B","B200")]
    rows=[]
    for old_scheme,new_scheme in pairs:
        a=h[h.scheme.eq(old_scheme)][["sig_id","pert_id","WTCS","ES_UP","ES_DOWN"]]
        b=n[n.scheme.eq(new_scheme)][["sig_id","pert_id","WTCS","ES_UP","ES_DOWN"]]
        m=a.merge(b,on=["sig_id","pert_id"],suffixes=("_historical","_recomputed"),validate="one_to_one")
        counts=len(m)
        rows.append({"historical_scheme":old_scheme,"recomputed_scheme":new_scheme,"historical_signatures":a.sig_id.nunique(),"recomputed_signatures":b.sig_id.nunique(),"exact_id_matches":counts,"missing_or_unmatched":max(a.sig_id.nunique(),b.sig_id.nunique())-counts,
          "max_abs_WTCS_difference":float((m.WTCS_historical-m.WTCS_recomputed).abs().max()),"max_abs_ES_UP_difference":float((m.ES_UP_historical-m.ES_UP_recomputed).abs().max()),"max_abs_ES_DOWN_difference":float((m.ES_DOWN_historical-m.ES_DOWN_recomputed).abs().max()),"mismatches_over_1e_10":int(((m.WTCS_historical-m.WTCS_recomputed).abs()>1e-10).sum()),"historical_sha256":sha(HIST),"recomputed_sha256":sha(NEW)})
    df=pd.DataFrame(rows);df.to_csv(OUT,index=False)
    manifest_path=OUT.with_name("run_manifest.json")
    if manifest_path.exists():
        manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["historical_reproduction_check"]={"file":OUT.name,"status":"PASS" if df.mismatches_over_1e_10.sum()==0 and (df.exact_id_matches==df.historical_signatures).all() else "FAIL","rows":rows}
        manifest_path.write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
        (OUT.parents[1]/"experiment_manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
    print(pd.DataFrame(rows).to_string(index=False))
if __name__=="__main__":main()
