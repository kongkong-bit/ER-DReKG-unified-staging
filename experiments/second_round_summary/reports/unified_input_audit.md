# Unified input audit

Audit time (UTC): 2026-11-12T04:46:48Z
Files enumerated: 28; missing: 0

## Historical count reconciliation
- S1 limma: 21655 rows; significant 7066 (UP 3422, DOWN 3644); 21653 case-normalized gene symbols.
- GCTX matrix shape (118050, 12328); GCTX column ID set equals sig_info IDs: True; row ID set equals gene_info IDs: True.
- Historical four-key metadata join yields 92723/118050 rows. Display-name perturbagen mismatches across sig_info and sig_metrics: 25327; pert_id and pert_type are the stable identifiers.
- Under historical strict join, MCF7/trt_cp has 10581 signatures and 1460 compounds; 24 h has 9843 signatures. Historical Q2 CC>=0.2 has 4761 signatures/1191 compounds.
- Joining metadata by stable IDs (sig_id, pert_id, pert_type) yields 5861 Q2 signatures/1471 compounds; 1100 additional 24 h Q2 IDs are excluded by the historical display-name join. Exp007/008 retain historical IDs for comparability; Exp009 will quantify the join sensitivity.
- Formal score table: 9522 rows with 4,761 IDs per A/B; matches independently recomputed historical strict-join Q2 IDs: True.
- Condition ranking: 7430 rows, 3,715 per scheme, unique on scheme+pert_id+cell+dose+time: True.
- Exp006: Top50 50 rows/50 compounds; full candidate table 819 rows/819 compounds.

## File-level checks
See results/input_audit.csv and results/input_audit.json for full paths, byte counts and SHA-256 values. Checks marked true were independently recomputed from source files. No historical input was modified by this audit.
