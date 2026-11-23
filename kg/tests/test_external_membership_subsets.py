import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_primekg_subset_is_exact_scoped_and_unsigned():
    base = ROOT / "data/kg_enrichment/normalized/primekg/2022-05"
    manifest = json.loads((base / "primekg_top10_manifest.json").read_text(encoding="utf-8"))
    nodes = rows(base / "primekg_top10_nodes.csv")
    edges = rows(base / "primekg_top10_edges.csv")
    assert manifest["license"] == "CC0-1.0"
    assert manifest["official_md5"] == "aac8191d4fbc5bf09cdf8c3c78b4e75f"
    assert manifest["counts"]["candidate_identity_coverage"] == "6/10"
    assert manifest["records_valid"] == len(edges) == 1026
    assert len({n["node_index"] for n in nodes}) == len(nodes)
    assert all(edge["sign"] == "unknown" for edge in edges)
    assert all(edge["direction"] == "undirected_or_unspecified" for edge in edges)
    assert {edge["relation"] for edge in edges} <= {"drug_protein", "protein_protein", "disease_protein"}
    assert all(edge["source_database"] == "PrimeKG" for edge in edges)


def test_reactome_gene_pathways_are_exact_unsigned_membership_annotations():
    base = ROOT / "data/kg_enrichment/normalized/reactome/2026-10"
    manifest = json.loads((base / "reactome_gene_pathways.manifest.json").read_text(encoding="utf-8"))
    memberships = rows(base / "reactome_gene_pathways.csv")
    assert manifest["records_valid"] == len(memberships) == 54361
    assert manifest["records_rejected"]["unmapped_or_ambiguous_uniprot"] == 108281
    assert all(row["organism"] == "Homo sapiens" for row in memberships)
    assert all(row["sign"] == "unknown" for row in memberships)
    keys = {(row["gene_id"], row["uniprot_accession"], row["pathway_id"], row["evidence_code"]) for row in memberships}
    assert len(keys) == len(memberships)


def test_candidate_paths_keep_reactome_membership_separate_from_regulation():
    subgraphs = sorted((ROOT / "artifacts/kg_enrichment/subgraphs").glob("*.json"))
    assert len(subgraphs) == 10
    for path in subgraphs:
        graph = json.loads(path.read_text(encoding="utf-8"))
        for mechanism in graph.get("candidate_mechanism_paths", []):
            assert "pathway_annotation_semantics" in mechanism
            assert "does not extend or sign" in mechanism["pathway_annotation_semantics"]
            assert all(item["evidence_id"] not in mechanism.get("edge_ids", []) for item in mechanism.get("s1_gene_current_reactome_pathway_annotations", []))
