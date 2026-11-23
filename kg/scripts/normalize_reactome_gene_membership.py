"""Normalize current Reactome human UniProt-to-pathway membership exactly."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/kg_enrichment/raw/reactome/2026-10/UniProt2Reactome_All_Levels.txt"
PATHWAYS = ROOT / "data/kg_enrichment/normalized/reactome/2026-10/reactome_pathway_nodes.csv"
CROSSWALK = ROOT / "data/kg_enrichment/normalized/optimuskg/3.2/uniprot_gene_crosswalk.csv"
OUT = ROOT / "data/kg_enrichment/normalized/reactome/2026-10"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    pathway_ids = {r["stable_id"] for r in csv.DictReader(PATHWAYS.open(encoding="utf-8-sig", newline=""))}
    accessions: dict[str, set[str]] = defaultdict(set)
    with CROSSWALK.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            acc, gene = row.get("uniprot_accession", "").strip(), row.get("gene_id", "").strip()
            if acc and gene:
                accessions[acc].add(gene)
    raw = valid = human = rejected = 0
    records: set[tuple[str, str, str, str, str]] = set()
    reject_reasons: dict[str, int] = defaultdict(int)
    input_hash = sha(RAW)
    with RAW.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, delimiter="\t")
        for line, row in enumerate(reader, 1):
            raw += 1
            if len(row) != 6:
                rejected += 1; reject_reasons["expected_6_columns"] += 1; continue
            accession, stable_id, url, name, evidence, species = (x.strip() for x in row)
            if species != "Homo sapiens":
                continue
            human += 1
            if stable_id not in pathway_ids:
                rejected += 1; reject_reasons["pathway_not_in_current_human_release"] += 1; continue
            genes = accessions.get(accession, set())
            if len(genes) != 1:
                rejected += 1; reject_reasons["unmapped_or_ambiguous_uniprot"] += 1; continue
            gene_id = next(iter(genes))
            records.add((gene_id, accession, stable_id, evidence or "unknown", url))
            valid += 1
    if args.dry_run:
        print(json.dumps({"records_raw": raw, "records_human": human, "records_valid_before_dedup": valid, "records_unique": len(records), "records_rejected": rejected, "reject_reasons": dict(reject_reasons)}, indent=2))
        return
    OUT.mkdir(parents=True, exist_ok=True)
    output = OUT / "reactome_gene_pathways.csv"
    fields = ["gene_id", "uniprot_accession", "pathway_id", "evidence_code", "source_record_id", "source_url", "organism", "source_database", "source_release", "license", "source_file_sha256", "sign"]
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader()
        for gene, acc, pathway, ev, url in sorted(records):
            writer.writerow({"gene_id": gene, "uniprot_accession": acc, "pathway_id": f"REACT:{pathway}", "evidence_code": ev,
                             "source_record_id": f"{acc}|{pathway}|{ev}", "source_url": url, "organism": "Homo sapiens",
                             "source_database": "Reactome", "source_release": "current-2026-10", "license": "CC0 1.0 Universal",
                             "source_file_sha256": input_hash, "sign": "unknown"})
    manifest = {"source_name": "Reactome human pathway gene membership", "source_url": "https://reactome.org/download/current/UniProt2Reactome_All_Levels.txt",
                "release_version": "current-2026-10", "retrieved_at": datetime.now(timezone.utc).isoformat(), "local_path": str(RAW.relative_to(ROOT)).replace("\\", "/"),
                "sha256": input_hash, "license": "CC0 1.0 Universal", "species": "Homo sapiens", "schema_version": "six-column Reactome mapping TSV",
                "records_raw": raw, "records_human": human, "records_valid_before_dedup": valid, "records_valid": len(records), "records_rejected": dict(reject_reasons),
                "mapping": "exact one-to-one UniProt accession to OptimusKG 3.2 Ensembl gene crosswalk; ambiguous/unmapped excluded",
                "sign_semantics": "unknown; pathway participation is not causal regulation", "normalized_path": str(output.relative_to(ROOT)).replace("\\", "/"), "normalized_sha256": sha(output)}
    (OUT / "reactome_gene_pathways.manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
