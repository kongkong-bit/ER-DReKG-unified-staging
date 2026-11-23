# S1 pathway enrichment

This self-contained R project performs GO Biological Process and Reactome over-representation analysis and Hallmark preranked GSEA from the existing GSE42568 limma table.

## Run

From PowerShell in this directory:

```powershell
.\run_enrichment.ps1
```

The isolated R 4.4 environment is stored in `r-env/`. The input limma file is copied byte-for-byte into `input/limma_all_genes.csv`; SHA-256 values for the original input copy and Hallmark GMT are recorded in `environment_manifest.json`. The original S1 directory is never written by this analysis.

## Method notes

- Limma contrast: Tumor minus Normal. ORA input: FDR < 0.05 and logFC direction.
- ORA universe: all unique Entrez IDs mapped from genes present in the full limma tested table.
- Hallmark GSEA ranking: all finite signed limma t statistics after Entrez mapping; duplicate Entrez IDs retain the row with greatest absolute t and deterministic tie breaking.
- Hallmark gene sets: official Broad MSigDB 2025.1.Hs Entrez GMT, included under `input/` to avoid runtime network requests.
- Hallmark engine: fgsea multilevel, seed 42, single process.
- Outputs include full pathway result tables, mapping audit, leading edge genes, figures, report, and run log.
