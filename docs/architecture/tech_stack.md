# Technology Stack and Decisions

| Layer | Initial choice | Reason / boundary |
|---|---|---|
| Python | 3.12+, `uv` | Reproducible CLI and service environment |
| Tabular ETL | Polars, DuckDB, PyArrow | Stream/scan large Parquet and CSV inputs; keep analytical staging outside the API process. GraphBundle node extraction uses DuckDB projection pushdown to skip unused OptimusKG payload columns; Polars remains in use for the smaller source edge tables. |
| Validation | Pydantic | Shared request/response and configuration validation |
| API | FastAPI | Typed REST API and generated OpenAPI |
| Metadata DB | PostgreSQL, SQLAlchemy, Alembic | Projects, datasets, runs, jobs, mappings, evidence registry |
| Graph DB | Neo4j + official Python driver | Normalized entities and provenance-bearing assertions |
| KG normalization and import | BioCypher 0.17 translator + versioned Neo4j MERGE importer | BioCypher translates project graph entities and relationships into the configured schema; the Neo4j importer consumes those translated entities and preserves GraphBuild membership, source assertions, and shared-entity idempotency. OptimusKG remains an external source, not data built by our pipeline |
| UI | React, TypeScript, Vite, Ant Design | Project-centric SPA |
| Graph UI | Cytoscape.js | Bounded interactive subgraphs only |
| Charts | Apache ECharts | S1/S2 and experiment summaries |
| Client state | TanStack Query, React Router | API cache and routed project pages |
| Deployment | Docker Compose | Isolated local development/test services |
| Async jobs | Deferred Celery/Redis | CLI pipeline first; add only when uploads/large jobs need queues |

Secrets are environment variables. `.env.example` contains names and safe placeholders only; no credentials are committed.
