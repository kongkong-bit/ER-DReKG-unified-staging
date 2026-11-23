"""Create an explicitly software-only fixture to verify cross-project KG reuse.

The fixture reuses real public Drug/Gene/Pathway assertions from the bounded
Phase B source bundle. Project links are synthetic software test records and
are marked test_only; they are not biomedical findings.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from sqlalchemy import select

from app.db import SessionLocal
from app.models import AnalysisRun, Candidate, Project


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments" / "platform_phase_b"
EXT = ROOT / "experiments" / "platform_phase_b_pathways"
SLUG = "software-test-graph-isolation"
RUN_ID = "RUN:TEST_GRAPH_ISOLATION_20261113"
TEST_PERT_ID = "SOFTWARE-TEST-PERT"
TEST_RELEASE = "DiseaseGraph Lab software test fixture; not biological evidence"
TEST_ASSERTION = {
    "test_only": True,
    "purpose": "Verify public entity reuse and project/GraphBuild isolation",
    "interpretation": "Synthetic project-specific links; not a biomedical assertion.",
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    public_nodes: dict[str, dict] = {}
    public_edges: list[dict] = []
    for path in [BASE / "subgraph_nodes.csv", EXT / "pathway_nodes.csv", EXT / "gene_nodes.csv"]:
        for row in read_rows(path):
            public_nodes[row["id"]] = row
    for path in [BASE / "subgraph_edges.csv", EXT / "pathway_edges.csv"]:
        public_edges.extend(read_rows(path))

    candidate_drugs = [row["to"] for row in public_edges if row["label"] == "PROJECT-REFERENCES_DRUG"]
    targets_by_drug: dict[str, list[dict]] = {}
    pathways_by_gene: dict[str, list[dict]] = {}
    for row in public_edges:
        if row["label"] == "DRG-GEN":
            targets_by_drug.setdefault(row["from"], []).append(row)
        elif row["label"] == "PWY-GEN":
            pathways_by_gene.setdefault(row["to"], []).append(row)

    chosen = None
    for drug_id in sorted(set(candidate_drugs)):
        for target_edge in targets_by_drug.get(drug_id, []):
            options = pathways_by_gene.get(target_edge["to"], [])
            if options:
                chosen = (drug_id, target_edge, sorted(options, key=lambda item: item["from"])[0])
                break
        if chosen:
            break
    if chosen is None:
        raise RuntimeError("No real bounded public Drug→Gene→Pathway seed is available")
    drug_id, target_edge, pathway_edge = chosen
    gene_id = target_edge["to"]
    pathway_id = pathway_edge["from"]
    required_public_ids = {drug_id, gene_id, pathway_id}
    if not required_public_ids.issubset(public_nodes):
        raise RuntimeError("Selected public edge endpoints are missing from node tables")

    with SessionLocal() as db:
        project = db.scalar(select(Project).where(Project.slug == SLUG))
        if project is None:
            project = Project(slug=SLUG, name="软件测试项目：跨项目图谱隔离（无科研数据）", disease_id="", status="test_only")
            db.add(project)
            db.flush()
        run = db.get(AnalysisRun, RUN_ID)
        if run is None:
            run = AnalysisRun(
                analysis_run_id=RUN_ID,
                project_id=project.project_id,
                run_type="software_test_graph_isolation",
                status="completed",
                parameters={"test_only": True, "public_seed_drug_id": drug_id, "public_seed_gene_id": gene_id, "public_seed_pathway_id": pathway_id},
                software_versions={"fixture": "build_phase_e_test_fixture.py"},
                input_hashes={},
            )
            db.add(run)
        elif run.project_id != project.project_id:
            raise RuntimeError("Existing software test run belongs to a different project")
        candidate_id = f"{project.project_id}:{RUN_ID}:{TEST_PERT_ID}"
        candidate = db.get(Candidate, candidate_id)
        if candidate is None:
            db.add(Candidate(
                candidate_id=candidate_id,
                project_id=project.project_id,
                analysis_run_id=RUN_ID,
                pert_id=TEST_PERT_ID,
                drug_name="软件测试候选（仅用于验证图谱隔离）",
                rank=1,
                score_name="software_test_only",
                score_value="NA",
                evidence_json={"test_only": True, "assertion": TEST_ASSERTION},
            ))
        db.commit()
        project_id = project.project_id
        project_slug = project.slug

    candidate_node = f"CANDIDATE:{project_id}:{RUN_ID}:{TEST_PERT_ID}"
    context_node = f"DISEASE_CONTEXT:TEST_ONLY:{project_id}:{RUN_ID}"
    nodes = [public_nodes[node_id] for node_id in sorted(required_public_ids)]
    nodes += [
        {"id": candidate_node, "type": "Candidate", "label": "Software test candidate", "properties_json": json.dumps({"project_id": project_id, "project_slug": project_slug, "analysis_run_id": RUN_ID, "pert_id": TEST_PERT_ID, "test_only": True}, sort_keys=True)},
        {"id": context_node, "type": "DiseaseContext", "label": "SOFTWARE TEST ONLY — no disease evidence", "properties_json": json.dumps({"project_id": project_id, "project_slug": project_slug, "analysis_run_id": RUN_ID, "test_only": True}, sort_keys=True)},
    ]

    edges = [target_edge, pathway_edge]
    def test_edge(source: str, label: str, target: str, relation: str) -> dict:
        return {"from": source, "label": label, "to": target, "relation": relation, "source_release": TEST_RELEASE, "undirected": "false", "properties_json": json.dumps(TEST_ASSERTION, ensure_ascii=False, sort_keys=True)}

    edges.extend([
        test_edge(context_node, "PROJECT-HAS_CANDIDATE", candidate_node, "test_only_project_candidate"),
        test_edge(candidate_node, "PROJECT-REFERENCES_DRUG", drug_id, "project_candidate_drug"),
        test_edge(context_node, "PROJECT-HAS_DEG", gene_id, "test_only_seed_gene"),
        test_edge(context_node, "S1-ENRICHED-PATHWAY", pathway_id, "test_only_pathway_link"),
        test_edge(pathway_id, "S1-ENRICHED-GENE", gene_id, "test_only_pathway_gene_link"),
    ])
    output = ROOT / "data" / "processed" / "projects" / project_id / "graph_bundle"
    write_rows(output / "subgraph_nodes.csv", ["id", "type", "label", "properties_json"], nodes)
    write_rows(output / "subgraph_edges.csv", ["from", "label", "to", "relation", "source_release", "undirected", "properties_json"], edges)
    manifest = {
        "bundle_version": "1",
        "status": "validated",
        "project_id": project_id,
        "analysis_run_id": RUN_ID,
        "test_only": True,
        "source_release": "OptimusKG 3.2 public assertions plus clearly marked software-only project links",
        "public_entities_reused": {"drug_id": drug_id, "gene_id": gene_id, "pathway_id": pathway_id},
        "test_assertion": TEST_ASSERTION,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }
    (output / "bundle_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "test_only": True, "project_id": project_id, "project_slug": project_slug, "analysis_run_id": RUN_ID, "candidate_pert_id": TEST_PERT_ID, "public_entities_reused": manifest["public_entities_reused"], "bundle_path": output.relative_to(ROOT).as_posix(), "nodes": len(nodes), "edges": len(edges)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
