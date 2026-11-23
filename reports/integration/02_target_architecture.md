# 02 Target architecture

## System boundary

The deliverable remains the syh application: one React/Vite frontend, one FastAPI app (`backend/app/main.py`), one SQLAlchemy/Alembic PostgreSQL layer, and one Neo4j graph access layer (`backend/app/graph_repository.py`). S1/S2 source analysis and experiment outputs remain under their current project directories. `kg/` owns bundle preparation/import tooling; the API consumes registered runs/builds and evidence through the existing project IDs.

## Request/data flow

```text
React pages (S1, S2, Top10, Graph)
  -> /api/v1/projects/{project_id}/...
  -> FastAPI main.py
  -> SQLAlchemy repositories / immutable run artifacts / Neo4j graph repository
  -> project_id + analysis_run_id + graph_build_id + pert_id + evidence_id
```

AI interpretation consumes an Evidence Package for the same project/build/drug, validates cited references, and caches against evidence hash + model + prompt version + mode. Current implementation is synchronous in the request path and cache files are local; do not claim background-job execution or PostgreSQL report history until added and verified.

## ID rules

- `project_id`: UUID string from PostgreSQL `projects.id`; do not infer from slug.
- `analysis_run_id`: immutable UUID run registered for S1/S2/enrichment; preserve source lineage and input manifest hashes.
- `graph_build_id`: `GRAPH_BUILD:<project_id>:<build_key-prefix>`; retain full key in build record and manifest.
- `pert_id`/drug ID: LINCS perturbagen ID is the API selection key for current S2 Top10; keep external identifiers such as InChIKey, PubChem, ChEMBL as mappings with source and match method.
- `evidence_id`: stable source evidence identity / EvidenceRecord key; citations must resolve in the package used to generate a report.
- `path_id`: stable path key scoped by project/build; never conflate a route display index with persistent path ID.
- Reports: current KG07 response/cache is identified by evidence input hash, model, prompt version and mode; there is not yet evidence of a SQL report table or immutable report ID.

## Compatibility boundaries

1. Keep syh S1/S2/WTCS and formal results unchanged; register other validated experiment lineages as separate runs.
2. Treat the delivery bundle's formal graph build as an auditable dataset, not as evidence the current local Neo4j has that state.
3. Keep offline Top10 mechanisms and live Neo4j graph APIs explicitly distinguishable in response metadata.
4. Use the existing settings object and `.env.example`; no second config loader or hard-coded machine path.
5. Preserve existing schema/migration history; only forward-only migration for a verified missing persisted contract.
