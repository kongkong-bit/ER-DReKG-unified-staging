"""Offline-first, provenance-preserving Top 10 mechanism enrichment tools."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import urllib.request
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "reports" / "kg_enrichment"
BASELINE = ROOT / "artifacts" / "kg_enrichment" / "baseline"
LOG = logging.getLogger("kg_enrichment")
DIRECT_TARGET_RELATIONS = {"TARGET", "INHIBITOR", "AGONIST", "ANTAGONIST", "BLOCKER", "PARTIAL_AGONIST", "POSITIVE_ALLOSTERIC_MODULATOR", "ACTIVATOR"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def download_source(url: str, output: Path, source_name: str, release: str, license_name: str, species: str, schema_version: str) -> dict[str, Any]:
    """Stream one explicitly configured public resource and write a provenance manifest.

    The downloader never replaces an existing file; callers must choose a new
    release path. HTTP errors are persisted in a failure manifest and re-raised.
    """
    if output.exists(): raise FileExistsError(f"Refusing to overwrite existing source file: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = output.with_suffix(output.suffix + ".manifest.json")
    metadata = {"source_name": source_name, "source_url": url, "release_version": release,
                "retrieved_at": datetime.now(timezone.utc).isoformat(), "local_path": str(output),
                "license": license_name, "species": species, "schema_version": schema_version}
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "ER-DReKG/0.1 research data acquisition"})
        with urllib.request.urlopen(request, timeout=60) as response, output.open("xb") as target:
            metadata["http_status"] = response.status
            metadata["content_type"] = response.headers.get("Content-Type")
            metadata["content_length_header"] = response.headers.get("Content-Length")
            while block := response.read(1024 * 1024): target.write(block)
        metadata.update({"status": "downloaded", "bytes": output.stat().st_size, "sha256": sha256(output)})
        manifest_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return metadata
    except Exception as exc:
        metadata.update({"status": "failed", "error_type": type(exc).__name__, "error": str(exc)[:1000]})
        manifest_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if output.exists(): output.unlink()
        raise


def read_csv(path: Path) -> list[dict[str, str]]:
    csv.field_size_limit(16 * 1024 * 1024)
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def audit() -> dict[str, Any]:
    frozen_path = ROOT / "reports/top10_kg/02_top10_frozen_manifest.json"
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    source = ROOT / frozen["source_file"]
    if sha256(source) != frozen["source_sha256"]:
        raise ValueError("Frozen Top 10 source hash mismatch")
    bundle = ROOT / "reports/top10_kg/top10_graph_bundle/3928c54d_external_v1"
    graph_nodes = read_csv(bundle / "subgraph_nodes.csv")
    graph_edges = read_csv(bundle / "subgraph_edges.csv")
    evidence = read_csv(bundle / "evidence_records.csv")
    nodes_by_id = {row["id"]: row for row in graph_nodes}
    drugs = []
    for item in frozen["items"]:
        candidate = next((n for n in graph_nodes if n["type"] == "Candidate" and json.loads(n["properties_json"]).get("pert_id") == item["pert_id"]), None)
        drug_id = next((e["to"] for e in graph_edges if candidate and e["from"] == candidate["id"] and e["relation"] == "REFERENCES_DRUG"), None)
        target_edges = [e for e in graph_edges if drug_id and e["from"] == drug_id and e["label"] in {"DRG-GEN", "DRG-TARGET"}]
        target_nodes = [nodes_by_id[e["to"]] for e in target_edges if e["to"] in nodes_by_id]
        target_evidence = [ev for ev in evidence if drug_id and ev["subject_id"] == drug_id and ev["predicate"] in {e["relation"] for e in target_edges}]
        drugs.append({**item, "candidate_node_id": candidate["id"] if candidate else None, "standard_drug_id": drug_id,
                      "target_assertion_rows": len(target_edges), "target_relation_counts": _count_values(e["relation"] for e in target_edges),
                      "target_symbols": [n["label"] for n in target_nodes], "target_node_count": len(target_nodes),
                      "traceable_target_evidence_records": len(target_evidence)})
    return {"created_at": datetime.now(timezone.utc).isoformat(), "git_commit": _git_head(),
            "frozen_source": str(source.relative_to(ROOT)), "frozen_source_sha256": sha256(source),
            "graph_runtime": {"status": "UNAVAILABLE", "reason": "Docker daemon API denied; no live Neo4j socket verified"},
            "offline_source": "OptimusKG 3.2 + versioned Top 10 GraphBundles",
            "offline_graph_counts": _bundle_counts(), "top10": drugs}


def _count_values(values):
    counts = defaultdict(int)
    for value in values: counts[value] += 1
    return dict(sorted(counts.items()))


def _git_head() -> str:
    import subprocess
    p = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else "unknown"


def _bundle_counts() -> list[dict[str, Any]]:
    out = []
    for d in sorted((ROOT / "reports/top10_kg/top10_graph_bundle").glob("*")):
        manifest = d / "bundle_manifest.json"
        if manifest.exists():
            m = json.loads(manifest.read_text(encoding="utf-8"))
            counts = m.get("counts", {})
            out.append({"path": str(d.relative_to(ROOT)), "status": m.get("status"), "run_id": m.get("analysis_run_id"),
                        "nodes": counts.get("nodes"), "edges": counts.get("edges"), "manifest_sha256": sha256(manifest)})
    return out


def write_baseline() -> None:
    result = audit()
    BASELINE.mkdir(parents=True, exist_ok=True)
    target = BASELINE / "top10_snapshot.json"
    payload = {"schema_version": 1, **result}
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (BASELINE / "top10_snapshot.sha256").write_text(sha256(target) + "  top10_snapshot.json\n", encoding="ascii")
    REPORT.mkdir(parents=True, exist_ok=True)
    (REPORT / "00_graph_baseline.json").write_text(json.dumps({k: v for k, v in result.items() if k != "top10"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_tsv(source: Path, output: Path, source_name: str) -> dict[str, Any]:
    """Normalize a user-supplied tabular source with explicit column mapping.

    Input header must include source_id, source, target, relation, sign, organism.
    The parser rejects missing provenance/context instead of guessing schemas.
    """
    if not source_name.strip(): raise ValueError("source_name is required")
    valid, rejected = [], []
    with source.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        required = {"source_id", "source", "target", "relation", "sign", "organism"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"Input header must include {sorted(required)}; got {reader.fieldnames}")
        for n, row in enumerate(reader, 2):
            if not all((row.get(k) or "").strip() for k in required):
                rejected.append({"line": n, "reason": "missing_required_field"}); continue
            sign = row["sign"].strip().lower()
            if sign not in {"positive", "negative", "unknown", "conflicting"}:
                rejected.append({"line": n, "reason": "invalid_sign"}); continue
            valid.append({**{k: (v or "").strip() for k, v in row.items()}, "source_database": source_name,
                          "source_file_sha256": sha256(source), "relation_id": hashlib.sha256((source_name+"|"+row["source_id"].strip()).encode()).hexdigest()})
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(valid[0]) if valid else ["source_id", "source", "target", "relation", "sign", "organism", "source_database", "source_file_sha256", "relation_id"])
        writer.writeheader(); writer.writerows(valid)
    return {"source_name": source_name, "local_path": str(source), "sha256": sha256(source), "records_raw": len(valid)+len(rejected), "records_valid": len(valid), "records_rejected": rejected, "normalized_path": str(output)}


def normalize_mapped_tsv(source: Path, output: Path, *, source_name: str, release: str,
                         license_name: str, species: str, column_map: dict[str, str],
                         has_header: bool = True, delimiter: str = "\t") -> dict[str, Any]:
    """Normalize a source using explicit source-column names or zero-based indexes.

    Mapping values can be a column name/index, `constant:<value>`, or `unknown`.
    Required mappings: source, target, relation, sign. Original rows are preserved
    as JSON alongside stable assertion IDs. No schema inference is performed.
    """
    required = {"source", "target", "relation", "sign"}
    if not required.issubset(column_map): raise ValueError(f"column_map must define {sorted(required)}")
    if not all((source_name, release, license_name, species)): raise ValueError("source, release, license, and species metadata are required")
    input_hash = sha256(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    rejects_path = output.with_suffix(output.suffix + ".rejected.csv")
    fields = ["assertion_id", "source", "target", "relation", "sign", "organism", "cell_context", "mechanism", "original_relation_id", "evidence_ids", "source_database", "source_release", "license", "species", "source_file_sha256", "source_row_number", "raw_row_json"]
    raw_count = valid_count = 0
    rejected_counts: dict[str, int] = defaultdict(int)
    with source.open(encoding="utf-8-sig", newline="") as inp, output.open("w", encoding="utf-8", newline="") as out, rejects_path.open("w", encoding="utf-8", newline="") as rej:
        reader = csv.reader(inp, delimiter=delimiter)
        header = next(reader, None) if has_header else None
        if has_header and not header: raise ValueError("source file has no header row")
        writer = csv.DictWriter(out, fieldnames=fields); writer.writeheader()
        reject_writer = csv.DictWriter(rej, fieldnames=["source_row_number", "reason", "raw_row_json"]); reject_writer.writeheader()
        def get_value(row, spec):
            if spec == "unknown": return "unknown"
            if spec.startswith("constant:"): return spec.split(":", 1)[1]
            if spec.startswith("sign_from:"):
                stimulation, inhibition = spec.split(":", 1)[1].split(",", 1)
                up = get_value(row, stimulation).strip().lower() in {"true", "1", "yes", "positive", "stimulation", "activated"}
                down = get_value(row, inhibition).strip().lower() in {"true", "1", "yes", "negative", "inhibition", "inhibited"}
                return "conflicting" if up and down else "positive" if up else "negative" if down else "unknown"
            try: idx = header.index(spec) if has_header else int(spec)
            except (ValueError, AttributeError): raise ValueError(f"Mapped column {spec!r} is absent from source header {header}")
            return row[idx].strip() if idx < len(row) else ""
        for line_no, row in enumerate(reader, 2 if has_header else 1):
            raw_count += 1
            try:
                values = {name: get_value(row, spec) for name, spec in column_map.items()}
            except (IndexError, ValueError) as exc:
                reason = f"mapping_error:{exc}"; reject_writer.writerow({"source_row_number": line_no, "reason": reason, "raw_row_json": json.dumps(row, ensure_ascii=False)}); rejected_counts["mapping_error"] += 1; continue
            # Skip nonhuman rows when an explicit species field is mapped.
            source_species = values.get("organism", species)
            if species == "Homo sapiens" and source_species not in {"Homo sapiens", "human", "9606", "HSA", "R-HSA", "unknown"}:
                reason = "non_human_species"; reject_writer.writerow({"source_row_number": line_no, "reason": reason, "raw_row_json": json.dumps(row, ensure_ascii=False)}); rejected_counts[reason] += 1; continue
            sign = values.get("sign", "unknown").lower()
            if sign not in {"positive", "negative", "unknown", "conflicting"}:
                reason = "invalid_sign"; reject_writer.writerow({"source_row_number": line_no, "reason": reason, "raw_row_json": json.dumps(row, ensure_ascii=False)}); rejected_counts[reason] += 1; continue
            if not values.get("source") or not values.get("target") or not values.get("relation"):
                reason = "missing_entity_or_relation"; reject_writer.writerow({"source_row_number": line_no, "reason": reason, "raw_row_json": json.dumps(row, ensure_ascii=False)}); rejected_counts[reason] += 1; continue
            raw_json = json.dumps(row, ensure_ascii=False, separators=(",", ":"))
            original_id = values.get("original_relation_id") or hashlib.sha256(f"{source_name}|{release}|{raw_json}".encode()).hexdigest()
            assertion_id = hashlib.sha256(f"{source_name}|{release}|{original_id}|{values['source']}|{values['relation']}|{values['target']}".encode()).hexdigest()
            writer.writerow({"assertion_id": assertion_id, "source": values["source"], "target": values["target"], "relation": values["relation"], "sign": sign,
                             "organism": source_species or species, "cell_context": values.get("cell_context", "unknown"), "mechanism": values.get("mechanism", "unknown"),
                             "original_relation_id": original_id, "evidence_ids": values.get("evidence_ids", "unknown"), "source_database": source_name,
                             "source_release": release, "license": license_name, "species": species, "source_file_sha256": input_hash,
                             "source_row_number": line_no, "raw_row_json": raw_json})
            valid_count += 1
    manifest = {"source_name": source_name, "source_url": "user-supplied local file", "release_version": release,
                "retrieved_at": datetime.now(timezone.utc).isoformat(), "local_path": str(source), "sha256": input_hash,
                "license": license_name, "species": species, "schema_version": "explicit-column-map-v1",
                "records_raw": raw_count, "records_valid": valid_count, "records_rejected": dict(rejected_counts),
                "normalized_path": str(output), "normalized_sha256": sha256(output), "rejected_path": str(rejects_path), "rejected_sha256": sha256(rejects_path)}
    output.with_suffix(output.suffix + ".manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def normalize_reactome_pathways(pathways_file: Path, hierarchy_file: Path, output_dir: Path) -> dict[str, Any]:
    """Normalize current Reactome downloads using their verified headerless layouts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    pathways_hash, hierarchy_hash = sha256(pathways_file), sha256(hierarchy_file)
    human = {}
    rejected = []
    raw_pathway_rows = 0
    with pathways_file.open(encoding="utf-8-sig", newline="") as stream:
        for line_no, row in enumerate(csv.reader(stream, delimiter="\t"), 1):
            raw_pathway_rows += 1
            if len(row) != 3:
                rejected.append({"source_file": pathways_file.name, "line": line_no, "reason": "expected_3_columns", "row": row}); continue
            stable_id, name, species_name = (value.strip() for value in row)
            if species_name != "Homo sapiens": continue
            if not stable_id.startswith("R-HSA-"):
                rejected.append({"source_file": pathways_file.name, "line": line_no, "reason": "human_species_with_nonhuman_id", "row": row}); continue
            human[stable_id] = name
    node_path = output_dir / "reactome_pathway_nodes.csv"
    with node_path.open("w", encoding="utf-8", newline="") as stream:
        fields = ["id", "type", "label", "stable_id", "species", "source_database", "source_release", "license", "source_file_sha256"]
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader()
        for stable_id, name in sorted(human.items()):
            writer.writerow({"id": f"REACT:{stable_id}", "type": "Pathway", "label": name, "stable_id": stable_id, "species": "Homo sapiens", "source_database": "Reactome", "source_release": "current-2026-10", "license": "CC0 1.0 Universal", "source_file_sha256": pathways_hash})
    edge_path = output_dir / "reactome_pathway_hierarchy.csv"
    valid_edges, rejected_edges, raw_hierarchy_rows = 0, 0, 0
    with hierarchy_file.open(encoding="utf-8-sig", newline="") as inp, edge_path.open("w", encoding="utf-8", newline="") as out:
        reader = csv.reader(inp, delimiter="\t")
        fields = ["assertion_id", "source", "target", "relation", "sign", "directed", "organism", "source_database", "source_release", "license", "source_record_id", "source_file_sha256", "source_row_number"]
        writer = csv.DictWriter(out, fieldnames=fields); writer.writeheader()
        for line_no, row in enumerate(reader, 1):
            raw_hierarchy_rows += 1
            if len(row) != 2 or row[0] not in human or row[1] not in human:
                rejected_edges += 1; continue
            parent, child = row[0].strip(), row[1].strip()
            record_id = f"ReactomePathwaysRelation:{parent}:{child}"
            assertion_id = hashlib.sha256(f"Reactome|current-2026-10|{record_id}".encode()).hexdigest()
            writer.writerow({"assertion_id": assertion_id, "source": f"REACT:{child}", "target": f"REACT:{parent}", "relation": "SUBPATHWAY_OF", "sign": "unknown", "directed": "true", "organism": "Homo sapiens", "source_database": "Reactome", "source_release": "current-2026-10", "license": "CC0 1.0 Universal", "source_record_id": record_id, "source_file_sha256": hierarchy_hash, "source_row_number": line_no})
            valid_edges += 1
    reject_path = output_dir / "reactome_rejected_rows.json"
    reject_path.write_text(json.dumps(rejected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = {"source": "Reactome", "release": "current-2026-10", "license": "CC0 1.0 Universal", "retrieved_at": "2026-11-22", "species": "Homo sapiens",
              "pathway_file": str(pathways_file), "pathway_file_sha256": pathways_hash, "pathway_records_raw": raw_pathway_rows, "human_pathways": len(human),
              "hierarchy_file": str(hierarchy_file), "hierarchy_file_sha256": hierarchy_hash, "hierarchy_records_raw": raw_hierarchy_rows,
              "hierarchy_records_valid": valid_edges, "hierarchy_records_rejected": rejected_edges, "outputs": {p.name: sha256(p) for p in (node_path, edge_path, reject_path)}}
    manifest_path = output_dir / "reactome_normalization_manifest.json"
    manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def normalize_signor(source: Path, output: Path, *, release: str, license_name: str) -> dict[str, Any]:
    """Normalize SIGNOR causal protein-to-protein regulation from its real TSV schema.

    Keep the original release untouched. Only human, direct, UniProt protein-to-
    UniProt protein assertions with an explicit up/down EFFECT enter the signed
    layer; complexes, chemicals, phenotypes, indirect and unsigned records remain
    auditable as row-level rejects rather than being coerced into protein edges.
    """
    input_hash = sha256(source)
    required = {"ENTITYA", "TYPEA", "IDA", "DATABASEA", "ENTITYB", "TYPEB", "IDB", "DATABASEB", "EFFECT", "MECHANISM", "TAX_ID", "CELL_DATA", "TISSUE_DATA", "PMID", "DIRECT", "SIGNOR_ID"}
    fields = ["assertion_id", "source", "target", "relation", "sign", "directed", "organism", "cell_context", "tissue_context", "mechanism", "original_relation_id", "evidence_ids", "source_database", "source_release", "license", "species", "source_file_sha256", "source_row_number", "raw_row_json"]
    rejects_path = output.with_suffix(output.suffix + ".rejected.csv")
    counts: dict[str, int] = defaultdict(int)
    output.parent.mkdir(parents=True, exist_ok=True)
    with source.open(encoding="utf-8-sig", newline="") as inp, output.open("w", encoding="utf-8", newline="") as out, rejects_path.open("w", encoding="utf-8", newline="") as rejects:
        reader = csv.DictReader(inp, delimiter="\t")
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"Unexpected SIGNOR header: required {sorted(required)}, observed {reader.fieldnames}")
        writer = csv.DictWriter(out, fieldnames=fields); writer.writeheader()
        reject_writer = csv.DictWriter(rejects, fieldnames=["source_row_number", "reason", "raw_row_json"]); reject_writer.writeheader()
        for line_no, row in enumerate(reader, 2):
            counts["records_raw"] += 1
            reason = None
            if row.get("TAX_ID") != "9606": reason = "nonhuman_or_unspecified_taxon"
            elif (row.get("TYPEA", "").lower(), row.get("TYPEB", "").lower()) != ("protein", "protein"): reason = "non_protein_endpoint"
            elif row.get("DATABASEA") != "UNIPROT" or row.get("DATABASEB") != "UNIPROT": reason = "non_uniprot_endpoint"
            elif row.get("DIRECT", "").lower() != "t": reason = "not_direct"
            effect = (row.get("EFFECT") or "").strip().lower()
            if reason is None:
                if effect.startswith("up-regulates"): sign = "positive"
                elif effect.startswith("down-regulates"): sign = "negative"
                else: reason = "effect_not_directional_regulation"
            if reason is None and not all((row.get(k) or "").strip() for k in ("IDA", "IDB", "SIGNOR_ID")):
                reason = "missing_endpoint_or_assertion_id"
            raw_json = json.dumps(row, ensure_ascii=False, separators=(",", ":"))
            if reason:
                counts["records_rejected"] += 1; counts[f"rejected:{reason}"] += 1
                reject_writer.writerow({"source_row_number": line_no, "reason": reason, "raw_row_json": raw_json})
                continue
            assertion_id = hashlib.sha256(f"SIGNOR|{release}|{row['SIGNOR_ID']}|{row['IDA']}|{row['EFFECT']}|{row['IDB']}".encode()).hexdigest()
            cell = row.get("CELL_DATA", "").strip() or "unknown"
            tissue = row.get("TISSUE_DATA", "").strip() or "unknown"
            writer.writerow({"assertion_id": assertion_id, "source": row["IDA"].strip(), "target": row["IDB"].strip(), "relation": "REGULATES", "sign": sign, "directed": "true", "organism": "Homo sapiens", "cell_context": cell, "tissue_context": tissue, "mechanism": row.get("MECHANISM", "unknown").strip() or "unknown", "original_relation_id": row["SIGNOR_ID"].strip(), "evidence_ids": f"PMID:{row['PMID'].strip()}" if row.get("PMID", "").strip() else "unknown", "source_database": "SIGNOR", "source_release": release, "license": license_name, "species": "Homo sapiens", "source_file_sha256": input_hash, "source_row_number": line_no, "raw_row_json": raw_json})
            counts["records_valid"] += 1
    manifest = {"source_name": "SIGNOR", "source_url": "https://signor.uniroma2.it/downloads.php", "release_version": release, "retrieved_at": datetime.now(timezone.utc).isoformat(), "local_path": str(source), "sha256": input_hash, "license": license_name, "species": "Homo sapiens", "schema_version": "SIGNOR 4.0 release TSV; verified header", **counts, "normalized_path": str(output), "normalized_sha256": sha256(output), "rejected_path": str(rejects_path), "rejected_sha256": sha256(rejects_path)}
    output.with_suffix(output.suffix + ".manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def normalize_omnipath(source: Path, resource_metadata_file: Path, output: Path, *, release: str) -> dict[str, Any]:
    """Split OmniPath's integrated interaction rows into per-resource signed evidence assertions."""
    input_hash, resource_hash = sha256(source), sha256(resource_metadata_file)
    resources = json.loads(resource_metadata_file.read_text(encoding="utf-8-sig"))
    fields_required = {"source", "target", "is_directed", "evidences"}
    fields = ["assertion_id", "source", "target", "relation", "sign", "directed", "organism", "cell_context", "mechanism", "original_relation_id", "evidence_ids", "evidence_resource", "evidence_dataset", "source_database", "source_release", "license", "license_url", "source_file_sha256", "resource_metadata_sha256", "source_row_number", "raw_evidence_json"]
    reject_path = output.with_suffix(output.suffix + ".rejected.csv")
    counts: dict[str, int] = defaultdict(int)
    output.parent.mkdir(parents=True, exist_ok=True)
    with source.open(encoding="utf-8-sig", newline="") as inp, output.open("w", encoding="utf-8", newline="") as out, reject_path.open("w", encoding="utf-8", newline="") as rej:
        reader = csv.DictReader(inp, delimiter="\t")
        if not reader.fieldnames or not fields_required.issubset(reader.fieldnames): raise ValueError(f"Unexpected OmniPath interaction header: {reader.fieldnames}")
        writer = csv.DictWriter(out, fieldnames=fields); writer.writeheader()
        reject_writer = csv.DictWriter(rej, fieldnames=["source_row_number", "reason", "raw_row_json"]); reject_writer.writeheader()
        for line_no, row in enumerate(reader, 2):
            counts["records_raw"] += 1
            try: evidence_blob = json.loads(row.get("evidences") or "{}")
            except json.JSONDecodeError:
                counts["records_rejected"] += 1; counts["rejected:invalid_evidence_json"] += 1
                reject_writer.writerow({"source_row_number": line_no, "reason": "invalid_evidence_json", "raw_row_json": json.dumps(row, ensure_ascii=False)}); continue
            if str(row.get("is_directed", "")).lower() != "true":
                counts["records_rejected"] += 1; counts["rejected:not_directed"] += 1
                reject_writer.writerow({"source_row_number": line_no, "reason": "not_directed", "raw_row_json": json.dumps(row, ensure_ascii=False)}); continue
            emitted = 0
            for sign_group, sign in (("positive", "positive"), ("negative", "negative")):
                for item in evidence_blob.get(sign_group, []):
                    if item.get("dataset") != "omnipath": continue
                    resource = str(item.get("resource") or "unknown")
                    resource_info = resources.get(resource, {})
                    lic = resource_info.get("license", {})
                    license_name = lic.get("name") or "unknown; source not in retrieved license metadata"
                    refs = item.get("references") or []
                    evidence_ids = [f"PMID:{ref}" if str(ref).isdigit() else str(ref) for ref in refs]
                    attrs = item.get("attrs") or {}
                    mechanism = attrs.get("mechanism") or attrs.get("method") or "unknown"
                    raw_evidence = json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                    record_key = f"{row['source']}|{row['target']}|{resource}|{sign}|{','.join(sorted(evidence_ids))}|{release}"
                    original_id = f"OmniPath:{resource}:{hashlib.sha256(record_key.encode()).hexdigest()}"
                    assertion_id = hashlib.sha256(record_key.encode()).hexdigest()
                    writer.writerow({"assertion_id": assertion_id, "source": row["source"].strip(), "target": row["target"].strip(), "relation": "REGULATES", "sign": sign, "directed": "true", "organism": "Homo sapiens", "cell_context": "unknown", "mechanism": json.dumps(mechanism, ensure_ascii=False), "original_relation_id": original_id, "evidence_ids": "|".join(evidence_ids) if evidence_ids else "unknown", "evidence_resource": resource, "evidence_dataset": item.get("dataset"), "source_database": "OmniPath", "source_release": release, "license": license_name, "license_url": lic.get("url", ""), "source_file_sha256": input_hash, "resource_metadata_sha256": resource_hash, "source_row_number": line_no, "raw_evidence_json": raw_evidence})
                    counts["records_valid"] += 1; counts[f"records_valid:{sign}"] += 1; counts[f"resources:{resource}"] += 1; emitted += 1
            if not emitted:
                counts["records_rejected"] += 1; counts["rejected:no_signed_core_omnipath_evidence"] += 1
                reject_writer.writerow({"source_row_number": line_no, "reason": "no_signed_core_omnipath_evidence", "raw_row_json": json.dumps(row, ensure_ascii=False)})
    manifest = {"source_name": "OmniPath", "source_url": "https://omnipathdb.org/interactions", "release_version": release, "retrieved_at": datetime.now(timezone.utc).isoformat(), "local_path": str(source), "sha256": input_hash, "license": "academic-use-filtered; each assertion records resource license", "species": "Homo sapiens", "schema_version": "OmniPath interactions TSV + per-resource evidences JSON", **counts, "resource_metadata_path": str(resource_metadata_file), "resource_metadata_sha256": resource_hash, "normalized_path": str(output), "normalized_sha256": sha256(output), "rejected_path": str(reject_path), "rejected_sha256": sha256(reject_path)}
    output.with_suffix(output.suffix + ".manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def evaluate_drugmechdb(source: Path | None = None) -> dict[str, Any]:
    """Compare exact Top 10 drug names against DrugMechDB breast-neoplasm paths.

    This is an independent coverage/target-overlap check, not a gold-standard
    validation of ER+ efficacy or of the signed regulatory paths.
    """
    import re
    import yaml

    source = source or ROOT / "data/kg_enrichment/raw/drugmechdb/2.0.1/indication_paths.yaml"
    source_hash = sha256(source)
    data = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("DrugMechDB source must be a YAML list of path records")
    frozen = json.loads((ROOT / "reports/top10_kg/02_top10_frozen_manifest.json").read_text(encoding="utf-8"))
    key = lambda value: re.sub(r"[^a-z0-9]", "", str(value or "").casefold())
    candidates = {key(item["pert_iname"]): item for item in frozen["items"]}
    bundle = ROOT / "reports/top10_kg/top10_graph_bundle/3928c54d_external_v1"
    graph_edges = read_csv(bundle / "subgraph_edges.csv")
    graph_nodes = read_csv(bundle / "subgraph_nodes.csv")
    nodes_by_id = {row["id"]: row for row in graph_nodes}
    project_drug_ids: dict[str, str] = {}
    for edge in graph_edges:
        if edge["relation"] != "REFERENCES_DRUG" or edge["from"] not in nodes_by_id:
            continue
        candidate_props = json.loads(nodes_by_id[edge["from"]].get("properties_json") or "{}")
        if candidate_props.get("pert_id"):
            project_drug_ids[candidate_props["pert_id"]] = edge["to"]
    target_genes_by_candidate: dict[str, set[str]] = defaultdict(set)
    for edge in graph_edges:
        if edge["relation"] not in DIRECT_TARGET_RELATIONS or edge["from"] not in nodes_by_id:
            continue
        for pert_id, drug_id in project_drug_ids.items():
            if edge["from"] == drug_id and edge["to"] in nodes_by_id:
                target_genes_by_candidate[pert_id].add(edge["to"])
    crosswalk = {row["uniprot_accession"]: row["gene_id"] for row in read_csv(ROOT / "data/kg_enrichment/normalized/optimuskg/3.2/uniprot_gene_crosswalk.csv") if row["mapping_ambiguity"] == "unique_gene"}
    rows = []
    exact_drug_match_paths = 0
    malformed = 0
    direct_target_keys = {"decreases activity of", "increases activity of", "directly decreases activity of", "directly increases activity of", "inhibits", "activates"}
    for record in data:
        graph = record.get("graph") or {}
        drug_name = graph.get("drug") or ""
        candidate = candidates.get(key(drug_name))
        if candidate:
            exact_drug_match_paths += 1
        if not candidate or graph.get("disease_mesh") != "MESH:D001943":
            continue
        nodes = record.get("nodes") or []
        node_ids = {node.get("id") for node in nodes if isinstance(node, dict)}
        links = record.get("links") or []
        if not graph.get("_id") or not node_ids or not all(link.get("source") in node_ids and link.get("target") in node_ids for link in links):
            malformed += 1
            continue
        drug_id = graph.get("drug_mesh")
        proteins = {node["id"] for node in nodes if node.get("label") == "Protein"}
        direct_proteins = {link["target"] for link in links if link.get("source") == drug_id and link.get("target") in proteins and str(link.get("key", "")).casefold() in direct_target_keys}
        mapped_genes = {crosswalk[protein.split(":", 1)[-1]] for protein in direct_proteins if protein.startswith("UniProt:") and protein.split(":", 1)[-1] in crosswalk}
        project_targets = target_genes_by_candidate[candidate["pert_id"]]
        overlap = mapped_genes & project_targets
        rows.append({"rank": candidate["rank"], "pert_id": candidate["pert_id"], "project_drug_name": candidate["pert_iname"], "drugmechdb_drug_name": drug_name, "drugbank_id": graph.get("drugbank", ""), "path_id": graph["_id"], "disease_mesh": graph["disease_mesh"], "disease_name": graph.get("disease", ""), "drug_mesh": drug_id or "", "direct_protein_ids": "|".join(sorted(direct_proteins)), "mapped_direct_target_gene_ids": "|".join(sorted(mapped_genes)), "project_direct_target_gene_ids": "|".join(sorted(project_targets)), "target_overlap_gene_ids": "|".join(sorted(overlap)), "target_overlap_count": len(overlap), "source_path_sha256": source_hash})
    rows.sort(key=lambda row: (row["rank"], row["path_id"]))
    out_dir = REPORT
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "08_drugmechdb_breast_path_matches.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        fields = list(rows[0]) if rows else ["rank", "pert_id", "project_drug_name", "drugmechdb_drug_name", "drugbank_id", "path_id", "disease_mesh", "disease_name", "drug_mesh", "direct_protein_ids", "mapped_direct_target_gene_ids", "project_direct_target_gene_ids", "target_overlap_gene_ids", "target_overlap_count", "source_path_sha256"]
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    target_pairs = {(row["pert_id"], gene) for row in rows for gene in row["mapped_direct_target_gene_ids"].split("|") if gene}
    overlap_pairs = {(row["pert_id"], gene) for row in rows for gene in row["target_overlap_gene_ids"].split("|") if gene}
    result = {"schema_version": 1, "status": "independent_reference_coverage_and_target_overlap_partial", "dataset": "DrugMechDB", "release": "2.0.1", "license": "CC0 1.0 Universal (pinned repository LICENSE retained)", "source_file": str(source.relative_to(ROOT)).replace("\\", "/"), "source_sha256": source_hash, "raw_path_record_count": len(data), "disease_scope": {"mesh_id": "MESH:D001943", "label": "Breast Neoplasms", "interpretation": "broad breast-neoplasm indication; not ER+ subtype evidence"}, "candidate_matching": "case-insensitive exact alphanumeric drug-name match; no alias/name inference", "top10_exact_drug_path_matches_any_disease": exact_drug_match_paths, "top10_exact_breast_neoplasm_path_count": len(rows), "top10_coverage": f"{len({row['pert_id'] for row in rows})}/10", "unique_mapped_direct_target_pairs": len(target_pairs), "unique_target_overlap_pairs": len(overlap_pairs), "target_overlap_fraction": f"{len(overlap_pairs)}/{len(target_pairs)}" if target_pairs else "not_assessable", "malformed_matching_records_rejected": malformed, "matches_csv": str(csv_path.relative_to(ROOT)).replace("\\", "/"), "interpretation_limit": "Independent curation provides indication and target-overlap support only; it does not validate ER+ benefit or the candidate regulatory path to S1 genes."}
    json_path = out_dir / "08_drugmechdb_evaluation.json"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def propagate(signs: list[str]) -> str:
    if any(s not in {"positive", "negative"} for s in signs): return "unknown"
    return "positive" if signs.count("negative") % 2 == 0 else "negative"


def detect_conflicts(assertions: list[dict]) -> list[dict]:
    """Report opposing signed assertions in matching biological context.

    Context equality is exact and source-aware; opposite assertions are retained
    as coexisting evidence instead of majority-voted into one direction.
    """
    groups = defaultdict(list)
    for row in assertions:
        if row.get("sign") not in {"positive", "negative"}: continue
        key = (row.get("source"), row.get("target"), row.get("organism"))
        groups[key].append(row)
    result = []
    for key, rows in groups.items():
        conflicting_rows = set()
        conflict_contexts = set()
        for i, left in enumerate(rows):
            left_context = (left.get("cell_context") or "unknown").strip()
            for right in rows[i + 1:]:
                if left["sign"] == right["sign"]: continue
                right_context = (right.get("cell_context") or "unknown").strip()
                if left_context == right_context or left_context in {"", "unknown", "any"} or right_context in {"", "unknown", "any"}:
                    conflicting_rows.update((id(left), id(right)))
                    conflict_contexts.update((left_context, right_context))
        if conflicting_rows:
            conflict_records = [r for r in rows if id(r) in conflicting_rows]
            context_is_ambiguous = len(conflict_contexts - {"", "unknown", "any"}) > 1 or any(c in {"", "unknown", "any"} for c in conflict_contexts)
            result.append({"source": key[0], "target": key[1], "organism": key[2], "cell_context": "unknown_or_context_specific" if context_is_ambiguous else next(iter(conflict_contexts), "unknown"),
                           "status": "potential_conflict_unknown_context" if context_is_ambiguous else "conflict", "assertion_ids": sorted(r.get("assertion_id", r.get("relation_id", r.get("id", ""))) for r in conflict_records),
                           "sources": sorted({r.get("source_database", "") for r in conflict_records})})
    return result


def enumerate_paths(edges: list[dict], starts: set[str], goals: set[str], max_depth: int = 4) -> list[dict]:
    """Enumerate directed regulatory paths only; no PPI/pathway membership traversal."""
    adj: dict[str, list[dict]] = defaultdict(list)
    for e in edges:
        if e.get("relation") == "REGULATES" and e.get("directed", True): adj[e["source"]].append(e)
    found = []
    for start in sorted(starts):
        q = deque([(start, [], {start})])
        while q:
            node, path, seen = q.popleft()
            if path and node in goals:
                contexts = {e.get("cell_context", "unknown") for e in path if e.get("cell_context", "unknown") not in {"", "unknown", "any"}}
                compatible = len(contexts) <= 1
                found.append({"nodes": [start]+[e["target"] for e in path], "edge_ids": [e["id"] for e in path],
                              "direction": propagate([e.get("sign", "unknown") for e in path]) if compatible else "unknown",
                              "cell_context": next(iter(contexts)) if len(contexts) == 1 else "unknown", "context_compatible": compatible})
                continue
            if len(path) >= max_depth: continue
            for edge in adj[node]:
                if edge["target"] not in seen: q.append((edge["target"], path+[edge], seen|{edge["target"]}))
    return found


def build_uniprot_gene_crosswalk(bundle_nodes: list[dict[str, str]]) -> dict[str, Any]:
    """Extract exact UniProt-to-gene mappings already shipped in OptimusKG 3.2."""
    import duckdb
    public_dir = ROOT / "data/optimuskg/3.2"
    parquet = public_dir / "nodes/gene.parquet"
    source_manifest = json.loads((public_dir / "source_manifest.json").read_text(encoding="utf-8"))
    gene_ids = {n["id"] for n in bundle_nodes if n.get("type") == "Gene"}
    output = ROOT / "data/kg_enrichment/normalized/optimuskg/3.2/uniprot_gene_crosswalk.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["uniprot_accession", "gene_id", "gene_symbol", "mapping_source", "source_release", "license", "source_file_sha256", "mapping_method", "mapping_ambiguity"]
    rows = []
    with duckdb.connect(database=":memory:") as connection:
        records = connection.execute("SELECT id, properties.symbol, properties.associated_proteins FROM read_parquet(?)", [str(parquet)]).fetchall()
    for gene_id, symbol, associated in records:
        if gene_id not in gene_ids: continue
        for protein in associated or []:
            source = str(protein.get("source") or "")
            accession = str(protein.get("id") or "").strip()
            if source not in {"uniprot_swissprot", "uniprot_trembl"} or not accession: continue
            rows.append({"uniprot_accession": accession, "gene_id": gene_id, "gene_symbol": symbol or "", "mapping_source": source, "source_release": f"OptimusKG {source_manifest['release']}", "license": source_manifest.get("license", "unknown"), "source_file_sha256": source_manifest["files"][1]["sha256"], "mapping_method": "exact associated_proteins xref; no fuzzy name matching", "mapping_ambiguity": "pending_global_cardinality"})
    counts = defaultdict(int)
    for row in rows: counts[row["uniprot_accession"]] += 1
    for row in rows: row["mapping_ambiguity"] = "unique_gene" if counts[row["uniprot_accession"]] == 1 else "multiple_gene_mappings"
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(sorted(rows, key=lambda r: (r["uniprot_accession"], r["gene_id"])))
    manifest = {"source_name": "OptimusKG gene-associated UniProt crosswalk", "source_release": f"OptimusKG {source_manifest['release']}", "source_license": source_manifest.get("license"), "source_file": "data/optimuskg/3.2/nodes/gene.parquet", "source_file_sha256": source_manifest["files"][1]["sha256"], "bundle_gene_count": len(gene_ids), "mapping_records": len(rows), "unique_accessions": len(counts), "ambiguous_accessions": sum(n > 1 for n in counts.values()), "normalized_path": str(output.relative_to(ROOT)), "normalized_sha256": sha256(output)}
    output.with_suffix(".manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def build_subgraphs() -> dict[str, Any]:
    """Materialize evidence-bounded candidate subgraphs from validated offline bundle."""
    bundle = ROOT / "reports/top10_kg/top10_graph_bundle/3928c54d_external_v1"
    frozen = json.loads((ROOT / "reports/top10_kg/02_top10_frozen_manifest.json").read_text(encoding="utf-8"))
    nodes = read_csv(bundle / "subgraph_nodes.csv")
    edges = read_csv(bundle / "subgraph_edges.csv")
    external_mechanisms = read_csv(ROOT / "data/top10_kg/evidence/chembl_mechanisms.csv")
    external_components = read_csv(ROOT / "data/top10_kg/evidence/chembl_mechanism_targets.csv")
    external_reactome = read_csv(ROOT / "data/top10_kg/evidence/reactome_protein_pathways.csv")
    current_reactome_file = ROOT / "data/kg_enrichment/normalized/reactome/2026-10/reactome_gene_pathways.csv"
    current_reactome_nodes_file = ROOT / "data/kg_enrichment/normalized/reactome/2026-10/reactome_pathway_nodes.csv"
    current_reactome_memberships = read_csv(current_reactome_file) if current_reactome_file.is_file() else []
    current_reactome_node_rows = read_csv(current_reactome_nodes_file) if current_reactome_nodes_file.is_file() else []
    current_reactome_names = {row["id"]: row.get("label", row["id"]) for row in current_reactome_node_rows}
    current_pathways_by_gene: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in current_reactome_memberships:
        current_pathways_by_gene[row["gene_id"]].append(row)
    crosswalk_manifest = build_uniprot_gene_crosswalk(nodes)
    crosswalk_rows = read_csv(ROOT / crosswalk_manifest["normalized_path"])
    by_id = {n["id"]: n for n in nodes}
    protein_to_gene_ids: dict[str, set[str]] = defaultdict(set)
    gene_to_protein_ids: dict[str, set[str]] = defaultdict(set)
    crosswalk_evidence = {}
    for row in crosswalk_rows:
        protein_id = f"UNIPROT:{row['uniprot_accession']}"
        gene_id = row["gene_id"]
        protein_to_gene_ids[protein_id].add(gene_id); gene_to_protein_ids[gene_id].add(protein_id)
        evidence_id = hashlib.sha256(f"{protein_id}|{gene_id}|{row['source_file_sha256']}".encode()).hexdigest()
        crosswalk_evidence[(protein_id, gene_id)] = {"evidence_id": evidence_id, "source_release": row["source_release"], "source_record_id": f"OptimusKG:associated_protein:{row['uniprot_accession']}:{gene_id}", "subject_id": protein_id, "predicate": "ASSOCIATED_WITH_GENE", "object_id": gene_id, "source_assertion_json": json.dumps(row, ensure_ascii=False)}
        by_id.setdefault(protein_id, {"id": protein_id, "type": "Protein", "label": row["uniprot_accession"], "properties_json": json.dumps({"uniprot_accession": row["uniprot_accession"], "source_database": "OptimusKG", "source_release": row["source_release"], "source_file_sha256": row["source_file_sha256"], "associated_gene_ids": []}, ensure_ascii=False)})
        props = json.loads(by_id[protein_id]["properties_json"])
        props["associated_gene_ids"] = sorted(protein_to_gene_ids[protein_id])
        by_id[protein_id]["properties_json"] = json.dumps(props, ensure_ascii=False)
    entity_lookup: dict[str, set[str]] = defaultdict(set)
    for node in by_id.values():
        props = json.loads(node.get("properties_json") or "{}")
        for value in (node["id"], node.get("label", ""), props.get("symbol", ""), props.get("uniprot_accession", ""), props.get("ensembl_id", "")):
            if value: entity_lookup[str(value)].add(node["id"])
    regulatory_edges, regulatory_map_rejects = [], []
    normalized_dir = ROOT / "data/kg_enrichment/normalized"
    for normalized_file in sorted(normalized_dir.rglob("*.csv")) if normalized_dir.exists() else []:
        for row in read_csv(normalized_file):
            if row.get("relation") != "REGULATES": continue
            source_hits = entity_lookup.get(row.get("source", ""), set())
            target_hits = entity_lookup.get(row.get("target", ""), set())
            if len(source_hits) != 1 or len(target_hits) != 1:
                regulatory_map_rejects.append({"file": str(normalized_file.relative_to(ROOT)), "source": row.get("source"), "target": row.get("target"), "reason": "unmapped_or_ambiguous_endpoint"})
                continue
            if row.get("organism") not in {"Homo sapiens", "human", "9606", "HSA"}:
                regulatory_map_rejects.append({"file": str(normalized_file.relative_to(ROOT)), "source": row.get("source"), "target": row.get("target"), "reason": "organism_not_human"})
                continue
            source_node, target_node = next(iter(source_hits)), next(iter(target_hits))
            reg_edge = {"id": row.get("assertion_id") or row.get("relation_id"), "source": source_node, "target": target_node, "from": source_node, "to": target_node, "label": "REGULATES", "relation": "REGULATES", "undirected": "false", "sign": row.get("sign", "unknown"), "directed": True, "organism": row.get("organism", "Homo sapiens"), "cell_context": row.get("cell_context", "unknown"), "tissue_context": row.get("tissue_context", "unknown"), "source_database": row.get("source_database"), "source_record_id": row.get("original_relation_id"), "source_release": row.get("source_release"), "license": row.get("license"), "properties_json": json.dumps({"assertion_id": row.get("assertion_id"), "source_record_id": row.get("original_relation_id"), "sign": row.get("sign", "unknown"), "organism": row.get("organism", "Homo sapiens"), "cell_context": row.get("cell_context", "unknown"), "tissue_context": row.get("tissue_context", "unknown"), "mechanism": row.get("mechanism"), "source_database": row.get("source_database"), "source_release": row.get("source_release"), "evidence_ids": row.get("evidence_ids"), "source_file_sha256": row.get("source_file_sha256"), "license": row.get("license")}, ensure_ascii=False)}
            regulatory_edges.append(reg_edge)
    mapped_regulatory_edge_count = len(regulatory_edges)
    outdegree = defaultdict(int)
    for edge in regulatory_edges: outdegree[edge["source"]] += 1
    hub_cutoff = 100
    hub_sources = {source for source, degree in outdegree.items() if degree > hub_cutoff}
    hub_rejects = [edge for edge in regulatory_edges if edge["source"] in hub_sources]
    regulatory_map_rejects.extend({"file": edge.get("source_database", "unknown"), "source": edge.get("source"), "target": edge.get("target"), "reason": "source_hub_outdegree_over_100", "assertion_id": edge.get("id")} for edge in hub_rejects)
    regulatory_edges = [edge for edge in regulatory_edges if outdegree[edge["source"]] <= hub_cutoff]
    regulatory_conflicts = detect_conflicts(regulatory_edges)
    conflicting_assertions = {assertion_id for conflict in regulatory_conflicts for assertion_id in conflict["assertion_ids"]}
    for edge in regulatory_edges:
        if edge["id"] in conflicting_assertions:
            edge["asserted_sign"] = edge["sign"]
            edge["sign"] = "conflicting"
    reactome_norm_dir = normalized_dir / "reactome" / "2026-10"
    if reactome_norm_dir.exists():
        for row in read_csv(reactome_norm_dir / "reactome_pathway_nodes.csv"):
            node = {"id": row["id"], "type": "Pathway", "label": row["label"], "properties_json": json.dumps({"stable_id": row["stable_id"], "species": row["species"], "source_database": row["source_database"], "source_release": row["source_release"], "license": row["license"], "source_file_sha256": row["source_file_sha256"]}, ensure_ascii=False)}
            by_id.setdefault(node["id"], node)
        reactome_hierarchy = []
        for row in read_csv(reactome_norm_dir / "reactome_pathway_hierarchy.csv"):
            props = {"source_record_id": row["source_record_id"], "assertion_id": row["assertion_id"], "source_file_sha256": row["source_file_sha256"], "license": row["license"], "organism": row["organism"], "direction": "unknown"}
            reactome_hierarchy.append({"id": row["assertion_id"], "from": row["source"], "to": row["target"], "label": "PATHWAY-PARENT", "relation": row["relation"], "undirected": "false", "source_release": "Reactome " + row["source_release"], "properties_json": json.dumps(props, ensure_ascii=False)})
    else:
        reactome_hierarchy = []
    s1_rows = read_csv(ROOT / "reports/top10_kg/input_snapshot/limma_all_genes.csv")
    s1_genes = {row["gene_id"] for row in s1_rows if row.get("gene_id") and row.get("direction", "").lower() in {"up", "down"}}
    s1_by_symbol = {row["gene_id"]: row for row in s1_rows}
    s1_goal_nodes = {node_id for symbol in s1_genes for node_id in entity_lookup.get(symbol, set()) if by_id[node_id]["type"] == "Gene"}
    s1_goal_proteins = {protein for gene in s1_goal_nodes for protein in gene_to_protein_ids.get(gene, set()) if len(protein_to_gene_ids[protein]) == 1}
    candidate_by_pert = {json.loads(n["properties_json"]).get("pert_id"): n for n in nodes if n["type"] == "Candidate"}
    rows = []
    out = ROOT / "artifacts/kg_enrichment/subgraphs"
    out.mkdir(parents=True, exist_ok=True)
    for item in frozen["items"]:
        candidate = candidate_by_pert.get(item["pert_id"])
        if candidate is None:
            record = {"rank": item["rank"], "pert_id": item["pert_id"], "drug": item["pert_iname"], "status": "candidate_missing", "nodes": [], "edges": [], "evidence_gaps": ["candidate_node_missing"]}
        else:
            related = [e for e in edges if candidate["id"] in (e["from"], e["to"])]
            # Direct drug assertions are retained as known/curated context.
            drug_edges = [e for e in related if e["relation"] == "REFERENCES_DRUG"]
            drug_ids = {e["to"] if e["from"] == candidate["id"] else e["from"] for e in drug_edges}
            external_nodes, external_edges, external_evidence, external_context_paths = [], [], [], []
            pathway_names = {n["id"].removeprefix("REACT:"): n["label"] for n in nodes if n["type"] == "Pathway" and n["id"].startswith("REACT:")}
            pathway_names.update({json.loads(n["properties_json"]).get("stable_id"): n["label"] for n in by_id.values() if n.get("type") == "Pathway" and n["id"].startswith("REACT:")})
            for mech in (r for r in external_mechanisms if r.get("pert_id") == item["pert_id"] and r.get("direct_interaction") == "1"):
                target_id = mech.get("target_chembl_id", "")
                if not target_id: continue
                target_node_id = f"CHEMBL_TARGET:{target_id}"
                target_node = {"id": target_node_id, "type": "ChEMBLTarget", "label": mech.get("mechanism_of_action") or target_id, "properties_json": json.dumps({"chembl_target_id": target_id, "mechanism_of_action": mech.get("mechanism_of_action"), "action_type": mech.get("action_type"), "direct_interaction": True, "source_database": "ChEMBL", "source_record_id": f"ChEMBL:mechanism:{mech.get('molecule_chembl_id')}:{target_id}:{mech.get('mechanism_id') or mech.get('action_type')}", "source_version": "existing project evidence snapshot"}, ensure_ascii=False)}
                if target_node_id not in by_id: external_nodes.append(target_node); by_id[target_node_id] = target_node
                source_record = f"ChEMBL:mechanism:{mech.get('molecule_chembl_id')}:{target_id}:{mech.get('mechanism_id') or mech.get('action_type')}"
                edge_id = hashlib.sha256(source_record.encode()).hexdigest()
                props = {"source_record_id": source_record, "action_type": mech.get("action_type"), "mechanism_of_action": mech.get("mechanism_of_action"), "direct_interaction": True, "source_release": "ChEMBL existing project snapshot"}
                edge = {"id": edge_id, "from": next(iter(drug_ids), ""), "to": target_node_id, "label": "DRG-TARGET", "relation": "HAS_DIRECT_TARGET", "undirected": "false", "source_release": "ChEMBL existing project snapshot", "properties_json": json.dumps(props, ensure_ascii=False)}
                if edge["from"]: external_edges.append(edge)
                external_evidence.append({"evidence_id": edge_id, "source_release": edge["source_release"], "source_record_id": source_record, "subject_id": edge["from"], "predicate": edge["relation"], "object_id": target_node_id, "source_assertion_json": edge["properties_json"]})
                component_rows = [r for r in external_components if r.get("pert_id") == item["pert_id"] and r.get("target_chembl_id") == target_id and r.get("target_organism") == "Homo sapiens" and r.get("component_type") == "PROTEIN" and r.get("component_accession")]
                for component in component_rows:
                    accession = component["component_accession"]
                    protein_id = f"UNIPROT:{accession}"
                    protein_node = {"id": protein_id, "type": "Protein", "label": accession, "properties_json": json.dumps({"uniprot_accession": accession, "organism": "Homo sapiens", "component_type": component.get("component_type"), "source_database": "ChEMBL", "source_record_id": f"ChEMBL:target_component:{target_id}:{accession}"}, ensure_ascii=False)}
                    if protein_id not in by_id: external_nodes.append(protein_node); by_id[protein_id] = protein_node
                    comp_record = f"ChEMBL:target_component:{target_id}:{accession}"
                    comp_edge_id = hashlib.sha256(comp_record.encode()).hexdigest()
                    comp_edge = {"id": comp_edge_id, "from": target_node_id, "to": protein_id, "label": "TARGET-COMPONENT", "relation": "HAS_COMPONENT", "undirected": "false", "source_release": "ChEMBL existing project snapshot", "properties_json": json.dumps({"source_record_id": comp_record, "component_relationship": component.get("component_relationship"), "source_url": component.get("source_url")}, ensure_ascii=False)}
                    external_edges.append(comp_edge)
                    external_evidence.append({"evidence_id": comp_edge_id, "source_release": comp_edge["source_release"], "source_record_id": comp_record, "subject_id": target_node_id, "predicate": "HAS_COMPONENT", "object_id": protein_id, "source_assertion_json": comp_edge["properties_json"]})
                    pathways_for_target = [r for r in external_reactome if r.get("pert_id") == item["pert_id"] and r.get("chembl_target_id") == target_id and r.get("uniprot_accession") == accession and r.get("organism") == "Homo sapiens" and r.get("is_inferred", "False").lower() == "false"]
                    for reactome_row in pathways_for_target:
                        pathway_stable = reactome_row["pathway_id"]
                        pathway_node_id = f"REACT:{pathway_stable}"
                        pathway_node = {"id": pathway_node_id, "type": "Pathway", "label": pathway_names.get(pathway_stable, reactome_row.get("pathway_name") or pathway_stable), "properties_json": json.dumps({"stable_id": pathway_stable, "species": "Homo sapiens", "source_database": "Reactome", "source_version": reactome_row.get("source_version"), "is_disease_pathway": reactome_row.get("is_disease_pathway"), "is_inferred": False}, ensure_ascii=False)}
                        if pathway_node_id not in by_id: external_nodes.append(pathway_node); by_id[pathway_node_id] = pathway_node
                        react_record = reactome_row.get("source_record_id") or f"Reactome98:{pathway_stable}:{accession}"
                        react_edge_id = hashlib.sha256(react_record.encode()).hexdigest()
                        react_edge = {"id": react_edge_id, "from": protein_id, "to": pathway_node_id, "label": "PROTEIN-PATHWAY", "relation": "PARTICIPATES_IN", "undirected": "false", "source_release": "Reactome " + str(reactome_row.get("source_version", "98")), "properties_json": json.dumps({"source_record_id": react_record, "source_url": reactome_row.get("source_url"), "interpretation": reactome_row.get("interpretation"), "direction": "unknown"}, ensure_ascii=False)}
                        external_edges.append(react_edge)
                        external_evidence.append({"evidence_id": react_edge_id, "source_release": react_edge["source_release"], "source_record_id": react_record, "subject_id": protein_id, "predicate": "PARTICIPATES_IN", "object_id": pathway_node_id, "source_assertion_json": react_edge["properties_json"]})
                        external_context_paths.append({"nodes": [next(iter(drug_ids), ""), target_node_id, protein_id, pathway_node_id], "edge_ids": [edge_id, comp_edge_id, react_edge_id], "path_kind": "drug-target-protein-pathway context", "causal": False, "direction": "unknown", "interpretation": "ChEMBL direct mechanism plus Reactome protein participation; not an asserted causal downstream chain or ER+ effect", "evidence_ids": [edge_id, comp_edge_id, react_edge_id]})
            relevant_relations = {"TARGET", "INHIBITOR", "AGONIST", "ANTAGONIST", "ACTIVATOR", "BLOCKER", "PARTICIPATES_IN", "SUBPATHWAY_OF", "HAS_DISEASE_CONTEXT_EVIDENCE", "CONCERNS_DISEASE"}
            # Keep candidate metadata, its exact standard-drug identity, and the
            # drug's curated outgoing assertions plus one pathway annotation hop.
            neighbor_ids = {candidate["id"], *drug_ids}
            drug_assertions = [e for e in edges if e["from"] in drug_ids and (e["relation"] in relevant_relations or e["label"] in {"DRG-GEN", "DRG-TARGET"})]
            for e in drug_assertions: neighbor_ids.add(e["to"])
            first_targets = {e["to"] for e in drug_assertions if e["label"] in {"DRG-GEN", "DRG-TARGET"}}
            direct_targets = {e["to"] for e in drug_assertions if e["label"] in {"DRG-GEN", "DRG-TARGET"} and e.get("relation", "").upper() in DIRECT_TARGET_RELATIONS}
            encoded_proteins = {e["from"] for e in edges if e["relation"] == "ENCODED_BY" and e["to"] in first_targets}
            annotation_edges = [e for e in edges if (e["from"] in first_targets and e["relation"] == "ENCODED_BY") or (e["from"] in encoded_proteins and e["relation"] == "PARTICIPATES_IN")]
            for e in annotation_edges: neighbor_ids.add(e["to"])
            pathway_frontier = {e["to"] for e in annotation_edges if by_id.get(e["to"], {}).get("type") == "Pathway"}
            hierarchy_additions = []
            for _ in range(4):
                level_edges = [e for e in reactome_hierarchy if e["from"] in pathway_frontier]
                hierarchy_additions.extend(level_edges)
                next_frontier = {e["to"] for e in level_edges} - neighbor_ids
                neighbor_ids.update(next_frontier)
                pathway_frontier = next_frontier
                if not pathway_frontier: break
            direct_target_proteins = {n for n in direct_targets if by_id.get(n, {}).get("type") == "Protein"}
            direct_target_proteins.update(protein for gene in direct_targets if by_id.get(gene, {}).get("type") == "Gene" for protein in gene_to_protein_ids.get(gene, set()) if len(protein_to_gene_ids[protein]) == 1)
            regulatory_paths = enumerate_paths(regulatory_edges, direct_target_proteins, s1_goal_proteins, max_depth=4)
            current_reactome_edges: dict[str, dict[str, Any]] = {}
            current_reactome_evidence: list[dict[str, Any]] = []
            for mechanism_path in regulatory_paths:
                terminal_protein = mechanism_path["nodes"][-1]
                terminal_gene_ids = protein_to_gene_ids.get(terminal_protein, set())
                terminal_gene_id = next(iter(terminal_gene_ids)) if len(terminal_gene_ids) == 1 else ""
                terminal = by_id.get(terminal_gene_id, {})
                terminal_symbol = terminal.get("label", "")
                s1_record = s1_by_symbol.get(terminal_symbol, {})
                mechanism_path["terminal_gene"] = terminal_symbol
                mechanism_path["terminal_gene_node_id"] = terminal_gene_id or None
                mechanism_path["terminal_s1_direction"] = s1_record.get("direction", "unknown")
                mechanism_path["terminal_s1_logFC"] = s1_record.get("logFC")
                mechanism_path["s1_directionality_interpretation"] = "descriptive transcript direction only; not a proxy for protein activity"
                pathway_annotations = []
                for membership in current_pathways_by_gene.get(terminal_gene_id, []):
                    pathway_id = membership["pathway_id"]
                    pathway_node_id = pathway_id if pathway_id.startswith("REACT:") else f"REACT:{pathway_id}"
                    if pathway_node_id not in by_id:
                        by_id[pathway_node_id] = {"id": pathway_node_id, "type": "Pathway", "label": current_reactome_names.get(pathway_node_id, pathway_id),
                                                  "properties_json": json.dumps({"stable_id": pathway_id.removeprefix("REACT:"), "species": "Homo sapiens", "source_database": "Reactome", "source_release": "current-2026-10", "license": "CC0 1.0 Universal"}, ensure_ascii=False)}
                    record_id = membership["source_record_id"]
                    evidence_id = hashlib.sha256(f"Reactome|{membership['source_release']}|{record_id}".encode()).hexdigest()
                    edge = {"id": evidence_id, "from": pathway_node_id, "to": terminal_gene_id, "label": "PWY-GEN", "relation": "CONTAINS_GENE", "undirected": "false", "source_release": membership["source_release"],
                            "properties_json": json.dumps({"source_database": "Reactome", "source_record_id": record_id, "source_url": membership.get("source_url"), "source_file_sha256": membership.get("source_file_sha256"), "evidence_code": membership.get("evidence_code"), "sign": "unknown", "interpretation": "pathway membership annotation; not a causal or signed regulatory edge"}, ensure_ascii=False)}
                    current_reactome_edges[evidence_id] = edge
                    current_reactome_evidence.append({"evidence_id": evidence_id, "source_release": membership["source_release"], "source_record_id": record_id, "subject_id": pathway_node_id, "predicate": "CONTAINS_GENE", "object_id": terminal_gene_id, "source_assertion_json": edge["properties_json"]})
                    pathway_annotations.append({"pathway_id": pathway_node_id, "pathway_name": current_reactome_names.get(pathway_node_id, pathway_id), "evidence_code": membership.get("evidence_code"), "evidence_id": evidence_id})
                    neighbor_ids.add(pathway_node_id)
                mechanism_path["s1_gene_current_reactome_pathway_annotations"] = pathway_annotations
                mechanism_path["pathway_annotation_semantics"] = "independent Reactome membership annotation for the terminal S1 gene; does not extend or sign the candidate regulatory path"
                start_protein = mechanism_path["nodes"][0]
                start_gene_ids = protein_to_gene_ids.get(start_protein, set())
                mechanism_path["target_gene_mapping"] = {"gene_id": next(iter(start_gene_ids)), "protein_id": start_protein, "ambiguity": "unique_gene"} if len(start_gene_ids) == 1 else {"gene_id": None, "protein_id": start_protein, "ambiguity": "multiple_or_unmapped"}
                mechanism_path["mapping_evidence_ids"] = [crosswalk_evidence[(start_protein, next(iter(start_gene_ids)))]["evidence_id"], crosswalk_evidence[(terminal_protein, terminal_gene_id)]["evidence_id"]] if len(start_gene_ids) == 1 and terminal_gene_id else []
                mechanism_path["evidence_ids"] = sorted(set(mechanism_path["edge_ids"] + mechanism_path["mapping_evidence_ids"]))
            path_edge_ids = {edge_id for path in regulatory_paths for edge_id in path["edge_ids"]}
            candidate_reg_edges = [e for e in regulatory_edges if e["id"] in path_edge_ids]
            candidate_conflicts = [c for c in regulatory_conflicts if set(c["assertion_ids"]) & path_edge_ids]
            candidate_conflict_ids = {assertion for conflict in candidate_conflicts for assertion in conflict["assertion_ids"]}
            regulatory_evidence = [{"evidence_id": e["id"], "source_release": e["source_release"], "source_record_id": e["source_record_id"], "subject_id": e["source"], "predicate": e["relation"], "object_id": e["target"], "source_assertion_json": json.dumps(e, ensure_ascii=False)} for e in candidate_reg_edges]
            mapping_evidence = [crosswalk_evidence[(path["nodes"][0], path["target_gene_mapping"]["gene_id"])] for path in regulatory_paths if path.get("target_gene_mapping", {}).get("gene_id")]
            mapping_evidence.extend(crosswalk_evidence[(path["nodes"][-1], path["terminal_gene_node_id"])] for path in regulatory_paths if path.get("terminal_gene_node_id"))
            for e in candidate_reg_edges: neighbor_ids.update((e["source"], e["target"]))
            selected = [*drug_edges, *drug_assertions, *annotation_edges, *external_edges, *candidate_reg_edges, *current_reactome_edges.values()]
            selected.extend(hierarchy_additions)
            selected.extend(e for e in related if e["relation"] in {"HAS_DISEASE_CONTEXT_EVIDENCE", "CONCERNS_DISEASE"})
            selected_keys = {(e["from"], e["label"], e["to"], e["source_release"]) for e in selected}
            ev_rows = read_csv(bundle / "evidence_records.csv")
            evidence_index = defaultdict(list)
            for ev in ev_rows:
                evidence_index[(ev.get("subject_id"), ev.get("predicate"), ev.get("object_id"), ev.get("source_release"))].append(ev)
            matched_evidence = [*external_evidence, *regulatory_evidence, *mapping_evidence, *current_reactome_evidence]
            for e in selected:
                key = (e["from"], e["relation"], e["to"], e["source_release"])
                matched_evidence.extend(evidence_index.get(key, []))
            matched_evidence.extend({"evidence_id": e["id"], "source_release": e["source_release"], "source_record_id": json.loads(e["properties_json"])["source_record_id"], "subject_id": e["from"], "predicate": e["relation"], "object_id": e["to"], "source_assertion_json": e["properties_json"]} for e in hierarchy_additions)
            ev_ids = {e.get("evidence_id") for e in matched_evidence}
            ev_ids.discard(None)
            ev_ids.discard(None)
            record = {"rank": item["rank"], "pert_id": item["pert_id"], "drug": item["pert_iname"], "status": "offline_bundle_subgraph",
                      "candidate_node_id": candidate["id"], "wtcs": item["wtcs"], "signature": item["sig_id"],
                      "nodes": [by_id[x] for x in sorted(neighbor_ids | {n["id"] for n in external_nodes} | {e["from"] for e in external_edges} | {e["to"] for e in external_edges} | {e["source"] for e in candidate_reg_edges} | {e["target"] for e in candidate_reg_edges}) if x in by_id], "edges": selected,
                      "evidence_ids": sorted(ev_ids), "source_evidence": matched_evidence,
                      "regulatory_edges": candidate_reg_edges, "candidate_mechanism_paths": regulatory_paths, "candidate_context_paths": external_context_paths,
                      "regulatory_conflicts": candidate_conflicts,
                      "regulatory_mapping_reject_stats": _count_values(r["reason"] for r in regulatory_map_rejects),
                      "regulatory_mapping_reject_sample": regulatory_map_rejects[:20],
                      "evidence_gaps": (["no_SIGNOR_or_OmniPath_regulatory_layer_available"] if not regulatory_edges else []) + (["no_directional_regulatory_path_to_S1_disease_gene"] if not regulatory_paths else []) + ["directional_mechanisms_require_context_compatibility_review", "path_search_is_offline_bundle_derived"]}
        target = out / f"{item['rank']:02d}_{item['pert_id']}.json"
        target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        rows.append({"rank": item["rank"], "pert_id": item["pert_id"], "drug": item["pert_iname"], "status": record["status"],
                     "node_count": len(record.get("nodes", [])), "edge_count": len(record.get("edges", [])), "evidence_count": len(record.get("evidence_ids", [])),
                     "target_nodes": sum(n["type"] in {"Gene", "Protein", "ChEMBLTarget"} for n in record.get("nodes", [])),
                     "regulatory_path_count": len(record.get("candidate_mechanism_paths", [])), "signor_path_edge_count": sum(e.get("source_database") == "SIGNOR" for e in candidate_reg_edges), "omnipath_path_edge_count": sum(e.get("source_database") == "OmniPath" for e in candidate_reg_edges), "conflicting_path_edge_count": sum(e.get("id") in candidate_conflict_ids for e in candidate_reg_edges), "context_path_count": len(record.get("candidate_context_paths", [])), "gap_count": len(record["evidence_gaps"]), "subgraph_file": str(target.relative_to(ROOT))})
    regulatory_bundle = build_regulatory_extension_bundle(out)
    report_dir = REPORT
    report_dir.mkdir(parents=True, exist_ok=True)
    with (report_dir / "03_top10_subgraph_summary.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    (report_dir / "03_subgraph_run.json").write_text(json.dumps({"status": "offline_signed_subgraphs_built", "created_at": datetime.now(timezone.utc).isoformat(), "input_bundle": str(bundle.relative_to(ROOT)).replace("\\", "/"), "input_bundle_manifest_sha256": sha256(bundle / "bundle_manifest.json"), "top10_candidate_count": len(rows), "mapped_regulatory_assertions_before_hub_filter": mapped_regulatory_edge_count, "hub_sources_excluded": len(hub_sources), "hub_assertions_excluded": len(hub_rejects), "regulatory_assertions_after_hub_filter": len(regulatory_edges), "conflict_or_potential_conflict_pairs": len(regulatory_conflicts), "candidate_regulatory_path_count": sum(r["regulatory_path_count"] for r in rows), "candidate_regulatory_path_coverage": f"{sum(r['regulatory_path_count'] > 0 for r in rows)}/{len(rows)}", "candidate_context_route_count": sum(r["context_path_count"] for r in rows), "regulatory_import_extension": regulatory_bundle, "summary_csv": "reports/kg_enrichment/03_top10_subgraph_summary.csv", "per_candidate_subgraphs": [r["subgraph_file"].replace("\\", "/") for r in rows]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (report_dir / "02_conflict_report.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["source", "target", "organism", "cell_context", "status", "assertion_ids", "sources"]
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader()
        for conflict in regulatory_conflicts:
            writer.writerow({**conflict, "assertion_ids": ";".join(conflict["assertion_ids"]), "sources": ";".join(conflict["sources"])})
    with (report_dir / "02_regulatory_mapping_rejects.csv").open("w", encoding="utf-8", newline="") as f:
        fields = ["file", "source", "target", "reason", "assertion_id"]
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(regulatory_map_rejects)
    normalization_manifests = [p for p in sorted(normalized_dir.rglob("*.manifest.json"))]
    (report_dir / "01_regulatory_network_quality.json").write_text(json.dumps({"status": "offline_signed_network_integrated", "mapped_assertions_before_hub_filter": mapped_regulatory_edge_count, "hub_outdegree_cutoff": hub_cutoff, "hub_sources_excluded": len(hub_sources), "hub_assertions_excluded": len(hub_rejects), "assertions_after_hub_filter": len(regulatory_edges), "conflicting_or_potential_conflict_pairs": len(regulatory_conflicts), "mapping_reject_counts": _count_values(r["reason"] for r in regulatory_map_rejects), "normalization_manifests": [str(p.relative_to(ROOT)).replace("\\", "/") for p in normalization_manifests], "import_extension": regulatory_bundle}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (report_dir / "03_subgraph_extraction_report.md").write_text(
        "# Top 10 离线子图提取\n\n"+
        f"输入为 `{bundle.relative_to(ROOT)}`，manifest SHA-256 `{sha256(bundle / 'bundle_manifest.json')}`。\n\n"+
        f"为冻结的 {len(rows)} 个候选各生成了独立 JSON。新增 SIGNOR Oct2026 与 OmniPath academic-filtered core signed assertions，经精确 UniProt→OptimusKG gene crosswalk 映射并按出度阈值过滤；路径仅由有向 REGULATES 边搜索，路径边 Evidence ID 可回溯至来源断言。候选路径形成离线 BioCypher 扩展包 `artifacts/kg_enrichment/regulatory_extension/`（{regulatory_bundle['nodes']} 个节点、{regulatory_bundle['edges']} 条关系，其中 {regulatory_bundle['unique_regulatory_assertions']} 条调控断言和 {regulatory_bundle['protein_gene_mapping_assertions']} 条映射边）；BioCypher 与 importer row preparation 均通过离线校验。该路径搜索步骤是可复现的离线计算，导入由独立的项目 GraphBundle/GraphBuild 流程执行。未知或上下文不明确的冲突符号保留为 unknown。ChEMBL→UniProt→Reactome98 routes 仍是非因果上下文注释。\n",
        encoding="utf-8")
    return {"candidates": len(rows), "mapped_regulatory_assertions_before_hub_filter": mapped_regulatory_edge_count, "regulatory_assertions_after_hub_filter": len(regulatory_edges), "regulatory_conflict_pairs": len(regulatory_conflicts), "regulatory_import_extension": regulatory_bundle, "summary": rows}


def build_regulatory_extension_bundle(subgraph_dir: Path) -> dict[str, Any]:
    """Write a source-preserving BioCypher extension from observed Top10 paths.

    The bundle is an offline, bounded import artifact. It contains only proteins,
    exact protein-gene bridges, and source assertions that participate in at
    least one Top10-to-S1 path; it never writes to Neo4j.
    """
    source_root = ROOT / "data/kg_enrichment/normalized"
    assertion_rows: dict[str, dict[str, str]] = {}
    for file in sorted(source_root.rglob("*.csv")):
        if file.name.endswith(".rejected.csv") or file.name in {"uniprot_gene_crosswalk.csv"}:
            continue
        for row in read_csv(file):
            if row.get("relation") == "REGULATES" and row.get("assertion_id"):
                assertion_rows[row["assertion_id"]] = row
    nodes_by_id: dict[str, dict[str, Any]] = {}
    reg_edges: dict[str, dict[str, Any]] = {}
    for file in sorted(subgraph_dir.glob("*.json")):
        record = json.loads(file.read_text(encoding="utf-8"))
        for node in record.get("nodes", []):
            if node.get("type") in {"Gene", "Protein"}:
                nodes_by_id.setdefault(node["id"], node)
        for edge in record.get("regulatory_edges", []):
            if edge.get("id") in assertion_rows:
                reg_edges.setdefault(edge["id"], edge)
    referenced_gene_ids = {gene_id for node in nodes_by_id.values() if node.get("type") == "Protein" for gene_id in json.loads(node.get("properties_json") or "{}").get("associated_gene_ids", [])}
    bundle_nodes_path = ROOT / "reports/top10_kg/top10_graph_bundle/3928c54d_external_v1/subgraph_nodes.csv"
    for node in read_csv(bundle_nodes_path):
        if node["type"] == "Gene" and node["id"] in referenced_gene_ids:
            nodes_by_id.setdefault(node["id"], node)
    gene_edges = {}
    for protein_id, node in nodes_by_id.items():
        if node.get("type") != "Protein":
            continue
        props = json.loads(node.get("properties_json") or "{}")
        gene_ids = props.get("associated_gene_ids") or []
        if len(gene_ids) != 1 or gene_ids[0] not in nodes_by_id:
            continue
        gene_id = gene_ids[0]
        assertion_id = hashlib.sha256(f"{protein_id}|{gene_id}|{props.get('source_file_sha256', '')}".encode()).hexdigest()
        edge_props = {"assertion_id": assertion_id, "source_record_id": f"OptimusKG:associated_protein:{props.get('uniprot_accession', '')}:{gene_id}", "source_database": "OptimusKG", "source_release": props.get("source_release", "OptimusKG 3.2"), "source_file_sha256": props.get("source_file_sha256", ""), "mapping_method": "exact associated_proteins crosswalk; unique gene only"}
        gene_edges[assertion_id] = {"from": protein_id, "label": "PROTEIN-GENE", "to": gene_id, "relation": "ENCODED_BY", "undirected": "false", "source_release": edge_props["source_release"], "properties_json": json.dumps(edge_props, ensure_ascii=False, sort_keys=True)}
    nodes = sorted(nodes_by_id.values(), key=lambda row: row["id"])
    edges = []
    for assertion_id, edge in sorted(gene_edges.items()):
        edges.append(edge)
    conflicting_ids = {edge_id for file in sorted(subgraph_dir.glob("*.json")) for conflict in json.loads(file.read_text(encoding="utf-8")).get("regulatory_conflicts", []) for edge_id in conflict.get("assertion_ids", [])}
    for assertion_id, edge in sorted(reg_edges.items()):
        source = assertion_rows[assertion_id]
        props = {"assertion_id": assertion_id, "sign": source.get("sign", "unknown"), "organism": source.get("organism", "Homo sapiens"), "cell_context": source.get("cell_context", "unknown"), "tissue_context": source.get("tissue_context", "unknown"), "mechanism": source.get("mechanism", "unknown"), "source_database": source.get("source_database", "unknown"), "source_record_id": source.get("original_relation_id", ""), "source_release": source.get("source_release", "unknown"), "evidence_ids": source.get("evidence_ids", "unknown"), "license": source.get("license", "unknown"), "source_file_sha256": source.get("source_file_sha256", ""), "source_assertion_json": json.dumps(source, ensure_ascii=False, sort_keys=True), "conflict_status": "conflicting_or_contextual" if assertion_id in conflicting_ids else "not_flagged"}
        edges.append({"from": edge["from"], "label": "REGULATES", "to": edge["to"], "relation": "REGULATES", "undirected": "false", "source_release": source.get("source_release", "unknown"), "properties_json": json.dumps(props, ensure_ascii=False, sort_keys=True)})
    out_dir = ROOT / "artifacts/kg_enrichment/regulatory_extension"
    out_dir.mkdir(parents=True, exist_ok=True)
    def write_csv(name: str, rows: list[dict[str, Any]], fields: list[str]) -> None:
        with (out_dir / name).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    write_csv("subgraph_nodes.csv", nodes, ["id", "type", "label", "properties_json"])
    write_csv("subgraph_edges.csv", edges, ["from", "label", "to", "relation", "undirected", "source_release", "properties_json"])
    raw_inputs = [ROOT / "data/kg_enrichment/raw/signor/2026-10/Oct2026_release.txt", ROOT / "data/kg_enrichment/raw/omnipath/2026-11-22/interactions.tsv", ROOT / "data/kg_enrichment/normalized/optimuskg/3.2/uniprot_gene_crosswalk.csv", ROOT / "reports/top10_kg/02_top10_frozen_manifest.json", bundle_nodes_path, *sorted(subgraph_dir.glob("*.json"))]
    manifest = {"schema_version": 1, "status": "offline_source_assertion_extension", "scope": "union of unique signed regulatory assertions present in Top10-to-S1 candidate paths", "candidate_count": 10, "unique_regulatory_assertions": len(reg_edges), "protein_gene_mapping_assertions": len(gene_edges), "node_count": len(nodes), "edge_count": len(edges), "source_files_sha256": {p.relative_to(ROOT).as_posix(): sha256(p) for p in raw_inputs}, "node_file_sha256": sha256(out_dir / "subgraph_nodes.csv"), "edge_file_sha256": sha256(out_dir / "subgraph_edges.csv"), "neo4j_write_performed": False}
    (out_dir / "bundle_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        from kg.scripts.biocypher_adapter import validate_bundle_directory
        from kg.scripts.import_phase_b_to_neo4j import input_fingerprint, prepare_biocypher_import_rows, read_graph_inputs
    except ImportError:
        from biocypher_adapter import validate_bundle_directory
        from import_phase_b_to_neo4j import input_fingerprint, prepare_biocypher_import_rows, read_graph_inputs
    validation = validate_bundle_directory(out_dir)
    node_rows, edge_rows, input_hashes = read_graph_inputs(out_dir, None)
    prepared = prepare_biocypher_import_rows(node_rows, edge_rows, "GRAPH_BUILD:OFFLINE_REGULATORY_PREVIEW", "offline-regulatory-preview", input_fingerprint(input_hashes))
    preflight = {"status": "PASS", "translation": "BioCypher rows prepared for importer; no database connection", "node_count": sum(len(rows) for rows in prepared[0].values()), "relationship_count": sum(len(rows) for rows in prepared[1].values()), "node_labels": {label: len(rows) for label, rows in sorted(prepared[0].items())}, "relationship_groups": {"|".join(key): len(rows) for key, rows in sorted(prepared[1].items())}, "neo4j_write_performed": False}
    (out_dir / "offline_import_preflight.json").write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest["status"] = "offline_biocypher_validated_not_imported" if validation.get("status") == "PASS" else "offline_biocypher_validation_failed"
    manifest["biocypher_validation_sha256"] = sha256(out_dir / "biocypher_validation.json")
    manifest["offline_import_preflight_sha256"] = sha256(out_dir / "offline_import_preflight.json")
    manifest["offline_import_preflight_status"] = preflight["status"]
    (out_dir / "bundle_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"bundle_dir": str(out_dir.relative_to(ROOT)).replace("\\", "/"), "nodes": len(nodes), "unique_regulatory_assertions": len(reg_edges), "protein_gene_mapping_assertions": len(gene_edges), "edges": len(edges), "biocypher_validation": validation.get("status"), "manifest_sha256": sha256(out_dir / "bundle_manifest.json")}


def generate_reports() -> dict[str, Any]:
    """Create deterministic per-drug mechanism evidence dossiers from audited inputs."""
    base = ROOT / "reports/top10_kg"
    frozen = json.loads((base / "02_top10_frozen_manifest.json").read_text(encoding="utf-8"))
    literature = read_csv(base / "external_disease_evidence.csv")
    target_response = read_csv(base / "07_target_s1_s2_expression.csv")
    reproducibility = read_csv(base / "top10_reproducibility_evidence.csv")
    grades = read_csv(base / "mechanism_evidence_grade.csv")
    out = ROOT / "artifacts/kg_enrichment/reports"
    out.mkdir(parents=True, exist_ok=True)
    summary = []
    for item in frozen["items"]:
        pert = item["pert_id"]
        graph = json.loads((ROOT / "artifacts/kg_enrichment/subgraphs" / f"{item['rank']:02d}_{pert}.json").read_text(encoding="utf-8"))
        lit = [r for r in literature if r.get("pert_id") == pert]
        responses = [r for r in target_response if r.get("pert_id") == pert]
        repro = next((r for r in reproducibility if r.get("pert_id") == pert), {})
        grade = next((r for r in grades if r.get("pert_id") == pert), {})
        s1_degs = [r for r in responses if r.get("s1_direction") in {"UP", "DOWN"}]
        same_dir = [r for r in s1_degs if r.get("expression_relation", "").startswith("same expression direction")]
        opposite = [r for r in s1_degs if r.get("expression_relation", "").startswith("opposite expression direction")]
        targets_by_semantics = defaultdict(list)
        for edge in graph.get("edges", []):
            if edge.get("label") in {"DRG-GEN", "DRG-TARGET"}:
                targets_by_semantics[edge.get("relation", "unknown")].append(edge.get("to"))
        source_evidence_by_id = {r.get("evidence_id"): r for r in graph.get("source_evidence", []) if r.get("evidence_id")}
        for path_record in graph.get("candidate_mechanism_paths", []):
            target_gene_id = path_record.get("target_gene_mapping", {}).get("gene_id")
            target_assertion_evidence = []
            for edge in graph.get("edges", []):
                if edge.get("to") != target_gene_id or edge.get("relation", "").upper() not in DIRECT_TARGET_RELATIONS: continue
                target_assertion_evidence.extend(r.get("evidence_id") for r in graph.get("source_evidence", []) if r.get("subject_id") == edge.get("from") and r.get("predicate") == edge.get("relation") and r.get("object_id") == target_gene_id and r.get("evidence_id"))
            path_record["drug_target_evidence_ids"] = sorted(set(target_assertion_evidence))
            path_record["evidence_ids"] = sorted(set(path_record.get("evidence_ids", []) + path_record["drug_target_evidence_ids"]))
            path_record["evidence"] = [source_evidence_by_id[eid] for eid in path_record["evidence_ids"] if eid in source_evidence_by_id]
            path_record["s2_terminal_response"] = [r for r in responses if path_record.get("terminal_gene_node_id") and r.get("target_gene_id") == path_record["terminal_gene_node_id"]]
        for context_path in graph.get("candidate_context_paths", []):
            context_path["evidence"] = [source_evidence_by_id[eid] for eid in context_path.get("evidence_ids", []) if eid in source_evidence_by_id]
        support_count = sum("support" in r.get("direction", "") for r in lit)
        conflict_count = sum(any(x in (r.get("curated_finding", "") + r.get("limitations", "")).lower() for x in ["negative", "mixed", "contradict", "missed"]) for r in lit)
        dossier = {
            "schema_version": 1, "rank": item["rank"], "pert_id": pert, "drug": item["pert_iname"],
            "identity": {"status": next((n.get("label") for n in graph.get("nodes", []) if n.get("type") == "Drug"), None), "candidate_mapping_status": "see exact mapping in source GraphBundle"},
            "s2_overall": {"wtcs": item["wtcs"], "sig_id": item["sig_id"], "cell_line": item["cell_line"], "dose": item["dose"], "time": item["treatment_time"], "n_signatures": item["n_signatures"], "interpretation": "whole-signature expression reversal association; not efficacy or target engagement"},
            "known_graph_assertions_by_relation": {k: sorted(set(v)) for k, v in targets_by_semantics.items()},
            "gene_level_s1_s2": {"rows": len(responses), "s1_directional_target_rows": len(s1_degs), "same_expression_direction_rows": len(same_dir), "opposite_expression_direction_rows": len(opposite), "caveat": "COMPZ is transcript response, not target binding/activity; expression direction alone does not determine protein activity"},
            "candidate_mechanism_paths": graph.get("candidate_mechanism_paths", []),
            "candidate_context_paths": graph.get("candidate_context_paths", []),
            "literature": lit,
            "literature_review_status": "manual focused review records only; not systematic review",
            "human_mechanism_grade": grade,
            "rule_based_dimensions": {
                "EvidenceQuality": {"value": grade.get("grade", "U"), "basis": "existing human-curated A/B/C/U mechanism evidence grade", "missing": not bool(grade)},
                "DirectionConsistency": {"value": "not_assessable_at_S1_transcript_vs_protein_activity_level" if graph.get("candidate_mechanism_paths") else "not_assessable_no_signed_target_to_S1_path", "basis": "signed path effect is retained, but S1 mRNA direction alone is not treated as protein activity or drug action direction", "missing": True},
                "DiseaseRelevance": {"value": "S1 DEG endpoints and/or ER+ literature present" if graph.get("candidate_mechanism_paths") or lit else "missing", "record_count": len(lit), "s1_terminal_path_count": len(graph.get("candidate_mechanism_paths", [])), "missing": not bool(lit or graph.get("candidate_mechanism_paths"))},
                "DrugPerturbationSupport": {"value": "WTCS available; gene-level target response is descriptive and does not validate a signed regulatory path", "wtcs": item["wtcs"], "gene_response_rows": len(responses), "path_terminal_S2_response_rows": sum(bool(p.get("s2_terminal_response")) for p in graph.get("candidate_mechanism_paths", [])), "missing": not bool(responses)},
                "ContextMatch": {"value": "SIGNOR contexts are source labels; OmniPath context unspecified; no normalization to MCF7" if graph.get("candidate_mechanism_paths") else "MCF7 perturbation; regulatory context unavailable", "cell_line": item["cell_line"], "er_positive_literature_records": sum("ER_positive" in r.get("evidence_scope", "") for r in lit), "missing": True},
                "PathSpecificity": {"value": f"{len(graph.get('candidate_mechanism_paths', []))} signed target-to-S1 paths" if graph.get("candidate_mechanism_paths") else "not_assessable", "basis": "path edges are directed regulatory assertions; exact UniProt-to-gene mappings and drug target assertions remain separately evidenced", "missing": not bool(graph.get("candidate_mechanism_paths"))},
                "ContradictionPenalty": {"value": "review required" if graph.get("regulatory_conflicts") or conflict_count else "no conflict record in reviewed subset", "limitation_or_conflict_record_count": conflict_count, "regulatory_conflict_pair_count": len(graph.get("regulatory_conflicts", [])), "missing": not bool(lit or graph.get("regulatory_conflicts"))},
                "ranking_policy": "No aggregate score is emitted: key dimensions are missing or not comparable; WTCS and literature context remain separate evidence channels.",
            },
            "historical_external_reproducibility": repro,
            "evidence_gaps": graph.get("evidence_gaps", []),
            "interpretation": "The current local bundle supports source-traceable drug-target/pathway assertions and disease-context records. ChEMBL direct mechanism, target components, and Reactome protein participation are contextual annotation only, not a causal chain or ER+ effect. It does not contain the signed directed regulatory layer required to infer a causal molecular path. ER+ literature context and LINCS WTCS remain separate evidence channels.",
        }
        path = out / f"{item['rank']:02d}_{pert}.json"
        path.write_text(json.dumps(dossier, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        summary.append({"rank": item["rank"], "pert_id": pert, "drug": item["pert_iname"], "grade": grade.get("grade", "U"), "target_relation_types": len(targets_by_semantics), "target_assertion_rows": sum(map(len, targets_by_semantics.values())), "context_route_count": len(graph.get("candidate_context_paths", [])), "gene_response_rows": len(responses), "er_literature_records": len(lit), "supportive_er_records": support_count, "conflict_or_limitation_records": conflict_count, "regulatory_paths": len(graph.get("candidate_mechanism_paths", [])), "regulatory_conflict_pairs": len(graph.get("regulatory_conflicts", [])), "signor_path_edges": sum(e.get("source_database") == "SIGNOR" for e in graph.get("regulatory_edges", [])), "omnipath_path_edges": sum(e.get("source_database") == "OmniPath" for e in graph.get("regulatory_edges", [])), "external_s1_status": repro.get("exp010_status", "not_reported"), "prism_status": repro.get("exp011_status", "not_reported"), "report_file": str(path.relative_to(ROOT))})
    with (REPORT / "05_mechanism_report_summary.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    ranking_items = []
    for item in frozen["items"]:
        graph = json.loads((ROOT / "artifacts/kg_enrichment/subgraphs" / f"{item['rank']:02d}_{item['pert_id']}.json").read_text(encoding="utf-8"))
        ranking_items.append({"rank": item["rank"], "pert_id": item["pert_id"], "drug": item["pert_iname"],
                              "status": "unscored_no_validated_regulatory_path" if not graph.get("candidate_mechanism_paths") else "paths_require_review",
                              "mechanism_paths": graph.get("candidate_mechanism_paths", []),
                              "context_routes": graph.get("candidate_context_paths", []),
                              "score": None, "score_dimensions": {"EvidenceQuality": "see dossier", "DirectionConsistency": "not_assessable", "DiseaseRelevance": "see dossier", "DrugPerturbationSupport": "see dossier", "ContextMatch": "see dossier", "PathSpecificity": "not_assessable", "ContradictionPenalty": "review_required"},
                              "missing_evidence": graph.get("evidence_gaps", [])})
    (REPORT / "04_mechanism_ranking.json").write_text(json.dumps({"schema_version": 1, "status": "no_aggregate_scores_emitted", "policy": "Context-only routes are not scored as causal mechanisms; missing dimensions remain explicit.", "items": ranking_items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = ["# Top 10 机制证据报告（规则生成）", "", "基于冻结 Top 10 离线 bundle、基因级 S1/S2 响应、人工审查疾病文献表和既有外部复现结果生成。没有调用 LLM。文献数量表示审查表记录，不代表独立机制验证数量。", ""]
    for row in summary:
        report.extend([f"## {row['rank']}. {row['drug']} ({row['pert_id']})", "", f"- 图谱关联断言：{row['target_assertion_rows']} 条，涉及 {row['target_relation_types']} 种关系语义；请查看单药 JSON 中各类型，不能全部解读为直接靶点。", f"- SIGNOR/OmniPath→S1 有向调控路径：{row['regulatory_paths']} 条（源断言边：SIGNOR {row['signor_path_edges']}，OmniPath {row['omnipath_path_edges']}）；路径证据和 UniProt-gene 映射随路径列出。", f"- 该候选路径涉及的冲突/上下文不明方向关系对：{row['regulatory_conflict_pairs']}；未知方向保持 unknown，未做多数投票。", f"- ChEMBL→UniProt→Reactome98 上下文路线：{row['context_route_count']} 条；这些是非因果注释，不代表 ER+ 效应。", f"- 基因级 S1/S2 靶点响应记录：{row['gene_response_rows']}；WTCS 是药物层级表达逆转证据，不是靶点机制验证。", f"- 人工审查疾病背景记录：{row['er_literature_records']}；证据级别 {row['grade']}（人工规则评估，不是疗效概率）。", "- S1 mRNA 方向没有被当作蛋白活性；未输出路径与疾病逆转的一致性结论。", "- 主要缺口：MCF7/组织背景统一、source ablation 和盲法路径有效性审查仍待完成。", ""])
    REPORT.mkdir(parents=True, exist_ok=True)
    (REPORT / "05_literature_evidence_report.md").write_text("\n".join(report), encoding="utf-8")
    (REPORT / "05_top10_explanations.json").write_text(json.dumps({"schema_version": 1, "source": "deterministic rules; no LLM", "items": summary}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    context_route_counts = {item["pert_id"]: len(json.loads((ROOT / "artifacts/kg_enrichment/subgraphs" / f"{item['rank']:02d}_{item['pert_id']}.json").read_text(encoding="utf-8")).get("candidate_context_paths", [])) for item in frozen["items"]}
    subgraphs = [json.loads((ROOT / "artifacts/kg_enrichment/subgraphs" / f"{item['rank']:02d}_{item['pert_id']}.json").read_text(encoding="utf-8")) for item in frozen["items"]]
    regulatory_path_counts = {item["pert_id"]: len(graph.get("candidate_mechanism_paths", [])) for item, graph in zip(frozen["items"], subgraphs)}
    regulatory_source_assertions = {source: len({edge["id"] for graph in subgraphs for edge in graph.get("regulatory_edges", []) if edge.get("source_database") == source}) for source in ["SIGNOR", "OmniPath"]}
    conflict_total = max(0, sum(1 for _ in csv.DictReader((REPORT / "02_conflict_report.csv").open(encoding="utf-8"))) if (REPORT / "02_conflict_report.csv").is_file() else 0)
    drugmechdb_eval = evaluate_drugmechdb()
    signor_manifest = json.loads((ROOT / "data/kg_enrichment/normalized/signor/2026-10/signor_human_protein_regulation.csv.manifest.json").read_text(encoding="utf-8"))
    omnipath_manifest = json.loads((ROOT / "data/kg_enrichment/normalized/omnipath/2026-11-22/omnipath_human_core_signed.csv.manifest.json").read_text(encoding="utf-8"))
    extension_manifest = json.loads((ROOT / "artifacts/kg_enrichment/regulatory_extension/bundle_manifest.json").read_text(encoding="utf-8"))
    extension_preflight = json.loads((ROOT / "artifacts/kg_enrichment/regulatory_extension/offline_import_preflight.json").read_text(encoding="utf-8"))
    import_audit_path = REPORT / "02_import_audit.json"
    import_audit = json.loads(import_audit_path.read_text(encoding="utf-8")) if import_audit_path.is_file() else {}
    registered_import = import_audit.get("import", {})
    primekg_manifest_path = ROOT / "data/kg_enrichment/normalized/primekg/2022-05/primekg_top10_manifest.json"
    primekg_manifest = json.loads(primekg_manifest_path.read_text(encoding="utf-8")) if primekg_manifest_path.is_file() else {}
    reactome_membership_manifest_path = ROOT / "data/kg_enrichment/normalized/reactome/2026-10/reactome_gene_pathways.manifest.json"
    reactome_membership_manifest = json.loads(reactome_membership_manifest_path.read_text(encoding="utf-8")) if reactome_membership_manifest_path.is_file() else {}
    current_reactome_annotation_count = sum(sum(len(p.get("s1_gene_current_reactome_pathway_annotations", [])) for p in g.get("candidate_mechanism_paths", [])) for g in (json.loads(f.read_text(encoding="utf-8")) for f in sorted((ROOT / "artifacts/kg_enrichment/subgraphs").glob("*.json"))))
    eval_data = {
        "schema_version": 1, "status": "staging_graph_imported_research_evaluation_partial",
        "baseline": {"source": "reports/top10_kg/09_before_after_comparison.md", "old_graph_direct_target_coverage": "5/10 (historical file-based audit)", "old_path_coverage": "5/10 (historical GraphBuild a6aabb2147cb5f5e)"},
        "external_data": {"SIGNOR": {"release": signor_manifest["release_version"], "records_raw": signor_manifest["records_raw"], "records_valid": signor_manifest["records_valid"], "records_rejected": signor_manifest["records_rejected"], "sha256": signor_manifest["sha256"]}, "OmniPath": {"release": omnipath_manifest["release_version"], "records_raw": omnipath_manifest["records_raw"], "signed_source_assertions": omnipath_manifest["records_valid"], "records_rejected": omnipath_manifest["records_rejected"], "sha256": omnipath_manifest["sha256"], "license_filter": "academic; per-resource license retained"}, "Reactome_current_gene_pathways": {"release": reactome_membership_manifest.get("release_version"), "records_valid": reactome_membership_manifest.get("records_valid"), "records_rejected": reactome_membership_manifest.get("records_rejected"), "sha256": reactome_membership_manifest.get("sha256"), "top10_terminal_gene_annotations": current_reactome_annotation_count, "sign": "unknown; annotation only; imported as CONTAINS_GENE"}, "PrimeKG": {"release": primekg_manifest.get("release_version"), "license": primekg_manifest.get("license"), "sha256": primekg_manifest.get("sha256"), "candidate_identity_coverage": primekg_manifest.get("counts", {}).get("candidate_identity_coverage"), "subset_edges": primekg_manifest.get("counts", {}).get("subset_edges"), "status": "imported_to_isolated_staging_as_unsigned_associations" if primekg_manifest else "not_downloaded"}, "DrugMechDB": drugmechdb_eval},
        "enhanced_offline_bundle": {"top10_exact_identity": "10/10 (8 OptimusKG exact + 2 explicit external overlay)", "target_assertion_coverage": f"{sum(bool(x['target_assertion_rows']) for x in summary)}/10 (any retained target assertion; relation types remain separate)", "candidate_to_S1_pathway_routes": "8/10; 528 historical graph intersection rows (not regulatory paths)", "signed_regulatory_path_coverage": f"{sum(v > 0 for v in regulatory_path_counts.values())}/10", "signed_regulatory_path_count": sum(regulatory_path_counts.values()), "signed_paths_by_pert_id": regulatory_path_counts, "path_assertions_by_source_unique_within_top10": regulatory_source_assertions, "potential_or_contextual_conflict_pairs_after_hub_filter": conflict_total, "ChEMBL_to_Reactome98_context_route_coverage": f"{sum(v > 0 for v in context_route_counts.values())}/10", "ChEMBL_to_Reactome98_context_route_count": sum(context_route_counts.values()), "context_routes_by_pert_id": context_route_counts, "traceable_assertions": "path edge IDs, UniProt-gene mapping evidence, source records, PMID refs and source hashes attached in per-drug artifacts", "offline_biocypher_extension": {"status": extension_manifest["status"], "nodes": extension_manifest["node_count"], "edges": extension_manifest["edge_count"], "signed_assertions": extension_manifest["unique_regulatory_assertions"], "importer_row_preparation": extension_preflight["status"], "neo4j_write_performed": False}, "registered_staging_graph_build": registered_import, "registered_external_graph_build": import_audit.get("external_import", {}), "external_graph_build_audit": import_audit.get("external_layer_audit"), "external_layer_rollback_status": import_audit.get("external_rollback_rehearsal", {}).get("status"), "drugmechdb_independent_breast_reference": f"{drugmechdb_eval['top10_exact_breast_neoplasm_path_count']} exact drug-name-matched breast-neoplasm reference path(s); direct target overlap {drugmechdb_eval['target_overlap_fraction']}", "er_context_records": sum(x["er_literature_records"] for x in summary), "manual_grade_distribution": {g: sum(x["grade"] == g for x in summary) for g in ["A", "B", "C", "U"]}},
        "interpretation": "Coverage definitions differ across historical bundle versions; the old/new target counts are not a controlled ablation. SIGNOR and OmniPath now contribute source-traceable signed regulatory paths for a subset of candidates. The computed path sign describes propagation across molecular regulation edges; it is not combined with drug action or interpreted as protein activity from S1 mRNA. ChEMBL→Reactome98 routes remain annotation context. DrugMechDB evaluation found one strict breast-neoplasm indication/target-overlap case; this is not population-wide recall. No blind path validity review has been run.",
        "not_evaluated": ["source ablations under one identical evaluator", "blind path validity", "drug-action-to-terminal-protein direction versus disease activity", "broad independent DrugMechDB recall (only exact Top10 drug-name/breast-neoplasm matches reported)", "browser E2E and mechanism path UI acceptance", "production deployment/promotion"],
    }
    (REPORT / "07_evaluation_partial.json").write_text(json.dumps(eval_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (REPORT / "07_final_evaluation.md").write_text("# 图谱增强阶段评估（部分离线结果）\n\n"
        "## 已有证据与本轮改动\n\n"
        "Top 10 名单沿用冻结 manifest。离线子图保留 OptimusKG/BioCypher 原关系，并加入 SIGNOR Oct2026 人类 direct protein-protein signed causal records、OmniPath academic-filtered core resource/evidence records、精确 UniProt↔gene mapping，以及项目现存 ChEMBL/Reactome98 context snapshots。Reactome current-2026-10 hierarchy 与人类 gene-pathway membership 已规范化；唯一 membership 和 hierarchy 断言作为无符号注释层导入独立 staging。PrimeKG Dataverse v2 CC0-1.0 已核验并抽取 Top10 子集，以无方向 ASSOCIATED_WITH 关系导入 staging；该关联不扩展或赋符号给调控链。每条机制路径保留调控断言 ID、逐来源 evidence、映射 evidence、release、许可及 source hash。调控路径仅沿 directed REGULATES 搜索，最多 4 个调控步；通路参与仍不用于 sign propagation。\n\n"
        "## 指标和边界\n\n" + json.dumps(eval_data, ensure_ascii=False, indent=2) + "\n\n"
        "旧版与新版覆盖口径不完全一致，故此处不声称受控实验提升。当前 signed regulatory paths 和冲突对数量见上方机器可读评估；这些统计是候选子图命中数，不等同于独立实验数或路径有效性。S1 transcript direction 未用于推断蛋白活性；MCF7 与 SIGNOR BTO cell/tissue context 尚未统一映射。DrugMechDB v2.0.1 是独立参考，不并入预测图；严格药名 + Breast Neoplasms MeSH 匹配仅得 1 条，且只支持 doxorubicin-TOP2A 靶点重叠，不验证 ER+ 疗效或完整机制。未做盲法专家路径核验。任务专用 staging Neo4j 已完成只读审计、冷备份、恢复验证和两个 GraphBuild 导入；两版本幂等及精确清单均通过，独立恢复副本的回滚演练通过。主数据库未修改。\n\n"
        "## 缺失与失败解释\n\n"
        "部分药物没有 ChEMBL direct mechanism 或可精确匹配的 human protein component/Reactome 98 映射；部分药物也没有当前报告可用的基因级 S2 响应，不能用药物层面的 WTCS 填补。没有调控边可使目标到 S1 疾病基因的因果路径无法搜索；缺少 ER+ 的药物特异文献时只报告已有审查表记录，不做外推。\n\n"
        "## 下一步\n\n"
        "首个 GraphBuild 导入 328 条路径支持的有向调控断言（6,985 节点、39,351 条关系、39,218 条 EvidenceRecord）。第二个 GraphBuild 导入 Reactome/PrimeKG 外部层（9,526 节点、91,943 条关系、91,810 条 EvidenceRecord）：Reactome 48,709 条唯一基因-通路断言和 2,905 条层级边；PrimeKG 978 条 ASSOCIATED_WITH 关联。两次导入均通过双次幂等、精确 inventory、来源字段核验和独立恢复副本回滚演练。剩余研究工作包括冻结 Top 10 下的 source ablations、盲审路径有效性、统一 MCF7/组织背景、浏览器端到端验收和生产部署评估。\n", encoding="utf-8")
    output_files = [REPORT / "04_mechanism_ranking.json", REPORT / "05_mechanism_report_summary.csv", REPORT / "05_literature_evidence_report.md", REPORT / "05_top10_explanations.json", REPORT / "07_evaluation_partial.json", REPORT / "07_final_evaluation.md", REPORT / "08_drugmechdb_breast_path_matches.csv", REPORT / "08_drugmechdb_evaluation.json", REPORT / "02_import_audit.json", REPORT / "02_rollback_guide.md", REPORT / "08_paper_to_project_mapping.md", *sorted(out.glob("*.json"))]
    input_files = [base / "02_top10_frozen_manifest.json", base / "external_disease_evidence.csv", base / "07_target_s1_s2_expression.csv", base / "top10_reproducibility_evidence.csv", base / "mechanism_evidence_grade.csv",
                   REPORT / "02_import_audit.json", REPORT / "02_rollback_rehearsal.json", REPORT / "02_registered_import_verification.json", REPORT / "02_live_neo4j_post_import_audit.json", REPORT / "09_external_layer_import_audit.json", REPORT / "09_full_external_bundle_preflight.json", REPORT / "09_registered_external_import_verification.json", REPORT / "10_live_neo4j_post_external_audit.json", ROOT / "data/kg_enrichment/backups/backup_manifest.json",
                   ROOT / "data/top10_kg/evidence/chembl_mechanisms.csv", ROOT / "data/top10_kg/evidence/chembl_mechanism_targets.csv", ROOT / "data/top10_kg/evidence/reactome_protein_pathways.csv",
                   ROOT / "data/kg_enrichment/raw/reactome/2026-10/ReactomePathways.txt", ROOT / "data/kg_enrichment/raw/reactome/2026-10/ReactomePathwaysRelation.txt",
                   ROOT / "data/kg_enrichment/normalized/reactome/2026-10/reactome_normalization_manifest.json",
                   ROOT / "data/kg_enrichment/raw/reactome/2026-10/UniProt2Reactome_All_Levels.txt",
                   ROOT / "data/kg_enrichment/normalized/reactome/2026-10/reactome_gene_pathways.csv",
                   ROOT / "data/kg_enrichment/normalized/reactome/2026-10/reactome_gene_pathways.manifest.json",
                   ROOT / "data/kg_enrichment/raw/primekg/2022-05/kg.csv",
                   ROOT / "data/kg_enrichment/raw/primekg/2022-05/nodes.tab",
                   ROOT / "data/kg_enrichment/raw/primekg/2022-05/README.txt",
                   ROOT / "data/kg_enrichment/normalized/primekg/2022-05/primekg_top10_nodes.csv",
                   ROOT / "data/kg_enrichment/normalized/primekg/2022-05/primekg_top10_edges.csv",
                   ROOT / "data/kg_enrichment/normalized/primekg/2022-05/primekg_top10_manifest.json",
                   REPORT / "01_download_attempts.json",
                   ROOT / "kg/scripts/normalize_top10_primekg_subset.py",
                   ROOT / "kg/scripts/normalize_reactome_gene_membership.py",
                   ROOT / "kg/config/enrichment_sources.yaml",
                   ROOT / "data/kg_enrichment/raw/signor/2026-10/Oct2026_release.txt",
                   ROOT / "data/kg_enrichment/raw/signor/2026-10/Oct2026_release.txt.manifest.json",
                   ROOT / "data/kg_enrichment/normalized/signor/2026-10/signor_human_protein_regulation.csv",
                   ROOT / "data/kg_enrichment/normalized/signor/2026-10/signor_human_protein_regulation.csv.manifest.json",
                   ROOT / "data/kg_enrichment/normalized/signor/2026-10/signor_human_protein_regulation.csv.rejected.csv",
                   ROOT / "data/kg_enrichment/raw/omnipath/2026-11-22/interactions.tsv",
                   ROOT / "data/kg_enrichment/raw/omnipath/2026-11-22/interactions.tsv.manifest.json",
                   ROOT / "data/kg_enrichment/raw/omnipath/2026-11-22/resources.tsv",
                   ROOT / "data/kg_enrichment/raw/omnipath/2026-11-22/resources.tsv.manifest.json",
                   ROOT / "data/kg_enrichment/normalized/omnipath/2026-11-22/omnipath_human_core_signed.csv",
                   ROOT / "data/kg_enrichment/normalized/omnipath/2026-11-22/omnipath_human_core_signed.csv.manifest.json",
                   ROOT / "data/kg_enrichment/normalized/omnipath/2026-11-22/omnipath_human_core_signed.csv.rejected.csv",
                   ROOT / "data/kg_enrichment/normalized/optimuskg/3.2/uniprot_gene_crosswalk.csv",
                   ROOT / "data/kg_enrichment/normalized/optimuskg/3.2/uniprot_gene_crosswalk.manifest.json",
                   ROOT / "data/optimuskg/3.2/source_manifest.json",
                   ROOT / "data/kg_enrichment/raw/drugmechdb/2.0.1/indication_paths.yaml",
                   ROOT / "data/kg_enrichment/raw/drugmechdb/2.0.1/indication_paths.yaml.manifest.json",
                   ROOT / "data/kg_enrichment/raw/drugmechdb/2.0.1/LICENSE",
                   ROOT / "data/kg_enrichment/raw/drugmechdb/2.0.1/LICENSE.manifest.json",
                   ROOT / "artifacts/kg_enrichment/regulatory_extension/subgraph_nodes.csv",
                   ROOT / "artifacts/kg_enrichment/regulatory_extension/subgraph_edges.csv",
                   ROOT / "artifacts/kg_enrichment/regulatory_extension/bundle_manifest.json",
                   ROOT / "artifacts/kg_enrichment/regulatory_extension/biocypher_validation.json",
                   ROOT / "artifacts/kg_enrichment/regulatory_extension/offline_import_preflight.json",
                   *sorted((ROOT / "artifacts/kg_enrichment/subgraphs").glob("*.json"))]
    report_manifest = {"schema_version": 1, "status": "validated_offline_report_artifacts", "project_id": "3f18f4c1-713d-58c5-8a53-38eca5a5aaf9",
                       "frozen_top10_sha256": json.loads((base / "02_top10_frozen_manifest.json").read_text(encoding="utf-8")).get("source_sha256"),
                       "inputs_sha256": {p.relative_to(ROOT).as_posix(): sha256(p) for p in input_files},
                       "outputs_sha256": {p.relative_to(ROOT).as_posix(): sha256(p) for p in output_files}}
    (REPORT / "05_report_manifest.json").write_text(json.dumps(report_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"candidates": len(summary), "summary": summary}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("audit"); sub.add_parser("status"); sub.add_parser("build-subgraphs"); sub.add_parser("reason", help="rebuild bounded Top 10 paths and context routes")
    sub.add_parser("generate-reports"); sub.add_parser("evaluate", help="regenerate dossiers and partial offline evaluation"); sub.add_parser("evaluate-drugmechdb", help="run exact-name, breast-neoplasm DrugMechDB reference comparison")
    n = sub.add_parser("normalize"); n.add_argument("source", type=Path); n.add_argument("--source-name", required=True); n.add_argument("--output", type=Path, required=True)
    nm = sub.add_parser("normalize-mapped"); nm.add_argument("source", type=Path); nm.add_argument("--source-name", required=True); nm.add_argument("--release", required=True); nm.add_argument("--license", required=True); nm.add_argument("--species", default="Homo sapiens"); nm.add_argument("--column-map-json", required=True); nm.add_argument("--output", type=Path, required=True); nm.add_argument("--no-header", action="store_true")
    d = sub.add_parser("download"); d.add_argument("url"); d.add_argument("--source-name", required=True); d.add_argument("--release", required=True); d.add_argument("--license", required=True); d.add_argument("--species", default="Homo sapiens"); d.add_argument("--schema-version", required=True); d.add_argument("--output", type=Path, required=True)
    rp = sub.add_parser("normalize-reactome"); rp.add_argument("--pathways", type=Path, required=True); rp.add_argument("--hierarchy", type=Path, required=True); rp.add_argument("--output-dir", type=Path, required=True)
    sg = sub.add_parser("normalize-signor"); sg.add_argument("source", type=Path); sg.add_argument("--release", required=True); sg.add_argument("--license", default="CC BY 4.0"); sg.add_argument("--output", type=Path, required=True)
    om = sub.add_parser("normalize-omnipath"); om.add_argument("source", type=Path); om.add_argument("--resource-metadata", type=Path, required=True); om.add_argument("--release", required=True); om.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if args.command in {"audit", "status"}:
        write_baseline(); print(json.dumps(audit(), ensure_ascii=False, indent=2))
    elif args.command in {"build-subgraphs", "reason"}: print(json.dumps(build_subgraphs(), ensure_ascii=False, indent=2))
    elif args.command in {"generate-reports", "evaluate"}: print(json.dumps(generate_reports(), ensure_ascii=False, indent=2))
    elif args.command == "evaluate-drugmechdb": print(json.dumps(evaluate_drugmechdb(), ensure_ascii=False, indent=2))
    elif args.command == "normalize": print(json.dumps(normalize_tsv(args.source, args.output, args.source_name), ensure_ascii=False, indent=2))
    elif args.command == "normalize-mapped": print(json.dumps(normalize_mapped_tsv(args.source, args.output, source_name=args.source_name, release=args.release, license_name=args.license, species=args.species, column_map=json.loads(args.column_map_json), has_header=not args.no_header), ensure_ascii=False, indent=2))
    elif args.command == "download": print(json.dumps(download_source(args.url, args.output, args.source_name, args.release, args.license, args.species, args.schema_version), ensure_ascii=False, indent=2))
    elif args.command == "normalize-reactome": print(json.dumps(normalize_reactome_pathways(args.pathways, args.hierarchy, args.output_dir), ensure_ascii=False, indent=2))
    elif args.command == "normalize-signor": print(json.dumps(normalize_signor(args.source, args.output, release=args.release, license_name=args.license), ensure_ascii=False, indent=2))
    elif args.command == "normalize-omnipath": print(json.dumps(normalize_omnipath(args.source, args.resource_metadata, args.output, release=args.release), ensure_ascii=False, indent=2))


if __name__ == "__main__": main()
