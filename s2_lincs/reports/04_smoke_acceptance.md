# S2 smoke acceptance

## Status

| Stage | Status | Evidence |
|---|---|---|
| S1 input audit and S1_100 UP/DOWN | PASS | required limma fields parsed; 100 unique genes per direction; contrast is Tumor - Normal |
| LINCS metadata/GCTX alignment | PASS | 118,050/118,050 signature IDs and 12,328/12,328 gene IDs align |
| Real MCF7 trt_cp extraction | PASS | 30 signatures, one per perturbagen, extracted by signature row |
| WTCS unit tests | PASS | pytest: 5 passed |
| Real smoke scoring | PASS | 30 rows in results/smoke_signature_scores.csv |

## Real data summary

GSE70138 Level 5 COMPZ; 118,050 signatures by 12,328 genes in the on-disk matrix layout. The matrix was decompressed to a local work copy and individual signature rows read. All signatures matched sig_info and all gene IDs matched gene_info. The 30 selected signatures represent 30 perturbagens. All are MCF7, trt_cp, 24 h, but doses vary and are retained as separate records. S1 UP coverage is 74%; DOWN coverage is 56%.

## Preview

The most negative WTCS among this quality-ranked smoke subset is the signature listed first in `results/smoke_candidate_preview.csv`. This limited subset is not a full LINCS ranking and does not establish therapeutic efficacy.

## Risks and next step

Selection used highest available distil_cc_q75 and one signature per perturbagen, with a 24 h filter emerging from the top-ranked records rather than a predeclared fixed dose. Doses therefore vary. The matrix stores signatures on axis 0 and genes on axis 1, contrary to a common assumed orientation. Proceed to a prespecified, dose-stratified larger MCF7 screen only after fixing the condition-selection rule.
