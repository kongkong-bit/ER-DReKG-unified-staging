"""Create a compact, candidate-level index of ChEMBL and DGIdb snapshots."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "data" / "top10_kg" / "evidence"
MANIFEST = EVIDENCE / "top10_source_evidence_manifest.json"
IDENTITY = ROOT / "data" / "top10_kg" / "identity" / "top10_identity_mapping.csv"


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    identities = read(IDENTITY)
    mechanisms = read(EVIDENCE / "chembl_mechanisms.csv")
    activities = read(EVIDENCE / "chembl_activities.csv")
    dgidb = read(EVIDENCE / "dgidb_interactions.csv")
    coverage = manifest["activity_coverage"]
    rows = []
    for item in identities:
        pid = item["lincs_pert_id"]
        activity_meta = coverage.get(pid, {})
        rows.append({
            "rank": item["rank"], "pert_id": pid, "canonical_name": item["canonical_name"],
            "chembl_id": item["chembl_id"],
            "chembl_mechanism_records": sum(row["pert_id"] == pid for row in mechanisms),
            "chembl_activity_records_saved": sum(row["pert_id"] == pid for row in activities),
            "chembl_activity_total_count": activity_meta.get("total_count", ""),
            "chembl_activity_status": activity_meta.get("status", "no_query"),
            "chembl_activity_truncated": activity_meta.get("truncated", ""),
            "dgidb_exact_name_interaction_records": sum(row["pert_id"] == pid for row in dgidb),
            "note": "Counts index retrieved source records; assays and aggregated interactions require interpretation and are not automatically direct-target claims.",
        })
    out = EVIDENCE / "top10_source_evidence_summary.csv"
    fields = list(rows[0])
    with out.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    manifest["outputs_sha256"][str(out.relative_to(ROOT))] = sha(out)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} rows={len(rows)} sha256={sha(out)}")


if __name__ == "__main__":
    main()
