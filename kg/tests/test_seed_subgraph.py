import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments" / "platform_phase_b"


def read_csv(name):
    with (OUT / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def test_subgraph_retains_source_assertions_and_stable_ids():
    nodes = read_csv("subgraph_nodes.csv")
    edges = read_csv("subgraph_edges.csv")
    assert len({n["id"] for n in nodes}) == len(nodes)
    assert all(e["from"] and e["to"] and e["source_release"] for e in edges)
    source_edges = [e for e in edges if e["label"] in {"DRG-GEN", "PWY-GEN"}]
    assert source_edges
    assert all(json.loads(e["properties_json"]) for e in source_edges)


def test_candidate_routes_are_supported_and_manifest_is_bounded():
    routes = read_csv("candidate_target_pathway_routes.csv")
    manifest = json.loads((OUT / "phase_b_manifest.json").read_text(encoding="utf-8"))
    assert len(routes) == manifest["counts"]["target_gene_pathway_routes"]
    assert routes
    assert all(r["drug_target_assertion"] and r["pathway_gene_assertion"] for r in routes)
    assert manifest["graph_source"] == "OptimusKG 3.2"
    assert manifest["license"] == "CC BY-NC-SA 4.0"
    assert "NOT_AVAILABLE" in manifest["disease_specific_pathway_seed"]


def test_unmatched_mapping_is_explicit():
    rows = read_csv("unmatched_entities.csv")
    assert rows
    assert all(r.get("mapping_status") for r in rows)
