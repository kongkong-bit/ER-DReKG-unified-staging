# 03 Feature merge report

## Unified ownership

- The staging copy of `syh` remains the canonical and only runtime: one FastAPI entry point, one React/Vite app, one SQLAlchemy/Alembic schema and one Neo4j repository.
- S1, enrichment, S2/WTCS, reliability, Top10 reports, GraphBundle/GraphBuild, KG06 and KG07 remain owned by their existing syh modules and evidence directories. No historical S1/S2 algorithm or Top10 score was recalculated as part of integration.
- The delivery package contributes a formal validated GraphBundle and A+ S2 run as separately identified input lineages. The bundle was copied into the canonical project-scoped staging location, registered/imported through the syh app, and queried from Neo4j.
- `wd`'s matching modules, tests and KG07 evaluation assets were reconciled against syh; duplicated runtime code was not copied. Its `.gitattributes` was added to staging so byte-verified data files are not silently rewritten by Git line-ending conversion.
- `zq` contained no visible files and therefore had no migration target.

## Implemented integration changes

- `backend/app/main.py` now selects the S2 CLI interpreter from `s2_lincs/.venv`, falling back to the backend process interpreter; it no longer assumes a machine-local S2 venv.
- `backend/app/main.py` resolves KG interpreter from `KG_PYTHON`, then `kg/.venv`, then `s2_lincs/.venv`; the importer child process runs with UTF-8 mode.
- `backend/app/main.py` returns explicit HTTP 503 responses for PostgreSQL connection failures and Neo4j service/session failures; isolated outage tests confirmed service recovery.
- `backend/app/core/config.py` and `.env.example` expose `KG_PYTHON`; `s2_lincs/requirements.txt` pins the observed screening environment and its README documents setup.
- The staging Top10 mechanism page retains syh's offline, source-linked mechanism dossier and now has a live GraphBuild selector plus KG06 Evidence Package and KG07 rule explanation section, keyed by the selected `pert_id` and imported Neo4j build.
- `frontend/vite.config.ts` supports `VITE_API_PROXY_TARGET` to permit isolated/browser acceptance on a non-default backend port while preserving the default port 8000.
- The staging acceptance Compose file accepts port overrides and uses a unique Compose project and isolated volumes.

## Validation results

- Backend suite: 71 passed. S2 focused suite: 9 passed.
- Frontend type-check and production build passed after the live Top10 UI change.
- PostgreSQL migrations, BioCypher preflight, full Neo4j import/idempotency, API smoke and browser navigation all passed in the isolated staging stack.
- All 10 Top10 candidates returned KG06/KG07 rule results and passed reference validation. Evidence gaps are recorded per row; two candidates have no path or unique evidence.
- Staging-local Python environments for backend, KG importer and S2 were provisioned, and the cross-store smoke plus GraphBundle import/idempotency checks passed using those environments. A fresh staging frontend `npm ci` and production build also passed.
- The live GLM mode was not run without a staging key; the missing-key response was verified explicitly.

## Deferred integration candidates

- wd's unique data-preparation scripts (`kg/scripts/fetch_optimuskg_subset.py`, `extend_s1_pathway_subgraph.py`, seed-subgraph builder and fixtures) remain unmerged pending a detailed behavior/license comparison with syh's newer GraphBundle and external evidence enrichment pipeline. Keeping one tested import/build path avoids introducing a second, unaudited KG pipeline.
- Full clean-machine source data acquisition, external provider generation, service-outage recovery and a sustained memory/load test remain open items.
