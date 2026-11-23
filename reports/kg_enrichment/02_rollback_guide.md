# Rollback and database safety

## Current state

The task-specific isolated staging databases were audited and backed up before import. The stopped-volume archives are under `data/kg_enrichment/backups/`; their SHA256 values and database versions are in `backup_manifest.json`. Both archives were restored to fresh temporary volumes, and the restored Neo4j returned 6,866 nodes/38,890 baseline relationships while PostgreSQL retained its baseline GraphBuild. The temporary services and volumes were removed after verification.

The enhanced GraphBuild is registered and remains in the task staging environment. No main/production database was modified. `02_import_audit.json` and `02_live_neo4j_post_import_audit.json` contain the applied-version verification.

## Rollback drill

The new GraphBuild was imported into a second pair of databases restored from the backup. The helper's dry-run and apply both passed for exactly `GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:c48926d9a9983865`. It removed 39,351 build-scoped relationships, 39,218 EvidenceRecord rows, and one DiseaseContext snapshot; the previous 38,890-relationship GraphBuild remained. It preserved all node rows, so 119 newly introduced Protein nodes remained isolated in the disposable rollback clone. That behavior avoids deleting shared entities; this rollback helper does not promise a byte-identical node inventory. The clone was discarded after validation. Full counts are in `02_rollback_rehearsal.json`.

For a future rollback, use `backend/tools/rollback_graph_build.py` only with an exact GraphBuild ID and matching `--confirm-graph-build-id`. Preview first and compare expected counts. The helper preserves nodes, removes only relationships with the build membership and ID suffix, and deletes only that build's PostgreSQL evidence/context snapshot. Never wipe a database, delete by label, or replace the project volume.

## Repeatable offline preparation

Commands include `python kg/scripts/kg_enrichment.py audit`, `status`, `build-subgraphs` (or `reason`), `generate-reports` (or `evaluate`), `normalize`, `normalize-mapped`, `normalize-reactome`, and `download`. `python kg/scripts/package_top10_regulatory_graph_bundle.py` creates a new immutable GraphBundle from the frozen baseline and validated regulatory extension. `python kg/scripts/preflight_graph_bundle_neo4j.py` runs BioCypher plus a read-only shared-entity/import-identity preflight. The resulting GraphBundle is registered and imported through the existing AnalysisRun/GraphBuild path.

## Reactome/PrimeKG 外部层回滚演练

第二个增量 GraphBuild `GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:6ea657f0a3a95099` 已在独立临时副本中完成恢复与回滚演练：预览和实际删除均为 91,943 条关系、91,810 条证据记录及 1 条疾病上下文，未删除共享节点；旧 GraphBuild 的 38,890 与 39,351 条关系保持不变。分析运行记录保留，临时容器和卷已清理。原 staging 保留导入结果。详情见 `09_external_layer_import_audit.json`。
