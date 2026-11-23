# Exp010: Independent S1 validation

This experiment checks whether the ER-positive tumor-versus-normal signal from GSE42568 is observed in a separate GEO cohort, then rebuilds an external disease query and scores it against the same historical LINCS Q2 profiles.

## Run

From PowerShell at the project root:

```powershell
powershell -ExecutionPolicy Bypass -File experiments/exp010_external_s1/run_exp010.ps1
```

The script uses the project R environment at `experiments/s1_pathway_enrichment/r-env` and Python environment at `s2_lincs/.venv`. It does not alter historical S1, S2, or Exp006 outputs.

## Primary outputs

- `results/external_limma_results.csv`
- `results/cross_cohort_gene_concordance.csv`
- `results/cross_cohort_pathway_comparison.csv`
- `results/external_s1_signature.csv`
- `results/external_s1_lincs_scores.csv`
- `results/external_s1_drug_ranking.csv`
- `reports/exp010_report.md`
- `external_dataset_audit.md`
- `figures/`

All input paths, hashes, sample IDs, parameters, and output hashes are recorded in `results/run_manifest.json`.
