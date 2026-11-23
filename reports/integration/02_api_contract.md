# 02 API contract and data schema mapping

## Current application contract surface

The single runtime contract is registered in `backend/app/main.py` and described in `docs/api/api_contract.yaml` (verify generated OpenAPI against both during runtime validation). Relevant existing routes include project/run CRUD and comparison, S1 summary/genes/volcano/pathways/external validation, S2 candidates/summary/conditions/stability/evidence/import/run, KG06 coverage/evidence package, KG07 interpretation, graph summary/search/subgraph, drug mechanisms, Top10 mechanisms/reports, evidence lookup, graph bundle registration, graph build/import/status.

There is no separate API to splice from the delivery package: its `main.py` is explicitly a derived KG-only file with collab imports removed. Keep the complete syh app and reconcile specific state behavior only.

Service error contract verified on staging: database connection loss and Neo4j unavailable/expired sessions return HTTP 503 with a retry-after-recovery detail; KG07 LLM mode without `ZHIPU_API_KEY` also returns HTTP 503 with an explicit configuration detail. Liveness `/health` remains a process check and does not imply database readiness.

## ID and schema mapping

| Domain | PostgreSQL/API | Neo4j/bundle | Rule |
|---|---|---|---|
| Project | `projects.id`, slug | project marker / `project_id` | UUID is canonical; slug is display/config only |
| S1/S2 run | analysis run IDs, type and manifest | `ANALYSIS_RUN:<type>:<uuid>` | maintain distinct run per dataset/version; input hashes immutable |
| Drug | S2 `pert_id` | drug/compound external identifier and `drug_id` | preserve LINCS ID plus explicit external ID mapping; do not join by display name alone |
| Target/gene | source IDs, HGNC symbol | UniProt/Entrez/HGNC nodes | canonical namespace plus source namespace and mapping provenance |
| Pathway | Reactome ID (where present) | pathway node IDs | use accession, label not key |
| Graph build | `graph_build_id`, `build_key`, status | build membership metadata | full build key retained; graph query filtered by requested build |
| Evidence | evidence record identifier/source/PubMed | source evidence relationship/node | PMID is a source citation, not universal evidence ID; merge source references without dropping provenance |
| Mechanism path | route/path identifier | path nodes/relationships | stable scoped ID plus ordered relation/evidence IDs |
| AI report | currently cache key derived from evidence hash/model/prompt/mode | not graph identity | reports are tied to exact Evidence Package; no database persistence claim yet |

No destructive schema merge is proposed. Migration head and live data counts must be checked in isolated PostgreSQL before schema changes.
