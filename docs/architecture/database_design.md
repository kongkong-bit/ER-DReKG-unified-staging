# Database Design

## PostgreSQL (system of record)

- `projects(project_id UUID PK, slug UNIQUE, name, disease_id, status, created_at)`
- `studies(study_id UUID PK, project_id FK, accession, title, organism, design_json)`; `(project_id, accession)` is unique, and repeated registration with identical metadata is idempotent.
- `datasets(dataset_id UUID PK, project_id FK, study_id FK NULL, source, release, source_url, license_status, sha256, state, metadata_json)`; an optional study link must belong to the same project.
- `analysis_runs(analysis_run_id UUID PK, project_id FK, run_type, status, created_at, parameters_json, software_json, input_hashes_json, output_manifest_json)`
- `disease_contexts(record_id SHA256 PK, graph_build_id FK, project_id FK, context_id, disease_id, context_label, context_json, context_sha256)`; unique `(graph_build_id, context_id)` preserves disease-specific S1/S2/enrichment run references for each immutable graph snapshot. Rows are loaded only from the SHA-256-verified `subgraph_nodes.csv`.
- `compound_mappings(mapping_id UUID PK, project_id FK NULL, source_namespace, source_id, target_namespace, target_id, method, status, confidence, audit_json)`
- `candidates(candidate_id UUID PK, project_id FK, run_id FK, compound_id, rank, score_name, score_value, condition_json)`
- `s2_condition_results(result_id PK, project_id FK, analysis_run_id FK, pert_id, condition_key, rank_within_condition, condition_json)`：每条记录代表单个 LINCS 药物在明确细胞、扰动类型、时间和剂量下的结果；唯一键为运行版本 + 条件 + perturbagen。不同剂量/时间不得折叠为一个全局药物分数。
- `evidence_records(record_id SHA256 PK, graph_build_id FK, project_id FK, evidence_id, source_release, source_record_id, subject_id, predicate, object_id, source_assertion JSON, source_url JSON, assertion_sha256)`; unique `(graph_build_id, evidence_id)` preserves the same source assertion separately in each immutable graph version. Imports validate the GraphBundle output SHA-256 and are idempotent.
- `graph_builds(graph_build_id UUID PK, project_id FK, run_id FK, source_release, seed_hash, config_hash, status, counts_json)`
- `jobs(job_id UUID PK, project_id FK, run_id FK NULL, state, progress, error_json, timestamps)`

Use JSONB only for source-specific attributes and algorithm parameters; identifiers and join keys remain typed columns. Foreign keys enforce project/run ownership. Unique keys make imports idempotent. Disease-specific DEG direction and WTCS are persisted as run-scoped evidence, never on shared entities. S2 condition results are versioned rows; a cross-condition candidate score requires a separately specified aggregation policy and is not inferred from the condition table.

## Neo4j

Shared nodes use uniqueness constraints on `(Drug.compound_id)`, `(Gene.ensembl_gene_id)`, `(ProteinTarget.protein_id)`, `(Disease.disease_id)`, and `(Pathway.pathway_id)`. Project result nodes include project/run IDs. Neo4j source relationships retain stable `evidence_ids`, source release, and the complete source-assertion JSON for bounded path queries; PostgreSQL stores the version-scoped EvidenceRecord system of record keyed by `(graph_build_id, evidence_id)`.

## Storage and transactions

Large matrices/Parquet remain files or object storage with Dataset records and SHA-256. PostgreSQL and Neo4j writes are coordinated through a persisted GraphBuild state and retryable idempotent batches, not a pretend cross-database transaction.
