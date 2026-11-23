"""Fetch Reactome human pathway mappings for proteins in ChEMBL mechanisms.

The output records protein-component participation only. It does not turn a
ChEMBL protein-family mechanism into direct targeting of every family member.
"""
from __future__ import annotations

import csv
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "data" / "top10_kg" / "evidence"
RAW = ROOT / "data" / "top10_kg" / "raw" / "reactome"
TARGETS = EVIDENCE / "chembl_mechanism_targets.csv"
CHEMBL_MANIFEST = EVIDENCE / "top10_source_evidence_manifest.json"
BASE = "https://reactome.org/ContentService"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def fetch_json(url: str) -> tuple[object | None, dict]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "ER-DReKG-Top10-pathway-evidence/1.0"})
    retrieved = datetime.now(timezone.utc).isoformat()
    try:
        with urlopen(request, timeout=45) as response:
            raw = response.read()
            parsed = json.loads(raw.decode("utf-8"))
            return parsed, {"status": "ok", "http_status": response.status, "retrieved_at_utc": retrieved,
                            "request_url": url, "response_sha256": hashlib.sha256(raw).hexdigest(), "response_bytes": len(raw)}
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        return None, {"status": "error", "retrieved_at_utc": retrieved, "request_url": url,
                      "error_type": type(error).__name__, "error": str(error)}


def main() -> None:
    chembl_manifest = json.loads(CHEMBL_MANIFEST.read_text(encoding="utf-8"))
    target_rows = read_csv(TARGETS)
    accessions = sorted({row["component_accession"] for row in target_rows if row.get("component_accession")})
    RAW.mkdir(parents=True, exist_ok=True)
    pathways_by_accession: dict[str, list[dict]] = {}
    calls: list[dict] = []
    for accession in accessions:
        url = f"{BASE}/data/mapping/UniProt/{quote(accession, safe='')}/pathways?species=Homo%20sapiens"
        raw_path = RAW / f"uniprot_{accession}_pathways.json"
        if raw_path.is_file():
            cached = json.loads(raw_path.read_text(encoding="utf-8"))
            payload = cached.get("payload")
            metadata = {**cached.get("metadata", {}), "status": "cached"}
        else:
            payload, metadata = fetch_json(url)
            if payload is not None:
                raw_path.write_text(json.dumps({"metadata": metadata, "payload": payload}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                metadata["raw_snapshot_sha256"] = sha(raw_path)
            time.sleep(0.15)
        pathways_by_accession[accession] = payload if isinstance(payload, list) else []
        calls.append({"source": "Reactome Content Service", "uniprot_accession": accession, **metadata,
                      "returned_pathway_rows": len(pathways_by_accession[accession])})

    version_url = f"{BASE}/data/database/version"
    version_path = RAW / "database_version.txt"
    if version_path.is_file():
        version_text = version_path.read_text(encoding="utf-8").strip()
        version_meta = {"status": "cached", "request_url": version_url}
    else:
        _, version_meta = fetch_json(version_url)
        # Version endpoint is text/plain; request it separately and preserve the exact body.
        try:
            request = Request(version_url, headers={"Accept": "text/plain", "User-Agent": "ER-DReKG-Top10-pathway-evidence/1.0"})
            with urlopen(request, timeout=45) as response:
                version_text = response.read().decode("utf-8").strip()
                version_meta = {"status": "ok", "http_status": response.status, "request_url": version_url}
                version_path.write_text(version_text + "\n", encoding="utf-8")
        except (HTTPError, URLError, TimeoutError) as error:
            version_text = "unknown"
            version_meta = {"status": "error", "request_url": version_url, "error": str(error)}
    calls.append({"source": "Reactome Content Service", "endpoint": "database_version", **version_meta, "version": version_text})

    pathway_records = {row.get("stId"): row for pathways in pathways_by_accession.values() for row in pathways
                       if isinstance(row, dict) and row.get("stId")}
    hierarchy_rows: dict[tuple[str, str], dict] = {}
    def hierarchy_payload(pathway_id: str) -> tuple[str, object, dict]:
        url = f"{BASE}/data/event/{quote(pathway_id, safe='')}/ancestors"
        raw_path = RAW / f"pathway_{pathway_id}_ancestors.json"
        if raw_path.is_file():
            cached = json.loads(raw_path.read_text(encoding="utf-8"))
            payload = cached.get("payload")
            metadata = {**cached.get("metadata", {}), "status": "cached"}
        else:
            payload, metadata = fetch_json(url)
            if payload is not None:
                raw_path.write_text(json.dumps({"metadata": metadata, "payload": payload}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                metadata["raw_snapshot_sha256"] = sha(raw_path)
        return pathway_id, payload, metadata

    with ThreadPoolExecutor(max_workers=8) as executor:
      for pathway_id, payload, metadata in executor.map(hierarchy_payload, sorted(pathway_records)):
        calls.append({"source": "Reactome Content Service", "endpoint": "event_ancestors", "pathway_id": pathway_id, **metadata})
        branches = payload if isinstance(payload, list) else []
        if branches and isinstance(branches[0], dict):
            branches = [branches]
        for branch in branches:
            if not isinstance(branch, list):
                continue
            chain = [event for event in branch if isinstance(event, dict) and event.get("stId")]
            for child, parent in zip(chain, chain[1:]):
                key = (child["stId"], parent["stId"])
                hierarchy_rows[key] = {
                    "child_pathway_id": child["stId"], "child_pathway_name": child.get("displayName", ""),
                    "parent_pathway_id": parent["stId"], "parent_pathway_name": parent.get("displayName", ""),
                    "organism": child.get("speciesName", ""), "source_database": "Reactome",
                    "source_version": version_text, "source_record_id": f"{child['stId']}:hasEvent:{parent['stId']}",
                    "source_url": f"https://reactome.org/content/detail/{child['stId']}",
                }

    rows: list[dict] = []
    for target in target_rows:
        accession = target.get("component_accession", "")
        for pathway in pathways_by_accession.get(accession, []):
            if pathway.get("speciesName") != "Homo sapiens" or pathway.get("schemaClass") != "Pathway":
                continue
            rows.append({
                "pert_id": target["pert_id"], "molecule_chembl_id": target["molecule_chembl_id"],
                "chembl_target_id": target["target_chembl_id"], "chembl_target_name": target["target_name"],
                "chembl_target_type": target["target_type"], "uniprot_accession": accession,
                "component_relation": target["component_relationship"], "pathway_id": pathway.get("stId", ""),
                "pathway_version": pathway.get("stIdVersion", ""), "pathway_name": pathway.get("displayName", ""),
                "organism": pathway.get("speciesName", ""), "is_disease_pathway": pathway.get("isInDisease", ""),
                "is_inferred": pathway.get("isInferred", ""), "mapping_release_date": pathway.get("releaseDate", ""),
                "source_database": "Reactome", "source_version": version_text,
                "source_record_id": f"{pathway.get('stId', '')}:{accession}",
                "source_url": f"https://reactome.org/content/detail/{pathway.get('stId', '')}",
                "interpretation": "UniProt protein-to-pathway mapping; participation only, no activation/inhibition or ER+ disease claim.",
            })
    output = EVIDENCE / "reactome_protein_pathways.csv"
    fields = list(rows[0]) if rows else ["pert_id", "molecule_chembl_id", "chembl_target_id", "chembl_target_name", "chembl_target_type", "uniprot_accession", "component_relation", "pathway_id", "pathway_version", "pathway_name", "organism", "is_disease_pathway", "is_inferred", "mapping_release_date", "source_database", "source_version", "source_record_id", "source_url", "interpretation"]
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    calls_path = EVIDENCE / "top10_reactome_api_calls.json"
    calls_path.write_text(json.dumps(calls, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    hierarchy_path = EVIDENCE / "reactome_pathway_hierarchy.csv"
    hierarchy_fields = ["child_pathway_id", "child_pathway_name", "parent_pathway_id", "parent_pathway_name", "organism", "source_database", "source_version", "source_record_id", "source_url"]
    with hierarchy_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=hierarchy_fields)
        writer.writeheader()
        writer.writerows(hierarchy_rows.values())
    raw_hashes = {path.name: sha(path) for path in sorted(RAW.iterdir()) if path.is_file()}
    manifest = {
        "status": "retrieved_with_recorded_source_call_status", "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "frozen_top10_sha256": chembl_manifest["frozen_top10_sha256"],
        "chembl_target_components_sha256": sha(TARGETS), "reactome_content_service": BASE,
        "reactome_release": version_text, "unique_uniprot_accessions_queried": len(accessions),
        "mechanism_target_component_rows": len(target_rows), "protein_pathway_rows": len(rows),
        "unique_pathways": len({row["pathway_id"] for row in rows}),
        "hierarchy_relation_rows": len(hierarchy_rows),
        "api_call_count": len(calls), "api_error_count": sum(call.get("status") == "error" for call in calls),
        "api_calls": calls, "raw_snapshot_sha256": raw_hashes,
        "output_sha256": {output.name: sha(output), hierarchy_path.name: sha(hierarchy_path), calls_path.name: sha(calls_path)},
        "policy": "Reactome mappings are human pathway participation associations for ChEMBL target components. Family components remain family components; no direct-target, direction, disease-specificity, or efficacy claims are inferred.",
    }
    (EVIDENCE / "top10_reactome_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "release": version_text, "accessions": len(accessions), "pathway_rows": len(rows), "unique_pathways": manifest["unique_pathways"], "errors": manifest["api_error_count"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
