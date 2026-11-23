# Identifier mapping report

## Drug candidates

The Top 10 is frozen by exact `pert_id`. Existing OptimusKG GraphBundle drug IDs are used when present; two compounds require explicit external overlay mappings recorded in the audit. ChEMBL context routes require exact candidate and target-component keys; no name-only target inference is used.

## Proteins and S1 genes

The source GraphBundle contains gene nodes but no protein nodes suitable for signed networks. We built `data/kg_enrichment/normalized/optimuskg/3.2/uniprot_gene_crosswalk.csv` from the OptimusKG 3.2 gene parquet `associated_proteins` field. The crosswalk has 27,895 unique UniProt accessions and 27,895 unique gene targets; no accession mapped to multiple project genes. The mapping manifest records the source parquet SHA-256 and project-specific filtering. Mapping relations are retained as provenance steps and are not interpreted as causal biological edges.

SIGNOR and OmniPath endpoints are UniProt accessions. Only exact accessions with one unambiguous project gene mapping are carried into candidate subgraphs. S1 differential expression seeds likewise use exact project gene identifiers. Protein→gene mapping is a representation bridge, not a signed regulation assertion.

Reactome current-2026-10 UniProt-to-pathway memberships use the same exact, one-to-one OptimusKG crosswalk; unmapped or ambiguous accessions are rejected, and the resulting relation is an unsigned pathway annotation. PrimeKG drug identities use only exact normalized canonical names and explicit aliases from the frozen Top10 identity table. This resolves 6/10 candidates; the other four are left unmapped. PrimeKG gene/protein identifiers remain in source-normalized records; no fuzzy name matching or inferred drug aliases are used.

## Exclusions and limitations

Unknown and ambiguous accessions are rejected with source row/reason in `02_regulatory_mapping_rejects.csv`. Sources with outdegree >100 are excluded from path search to reduce generic-hub routes; excluded source assertions remain enumerated in the rejection report. Do not infer a protein activity change from gene mRNA or an overall drug response from the KG path sign.
