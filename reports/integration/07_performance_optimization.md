# 07 Performance baseline and optimization notes

## Measured baseline

On 2026-11-22, the staging API was measured through FastAPI TestClient against the isolated PostgreSQL 17 and Neo4j 5 acceptance dataset. Each endpoint had one warm-up request excluded, then five sequential warm-cache samples. The full values and method are in `07_api_latency_samples.json` and `07_performance_baseline.csv`.

| API | p50 | p95 | Samples |
|---|---:|---:|---:|
| Top10 index | 50.51 ms | 56.08 ms | 5 |
| DiseaseContext two-hop graph summary | 1,269.00 ms | 1,371.86 ms | 5 |
| KG06 Evidence Package (ponatinib) | 418.07 ms | 729.85 ms | 5 |
| KG07 rule explanation (ponatinib) | 440.20 ms | 548.98 ms | 5 |

This is a small sequential warm-cache sample, not a representative load test or browser latency measurement. No syh-before comparison under the same isolated data and hardware was captured, so performance improvement/regression is not claimed. The graph summary is the slowest measured route and should be profiled with Neo4j query plans before changing its scope or cache semantics.

## Optimization and runtime findings

- KG06/KG07 operate on a selected, build-scoped candidate rather than rebuilding the full graph on each request. The browser uses the existing React Query cache keyed by project, GraphBuild and `pert_id`.
- Top10 data is read from the validated local artifact; the new live section separately queries materialized Neo4j GraphBuilds. This avoids conflating offline report data with imported graph evidence.
- Neo4j reports that `Candidate.rank` and `Candidate.wtcs_median_B` are absent. That yields warnings and null properties in KG06's live graph candidate fields. S2 condition evidence and the frozen Top10 record contain the ranking/WTCS data; a follow-up could enrich the graph candidate node with those explicit source fields after checking import contracts.
- Vite production build warns that the main and chart chunks exceed 500 kB. Top10's Cytoscape dependency is dynamically imported; future bundle splitting should preserve the existing route-level lazy loading and be measured after changes.
- No scientific algorithm or score calculation was modified for performance.
- Memory stability, concurrent load, browser rendering latency and external GLM response time were not measured.
