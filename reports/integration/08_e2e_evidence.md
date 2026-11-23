# 08 Browser and cross-store E2E evidence

Date: 2026-11-22. Test environment: staging source under `D:\CLASS\ER-DReKG-unified-staging`; dedicated PostgreSQL 17/Neo4j 5 acceptance containers; staging FastAPI on `127.0.0.1:18080`; staging Vite frontend on `127.0.0.1:15173`; Microsoft Edge.

## Browser flow

1. Opened the unified frontend at `http://127.0.0.1:15173`; Vite served HTTP 200 and proxied API requests to the staging backend.
2. Project overview loaded **ER 阳性乳腺癌药物重定位（GSE42568）** and showed completed S1, enrichment, S2, GraphBundle and graph history rows.
3. Used the app navigation to open **Top 10 机制图谱**.
4. Verified the first frozen Top10 row: ponatinib, `BRD-K44227013`, WTCS `-0.5167`, `LJP009_MCF7_24H:E19`; the detail page showed exact InChIKey mapping to `CHEMBL1171837` and source-linked mechanism evidence.
5. The new live GraphBuild card selected the Neo4j build `GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:06aabcb9af9d1e22` and rendered KG06 package `KG06:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:06aabcb9af9d1e22:BRD-K44227013:fc4a92159faaf455`: 157 paths, 258 unique and verified evidence IDs, five S2 conditions, integrity pass.
6. The same card rendered KG07 `rule_template`, citation-reference validation pass, and a human-review-required status. Rule claims retained evidence/path IDs. It clearly labels this output as a rule template rather than a GLM result.
7. The offline Top10 dossier and live imported GraphBuild results are labeled separately. The user can choose a different materialized Neo4j GraphBuild and the selected perturbagen's package is refetched.

## Batch and service evidence

- `cross_store_e2e.json`: PASS. The normal API flow imported the S2 run (3,943 conditions), registered/built the GraphBundle and returned the Neo4j DiseaseContext two-hop projection (12,171 nodes / 44,932 edges).
- `08_top10_acceptance.csv`: 10/10 rows returned KG06 and KG07 rule output; citation-reference validation passed on every row. Candidate-level evidence gaps are recorded in the final column. Ranks 6 and 9 have no path and zero unique evidence; this is an explicit evidence gap, not a positive mechanism.
- Full graph inventory from the import verifier: 12,899 nodes / 48,729 edges, zero inventory problems. It is a separate scope from the API two-hop projection.
- Missing-key fault check: `kg_llm` returned HTTP 503 with `Zhipu API key is not configured (ZHIPU_API_KEY)`. No external provider request was made.
- Neo4j fault/recovery: while the isolated Neo4j container was stopped, graph summary returned HTTP 503 with `Neo4j is unavailable; retry after the graph service recovers.` After restarting Neo4j to healthy, graph requests succeeded again.
- PostgreSQL fault/recovery: with the acceptance API's `connect_timeout=1` and only the isolated PostgreSQL container stopped, project list returned HTTP 503 with `PostgreSQL is unavailable; retry after the database service recovers.` After PostgreSQL restarted, the same endpoint returned HTTP 200 with the registered project.
- Uvicorn health returned `{"status":"ok"}` and OpenAPI exposed 41 route paths.

## Not covered

- Browser UI was inspected for the project overview and the first Top10 candidate only; batch API checks cover the remaining nine. UI selection of every row was not exercised.
- No GLM request, timeout, or model-generated cached-report display was tested because no provider key was configured.
- Upload UI, and sustained browser performance/memory were not tested.
- Neo4j emitted warnings because `Candidate.rank` and `Candidate.wtcs_median_B` properties are absent from this imported graph. KG06/KG07 succeeded; graph rank/WTCS values remain sourced from the verified Top10/S2 result rather than those absent properties.
