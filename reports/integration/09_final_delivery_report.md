# 09 Final delivery report

Date: 2026-11-22. Status: **integrated staging deliverable with core acceptance passed; final clean-machine and external-provider gates remain open**.

## 1. Source projects and final ownership

- `D:\CLASS\syh` is the canonical source and runtime base. Its dirty working tree and historical results were copied into staging without editing the source tree.
- `D:\CLASS\ER-DReKG-KG-delivery-20261120` contributes the validated formal GraphBundle and a distinct A+ S2 run. Both are integrated by the syh APIs in staging, without replacing syh's existing S1/S2/Top10 lineage.
- `D:\CLASS\wd` is a largely overlapping implementation. Matching KG07 evaluation helpers and runtime modules were already present in syh; its `.gitattributes` was the file-level integration used to protect hash-verified data bytes. Unique KG data-preparation scripts were reviewed and deferred until their contracts and data licenses are reconciled with syh's newer builder.
- `D:\CLASS\zq` contained no visible files at audit time.

## 2. Feature ownership and source decisions

One syh FastAPI app, one React/Vite frontend, one PostgreSQL/Alembic chain and one Neo4j graph repository remain. S1, pathway enrichment, S2/WTCS, reliability/PRISM, Top10, GraphBuild, KG06 and KG07 keep their syh module ownership. Offline Top10 evidence and imported GraphBuild evidence remain separately labeled and are tied together by exact LINCS `pert_id`; no ranking or research score was overwritten. See `00_four_project_feature_matrix.csv`, `00_file_migration_plan.md`, `02_module_ownership.md`, `02_data_schema_mapping.md` and `03_feature_merge_report.md`.

## 3. Implemented staging changes

- Hardened S2/KG Python interpreter selection and added configurable `KG_PYTHON`.
- Added clear HTTP 503 handling for PostgreSQL connection loss and Neo4j unavailable/expired sessions; verified outage and recovery against isolated acceptance services.
- Added pinned S2 scientific dependencies and setup guidance.
- Added `VITE_API_PROXY_TARGET` for isolated/non-default API ports.
- Added environment-overridable ports for the isolated acceptance Compose stack.
- Added a live, GraphBuild-scoped KG06 Evidence Package and KG07 rule section to the Top10 mechanism page. The page selects only a materialized Neo4j GraphBuild, fetches data for the selected candidate, displays paths/evidence and citation validation, and surfaces no-build/API errors. The offline dossier remains visibly distinct.
- Added runbooks, source/schema mappings, row-level Top10 status, database/data integrity reports, cross-store and browser evidence, and latency samples under `reports/integration/`.

## 4. Data and database status

- Staging PostgreSQL migrated through `e4f62ab7093c`; isolated SQLite migration rehearsal also passed.
- The formal GraphBundle has 11 checksums with zero mismatches; the delivery manifest has 89 entries with zero mismatches.
- BioCypher preflight and isolated Neo4j import passed; full imported inventory is 12,899 nodes / 48,729 edges. Import was repeated with zero inventory problems.
- S2 import registered 3,943 A+ condition rows under its own run ID. The Neo4j API DiseaseContext two-hop projection is 12,171 nodes / 44,932 edges. These are intentionally different scopes.
- Top10 → KG06 → KG07 example verified for `BRD-K44227013` (ponatinib), including GraphBuild/package IDs and 258 verified evidence IDs. All 10 candidates returned KG06/KG07 rule results; two candidates have no paths and zero unique evidence. No unsupported mechanisms were invented.
- Neo4j warns that imported Candidate nodes lack `rank` and `wtcs_median_B` properties. KG06/KG07 still pass; WTCS and ranking remain tied to the validated S2/Top10 records rather than these absent graph fields.

## 5. Tests and full-stack runtime

- Backend: 71 tests passed; S2 focused tests: 9 passed; Python compileall passed.
- Staging-local dependency provisioning passed: locked `kg/` and `backend/` environments installed, S2 requirements installed in `s2_lincs/.venv`, and a fresh frontend `npm ci --no-audit --no-fund` completed.
- Frontend: TypeScript and Vite production build passed after the live GraphBuild UI change (3,826 modules, 19.42 s). Vite still warns that two chunks exceed 500 kB.
- Isolated PostgreSQL, Neo4j, API health/OpenAPI, all Top10 API acceptance rows, KG06/KG07 rule mode and missing-GLM-key behavior passed. Cross-store smoke and formal bundle import/idempotency were rerun with staging-local Python environments.
- Microsoft Edge loaded the staging frontend and project overview, navigated to Top10, and rendered the selected real candidate, WTCS, exact compound mapping, live GraphBuild, KG06 evidence paths, KG07 rule explanation and citation validation. Batch API checks, rather than individual browser selection, cover the other nine candidates.
- `kg_llm` without `ZHIPU_API_KEY` returned HTTP 503 with an explicit configuration message. No external model request was sent.

## 6. Performance baseline

Five sequential warm-cache local API samples per endpoint measured Top10 p50/p95 at 50.51/56.08 ms; graph summary at 1,269/1,371.86 ms; KG06 at 418.07/729.85 ms; and KG07 rule mode at 440.20/548.98 ms. These are not load-test or browser latencies. No comparable pre-integration baseline, sustained memory profile or GLM-provider timing was captured. See `07_performance_baseline.csv` and `07_performance_optimization.md`.

## 7. Deployment rehearsal and constraints

- Staging PostgreSQL/Neo4j services and the API/frontend were started on isolated ports and volumes. The API returned healthy, the browser reached the application, and the cross-store workflow completed.
- The staging-local locked `kg/.venv`, `backend/.venv`, and S2 environment are provisioned and were used for acceptance. A separate clean-machine installation still needs rehearsal.
- Frontend dependency installation used `npm ci` in staging and its production build and browser checks passed.
- The actual `ZHIPU_API_KEY` is not provided in the project. External GLM generation, cached model-response display, timeout/retry and provider cost were not verified.
- Clean-machine source-data acquisition/license audit, all service-outage recovery cases, memory stability, and a same-hardware syh-vs-staging performance comparison remain open.

## 8. Delivery directory and startup

Working deliverable: `D:\CLASS\ER-DReKG-unified-staging`. Its source structure is based on syh. The root `README.md`, `.env.example`, `docs/REPRODUCIBILITY.md`, backend Alembic migrations, KG scripts, S2 requirements and `06_deployment_guide.md` describe setup and run commands. Large licensed/raw inputs must be obtained according to their source terms and verified against recorded hashes.

## 9. Rollback and source safety

Discard or recreate only the staging copy to roll back integration edits. Do not delete the acceptance database volumes if their evidence is still needed. The source `syh`, `wd`, delivery package and `zq` trees were not modified. The main `syh` working tree had 63 existing modified/untracked status entries at the baseline; it has not been merged or overwritten. Do not merge into the source tree until those user changes are protected and the remaining installation/provider/data gates are reviewed.

## 10. Remaining release gates

1. Run a clean-machine install and documented source-data preparation, including a fresh dependency install.
2. Configure a user-owned GLM key if LLM reports are required; verify cache, timeout, retry and citation behavior without storing secrets.
3. Repeat browser interaction for the remaining candidates and record a sustained memory/load profile.
4. Reconcile the two zero-evidence candidates and review source licensing/availability before a distributable release.
5. After the existing dirty syh tree is safely protected, decide whether to merge the accepted staging changes back into `D:\CLASS\syh`.

## 11. Clean-room evidence update (2026-11-22)

The earlier “clean-machine install” and “repeat browser interaction” gates above are superseded by a successful isolated clean-room clone rehearsal on the same physical host. Fresh backend/KG/S2/frontend dependency installs, backend (71) and S2 (9) tests, frontend production build, empty PostgreSQL migration, Neo4j formal bundle import/idempotency, cross-store API smoke, full Top10 UI selection, and PostgreSQL dump/restore were completed. The restore matched all 10 public table row counts and Alembic head. See `10_cleanroom_deployment_rehearsal.md` and the `cleanroom_*` evidence files. This does not claim a separate physical-machine test.

A five-sample same-host warm-cache comparison is now recorded in `08_performance_comparison_same_hardware.json`. Medians were similar or lower except KG07 (443.50 ms integrated vs 422.49 ms baseline); KG06 integrated p95 was higher (738.90 vs 676.93 ms). The sample is too small and noisy to claim a performance improvement. Sustained-load and memory stability remain open.

Remaining release gates: (1) provide a user-owned GLM key only if provider generation/caching must be accepted; (2) audit source-data acquisition and licenses before redistribution; (3) reconcile scientific coverage for rank 6 and rank 9, which have zero KG06 paths/evidence; (4) run sustained load/memory profiling and optionally a separate physical-host deployment; (5) decide separately whether to merge into the dirty `D:\CLASS\syh` tree. The integrated project is deliverable in `D:\CLASS\ER-DReKG-unified-staging`; no source tree was overwritten.
