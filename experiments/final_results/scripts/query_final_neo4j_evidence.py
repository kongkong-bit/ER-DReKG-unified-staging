from __future__ import annotations

import csv
import gzip
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parents[1]
GRAPH_BUILD_ID = "GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:a6aabb2147cb5f5e"
sys.path.insert(0, str(ROOT / "backend"))
from app.core.config import settings  # noqa: E402
from neo4j import GraphDatabase  # noqa: E402


def read_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_rows(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    top = read_rows(OUT / "results" / "final_top10.csv")
    pert_path = next((ROOT / "s2_lincs" / "data").glob("*pert_info*.gz"))
    pert = {}
    with gzip.open(pert_path, "rt", encoding="utf-8", newline="") as stream:
        for item in csv.DictReader(stream, delimiter="\t"):
            pert.setdefault(item["pert_id"], item)
    s1_path = ROOT / "data" / "processed" / "projects" / "3f18f4c1-713d-58c5-8a53-38eca5a5aaf9" / "graph_bundle" / "runs" / "8eda9601-2fd3-48cc-9a45-74809870a480" / "s1_gene_mapping_audit.csv"
    s1 = {}
    for item in read_rows(s1_path):
        s1.setdefault(item["ensembl_gene_id"], item)
    target_rows: list[dict] = []
    pathway_rows: list[dict] = []
    match_rows: list[dict] = []
    driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    try:
        with driver.session(database=settings.neo4j_database) as session:
            for row in top:
                meta = pert.get(row["pert_id"])
                inchi_key = str(meta.get("inchi_key") or "").strip() if meta else ""
                if not inchi_key:
                    match_rows.append({"rank": row["rank"], "pert_id": row["pert_id"], "drug_name": row["drug_name"], "inchi_key": "", "neo4j_mapping": "missing LINCS InChIKey"})
                    continue
                drugs = session.execute_read(lambda tx, key: tx.run(
                    "MATCH (d:Drug {inchi_key:$key}) RETURN d.id AS drug_id,d.name AS graph_name,d.sources AS sources,d.source_ids AS source_ids LIMIT 5", key=key
                ).data(), inchi_key)
                if not drugs:
                    match_rows.append({"rank": row["rank"], "pert_id": row["pert_id"], "drug_name": row["drug_name"], "inchi_key": inchi_key, "neo4j_mapping": "no exact InChIKey node in current graph"})
                    continue
                drug_ids = sorted({str(item["drug_id"]) for item in drugs if item.get("drug_id")})
                match_rows.append({"rank": row["rank"], "pert_id": row["pert_id"], "drug_name": row["drug_name"], "inchi_key": inchi_key,
                                   "neo4j_mapping": "exact InChIKey", "graph_drug_ids": ";".join(drug_ids),
                                   "graph_names": ";".join(sorted({str(item.get("graph_name") or "") for item in drugs}))})
                for drug_id in drug_ids:
                    targets = session.execute_read(lambda tx, did: tx.run(
                        "MATCH (d:Drug {id:$id})-[r:TARGETS]->(g:Gene) "
                        "WHERE $build_id IN coalesce(r.graph_build_ids,[]) "
                        "RETURN DISTINCT d.id AS drug_id,g.id AS target_gene_id,g.symbol AS target_symbol, "
                        "r.evidence_ids AS target_evidence_ids,r.source_assertion_json AS target_assertion", id=did, build_id=GRAPH_BUILD_ID
                    ).data(), drug_id)
                    for target in targets:
                        gene_id = str(target["target_gene_id"])
                        s1row = s1.get(gene_id)
                        common = {
                            "rank": row["rank"], "pert_id": row["pert_id"], "drug_name": row["drug_name"], "inchi_key": inchi_key,
                            "graph_drug_id": drug_id, "target_gene_id": gene_id, "target_symbol": target.get("target_symbol") or "",
                            "target_evidence_ids": ";".join(target.get("target_evidence_ids") or []),
                            "target_assertion_json": target.get("target_assertion") or "",
                            "target_in_s1_tested_universe": bool(s1row),
                            "s1_direction": s1row.get("direction", "") if s1row else "",
                            "s1_logFC": float(s1row["logFC"]) if s1row and s1row.get("logFC") else None,
                            "s1_FDR": float(s1row["adj.P.Val"]) if s1row and s1row.get("adj.P.Val") else None,
                        }
                        target_rows.append(common)
                        pathways = session.execute_read(lambda tx, gid: tx.run(
                            "MATCH (p)-[eg:HAS_ENRICHED_GENE]->(g:Gene {id:$gid}) "
                            "MATCH (ctx:DiseaseContext {project_slug:'erpos-gse42568'})-[cp:HAS_ENRICHED_PATHWAY]->(p) "
                            "WHERE (p:Pathway OR p:GeneSet) AND $build_id IN coalesce(eg.graph_build_ids,[]) "
                            "AND $build_id IN coalesce(cp.graph_build_ids,[]) "
                            "RETURN DISTINCT p.id AS pathway_id,p.label AS pathway_label, "
                            "eg.evidence_ids AS gene_link_evidence_ids,eg.source_assertion_json AS gene_link_assertion, "
                            "cp.evidence_ids AS context_evidence_ids,cp.source_assertion_json AS context_assertion", gid=gid, build_id=GRAPH_BUILD_ID
                        ).data(), gene_id)
                        for pathway in pathways:
                            pathway_rows.append({**common,
                                "pathway_id": pathway.get("pathway_id"), "pathway_label": pathway.get("pathway_label"),
                                "gene_pathway_evidence_ids": ";".join(pathway.get("gene_link_evidence_ids") or []),
                                "gene_pathway_assertion_json": pathway.get("gene_link_assertion") or "",
                                "disease_context_evidence_ids": ";".join(pathway.get("context_evidence_ids") or []),
                                "disease_context_assertion_json": pathway.get("context_assertion") or "",
                            })
    finally:
        driver.close()

    mapping_columns = ["rank", "pert_id", "drug_name", "inchi_key", "neo4j_mapping", "graph_drug_ids", "graph_names"]
    target_columns = ["rank", "pert_id", "drug_name", "inchi_key", "graph_drug_id", "target_gene_id", "target_symbol", "target_evidence_ids", "target_assertion_json", "target_in_s1_tested_universe", "s1_direction", "s1_logFC", "s1_FDR"]
    pathway_columns = target_columns + ["pathway_id", "pathway_label", "gene_pathway_evidence_ids", "gene_pathway_assertion_json", "disease_context_evidence_ids", "disease_context_assertion_json"]
    write_rows(OUT / "mechanism" / "final_neo4j_drug_mapping.csv", match_rows, mapping_columns)
    write_rows(OUT / "mechanism" / "final_neo4j_direct_targets.csv", target_rows, target_columns)
    write_rows(OUT / "mechanism" / "final_neo4j_s1_pathway_links.csv", pathway_rows, pathway_columns)
    report = {
        "status": "PASS", "query_time_utc": datetime.now(timezone.utc).isoformat(),
        "connection": "local Neo4j read-only MATCH queries; exact LINCS InChIKey only",
        "project_slug": "erpos-gse42568", "graph_build_id": GRAPH_BUILD_ID, "top10": len(top),
        "exact_graph_drug_mappings": sum(item["neo4j_mapping"] == "exact InChIKey" for item in match_rows),
        "candidates_with_direct_targets": len({item["pert_id"] for item in target_rows}),
        "candidates_with_s1_pathways": len({item["pert_id"] for item in pathway_rows}),
        "direct_target_rows": len(target_rows), "target_pathway_link_rows": len(pathway_rows),
        "ppi_expansion": "not used; current Neo4j relationship type audit has no supported PPI relation",
        "mapping_rows": match_rows,
    }
    (OUT / "mechanism" / "neo4j_query_manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "exact_graph_drug_mappings", "direct_target_rows", "target_pathway_link_rows", "ppi_expansion")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
