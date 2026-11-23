# 05 Frontend/backend integration

The staging project has one React/Vite frontend and one FastAPI app. The integrated frontend preserves the syh navigation and offline Top10 evidence dossier, and now exposes the selected candidate's live imported GraphBuild data in the same Top10 page.

## Browser workflow verified

On 2026-11-22, Microsoft Edge opened the staging app at `http://127.0.0.1:15173` while Vite proxied `/api` to the staging FastAPI service on port `18080`. The project overview rendered the ER-positive research project and registered S1/S2/enrichment/GraphBundle run history. Navigation opened **Top 10 机制图谱**. The browser rendered the formal 10-candidate list and ponatinib (`BRD-K44227013`) with WTCS `-0.5167`, then loaded the `materialized` Neo4j GraphBuild `...:06aabcb9af9d1e22`, its KG06 package (157 paths, 258 unique/verified evidence IDs, five S2 conditions), and KG07 `rule_template` explanation with citation-reference validation passing and human review required. The UI keeps the offline dossier and live GraphBuild outputs explicitly labeled as separate artifacts.

The same candidate's API identifiers agree across the Top10 row, GraphBuild, KG06 package and KG07 candidate. The backend's batch check verified all ten candidates; the UI was click-through verified for the first candidate only. Two of ten candidate packages contain zero paths and zero unique evidence, and their gaps remain visible instead of being converted into positive claims.

## Limits

- The browser rendered and fetched live API data through the unified Vite proxy. It did not submit uploads, create projects, or invoke external GLM.
- The in-page LLM generation action was not used because staging has no `ZHIPU_API_KEY`; the live KG07 block intentionally uses `kg_rule`. No external data was transmitted.
- The homepage's “知识图谱局部子图 0 节点” KPI reflects the generic local-subgraph selection, not failure of the selected project GraphBuild. The live Top10 card confirms Neo4j returns graph data for the selected build.
- The existing offline package warning now explains that the offline dossier is separate from the new live GraphBuild card, avoiding a false claim that the live build is not imported.
