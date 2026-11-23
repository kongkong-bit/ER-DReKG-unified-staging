# 02 Module ownership

| Module | Owner in unified staging | Source decision |
|---|---|---|
| S1 expression and pathway enrichment | `backend/app/s1_*`, `experiments/s1_pathway_enrichment`, `s1_初步_gse42568_limma` | syh owns canonical implementation and results; keep external S1 as separate validation run |
| S2 LINCS / WTCS / ranking | `backend/app/s2_*`, `s2_lincs` | syh owns canonical current results; A+ delivery input is separate run lineage |
| Reliability / PRISM | `experiments/exp007..exp011`, `experiments/second_round_summary` | preserve syh reports and data; compare wd additions by manifest/hash before migration |
| PostgreSQL project/run/evidence models | `backend/app/models.py`, `backend/migrations` | one schema and migration chain, syh is authority |
| KG bundle build and import | `kg/scripts`, `kg/config` | syh current working implementation; compare delivery scripts by exact hash/behavior; delivery evidence is authoritative for that recorded build only |
| Live graph read/query | `backend/app/graph_repository.py`, graph routes in `backend/app/main.py` | one Neo4j repository; avoid importing duplicate wd repository |
| KG06 evidence package / KG07 explanation | `backend/app/kg06.py`, `backend/app/kg07.py` | syh implementation; wd evaluations may be adopted as experiments after input/source audit |
| Frontend and navigation | `frontend/src` | syh React/Vite application; do not keep `frontend_redesign` as a second runtime unless it is shown to be the actual selected entry |
| Ops and audit scripts | `scripts/`, `backend/tools/`, `kg/scripts/` | consolidate into existing ownership; every imported CLI must accept configured paths and have dry-run where it writes data |
| zq material | none observed | no code available to assign |
