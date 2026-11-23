# 04 Database migration and graph import report

Date: 2026-11-22. All live database work below used the isolated `er-drekg-acceptance` Compose project and its dedicated volumes/ports (PostgreSQL `25432`, Neo4j Bolt `27687`). No source application database or pre-existing Compose project was modified.

- PostgreSQL 17: containers healthy; Alembic upgraded the isolated database through head `e4f62ab7093c` (seven revisions after base). The API connected to this database during the cross-store smoke run.
- SQLite compatibility: PASS. Alembic upgraded an isolated rehearsal file through the same head.
- Neo4j 5: container healthy. `verify_neo4j_import.py` imported the formal GraphBundle twice and returned PASS: 12,899 nodes, 48,729 edges, zero inventory problems. Re-import idempotency was exercised.
- BioCypher preflight: PASS against the formal GraphBundle with 12,899 nodes and 48,729 edges. Hash verification was clean. Preflight emitted expected schema warnings for labels/properties not declared in the current BioCypher schema.
- API graph-build integration: PASS. The cross-store run created `GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:06aabcb9af9d1e22`; its DiseaseContext two-hop API projection returned 12,171 nodes and 44,932 edges from Neo4j. These counts describe different scopes from the full imported bundle and should not be conflated.
- KG runtime qualification: `uv sync --project kg --locked --all-groups` installed the complete staging-local environment. `verify_neo4j_import.py`, run with `kg/.venv`, imported the formal bundle twice and returned PASS with 12,899 nodes, 48,729 edges and zero inventory problems. The cross-store smoke also passed with staging `backend/.venv` and `KG_PYTHON` pointing to staging `kg/.venv`.
- Neo4j query notifications note missing `rank` and `wtcs_median_B` properties on imported `Candidate` nodes. KG06/KG07 checks still completed and preserved citation-reference validation, but candidate score/rank fields are not available from those graph nodes.
- Migration caution: downgrade revisions drop tables/columns and are destructive on populated databases. Only disposable rehearsal databases should be used for downgrade checks.
