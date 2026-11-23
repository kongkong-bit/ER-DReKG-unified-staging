# DiseaseGraph Lab API

## Local development

The runnable FastAPI application is the complete `backend/app/` tree in the project root. The similarly named `ER-DReKG-KG-delivery-20261120/04_code/backend/app/main.py` is only a KG-review derivative and must not be used to start this application.

For the standalone Windows project, follow the root README and run `scripts/start-project.ps1`; it starts only this project's Compose services and API/frontend on `127.0.0.1:18083` and `127.0.0.1:15175`. The API reads configuration from the root `.env`, not `backend/.env`.

For manual development, from the project root:

1. Run `docker compose --project-name er-drekg-unified-staging up -d --wait postgres neo4j`.
2. In `backend/`, run `uv sync` and `uv run alembic upgrade head`.
3. Run `uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 18083`.
4. In `frontend/`, run `npm ci` and `npm run dev -- --host 127.0.0.1 --port 15175 --strictPort`.
5. Open `http://127.0.0.1:18083/docs` for the generated OpenAPI interface.

For local API-only checks, set `DATABASE_URL=sqlite:///./diseasegraph.db`, `GRAPH_SOURCE=csv`, and `GRAPH_DATA_DIR=experiments/platform_phase_b` in the process environment, then apply Alembic migrations. The normal standalone app uses PostgreSQL/Neo4j from the root `.env`; CSV mode reads the real bounded Phase B extract and does not invent graph data.

Current endpoints are read-only for scientific outputs. Dataset registration always creates `validation_pending` state. Graph responses cap at 200 nodes, depth at 2, and use fixed query templates. Async job queue is intentionally deferred.

