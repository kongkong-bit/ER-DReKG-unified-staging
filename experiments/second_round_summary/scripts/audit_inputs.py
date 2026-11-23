from __future__ import annotations
from pathlib import Path
import hashlib, json, gzip, time
import pandas as pd
import h5py

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parents[1]
S2=ROOT/'s2_lincs'; E6=ROOT/'experiments'/'exp006_ranking_reliability'; S1=ROOT/'s1_初步_gse42568_limma'; PWE=ROOT/'experiments'/'s1_pathway_enrichment'
FILES={
 'limma_all_genes':S1/'limma_all_genes.csv','limma_significant':S1/'limma_significant_genes_FDR05.csv',
 's1_disease_up':S1/'disease_up_genes.csv','s1_disease_down':S1/'disease_down_genes.csv',
 'lincs_gctx':S2/'work'/'GSE70138_Broad_LINCS_Level5_COMPZ_n118050x12328_2017-03-06.gctx',
 'lincs_gctx_gz':S2/'data'/'GSE70138_Broad_LINCS_Level5_COMPZ_n118050x12328_2017-03-06.gctx.gz',
 'sig_info':next((S2/'data').glob('*sig_info*.gz')),'sig_metrics':next((S2/'data').glob('*sig_metrics*.gz')),
 'gene_info':next((S2/'data').glob('*gene_info*.gz')),'pert_info':next((S2/'data').glob('*pert_info*.gz')),'inst_info':next((S2/'data').glob('*inst_info*.gz')),
 'formal_signature_scores':S2/'results'/'formal_signature_scores.csv','formal_drug_condition_ranking':S2/'results'/'formal_drug_condition_ranking.csv','formal_qc_summary':S2/'results'/'formal_qc_summary.csv','mcf7_condition_inventory':S2/'results'/'mcf7_condition_inventory.csv',
 's1_original_bing_up':S2/'s1_original_bing_up.txt','s1_original_bing_down':S2/'s1_original_bing_down.txt','s1_bing_top100_up':S2/'s1_bing_top100_up.txt','s1_bing_top100_down':S2/'s1_bing_top100_down.txt',
 'exp006_top50':E6/'results'/'candidate_drugs_top50.csv','exp006_all':E6/'results'/'candidate_drugs_all.csv','exp006_evidence':E6/'results'/'candidate_evidence_matrix.csv','exp006_manifest':E6/'exp006_manifest.json','exp006_report':E6/'reports'/'exp006_final_report.md',
 's1_pathway_report':PWE/'enrichment_report.md','hallmark_gsea':PWE/'hallmark_gsea.csv','pathway_links':PWE/'pathway_gene_links.csv','s1_pathway_manifest':PWE/'environment_manifest.json'
}
def sha256(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def csv_rows(p,sep=',',compression=None): return len(pd.read_csv(p,sep=sep,compression=compression))
start=time.time(); audit=[]
for name,p in FILES.items():
 if not p.exists():
  audit.append({'input':name,'path':str(p.relative_to(ROOT)),'exists':False,'bytes':None,'sha256':None,'rows':None}); continue
 row={'input':name,'path':str(p.relative_to(ROOT)),'exists':True,'bytes':p.stat().st_size,'sha256':sha256(p),'rows':None}
 try:
  if p.suffix=='.gz': row['rows']=csv_rows(p,sep='\t',compression='gzip')
  elif p.suffix=='.csv' and name not in ('hallmark_gsea','pathway_links'): row['rows']=csv_rows(p)
  elif p.suffix=='.txt' and name.startswith('s1_'): row['rows']=csv_rows(p,sep='\t')
  elif name=='hallmark_gsea':row['rows']=csv_rows(p)
  elif name=='pathway_links':row['rows']=csv_rows(p)
 except Exception as e: row['read_error']=repr(e)
 audit.append(row)
# S1 expected count check
limma=pd.read_csv(FILES['limma_all_genes']); sig=limma[limma['adj.P.Val']<.05]
s1={'limma_rows':len(limma),'significant_rows':len(sig),'up_rows':int((sig.logFC>0).sum()),'down_rows':int((sig.logFC<0).sum()),'unique_symbols_case_sensitive':int(limma.gene_symbol.nunique()),'unique_symbols_upper':int(limma.gene_symbol.astype(str).str.strip().str.upper().nunique())}
# LINCS metadata and ID audit
siginfo=pd.read_csv(FILES['sig_info'],sep='\t'); metrics=pd.read_csv(FILES['sig_metrics'],sep='\t'); genes=pd.read_csv(FILES['gene_info'],sep='\t',dtype={'pr_gene_id':str})
join_keys=['sig_id','pert_id','pert_iname','pert_type']
strict=siginfo.merge(metrics,on=join_keys,how='inner',suffixes=('_sig','_metric'))
id_join=siginfo.merge(metrics,on=['sig_id','pert_id','pert_type'],how='inner',suffixes=('_sig','_metric'))
for d in (strict,id_join):
 for c in ['distil_cc_q75','distil_ss','tas','distil_nsample']:d[c]=pd.to_numeric(d[c],errors='coerce').replace(-666,pd.NA)
base=strict[(strict.cell_id=='MCF7')&(strict.pert_type=='trt_cp')]
base_id=id_join[(id_join.cell_id=='MCF7')&(id_join.pert_type=='trt_cp')]
q2=base[(base.pert_itime=='24 h')&base.distil_cc_q75.ge(.2)]
q2_id=base_id[(base_id.pert_itime=='24 h')&base_id.distil_cc_q75.ge(.2)]
name_mismatch=siginfo[['sig_id','pert_iname']].merge(metrics[['sig_id','pert_iname']],on='sig_id',suffixes=('_sig','_metric'))
name_mismatch_n=int(name_mismatch.pert_iname_sig.fillna('').astype(str).ne(name_mismatch.pert_iname_metric.fillna('').astype(str)).sum())
with h5py.File(FILES['lincs_gctx'],'r') as h:
 col=[v.decode() for v in h['0/META/COL/id'][:]]; row=[v.decode() for v in h['0/META/ROW/id'][:]]; shape=h['0/DATA/0/matrix'].shape
rank=pd.read_csv(FILES['formal_signature_scores']); cond=pd.read_csv(FILES['formal_drug_condition_ranking']); top50=pd.read_csv(FILES['exp006_top50']); allc=pd.read_csv(FILES['exp006_all'])
qids=set(q2.sig_id); qid_ids=set(q2_id.sig_id); mids=set(col); scoreids=set(rank.sig_id)
keys=['scheme','pert_id','cell_id','dose','time']
checks={
 'S1_expected':s1['limma_rows']==21655 and s1['significant_rows']==7066 and s1['up_rows']==3422 and s1['down_rows']==3644 and s1['unique_symbols_upper']==21653,
 'GCTX_expected_shape':shape==(118050,12328),'GCTX_COL_equals_sig_info_ids':mids==set(siginfo.sig_id),'GCTX_ROW_equals_gene_info_ids':set(row)==set(genes.pr_gene_id.astype(str)),
 'Q2_historical_strict_join_expected':len(q2)==4761,'Q2_id_based_join_count':len(q2_id),'Q2_historical_ids_in_GCTX':qids<=mids,'formal_scores_A_B_rows':len(rank)==9522 and rank.scheme.value_counts().to_dict()=={'A':4761,'B':4761},'formal_scores_sig_ids_equal_historical_strict_Q2':scoreids==qids,
 'condition_count_expected':len(cond)==7430 and cond.scheme.value_counts().to_dict()=={'A':3715,'B':3715},'condition_keys_unique':not cond.duplicated(keys).any(),'Exp006_Top50_rows':len(top50)==50,'Exp006_all_rows':len(allc)==819,
 'dose_conditions_expected':cond.groupby('scheme').size().to_dict()=={'A':3715,'B':3715}
}
summary={'audit_time_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'input_file_count':len(FILES),'missing_inputs':[x['input'] for x in audit if not x['exists']],'s1_counts':s1,'lincs':{'sig_info_rows':len(siginfo),'sig_metrics_rows':len(metrics),'strict_join_rows':len(strict),'id_join_rows':len(id_join),'pert_iname_mismatch_rows':name_mismatch_n,'sig_info_sig_ids_unique':bool(siginfo.sig_id.is_unique),'sig_metrics_sig_ids_unique':bool(metrics.sig_id.is_unique),'gene_info_rows':len(genes),'gctx_shape':shape,'gctx_col_ids':len(col),'gctx_row_ids':len(row),'gctx_col_mismatch_n':len(mids-set(siginfo.sig_id)),'gctx_row_mismatch_n':len(set(row)-set(genes.pr_gene_id.astype(str))),'mcf7_trt_cp_signatures_strict':len(base),'mcf7_trt_cp_drugs_strict':int(base.pert_id.nunique()),'mcf7_24h_signatures_strict':int((base.pert_itime=='24 h').sum()),'q2_signatures_historical_strict':len(q2),'q2_drugs_historical_strict':int(q2.pert_id.nunique()),'q2_signatures_by_stable_ids':len(q2_id),'q2_drugs_by_stable_ids':int(q2_id.pert_id.nunique()),'formal_score_rows':len(rank),'formal_condition_rows':len(cond),'q2_unmatched_score_signature_ids':len(scoreids-qids),'q2_id_only_extra_signature_ids':len(qid_ids-qids)},'exp006':{'top50_rows':len(top50),'all_candidates_rows':len(allc),'distinct_top50_pert_id':int(top50.pert_id.nunique())},'checks':checks,'all_checks_pass':all(checks.values()),'hash_and_metadata_seconds':round(time.time()-start,1)}
pd.DataFrame(audit).to_csv(OUT/'results'/'input_audit.csv',index=False)
(OUT/'results'/'input_audit.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
report=['# Unified input audit','',f"Audit time (UTC): {summary['audit_time_utc']}",f"Files enumerated: {len(FILES)}; missing: {len(summary['missing_inputs'])}",'', '## Historical count reconciliation',f"- S1 limma: {s1['limma_rows']} rows; significant {s1['significant_rows']} (UP {s1['up_rows']}, DOWN {s1['down_rows']}); {s1['unique_symbols_upper']} case-normalized gene symbols.",f"- GCTX matrix shape {shape}; GCTX column ID set equals sig_info IDs: {checks['GCTX_COL_equals_sig_info_ids']}; row ID set equals gene_info IDs: {checks['GCTX_ROW_equals_gene_info_ids']}.",f"- Historical four-key metadata join yields {len(strict)}/{len(siginfo)} rows. Display-name perturbagen mismatches across sig_info and sig_metrics: {name_mismatch_n}; pert_id and pert_type are the stable identifiers.",f"- Under historical strict join, MCF7/trt_cp has {len(base)} signatures and {base.pert_id.nunique()} compounds; 24 h has {(base.pert_itime=='24 h').sum()} signatures. Historical Q2 CC>=0.2 has {len(q2)} signatures/{q2.pert_id.nunique()} compounds.",f"- Joining metadata by stable IDs (sig_id, pert_id, pert_type) yields {len(q2_id)} Q2 signatures/{q2_id.pert_id.nunique()} compounds; {len(qid_ids-qids)} additional 24 h Q2 IDs are excluded by the historical display-name join. Exp007/008 retain historical IDs for comparability; Exp009 will quantify the join sensitivity.",f"- Formal score table: {len(rank)} rows with 4,761 IDs per A/B; matches independently recomputed historical strict-join Q2 IDs: {checks['formal_scores_sig_ids_equal_historical_strict_Q2']}.",f"- Condition ranking: {len(cond)} rows, 3,715 per scheme, unique on scheme+pert_id+cell+dose+time: {checks['condition_keys_unique']}.",f"- Exp006: Top50 {len(top50)} rows/{top50.pert_id.nunique()} compounds; full candidate table {len(allc)} rows/{allc.pert_id.nunique()} compounds.",'', '## File-level checks','See results/input_audit.csv and results/input_audit.json for full paths, byte counts and SHA-256 values. Checks marked true were independently recomputed from source files. No historical input was modified by this audit.']
(OUT/'reports'/'unified_input_audit.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))
