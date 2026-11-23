# Formal S2 MCF7 drug reversal screen

## Gate outcomes
- WTCS reference-value gate: PASS. Hand-solvable ordered vectors returned ES/WTCS (+1) for same-direction and (-1) for inverse-direction cases. This confirms score signs and descending ranked-list orientation against the Cell 2017 formula.
- Metadata / matrix alignment inherited and verified: exact GCTX signature and gene IDs align to source metadata.
- Batch-safe extraction: PASS. Read one signature row at a time from HDF5; no full matrix materialization.
- Formal scoring: PASS for 4761 qualified signatures; both A and B scored.

## Data inventory and inclusion
GSE70138 Level 5 COMPZ. MCF7 chemical perturbations (`trt_cp`): 12737 signatures across 1785 unique compounds. 24 h: 11850 signatures, 1750 compounds. Main QC retains 24 h signatures with `distil_cc_q75 >= 0.2`, yielding 4761 signatures and 1191 compounds. The `-666` sentinel is treated as missing. QC threshold is a documented reproducibility metric; the explicit cutoff is the project’s prespecified operational filter. No TAS threshold was applied. Dose strata remain separate.

## Query schemes and WTCS
Scheme B is primary: limma results restricted to BING then FDR < 0.05 and top 100 per sign, ranked by adjusted P ascending and absolute logFC descending. Scheme A is the comparison: original top 100 clipped to BING, with observed sizes UP 70 and DOWN 55. Both use the same BING background and the same real signatures. WTCS uses weighted KS ES and `(ES_UP - ES_DOWN)/2` when signs differ, otherwise zero. Negative values mean inverse connectivity, not demonstrated efficacy.

## Drug-level aggregation and stability
Drug condition is keyed by compound ID, MCF7, treatment time, and dose. Within each condition, aggregate signature WTCS by median. Also report mean, SD, MAD, and signature count. Do not merge dose strata or select best individual signatures. Formal condition rows: 7430.

Across matched drug-condition rows, A/B median-WTCS rank Spearman correlation is 0.8940. This difference reflects query membership and size only; the screen does not establish that B is superior.

## Outputs
- `results/formal_signature_scores.csv` (9522 rows, both schemes)
- `results/formal_drug_condition_ranking.csv` (7430 condition rows)
- `results/formal_qc_summary.csv` and `results/mcf7_condition_inventory.csv`
- `figures/formal_top25_A.png`, `figures/formal_top25_B.png`, `figures/formal_AB_comparison.png`

This is a full qualified MCF7 24 h screen within the available GSE70138 Level 5 dataset, not a final Top 10 claim or clinical efficacy assessment. Historical Smoke Test and raw LINCS/S1 inputs were preserved.
