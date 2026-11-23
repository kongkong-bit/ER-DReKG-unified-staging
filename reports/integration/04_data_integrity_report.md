# 04 Data integrity report

- Delivery archive manifest: 89 entries checked against the copied bytes; 0 mismatches.
- Formal GraphBundle `e0421796-2aff-47e2-9228-d683eab05fa9`: 11 entries in `bundle_checksums.json` checked; 0 mismatches.
- Spot SHA-256 checks from syh to staging matched for API main/repository, frontend App/API/Top10 page, KG bundle builder/importer, S2 report and README. The frontend `package-lock.json` hashes also matched.
- S1/S2 formal artifacts remain in the copied syh lineage. The package A+ inputs are a separate analysis run and are not substituted for the syh ranking.
- `wd/.gitattributes` was added to staging to prevent Git line-ending conversion of hash-verified scientific files. No data bytes were rewritten by this addition.
- Full S1/LINCS/PRISM manifests have not all been replayed or independently rehashed; 20.2 GB of files exist in staging, but this is not proof every ignored/external source input required for a clean deployment is present.
- The verified delivery GraphBundle is now registered beneath the canonical project-scoped staging data path. The successful Neo4j import preserved 12,899 nodes / 48,729 edges, and the corresponding GraphBuild records the source input hashes.
- The delivery A+ S2 run is registered as a distinct run and imported at 3,943 conditions. It is not substituted for the historical syh Top10 ranking; both lineages remain independently identifiable.
- The UI/API smoke verified the same selected `pert_id` through the frozen Top10 row, GraphBuild, KG06 Evidence Package and KG07 rule response. The full exact identity record is captured in `02_data_schema_mapping.md` and `cross_store_e2e.json`.
- Two of the ten candidates have no GraphBuild path or unique evidence in their KG06 output. They remain in the acceptance list with explicit gaps and are not converted into supported mechanisms.
