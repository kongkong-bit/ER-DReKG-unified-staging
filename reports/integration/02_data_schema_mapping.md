# 02 Data schema and identity mapping

The existing syh/PostgreSQL models and graph bundle identifiers remain authoritative. This mapping describes how the unified API connects the independent result lineages without rewriting source data.

| Entity | Canonical project contract | External / source identity | Integrity rule |
|---|---|---|---|
| Project | PostgreSQL `projects.project_id` UUID | `project.slug` and graph `project_slug` | UUID scopes runs and GraphBuilds; slug is a lookup/display key, never the project primary key. |
| Dataset / study | Dataset and Study model IDs | GEO/LINCS accession, release, source file and SHA-256 | Keep accession/release and file hash; never treat an accession as a local dataset ID. |
| Analysis run | `analysis_runs.analysis_run_id` | `ANALYSIS_RUN:<run_type>:<uuid>` | S1, enrichment, S2, and GraphBundle keep separate immutable run identities and input hashes. |
| Drug perturbagen | S2 `pert_id` | LINCS perturbagen; mapped compound identifier such as ChEMBL | Exact InChIKey/mapping evidence is required for compound joins; names are labels, not join keys. Preserve unresolved perturbagens. |
| Target / gene | HGNC symbol or Ensembl/Entrez identity with namespace | OptimusKG identifiers, UniProt, ChEMBL target IDs | Store namespace and source mapping provenance; do not join across identifier types by display symbol alone. |
| Pathway | Pathway accession and source namespace | Reactome pathway ID/version or source graph node ID | Preserve source release, hierarchy and mapping kind; distinguish enrichment overlap from directed regulation. |
| GraphBuild | PostgreSQL GraphBuild ID / build key | `GRAPH_BUILD:<project UUID>:<build key prefix>` | Every Neo4j query filters the build ID; a CSV snapshot build is not a Neo4j import. Keep source and status explicit. |
| Evidence | `EvidenceRecord` scoped to project + GraphBuild | Stable source record ID, release, source URL, PMID where supplied | PMID is a citation field, not an evidence primary key. Preserve source record/release and de-duplicate identical assertions by source identity/hash. |
| Mechanism path | Evidence Package `path_id` scoped to GraphBuild | Ordered relation and evidence IDs | Reconstruct paths from current build; retain empty-path/evidence gaps rather than manufacturing a mechanism. |
| AI explanation | KG07 interpretation keyed by exact Evidence Package hash, prompt, mode and model | `KG06.package_id`, evidence hash, cached provider report | Validate every retained reference against package evidence/path IDs. A KG07 `rule_template` is distinct from an LLM report. |

The S2 Top10 offline artifact and the delivery A+ GraphBundle are separate analysis lineages. A matching `pert_id` connects one perturbagen across those views, but it does not make their ranking, condition sets, identity mappings, or evidence packages interchangeable. The browser labels the offline Top10 dossier and the live GraphBuild KG06/KG07 block separately.

Verified live staging example: project `3f18f4c1-713d-58c5-8a53-38eca5a5aaf9`, Top10 perturbagen `BRD-K44227013`, S2 run `eab2f02a-2bdf-53c8-833b-fedab03070c5`, Neo4j GraphBuild `GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:06aabcb9af9d1e22`, and KG06 Evidence Package `KG06:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:06aabcb9af9d1e22:BRD-K44227013:fc4a92159faaf455`. This proves the exact ID chain on staging. It does not prove clinical efficacy or biological causality.
