# 08 Test report (staging acceptance)

Date: 2026-11-22. Staging source: `D:\CLASS\ER-DReKG-unified-staging`. Backend unit tests used isolated SQLite/CSV fixtures. Cross-store and browser acceptance used dedicated PostgreSQL 17/Neo4j 5 containers, ports `25432`/`27687`, FastAPI on `18080`, Vite on `15173`, and Microsoft Edge. The pre-existing application ports `8000` and `5173` were occupied and were not altered.

| Check | Result | Evidence / limits |
|---|---|---|
| Python compileall | PASS | `python -m compileall -q backend/app`. |
| Backend pytest | PASS, 71 tests | `pytest -q backend/tests`; one Starlette/httpx deprecation warning. |
| S2 focused pytest | PASS, 9 tests | Project screening and WTCS tests using staging `s2_lincs/.venv`. |
| Frontend TypeScript + production build | PASS | Rebuilt after live Top10 KG06/KG07 UI change; 3,826 modules, 19.42 s Vite build. Two bundles exceed 500 kB. Fresh staging `npm ci` completed before the build. |
| Isolated PostgreSQL migrations | PASS | Alembic through head `e4f62ab7093c`; API also connected to the same isolated PostgreSQL database. |
| SQLite migration rehearsal | PASS | Isolated rehearsal file upgraded through the same head. |
| Delivery checksums | PASS | 89 source manifest files and 11 GraphBundle checksums; no mismatches. |
| BioCypher preflight | PASS with schema warnings | Formal bundle: 12,899 nodes / 48,729 edges. Warnings identify labels/properties outside the declared schema. |
| Neo4j import/idempotency | PASS | Isolated Neo4j import run twice using staging `kg/.venv`; 12,899 nodes / 48,729 edges, zero inventory problems. |
| API health and OpenAPI | PASS | Health response `{"status":"ok"}`; 41 route paths. |
| Cross-store API smoke | PASS | S2 import 3,943 conditions; GraphBuild API; Neo4j two-hop summary 12,171 nodes / 44,932 edges; Top10 10 rows; KG06/KG07 and missing-key behavior. |
| All Top10 KG06/KG07 API checks | PASS with evidence gaps retained | 10/10 available; all 10 KG07 citation-reference checks passed. Candidates ranked 6 and 9 have zero KG06 path/evidence counts; see `08_top10_acceptance.csv`. |
| Browser UI E2E | PASS for overview and first candidate | Edge rendered the project overview, navigation, Top10 page, actual WTCS and exact compound mapping, live GraphBuild selection, KG06 counts/evidence paths, and KG07 rule explanation. Remaining nine rows were covered by batch API checks, not individual browser selection. |
| Missing GLM key | PASS | `kg_llm` returned HTTP 503 with explicit missing `ZHIPU_API_KEY`; no external model request. |
| Neo4j outage/recovery | PASS | With only the isolated Neo4j container stopped, graph summary returned HTTP 503 with a retry-after-recovery message; after restart/healthy, graph requests worked again. |
| PostgreSQL outage/recovery | PASS | With only the isolated PostgreSQL container stopped and acceptance-only `connect_timeout=1`, project list returned HTTP 503 with a PostgreSQL recovery message; after restart, it returned HTTP 200 with the registered project. |
| GLM generation/cached LLM report | NOT RUN | No staging API key; model response and cache UI were not exercised. |
| Performance | PARTIAL | Five warm-cache API samples for Top10, graph summary, KG06 and KG07; report includes p50/p95. No comparable baseline, load test, memory stability or browser p50/p95. |
| Staging-local dependency install | PASS | Locked `kg/` and `backend/` environments installed; S2 requirements installed; fresh frontend `npm ci` completed. Cross-store smoke and importer were rerun with staging-local Python environments. |
| Clean-machine install/deploy | PARTIAL | Staging API/database/browser workflow passed, but a separate clean-machine install and full external data setup were not rehearsed. |

Detailed results: `cross_store_e2e.json`, `neo4j_import_acceptance.json`, `08_top10_acceptance.csv`, `08_e2e_evidence.md`, `07_api_latency_samples.json` and `07_performance_baseline.csv`. Successful runtime verification does not by itself establish scientific causality or treatment efficacy.

## Clean-room repeat (supersedes the earlier partial clean-machine and browser rows above)

An isolated copy under `D:\CLASS\.tmp\ER-DReKG-cleanroom-20261122` received fresh dependency installs and passed the same 71 backend tests, 9 S2 tests, compileall and frontend production build. Fresh PostgreSQL/Neo4j services, empty-database migration, GraphBundle import/idempotency, cross-store API smoke, and PostgreSQL dump/restore all passed. The Vite UI was exercised in browser for each of ranks 1–10, including KG06 package state and KG07 rule/citation result. This is same-host clean-room evidence rather than a second physical machine. See `10_cleanroom_deployment_rehearsal.md`, `cleanroom_cross_store_e2e.json`, and `cleanroom_neo4j_import.json`.

Same-host warm-cache p50/p95 comparison is documented in `08_performance_comparison_same_hardware.json`; each endpoint has only five samples. No sustained-load or memory-stability run was completed. LLM provider generation/caching remains untested without a user key. The two candidates with zero KG06 evidence remain a data-coverage limitation, not a failed UI/API check.
