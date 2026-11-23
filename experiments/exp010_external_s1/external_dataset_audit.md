# External cohort inventory and selection audit

## Selection rule fixed before examining similarity

The primary validation cohort had to be a human breast-tissue dataset with a sample-level ER result, normal tissue, usable expression values and annotation, and no sample overlap with GSE42568. Selection was based on these fields and sample design, not on whether its results resembled GSE42568.

## Candidate comparison

| GEO accession | Audit finding | Decision |
|---|---|---|
| GSE139038 | 65 samples; per-sample ER status in GEO characteristics; 26 ER-positive tumors, 15 ER-negative tumors, 18 paired normal tissues, and 6 apparently normal tissues. GPL27630 two-colour spotted array has downloadable processed log ratios and matching probe annotation. Fourteen ER-positive tumors have a same-patient paired normal in the deposited sample set. | Selected as primary, using only those 14 matched ER-positive patient pairs. |
| GSE65194 | 178 deposited arrays; 130 unique tumors, 11 healthy breast tissues, and 14 cell lines. Tumors have TNBC/Her2/Luminal A/Luminal B sample-group labels. The inspected series matrix does not provide a direct per-sample ER status field; Luminal subtype is not substituted for an explicit ER assay. | Not selected as the primary ER-specific validation cohort. Kept as an audited candidate. |
| GSE42568 | Discovery cohort used by S1. | Reference only; not an external validation cohort. |

The selected GSE139038 accession is distinct from GSE42568. An independent check of the actual GSM accessions reports zero shared sample IDs (`results/sample_independence_check.csv`).

## GSE139038 data and processing audit

- Series matrix: 44,544 feature rows × 65 GSM columns, GPL27630.
- Platform table: 44,544 feature IDs; all series-matrix feature IDs matched the platform table.
- The platform is a spotted two-colour array. GEO reports the processed value as log ratio (635/532), median-centred per array; this is not an Affymetrix intensity matrix.
- GEO sample characteristics record 26 ER-positive tumors, 15 ER-negative tumors, 18 paired normal tissues, and 6 apparently normal tissues. Fourteen ER-positive tumors had a matching normal tissue from the same numbered patient and entered the primary paired analysis.
- GPL27630 annotation maps 44,493 spots to a gene symbol; 27,086 unique symbols remain after normalization. Of these, 26,590 map to Entrez IDs.
- Repeated spots were averaged by uppercase gene symbol. Limma modeled patient and group, with the contrast `ER+ Tumor − Normal`.
- The independent cohort's GSM identifiers do not overlap the GSE42568 sample-group file.

## Source files and official records

- GSE139038 series: <https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE139038>
- GPL27630 platform annotation: <https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GPL27630>
- Audited alternate GSE65194 series: <https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE65194>
- Discovery GSE42568 series: <https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE42568>

## Limits

Fourteen paired ER-positive patients are a small external cohort. The custom two-colour platform and its roughly 27,000 mapped genes differ from the discovery Affymetrix platform. This cohort is usable for a cautious replication check, not for a definitive population-level conclusion.
