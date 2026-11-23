# DiseaseGraph Lab Architecture

## Goals

Keep the existing S1/S2 experiments immutable and build a reusable platform around them. Projects own studies, datasets, analysis runs, disease contexts, candidates, and graph builds. Biomedical entities and source assertions are shared by stable identifiers across projects.

## Components

- `experiments/`: historical, reproducible research outputs; read-only to platform ingestion.
- `backend/`: FastAPI application, SQLAlchemy/PostgreSQL project and evidence metadata, Neo4j query service.
- `kg/`: source adapters, identifier mapping, bounded subgraph extraction, validation, and import.
- `frontend/`: React client; it calls FastAPI only and never connects to Neo4j.
- `infrastructure/`: Docker Compose and local development configuration.
- `data/`: immutable raw inputs, derived staging files, manifests, and generated graph snapshots.

## Data flow

1. Register a Project and DiseaseContext.
2. Register immutable Dataset records with source/version/hash/license metadata.
3. Import existing S1/S2/Exp006–Exp011 results as AnalysisRun outputs; do not rerun or mutate them.
4. Map project seeds to public entities with explicit confidence, method, and unresolved/conflict records.
5. Extract only bounded, evidence-bearing subgraphs from a pinned source release.
6. Validate node/edge IDs and provenance, then import idempotently into Neo4j.
7. Serve paged subgraphs through allow-listed FastAPI query templates.

## Trust boundaries

Raw research files are immutable. Staging data is disposable and hashed. PostgreSQL is authoritative for project/run metadata; Neo4j stores the normalized graph and source assertions. API callers cannot submit arbitrary Cypher. Public data reuse is constrained by each source's data license, independently of code licenses.

## Initial implementation boundary

First prove one traceable candidate → target → gene/pathway evidence chain. Do not load the complete OptimusKG release into Neo4j. If a candidate has no defensible mapping or source assertion, preserve it as unresolved rather than inventing a relation.
