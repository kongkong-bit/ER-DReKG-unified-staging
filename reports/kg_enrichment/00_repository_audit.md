# Phase 0 repository audit

Generated from the current checkout. Git worktree is dirty; existing modifications and untracked artifacts were preserved. The frozen Top 10 source and hash are recorded in `00_graph_baseline.json`.

## Components and data flow

- S1 differential expression: `backend/app/s1_expression.py`, `backend/app/s1_genes.py`, `reports/top10_kg/input_snapshot/limma_all_genes.csv`.
- S1 pathways: `backend/app/s1_pathways.py`, `reports/top10_kg/input_snapshot/pathway_gene_links.csv`, and `reports/top10_kg/04_pathway_enrichment_report.md`.
- S2/WTCS: `s2_lincs/formal_screen.py`, `s2_lincs/scoring.py`, `experiments/final_results/results/final_top10.csv`, and `reports/top10_kg/02_top10_frozen_manifest.json`.
- Gene-level perturbation: `reports/top10_kg/08_target_s2_response.csv`; these are transcript responses and do not establish target activity.
- Large graph source: OptimusKG 3.2; only five Parquet tables listed in `data/optimuskg/3.2/source_manifest.json` are present. Project GraphBundles use `kg/config/biocypher_schema.yaml`.
- Graph construction/import: `kg/scripts/build_project_graph_bundle.py`, `kg/scripts/build_top10_chembl_reactome_bundle.py`, `kg/scripts/import_phase_b_to_neo4j.py`, and `kg/scripts/verify_neo4j_import.py`.
- Backend persistence/API: SQLAlchemy models in `backend/app/models.py`; GraphBuild registration and routes in `backend/app/main.py`; Neo4j queries in `backend/app/graph_repository.py`.
- Frontend: `frontend/src/pages/GraphPage.tsx`, `frontend/src/pages/Top10MechanismsPage.tsx`, and `frontend/src/api.ts`.

## Runtime and safety

The task-specific isolated staging Neo4j was read-audited before and after import at `bolt://127.0.0.1:17687` (Neo4j 5.26.33 Community); staging PostgreSQL is at `127.0.0.1:15432`. Before import, the graph held 38,890 relationships in the registered baseline GraphBuild. The post-import audit reports the preserved baseline plus the new project GraphBuild, zero duplicate node IDs, and zero duplicate relationship IDs. See `02_live_neo4j_audit.json` and `02_live_neo4j_post_import_audit.json`. The main project Neo4j container was not started or modified.

Stopped-volume archives for both task-specific staging databases are in `data/kg_enrichment/backups/`, with versions, SHA256, restoration checks, and rollback results recorded in `backup_manifest.json`. Both archives restored into fresh temporary instances and the baseline was queryable. The enhancement was imported only into isolated staging; a second restored clone passed a GraphBuild-scoped rollback drill and was cleaned up. The rollback helper intentionally leaves nodes, so 119 newly introduced protein nodes remain isolated in the disposable rollback clone; the old graph version and its relationships remained intact. Full evidence is in `02_import_audit.json` and `02_rollback_rehearsal.json`.

## Integration design and outcome

The frozen Top 10 and current project GraphBundle were retained. New SIGNOR and OmniPath assertions preserve original source record IDs, releases, source evidence, license, and context. Only directed `REGULATES` assertions participate in signed path propagation; Reactome membership and PPI remain unsigned annotation/association evidence. The validated overlay was packaged and registered through AnalysisRun, then imported through the existing GraphBuild API as a new version. A verified import report and exact bundle are linked from `02_import_audit.json`.
