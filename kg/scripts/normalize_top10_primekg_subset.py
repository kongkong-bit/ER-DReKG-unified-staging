"""Extract an exact-identity, auditable PrimeKG subset for the frozen ER+ Top 10.

The full PrimeKG CSV is streamed once. No fuzzy name matching is used and all
PrimeKG relations remain unsigned associations unless their native label is a
drug indication/target relation. This script does not write to Neo4j.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOP10 = ROOT / "artifacts/kg_enrichment/baseline/top10_snapshot.json"
IDENTITY = ROOT / "data/top10_kg/identity/top10_identity_mapping.csv"
S1_MAPPING = ROOT / "ER-DReKG-KG-delivery-20261120/01_inputs/s1_and_enrichment/gene_mapping_audit.csv"
RAW = ROOT / "data/kg_enrichment/raw/primekg/2022-05"
OUT = ROOT / "data/kg_enrichment/normalized/primekg/2022-05"
DATA_FILE_MD5 = "aac8191d4fbc5bf09cdf8c3c78b4e75f"
NODE_FILE_MD5 = "7f9ab4109c54049e819ecd14e15a6038"
csv.field_size_limit(2_147_483_647)


def digest(path: Path, algorithm: str = "sha256") -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def compact_id(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.casefold())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="validate hashes and report counts without writing outputs")
    args = parser.parse_args()
    data_path, node_path = RAW / "kg.csv", RAW / "nodes.tab"
    if digest(data_path, "md5") != DATA_FILE_MD5 or digest(node_path, "md5") != NODE_FILE_MD5:
        raise SystemExit("PrimeKG official Dataverse MD5 mismatch; refusing extraction")
    data_sha256 = digest(data_path)
    node_sha256 = digest(node_path)

    frozen = json.loads(TOP10.read_text(encoding="utf-8"))
    identity_rows = list(csv.DictReader(IDENTITY.open(encoding="utf-8-sig", newline="")))
    aliases_by_pert: dict[str, set[str]] = defaultdict(set)
    for row in identity_rows:
        aliases_by_pert[row["lincs_pert_id"]].add(compact_id(row.get("canonical_name", "")))
        aliases_by_pert[row["lincs_pert_id"]].add(compact_id(row.get("lincs_name", "")))
        aliases_by_pert[row["lincs_pert_id"]].update(compact_id(a) for a in row.get("aliases", "").split("|") if a)

    nodes: dict[str, dict[str, str]] = {}
    nodes_by_native_id: dict[tuple[str, str], set[str]] = defaultdict(set)
    drug_hits: dict[str, set[str]] = defaultdict(set)
    breast_disease_ids: set[str] = set()
    gene_ids: set[str] = set()
    genes_by_name: dict[str, set[str]] = defaultdict(set)
    with node_path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            idx = row["node_index"].strip()
            nodes[idx] = row
            kind = row["node_type"].strip().casefold()
            name = compact_id(row["node_name"])
            source = row["node_source"].strip().casefold()
            nodes_by_native_id[(source, row["node_id"].strip())].add(idx)
            if kind == "drug":
                for top in frozen["top10"]:
                    if name and name in aliases_by_pert[top["pert_id"]]:
                        drug_hits[top["pert_id"]].add(idx)
            elif kind in {"gene/protein", "gene", "protein"}:
                genes_by_name[compact_id(row["node_name"])].add(idx)
                if source in {"ncbi", "entrez"}:
                    gene_ids.add(idx)
            elif kind == "disease" and ("breastcancer" in name or name == "breastneoplasms"):
                breast_disease_ids.add(idx)

    s1_gene_ids: set[str] = set()
    with S1_MAPPING.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            try:
                significant = float(row.get("adj.P.Val", "nan")) < 0.05
            except ValueError:
                significant = False
            entrez = row.get("ENTREZID", "").strip()
            if significant and entrez and entrez.casefold() not in {"na", "nan"}:
                s1_gene_ids.update(genes_by_name.get(compact_id(row.get("gene_symbol") or row.get("gene_id") or ""), set()))
                s1_gene_ids.update(nodes_by_native_id.get(("ncbi", entrez), set()))
                s1_gene_ids.update(nodes_by_native_id.get(("entrez", entrez), set()))

    drug_indices = {idx for ids in drug_hits.values() for idx in ids}
    # Retain candidate-drug targets, their links to S1 genes, and breast-disease
    # associations. PPI rows are canonicalized below because PrimeKG stores both
    # endpoint orders for many undirected relationships.
    edges: list[dict[str, str]] = []
    s1_ppi_rows: list[dict[str, str]] = []
    candidate_target_indices: set[str] = set()
    raw_rows = 0
    allowed = {"drug_protein", "indication", "contraindication", "off-label use", "disease_protein", "protein_protein"}
    with data_path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            raw_rows += 1
            x, y, rel = row["x_index"].strip(), row["y_index"].strip(), row["relation"].strip()
            if rel not in allowed:
                continue
            if rel == "drug_protein" and ((x in drug_indices and y in gene_ids) or (y in drug_indices and x in gene_ids)):
                drug_idx, target_idx = (x, y) if x in drug_indices else (y, x)
                candidate_target_indices.add(target_idx)
                edges.append(row)
            elif rel in {"indication", "contraindication", "off-label use"} and ((x in drug_indices and y in breast_disease_ids) or (y in drug_indices and x in breast_disease_ids)):
                edges.append(row)
            elif rel == "disease_protein" and ((x in breast_disease_ids and y in s1_gene_ids) or (y in breast_disease_ids and x in s1_gene_ids)):
                edges.append(row)
            elif rel == "protein_protein" and x in s1_gene_ids and y in s1_gene_ids:
                s1_ppi_rows.append(row)

    edges.extend(r for r in s1_ppi_rows if (r["x_index"] in candidate_target_indices and r["y_index"] in s1_gene_ids) or (r["y_index"] in candidate_target_indices and r["x_index"] in s1_gene_ids))
    unique_edges: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in edges:
        x, y = row["x_index"].strip(), row["y_index"].strip()
        # These retained PrimeKG relation families are association assertions;
        # canonical endpoint ordering removes reciprocal duplicate records.
        a, b = sorted((x, y), key=lambda value: int(value))
        unique_edges[(row["relation"], a, b)] = row
    edges = list(unique_edges.values())

    counts = {
        "raw_records": raw_rows,
        "candidate_exact_name_matches": {k: sorted(v) for k, v in drug_hits.items()},
        "candidate_identity_coverage": f"{sum(bool(v) for v in drug_hits.values())}/{len(frozen['top10'])}",
        "breast_neoplasm_nodes": len(breast_disease_ids),
        "s1_significant_gene_nodes_matched": len(s1_gene_ids),
        "candidate_target_gene_nodes": len(candidate_target_indices),
        "subset_edges": len(edges),
        "subset_relations": dict(sorted(__import__("collections").Counter(e["relation"] for e in edges).items())),
    }
    if args.dry_run:
        print(json.dumps(counts, ensure_ascii=False, indent=2))
        return

    OUT.mkdir(parents=True, exist_ok=True)
    used_nodes = {v for e in edges for v in (e["x_index"], e["y_index"])}
    node_out = OUT / "primekg_top10_nodes.csv"
    edge_out = OUT / "primekg_top10_edges.csv"
    with node_out.open("w", encoding="utf-8", newline="") as stream:
        fields = ["node_index", "node_id", "node_type", "node_name", "node_source", "source_database", "source_release", "source_file_sha256"]
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader()
        for idx in sorted(used_nodes, key=lambda x: int(x)):
            n = nodes[idx]
            writer.writerow({**n, "source_database": "PrimeKG", "source_release": "Dataverse-v2-2022-05", "source_file_sha256": data_sha256})
    with edge_out.open("w", encoding="utf-8", newline="") as stream:
        fields = list(edges[0].keys()) + ["source_database", "source_release", "source_file_sha256", "source_record_id", "sign", "direction"] if edges else []
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader()
        for row in edges:
            row = dict(row)
            row.update(source_database="PrimeKG", source_release="Dataverse-v2-2022-05", source_file_sha256=data_sha256, source_record_id=f"{row['x_index']}|{row['relation']}|{row['y_index']}", sign="unknown", direction="undirected_or_unspecified")
            writer.writerow(row)
    manifest = {
        "source_name": "PrimeKG", "source_url": "https://doi.org/10.7910/DVN/IXA7BM",
        "official_download_url": "https://dataverse.harvard.edu/api/access/datafile/6180620",
        "release_version": "Harvard Dataverse v2 (2022-05-02)", "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "license": "CC0-1.0", "species": "human", "schema_version": "PrimeKG kg.csv header v2",
        "local_path": str(data_path.relative_to(ROOT)).replace("\\", "/"), "sha256": data_sha256, "official_md5": DATA_FILE_MD5,
        "node_file": str(node_path.relative_to(ROOT)).replace("\\", "/"), "node_sha256": node_sha256, "node_official_md5": NODE_FILE_MD5,
        "records_raw": raw_rows, "records_valid": len(edges), "records_rejected_or_out_of_scope": raw_rows-len(edges),
        "selection": "Top10 exact canonical/alias drug name; significant mapped S1 genes (FDR<0.05); breast cancer disease labels; selected native PrimeKG relations; no fuzzy drug matching",
        "counts": counts, "normalized_nodes": str(node_out.relative_to(ROOT)).replace("\\", "/"), "normalized_edges": str(edge_out.relative_to(ROOT)).replace("\\", "/"),
        "warning": "PrimeKG relations are association-level for this project; no causal sign or ER+ specificity is inferred. PrimeKG is excluded from S1/S2 model inputs and only used as an external knowledge/evidence layer."
    }
    (OUT / "primekg_top10_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(counts, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
