# S1 pathway enrichment report

Run date: 2026-11-12 12:09:42 CST

## Inputs and mapping
- Full limma rows: 21655
- Unique input symbols: 21653
- Mapped symbols: 17646; unmapped symbols: 4007
- Successfully mapped Entrez universe: 17649
- Symbols with one-to-many mappings: 6
- Limma contrast: Tumor - Normal; FDR < 0.05 directional symbols before mapping: UP 3422; DOWN 3644
- Directional mapping: UP 2991/3422 symbols; DOWN 3163/3644 symbols; mapped Entrez inputs 2991 / 3164
- Universe is all unique Entrez IDs successfully mapped from genes in the full S1 tested limma table.
- GO and Reactome use BH correction over tested pathways; full pathway tables are retained.

## Results
- GO BP FDR < 0.05: UP 206; DOWN 343
- Reactome FDR < 0.05: UP 135; DOWN 26
- Hallmark GSEA FDR < 0.05: 29 of 50 sets
- Significant GO BP examples: DNA replication among UP genes; organic-compound oxidation among DOWN genes.
- Significant Reactome examples: epigenetic regulation of gene expression among UP genes; aerobic respiration and respiratory electron transport among DOWN genes.
- Significant Hallmark positive NES: E2F targets, G2M checkpoint, early estrogen response, and late estrogen response. Significant negative NES includes adipogenesis, fatty-acid metabolism, and oxidative phosphorylation.
- Hallmark ranking uses all finite limma t statistics after Entrez mapping; duplicate Entrez IDs retain the row with largest absolute t, with deterministic tie-breaking.
- Because limma contrast is Tumor - Normal, positive NES means enrichment toward tumor-up genes; negative NES means enrichment toward normal-up genes. NES is not standalone proof of pathway activation.

## Methods and reproducibility
- GO BP: clusterProfiler::enrichGO; Reactome: ReactomePA::enrichPathway; universe as defined above; BH adjustment; significance threshold adjusted p < 0.05.
- Hallmark sets: official Broad Institute MSigDB 2025.1.Hs Entrez GMT. The direct official GMT was used because the msigdbr data download endpoint was unreachable through the stale localhost proxy; the msigdbr package is installed in the project R environment.
- Hallmark ranking and enrichment: fgseaMultilevel, seed 42, single process, minSize 10, maxSize 500, eps 1e-10.
- Gene symbols were mapped with org.Hs.eg.db; mapping failures and one-to-many mappings are retained in gene_mapping_audit.csv. Input and GMT SHA-256 values are in environment_manifest.json.

## Interpretation and limitations
- Enrichment is exploratory annotation of differential expression, not evidence of drug efficacy or causal pathway activation.
- GO/Reactome ORA depends on the S1 FDR threshold and annotation coverage.
- Hallmark GSEA uses signed limma t statistics; gene ID mapping and duplicate resolution can alter ranked positions.
- fgsea reported a small fraction of tied t statistics and some pathway p-value estimation limits; see final_run.log.
- Pathway terms overlap and are not independent. The S1-tested mapped genes define the background rather than all human genes.
- The tumor-up E2F/G2M and estrogen-response patterns are directionally consistent with proliferative and estrogen-associated biology in ER-positive breast cancer; these are cohort-level associations for downstream interpretation, not causal claims.
- No pathway is required to appear; interpret disease relevance with independent biological evidence.
