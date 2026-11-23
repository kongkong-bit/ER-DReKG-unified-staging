"""Build a frozen, evidence-linked local graph for the v4 mechanism Top10."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = ROOT / "experiments" / "robust_candidate_prioritization"
RESULTS = EXPERIMENT / "results"
MANIFEST = RESULTS / "v4_manifest.json"
TOP10 = RESULTS / "v4_mechanism_top10.csv"
CHAINS = RESULTS / "v4_chains.csv"
BUNDLE_REL = Path("data/processed/projects/3f18f4c1-713d-58c5-8a53-38eca5a5aaf9/graph_bundle/runs/e0421796-2aff-47e2-9228-d683eab05fa9")
BUNDLE = ROOT / BUNDLE_REL
BUNDLE_AUDIT = EXPERIMENT / "inputs" / "graph_bundle_manifest.json"
OUTPUTS = [RESULTS / "v4_top10_local_subgraph.json", ROOT / "frontend" / "public" / "robust-top10-subgraph.json"]
OUTPUT_MANIFEST = RESULTS / "v4_top10_local_subgraph_manifest.json"
csv.field_size_limit(32 * 1024 * 1024)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def json_field(value: str | None) -> Any:
    if not value:
        return {}
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {}


def evidence_key(subject: str, predicate: str, obj: str) -> tuple[str, str, str]:
    return subject, predicate, obj


def main() -> None:
    frozen = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if frozen.get("status") != "PASS":
        raise SystemExit("v4 result manifest must be PASS")
    for path in (TOP10, CHAINS):
        expected = frozen.get("outputs", {}).get(path.name)
        if not expected or sha256(path) != expected:
            raise SystemExit(f"v4 output hash mismatch: {path.name}")
    source_hashes = frozen.get("input_sha256", {})
    for relative, path in {
        "graph_bundle_manifest.json": BUNDLE / "bundle_manifest.json",
        "graph_subgraph_nodes.csv": BUNDLE / "subgraph_nodes.csv",
        "graph_subgraph_edges.csv": BUNDLE / "subgraph_edges.csv",
        "graph_evidence_records.csv": BUNDLE / "evidence_records.csv",
        "graph_candidate_mapping_audit.csv": BUNDLE / "candidate_mapping_audit.csv",
    }.items():
        if sha256(path) != source_hashes.get(relative):
            raise SystemExit(f"frozen GraphBundle input hash mismatch: {relative}")
    audit = json.loads(BUNDLE_AUDIT.read_text(encoding="utf-8"))
    if audit.get("files", {}).get("subgraph_nodes.csv", {}).get("sha256") != source_hashes["graph_subgraph_nodes.csv"]:
        raise SystemExit("the v4 graph bundle audit does not match the frozen v4 inputs")

    top10 = rows(TOP10)
    chain_rows = rows(CHAINS)
    mapping_rows = {row["pert_id"]: row for row in rows(BUNDLE / "candidate_mapping_audit.csv")}
    graph_nodes = {row["id"]: row for row in rows(BUNDLE / "subgraph_nodes.csv")}
    evidence_rows = rows(BUNDLE / "evidence_records.csv")
    evidence_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for item in evidence_rows:
        key = evidence_key(item["subject_id"], item["predicate"], item["object_id"])
        evidence_by_key.setdefault(key, []).append({
            "evidence_id": item["evidence_id"],
            "source_release": item["source_release"],
            "source_record_id": item["source_record_id"],
            "source_assertion": json_field(item.get("source_assertion_json")),
        })
    graph_edges: list[dict[str, Any]] = []
    for row in rows(BUNDLE / "subgraph_edges.csv"):
        graph_edges.append({**row, "properties": json_field(row.get("properties_json"))})

    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[str, dict[str, Any]] = {}
    missing: list[dict[str, str]] = []
    pathway_edge_index: dict[str, list[dict[str, Any]]] = {}
    for row in graph_edges:
        if row["label"] == "S1-ENRICHED-GENE":
            pathway_edge_index.setdefault(row["to"], []).append(row)

    def add_source_node(node_id: str) -> None:
        source = graph_nodes.get(node_id)
        if source is None:
            return
        props = json_field(source.get("properties_json"))
        kind = source["type"].lower()
        nodes[node_id] = {
            "id": node_id, "label": source["label"], "kind": kind,
            "detail": {"node_id": node_id, "node_type": source["type"], "properties": props},
        }

    def add_edge(source: str, target: str, relation: str, category: str, evidence: list[dict[str, Any]], detail: dict[str, Any], *, synthetic: bool = False) -> None:
        key = f"{source}|{category}|{relation}|{target}"
        edges[key] = {
            "id": key, "source": source, "target": target, "relation": relation,
            "category": category, "directed": True,
            "evidence_ids": [item["evidence_id"] for item in evidence],
            "evidence": evidence, "detail": detail, "synthetic": synthetic,
        }

    for candidate in top10:
        pert_id = candidate["pert_id"]
        audit_row = mapping_rows.get(pert_id, {})
        if audit_row.get("mapping_status") != "matched_exact_inchikey" or audit_row.get("inchi_key") != candidate.get("inchi_key"):
            missing.append({"pert_id": pert_id, "stage": "drug_mapping", "reason": "no exact InChIKey match in frozen GraphBundle"})
            continue
        drug_id = audit_row.get("graph_drug_id", "")
        if drug_id not in graph_nodes:
            missing.append({"pert_id": pert_id, "stage": "drug_node", "reason": "mapped drug node is absent from frozen GraphBundle"})
            continue
        candidate_id = f"robust-candidate:{pert_id}"
        nodes[candidate_id] = {
            "id": candidate_id, "label": candidate.get("drug_name") or pert_id, "kind": "robust-candidate",
            "detail": {"rank_mech": int(candidate["rank_mech"]), "rank_v4": int(candidate["rank_v4"]), "pert_id": pert_id,
                       "drug_name": candidate.get("drug_name"), "S_disc": float(candidate["S_disc"]),
                       "stability_top20": float(candidate["stability_top20"]), "n_dose_conditions": int(candidate["n_dose_conditions"]),
                       "inchi_key": candidate.get("inchi_key"), "top10_definition": "v4 mechanism Top10, rank_mech order"},
        }
        add_source_node(drug_id)
        add_edge(candidate_id, drug_id, "exact InChIKey", "candidate-mapping", [],
                 {"pert_id": pert_id, "inchi_key": candidate["inchi_key"], "mapping_method": audit_row.get("mapping_method"), "source": "frozen GraphBundle candidate_mapping_audit.csv"}, synthetic=True)
        candidate_chains = [row for row in chain_rows if row.get("pert_id") == pert_id]
        chain_count = 0
        for chain in candidate_chains:
            symbol = chain.get("target", "")
            relation = chain.get("relation", "")
            target_id = ""
            # Match the chain's exact target symbol and exact directional assertion.
            for node_id, node in graph_nodes.items():
                if node["type"] == "Gene" and node["label"].upper() == symbol.upper() and evidence_by_key.get(evidence_key(drug_id, relation, node_id)):
                    target_id = node_id
                    break
            if not target_id:
                missing.append({"pert_id": pert_id, "stage": "direct_target", "reason": f"no cited {relation} edge for target {symbol}"})
                continue
            target_evidence = evidence_by_key[evidence_key(drug_id, relation, target_id)]
            add_source_node(target_id)
            add_edge(drug_id, target_id, relation, "drug-target", target_evidence,
                     {"direction": chain.get("drug_direction"), "s1_logFC": float(chain["s1_logFC"]),
                      "s1_deg": True, "relation_conflict": False, "chain_definition": "v4 direction-coherent, evidence-linked direct target"})
            pathway_names = {value.strip() for value in (chain.get("pathways") or "").split(";") if value.strip()}
            matched_pathways = 0
            for row in pathway_edge_index.get(target_id, []):
                pathway_node = graph_nodes.get(row["from"])
                if not pathway_node or pathway_node["label"] not in pathway_names:
                    continue
                link_assertions = row["properties"].get("analysis_assertions", [])
                link_evidence: list[dict[str, Any]] = []
                # Enrichment EvidenceRecords are indexed as pathway -> gene.
                for assertion in link_assertions:
                    analysis = str(assertion.get("analysis") or "")
                    predicate = f"HAS_ENRICHED_GENE"
                    link_evidence.extend(evidence_by_key.get(evidence_key(row["from"], predicate, target_id), []))
                    if analysis and assertion.get("adjusted_p") is not None:
                        pass
                if not link_evidence:
                    continue
                add_source_node(row["from"])
                pvalues = [item.get("adjusted_p") for item in link_assertions if item.get("adjusted_p") is not None]
                analyses = sorted({str(item.get("analysis")) for item in link_assertions if item.get("analysis")})
                add_edge(target_id, row["from"], "belongs to S1-enriched pathway", "target-pathway", link_evidence,
                         {"analysis": analyses, "adjusted_p": min(pvalues) if pvalues else None,
                          "s1_logFC": float(chain["s1_logFC"]), "er_program": str(chain.get("er_program", "")).lower() == "true",
                          "source_relation": row["label"], "interpretation": "enrichment overlap, not causality or efficacy"})
                matched_pathways += 1
            if matched_pathways == 0:
                missing.append({"pert_id": pert_id, "stage": "target_pathway", "reason": f"no evidence-linked S1 pathway node for target {symbol}"})
            chain_count += 1
        if chain_count == 0:
            missing.append({"pert_id": pert_id, "stage": "chain", "reason": "no v4 chain could be materialized from the frozen GraphBundle"})

    artifact = {
        "schema_version": "robust-top10-local-subgraph-v1",
        "status": "PASS" if len(top10) == 10 and len({row["pert_id"] for row in top10}) == 10 and not missing else "PARTIAL",
        "ranking": {"kind": "v4 mechanism Top10", "protocol": frozen.get("protocol"), "protocol_sha256": frozen.get("spec_sha256"), "manifest_sha256": sha256(MANIFEST), "result_sha256": sha256(TOP10), "candidate_count": len(top10)},
        "graph": {"project_id": "3f18f4c1-713d-58c5-8a53-38eca5a5aaf9", "project_slug": "erpos-gse42568", "analysis_run_id": "ANALYSIS_RUN:KG_GRAPH_BUNDLE:e0421796-2aff-47e2-9228-d683eab05fa9", "source_release": "OptimusKG 3.2 + project S1 enrichment", "bundle_manifest_sha256": sha256(BUNDLE / "bundle_manifest.json"), "bundle_path": BUNDLE_REL.as_posix()},
        "nodes": sorted(nodes.values(), key=lambda item: (item["kind"], item["label"].casefold(), item["id"])),
        "edges": sorted(edges.values(), key=lambda item: (item["category"], item["source"], item["target"])),
        "coverage": {"candidate_count": len(top10), "candidate_nodes": sum(node["kind"] == "robust-candidate" for node in nodes.values()), "mapped_graph_drugs": sum(node["kind"] == "drug" for node in nodes.values()), "target_nodes": sum(node["kind"] == "gene" for node in nodes.values()), "pathway_nodes": sum(node["kind"] == "pathway" for node in nodes.values()), "edge_count": len(edges), "missing_routes": missing},
        "limits": ["候选到图谱药物节点的映射基于完全一致的 InChIKey。", "只展示 v4 机制 Top10 方向一致且带来源证据的药物—靶点—S1 通路链。", "图谱关系与富集重叠不是因果、疗效或临床证据。", "没有纳入 PPI 扩展；不以邻近关系补造路径。"],
    }
    if not artifact["coverage"]["candidate_nodes"] == 10:
        artifact["status"] = "PARTIAL"
    payload = json.dumps(artifact, ensure_ascii=False, indent=2) + "\n"
    for path in OUTPUTS:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
    out_manifest = {
        "status": artifact["status"], "schema_version": artifact["schema_version"],
        "generated_utc": datetime.now(timezone.utc).isoformat(), "generator_sha256": sha256(Path(__file__)), "ranking_manifest_created_utc": frozen.get("created_utc"), "inputs": {
            "v4_manifest.json": sha256(MANIFEST), "v4_mechanism_top10.csv": sha256(TOP10), "v4_chains.csv": sha256(CHAINS),
            "graph_bundle_manifest.json": sha256(BUNDLE / "bundle_manifest.json"), "subgraph_nodes.csv": sha256(BUNDLE / "subgraph_nodes.csv"),
            "subgraph_edges.csv": sha256(BUNDLE / "subgraph_edges.csv"), "evidence_records.csv": sha256(BUNDLE / "evidence_records.csv"),
            "candidate_mapping_audit.csv": sha256(BUNDLE / "candidate_mapping_audit.csv"),
        },
        "outputs": {path.relative_to(ROOT).as_posix(): sha256(path) for path in OUTPUTS},
        "counts": artifact["coverage"],
    }
    OUTPUT_MANIFEST.write_text(json.dumps(out_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": artifact["status"], "nodes": len(nodes), "edges": len(edges), "coverage": artifact["coverage"], "manifest": OUTPUT_MANIFEST.relative_to(ROOT).as_posix()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
