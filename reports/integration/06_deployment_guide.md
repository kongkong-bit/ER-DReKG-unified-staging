# 06 Deployment guide

The deliverable is a Windows-first React/Vite + FastAPI project. The root README and `docs/REPRODUCIBILITY.md` remain the primary onboarding guides. This note records the integration-specific environments and their verification status.

## Requirements and local setup

- Windows 10/11, Python 3.12, `uv`, Node.js/npm, Git, and Docker Desktop.
- R and the cited Bioconductor packages are needed only to rerun the historical S1 limma workflow. Large LINCS GCTX files must be obtained under their source terms; they are not silently replaced by mock data.
- Copy `.env.example` to `.env`; set distinct local PostgreSQL/Neo4j passwords and any optional `ZHIPU_API_KEY`. Do not commit `.env`.
- Run `docker compose up -d postgres neo4j`, `docker compose ps`, then from `backend` run `uv sync`, `uv run alembic upgrade head`, and `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000`.
- In another terminal, from `frontend` run `npm ci`, `npm run build`, and `npm run dev -- --host 127.0.0.1 --port 5173`. Vite proxies `/api` to `127.0.0.1:8000`; the proxy target can be overridden with `VITE_API_PROXY_TARGET`.
- Set `KG_PYTHON` when the BioCypher importer is in a separate environment. Otherwise the API checks `kg/.venv` and then `s2_lincs/.venv`. S2 runs use `s2_lincs/.venv` when present and fall back to the backend interpreter; install `s2_lincs/requirements.txt` into whichever interpreter will run S2.

## Database and graph initialization

The tested staging flow used isolated acceptance services, not a populated user database: PostgreSQL migrations reached Alembic head `e4f62ab7093c`; Neo4j imported the verified GraphBundle idempotently; the browser/API used the project-scoped Neo4j GraphBuild. The acceptance Compose file is `docker-compose.top10kg-staging.yml`; its ports default to 25432/27474/27687 and can be changed with `STAGING_*_PORT` variables. It is for isolated verification only; do not attach production volumes to it.

For another installation, migrate the new PostgreSQL database before starting the API. Register the applicable analysis runs and GraphBundle, verify bundle hashes, then create/import a GraphBuild before using live KG06. `kg/scripts/verify_neo4j_import.py` checks imported inventory. Follow `docs/REPRODUCIBILITY.md` for source data, licensing, hash verification, backups and restores. Never use `docker compose down -v` on a database with data that must be retained.

## Verified versus environment-dependent

- PostgreSQL, SQLite migrations, Neo4j import, API health/OpenAPI, backend tests, S2 tests and frontend production build passed on this host.
- Staging-local locked environments were provisioned for `kg/` and `backend/` with `uv sync --project kg --locked --all-groups` and `uv sync --project backend --locked --all-groups`; the S2 environment was created under `s2_lincs/.venv` with `requirements.txt`. The importer and cross-store smoke passed using these staging-local interpreters. Independent clean-machine provisioning remains to be rehearsed.
- `npm ci --no-audit --no-fund` completed in the staging frontend and the production build passed from those installed dependencies.
- `ZHIPU_API_KEY` is optional for rule-based KG07 explanations and required only for external model modes. Without it, the endpoint returns an explicit 503; no model is contacted.
- Full clean-machine installation has not yet been rehearsed. Availability and licensing of external/raw source datasets must be checked for the target deployment.
