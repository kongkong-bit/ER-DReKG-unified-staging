"""Build reproducible, source-aware identity files for the frozen Top 10."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports" / "top10_kg"
AUDIT = REPORTS / "top10_graph_bundle" / "3928c54d_external_v1" / "candidate_mapping_audit.csv"
NODES = REPORTS / "top10_graph_bundle" / "3928c54d_external_v1" / "subgraph_nodes.csv"
EXTERNAL = REPORTS / "external_identity_and_mechanism_evidence.csv"
FROZEN = REPORTS / "02_top10_frozen_manifest.json"
OUT = ROOT / "data" / "top10_kg" / "identity"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    audits = {row["pert_id"]: row for row in read_csv(AUDIT)}
    external_rows = read_csv(EXTERNAL)
    external_by_pert: dict[str, dict[str, str]] = {}
    for row in external_rows:
        external_by_pert.setdefault(row["pert_id"], row)

    synonyms: dict[str, list[str]] = {}
    canonical_names: dict[str, str] = {}
    for row in read_csv(NODES):
        if row.get("type") != "Drug":
            continue
        props = json.loads(row.get("properties_json") or "{}")
        for pert_id, audit in audits.items():
            if audit.get("graph_drug_id") == row.get("id"):
                synonyms[pert_id] = sorted(set(props.get("synonyms", [])))
                canonical_names[pert_id] = row.get("label", "")

    fields = [
        "rank", "lincs_pert_id", "lincs_name", "canonical_name", "aliases",
        "pubchem_cid", "chembl_id", "inchikey", "identity_source",
        "source_graph_match", "identity_status", "condition_rows",
    ]
    rows: list[dict[str, str]] = []
    unresolved: list[dict[str, str]] = []
    for candidate in frozen["items"]:
        pert_id = candidate["pert_id"]
        audit = audits[pert_id]
        external = external_by_pert.get(pert_id, {})
        exact_graph = audit["mapping_status"] == "matched_exact_inchikey"
        external_exact = audit["mapping_status"] == "matched_external_exact_inchikey"
        graph_id = audit.get("graph_drug_id", "")
        if graph_id.startswith("CHEMBL"):
            chembl_id = graph_id
        else:
            chembl_id = external.get("chembl_id", "")
        alias_values = set(synonyms.get(pert_id, []))
        alias_values.discard(candidate["pert_iname"])
        source = "LINCS PertInfo InChIKey; OptimusKG 3.2 exact InChIKey"
        if external_exact:
            source = "LINCS PertInfo InChIKey; external PubChem/ChEMBL exact identity cross-reference"
        row = {
            "rank": str(candidate["rank"]),
            "lincs_pert_id": pert_id,
            "lincs_name": candidate["pert_iname"],
            "canonical_name": canonical_names.get(pert_id) or candidate["pert_iname"],
            "aliases": "|".join(sorted(alias_values)),
            "pubchem_cid": external.get("pubchem_cid", ""),
            "chembl_id": chembl_id,
            "inchikey": audit.get("inchi_key", ""),
            "identity_source": source,
            "source_graph_match": graph_id,
            "identity_status": "matched_external_exact_inchikey" if external_exact else audit["mapping_status"],
            "condition_rows": audit.get("condition_rows", ""),
        }
        rows.append(row)
        if not exact_graph and not external_exact:
            unresolved.append({"pert_id": pert_id, "name": candidate["pert_iname"], "inchikey": row["inchikey"], "reason": audit["mapping_status"]})

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "top10_identity_mapping.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    with (OUT / "unresolved_identity_candidates.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["pert_id", "name", "inchikey", "reason"])
        writer.writeheader()
        writer.writerows(unresolved)
    manifest = {
        "status": "built_from_frozen_manifest_and_exact_identity_audits",
        "candidate_count": len(rows),
        "exactly_resolved_count": len(rows) - len(unresolved),
        "unresolved_count": len(unresolved),
        "frozen_top10_sha256": frozen["source_sha256"],
        "source_hashes": {str(path.relative_to(ROOT)): sha256(path) for path in [FROZEN, AUDIT, NODES, EXTERNAL]},
        "outputs": {
            "top10_identity_mapping.csv": sha256(OUT / "top10_identity_mapping.csv"),
            "unresolved_identity_candidates.csv": sha256(OUT / "unresolved_identity_candidates.csv"),
        },
        "policy": "No fuzzy name matching. Local exact graph mapping and external exact InChIKey resolution remain distinct statuses.",
    }
    (OUT / "identity_mapping_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
