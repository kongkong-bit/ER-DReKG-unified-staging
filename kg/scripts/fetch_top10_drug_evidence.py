"""Fetch source records for frozen Top 10 from ChEMBL and DGIdb.

Raw API JSON is retained for audit. This script never promotes interactions to
direct targets; classification happens in a separate evidence review step.
"""
from __future__ import annotations

import csv
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
FROZEN = ROOT / "reports" / "top10_kg" / "02_top10_frozen_manifest.json"
IDENTITY = ROOT / "data" / "top10_kg" / "identity" / "top10_identity_mapping.csv"
RAW = ROOT / "data" / "top10_kg" / "raw"
EVIDENCE = ROOT / "data" / "top10_kg" / "evidence"
CHEMBL_BASE = "https://www.ebi.ac.uk/chembl/api/data"
DGIDB_URL = "https://dgidb.org/api/graphql"
MAX_ACTIVITIES_PER_DRUG = 1000


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def request_json(url: str, body: dict | None = None) -> tuple[dict, dict]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Accept": "application/json", "User-Agent": "ER-DReKG-Top10-evidence-fetch/1.0"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method="POST" if data is not None else "GET")
    timestamp = datetime.now(timezone.utc).isoformat()
    try:
        with urlopen(request, timeout=45) as response:
            raw = response.read()
            parsed = json.loads(raw.decode("utf-8"))
            return parsed, {"status": "ok", "http_status": response.status, "retrieved_at_utc": timestamp,
                            "request_url": url, "response_sha256": sha_bytes(raw), "response_bytes": len(raw)}
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        return {}, {"status": "error", "retrieved_at_utc": timestamp, "request_url": url,
                    "error_type": type(error).__name__, "error": str(error)}


def save_raw(path: Path, payload: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    path.write_bytes(data)
    return sha_bytes(data)


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    identities = {row["lincs_pert_id"]: row for row in read_csv(IDENTITY)}
    mechanisms: list[dict] = []
    activities: list[dict] = []
    mechanism_targets: list[dict] = []
    calls: list[dict] = []
    outputs: dict[str, str] = {}
    activity_coverage: dict[str, dict] = {}

    for item in frozen["items"]:
        pid = item["pert_id"]
        chembl_id = identities.get(pid, {}).get("chembl_id", "")
        if not chembl_id.startswith("CHEMBL"):
            activity_coverage[pid] = {"status": "no_chembl_id_in_identity_audit", "records": 0}
            continue
        for endpoint in ("mechanism", "activity"):
            params = {"molecule_chembl_id": chembl_id, "limit": MAX_ACTIVITIES_PER_DRUG if endpoint == "activity" else 1000, "offset": 0}
            url = f"{CHEMBL_BASE}/{endpoint}.json?{urlencode(params)}"
            safe_id = f"{pid}_{chembl_id}_{endpoint}.json"
            raw_path = RAW / "chembl" / safe_id
            if raw_path.is_file():
                cached = json.loads(raw_path.read_text(encoding="utf-8"))
                payload, meta = cached.get("payload", {}), {**cached.get("metadata", {}), "status": "cached"}
            else:
                payload, meta = request_json(url)
                if payload:
                    raw_hash = save_raw(raw_path, {"metadata": meta, "payload": payload})
                    meta["raw_snapshot_sha256"] = raw_hash
            calls.append({"source": "ChEMBL", "pert_id": pid, "chembl_id": chembl_id, "endpoint": endpoint, **meta})
            if meta["status"] not in {"ok", "cached"}:
                if endpoint == "activity":
                    activity_coverage[pid] = {"status": "api_error", "records": 0, "error": meta.get("error", "")}
                time.sleep(0.35)
                continue
            records = payload.get("mechanisms" if endpoint == "mechanism" else "activities", [])
            page_meta = payload.get("page_meta", {})
            if endpoint == "mechanism":
                for row in records:
                    mechanisms.append({"pert_id": pid, "rank": item["rank"], "molecule_chembl_id": chembl_id,
                                       "mechanism_id": row.get("mechanism_id"), "target_chembl_id": row.get("target_chembl_id"),
                                       "mechanism_of_action": row.get("mechanism_of_action"), "action_type": row.get("action_type"),
                                       "direct_interaction": row.get("direct_interaction"), "selectivity": row.get("selectivity"),
                                       "binding_site_name": row.get("binding_site_name"),
                                       "mechanism_refs": json.dumps(row.get("mechanism_refs", []), ensure_ascii=False),
                                       "record": json.dumps(row, ensure_ascii=False, sort_keys=True)})
            else:
                truncated = bool(page_meta.get("next"))
                activity_coverage[pid] = {"status": "partial_at_1000_cap" if truncated else "complete_for_endpoint_query",
                                          "records": len(records), "total_count": page_meta.get("total_count"), "truncated": truncated}
                for row in records:
                    activities.append({"pert_id": pid, "rank": item["rank"], "molecule_chembl_id": chembl_id,
                                       "activity_id": row.get("activity_id"), "target_chembl_id": row.get("target_chembl_id"),
                                       "target_pref_name": row.get("target_pref_name"), "target_organism": row.get("target_organism"),
                                       "target_type": row.get("target_type"), "standard_type": row.get("standard_type"),
                                       "standard_relation": row.get("standard_relation"), "standard_value": row.get("standard_value"),
                                       "standard_units": row.get("standard_units"), "pchembl_value": row.get("pchembl_value"),
                                       "assay_chembl_id": row.get("assay_chembl_id"), "assay_type": row.get("assay_type"),
                                       "assay_description": row.get("assay_description"), "document_chembl_id": row.get("document_chembl_id"),
                                       "record": json.dumps(row, ensure_ascii=False, sort_keys=True)})
            time.sleep(0.35)

    target_ids = sorted({row["target_chembl_id"] for row in mechanisms if row.get("target_chembl_id")})
    for target_id in target_ids:
        url = f"{CHEMBL_BASE}/target/{target_id}.json"
        raw_path = RAW / "chembl" / f"target_{target_id}.json"
        if raw_path.is_file():
            cached = json.loads(raw_path.read_text(encoding="utf-8"))
            target, meta = cached.get("payload", {}), {**cached.get("metadata", {}), "status": "cached"}
        else:
            target, meta = request_json(url)
            if target:
                meta["raw_snapshot_sha256"] = save_raw(raw_path, {"metadata": meta, "payload": target})
        calls.append({"source": "ChEMBL", "endpoint": "target", "target_chembl_id": target_id, **meta})
        if meta["status"] not in {"ok", "cached"}:
            continue
        components = target.get("target_components", []) or []
        if not components:
            components = [{}]
        related_mechanisms = [row for row in mechanisms if row.get("target_chembl_id") == target_id]
        for mechanism in related_mechanisms:
            for component in components:
                mechanism_targets.append({"pert_id": mechanism["pert_id"], "molecule_chembl_id": mechanism["molecule_chembl_id"],
                                         "mechanism_id": mechanism["mechanism_id"], "target_chembl_id": target_id,
                                         "target_name": target.get("pref_name"), "target_type": target.get("target_type"),
                                         "target_organism": target.get("organism"), "component_accession": component.get("accession"),
                                         "component_type": component.get("component_type"), "component_relationship": component.get("relationship"),
                                         "component_synonyms": json.dumps(component.get("target_component_synonyms", []), ensure_ascii=False),
                                         "component_xrefs": json.dumps(component.get("target_component_xrefs", []), ensure_ascii=False),
                                         "source_url": f"{CHEMBL_BASE}/target/{target_id}.json"})
        time.sleep(0.35)

    dgidb_names = [item["pert_iname"].upper() for item in frozen["items"]]
    gql = """query Top10Interactions($names: [String!]!) {
      drugs(names: $names) { nodes { name conceptId interactions {
        gene { name conceptId longName } interactionScore
        interactionTypes { type directionality }
        interactionAttributes { name value }
        publications { pmid } sources { sourceDbName }
      } } }
    }"""
    gql_body = {"query": gql, "variables": {"names": dgidb_names}}
    dgidb_cache_path = RAW / "dgidb" / "top10_drug_interactions.json"
    if dgidb_cache_path.is_file():
        cached = json.loads(dgidb_cache_path.read_text(encoding="utf-8"))
        dgidb_payload, dgidb_meta = cached.get("payload", {}), {**cached.get("metadata", {}), "status": "cached"}
    else:
        dgidb_payload, dgidb_meta = request_json(DGIDB_URL, gql_body)
    dgidb_raw_hash = ""
    dgidb_rows: list[dict] = []
    dgidb_query_nodes: list[dict] = []
    if dgidb_payload:
        if not dgidb_cache_path.is_file():
            dgidb_raw_hash = save_raw(dgidb_cache_path, {"metadata": dgidb_meta, "query": gql_body, "payload": dgidb_payload})
        else:
            dgidb_raw_hash = sha_bytes(dgidb_cache_path.read_bytes())
        for drug in (((dgidb_payload.get("data") or {}).get("drugs") or {}).get("nodes") or []):
            pert_candidates = [item for item in frozen["items"] if item["pert_iname"].casefold() == str(drug.get("name", "")).casefold()]
            pid = pert_candidates[0]["pert_id"] if pert_candidates else ""
            interactions = drug.get("interactions", [])
            dgidb_query_nodes.append({"returned_drug_name": drug.get("name"), "dgidb_drug_id": drug.get("conceptId"),
                                      "exact_pert_id_match": pid, "identity_status": "exact_name" if pid else "unresolved_returned_name",
                                      "interaction_count": len(interactions)})
            for interaction in interactions:
                dgidb_rows.append({"pert_id": pid, "query_drug_name": drug.get("name"), "dgidb_drug_id": drug.get("conceptId"),
                                   "gene_name": (interaction.get("gene") or {}).get("name"),
                                   "gene_concept_id": (interaction.get("gene") or {}).get("conceptId"),
                                   "gene_long_name": (interaction.get("gene") or {}).get("longName"),
                                   "interaction_score": interaction.get("interactionScore"),
                                   "interaction_types": json.dumps(interaction.get("interactionTypes", []), ensure_ascii=False),
                                   "interaction_attributes": json.dumps(interaction.get("interactionAttributes", []), ensure_ascii=False),
                                   "publications": json.dumps(interaction.get("publications", []), ensure_ascii=False),
                                   "sources": json.dumps(interaction.get("sources", []), ensure_ascii=False),
                                   "interpretation": "Aggregated drug-gene interaction only; not automatically a direct target claim."})
    dgidb_meta["raw_snapshot_sha256"] = dgidb_raw_hash
    calls.append({"source": "DGIdb", "endpoint": DGIDB_URL, "query_drug_count": len(dgidb_names), **dgidb_meta})

    write_csv(EVIDENCE / "chembl_mechanisms.csv", mechanisms,
              ["pert_id", "rank", "molecule_chembl_id", "mechanism_id", "target_chembl_id", "mechanism_of_action", "action_type", "direct_interaction", "selectivity", "binding_site_name", "mechanism_refs", "record"])
    write_csv(EVIDENCE / "chembl_mechanism_targets.csv", mechanism_targets,
              ["pert_id", "molecule_chembl_id", "mechanism_id", "target_chembl_id", "target_name", "target_type", "target_organism", "component_accession", "component_type", "component_relationship", "component_synonyms", "component_xrefs", "source_url"])
    write_csv(EVIDENCE / "chembl_activities.csv", activities,
              ["pert_id", "rank", "molecule_chembl_id", "activity_id", "target_chembl_id", "target_pref_name", "target_organism", "target_type", "standard_type", "standard_relation", "standard_value", "standard_units", "pchembl_value", "assay_chembl_id", "assay_type", "assay_description", "document_chembl_id", "record"])
    write_csv(EVIDENCE / "dgidb_interactions.csv", dgidb_rows,
              ["pert_id", "query_drug_name", "dgidb_drug_id", "gene_name", "gene_concept_id", "gene_long_name", "interaction_score", "interaction_types", "interaction_attributes", "publications", "sources", "interpretation"])
    write_csv(EVIDENCE / "dgidb_returned_drug_nodes.csv", dgidb_query_nodes,
              ["returned_drug_name", "dgidb_drug_id", "exact_pert_id_match", "identity_status", "interaction_count"])
    call_path = EVIDENCE / "top10_source_api_calls.json"
    call_path.write_text(json.dumps(calls, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for path in [EVIDENCE / "chembl_mechanisms.csv", EVIDENCE / "chembl_mechanism_targets.csv", EVIDENCE / "chembl_activities.csv", EVIDENCE / "dgidb_interactions.csv", EVIDENCE / "dgidb_returned_drug_nodes.csv", call_path]:
        outputs[str(path.relative_to(ROOT))] = sha_bytes(path.read_bytes())
    exact_dgidb_ids = sorted({row["exact_pert_id_match"] for row in dgidb_query_nodes if row["exact_pert_id_match"]})
    manifest = {"status": "retrieved_with_recorded_source_call_status", "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                "frozen_top10_sha256": frozen["source_sha256"], "identity_mapping_sha256": sha_bytes(IDENTITY.read_bytes()),
                "chembl_api_base": CHEMBL_BASE, "dgidb_api_endpoint": DGIDB_URL,
                "activity_per_molecule_cap": MAX_ACTIVITIES_PER_DRUG, "activity_coverage": activity_coverage,
                "chembl_mechanism_rows": len(mechanisms), "chembl_activity_rows": len(activities), "dgidb_interaction_rows": len(dgidb_rows),
                "chembl_mechanism_target_component_rows": len(mechanism_targets),
                "dgidb_exact_name_candidate_coverage": len(exact_dgidb_ids), "dgidb_exact_name_pert_ids": exact_dgidb_ids,
                "dgidb_unresolved_interaction_rows": sum(1 for row in dgidb_rows if not row["pert_id"]),
                "api_call_count": len(calls), "api_error_count": sum(1 for call in calls if call.get("status") not in {"ok", "cached"}),
                "outputs_sha256": outputs,
                "policy": "Raw responses retained. No API errors or truncated results are interpreted as no known relationship. ChEMBL activities and DGIdb interactions are not promoted automatically to direct targets."}
    (EVIDENCE / "top10_source_evidence_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "chembl_mechanism_rows": len(mechanisms),
                      "chembl_activity_rows": len(activities), "dgidb_interaction_rows": len(dgidb_rows),
                      "api_errors": manifest["api_error_count"], "activity_coverage": activity_coverage,
                      "manifest": str((EVIDENCE / "top10_source_evidence_manifest.json").relative_to(ROOT))}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
