# Phase 6 API contract

## Offline report endpoint

`GET /api/v1/projects/{project_id}/top10/mechanism-reports/{pert_id}` returns the rule-generated dossier for a frozen Top 10 candidate. It verifies project ownership, exact frozen candidate membership, all manifest input hashes, and the requested output hash before returning content. Unknown project/candidate returns 404; missing or hash-invalid artifact returns 503. It reads a precomputed local report and does not scan Neo4j.

Response shape:

```json
{
  "project_id": "<project UUID>",
  "artifact_status": "validated_offline_report_artifacts",
  "report": {"rank": 1, "pert_id": "<frozen perturbagen ID>", "candidate_context_paths": [], "evidence_gaps": []},
  "provenance": {"manifest_sha256": "<sha256>", "frozen_top10_sha256": "<sha256>", "report_sha256": "<sha256>"}
}
```

The report object contains detailed evidence dimensions, source-linked literature, target relations, candidate paths and explicit missingness. Consumers must preserve `causal=false` on context paths and must not interpret WTCS as target engagement or a clinical outcome. This endpoint does not yet expose a general graph-version query, path pagination, source-filtered Neo4j traversal or import status API; the offline artifact remains small and bounded to Top 10.
