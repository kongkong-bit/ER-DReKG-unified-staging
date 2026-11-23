import csv
import hashlib
import gzip
import json
from pathlib import Path
import shutil

import polars as pl
import pytest

from kg.scripts.build_project_graph_bundle import build_bundle, jdump, _edge, read_projected_parquet_nodes


def write_rows(path: Path, columns: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_duplicate_edge_preserves_two_json_serializable_assertions():
    edges = {}
    _edge(edges, "CTX:1", "PROJECT-HAS_DEG", "ENSG1", "HAS_DEG", {"source_record_id": "run:gene-a", "direction": "UP"}, "Project S1")
    _edge(edges, "CTX:1", "PROJECT-HAS_DEG", "ENSG1", "HAS_DEG", {"source_record_id": "run:gene-b", "direction": "DOWN"}, "Project S1")
    edge = next(iter(edges.values()))
    serialized = jdump(edge["properties"])
    assert '"source_assertion_count":2' in serialized
    assert [item["source_record_id"] for item in edge["properties"]["source_assertions"]] == ["run:gene-a", "run:gene-b"]


def test_duckdb_parquet_projection_preserves_nested_properties_and_skips_unused_columns(tmp_path: Path):
    source = tmp_path / "drug.parquet"
    pl.DataFrame([{
        "id": "CHEMBLTEST1",
        "label": "DRG",
        "properties": {
            "name": "Drug A",
            "inchi_key": "INCHI-A",
            "sources": {"direct": ["TEST"], "indirect": []},
            "unused_payload": "large data ignored by this query",
        },
    }]).write_parquet(source)

    rows = read_projected_parquet_nodes(source, ["name", "inchi_key", "sources"])

    assert rows == [{
        "id": "CHEMBLTEST1",
        "label": "DRG",
        "properties": {
            "name": "Drug A",
            "inchi_key": "INCHI-A",
            "sources": {"direct": ["TEST"], "indirect": []},
        },
    }]
    with pytest.raises(ValueError, match="simple schema identifiers"):
        read_projected_parquet_nodes(source, ["name; DROP TABLE nodes"])


def test_project_bundle_uses_exact_compound_mapping_and_preserves_s2_conditions(tmp_path: Path):
    root = tmp_path
    public = root / "optimuskg"
    (public / "nodes").mkdir(parents=True)
    (public / "edges").mkdir(parents=True)
    (public / "source_manifest.json").write_text(json.dumps({"release": "3.2", "license": "CC BY-NC-SA 4.0"}), encoding="utf-8")
    pl.DataFrame([{"id": "CHEMBLTEST1", "label": "DRG", "properties": {"name": "Drug A", "inchi_key": "INCHI-A", "canonical_smiles": "C", "sources": {"direct": ["TEST"], "indirect": []}, "source_ids": [], "synonyms": []}}]).write_parquet(public / "nodes" / "drug.parquet")
    pl.DataFrame([{"id": "ENSG00000000001", "label": "GEN", "properties": {"symbol": "TP53", "name": "Tumor protein p53", "biotype": "protein_coding", "symbol_synonyms": ["P53"], "obsolete_symbols": [], "xrefs": [], "sources": {"direct": ["TEST"], "indirect": []}}}]).write_parquet(public / "nodes" / "gene.parquet")
    pl.DataFrame(schema={"id": pl.String, "label": pl.String, "properties": pl.Struct({"name": pl.String, "species": pl.String})}).write_parquet(public / "nodes" / "pathway.parquet")
    pl.DataFrame([{"from": "CHEMBLTEST1", "to": "ENSG00000000001", "label": "DRG-GEN", "relation": "TARGET", "undirected": False, "properties": {"relation_conflict": True, "relation_assertions": [{"source": "TEST_DB", "relation": "TARGET"}], "sources": {"direct": ["TEST_DB"], "indirect": []}}}]).write_parquet(public / "edges" / "drug_gene.parquet")
    pl.DataFrame(schema={"from": pl.String, "to": pl.String, "label": pl.String, "relation": pl.String, "undirected": pl.Boolean, "properties": pl.Struct({"sources": pl.Struct({"direct": pl.List(pl.String), "indirect": pl.List(pl.String)})})}).write_parquet(public / "edges" / "pathway_gene.parquet")

    s1 = root / "s1.csv"
    write_rows(s1, ["gene_id", "gene_symbol", "logFC", "adj.P.Val", "t"], [{"gene_id": "TP53", "gene_symbol": "TP53", "logFC": 2.1, "adj.P.Val": 0.001, "t": 5.0}])
    mapping = root / "gene_mapping_audit.csv"
    write_rows(mapping, ["gene_id", "ENTREZID", "ensembl_gene_ids", "mapping_status"], [{"gene_id": "TP53", "ENTREZID": "7157", "ensembl_gene_ids": "ENSG00000000001", "mapping_status": "mapped_one_to_one"}])
    enrichment = root / "enrichment"
    enrichment.mkdir()
    # Match the current project R output contract: `analysis` carries the
    # stable GO ID while `pathway` is only its human-readable description.
    write_rows(enrichment / "pathway_gene_links.csv", ["analysis", "pathway", "adjusted_p", "ENTREZID", "gene_symbol", "ensembl_gene_ids"], [{"analysis": "GO:0000001", "pathway": "test pathway", "adjusted_p": 0.01, "ENTREZID": "7157", "gene_symbol": "TP53", "ensembl_gene_ids": "ENSG00000000001"}])
    write_rows(enrichment / "go_up.csv", ["ID", "Description", "p.adjust"], [{"ID": "GO:0000001", "Description": "test pathway", "p.adjust": 0.01}])
    for filename, columns in [("go_down.csv", ["ID", "Description", "p.adjust"]), ("reactome_up.csv", ["ID", "Description", "p.adjust"]), ("reactome_down.csv", ["ID", "Description", "p.adjust"]), ("hallmark_gsea.csv", ["pathway", "padj", "NES"])]:
        write_rows(enrichment / filename, columns, [])

    conditions = root / "drug_condition_summary.csv"
    write_rows(conditions, ["pert_id", "drug_name", "cell_id", "pert_type", "dose", "time", "n_signatures", "WTCS_median", "WTCS_mean", "WTCS_sd", "WTCS_mad", "quality_cc_median", "TAS_median", "replicates_median", "rank_within_condition"], [
        {"pert_id": "BRD-EXACT", "drug_name": "Drug A", "cell_id": "MCF7", "pert_type": "trt_cp", "dose": "1 uM", "time": "24 h", "n_signatures": 2, "WTCS_median": -0.4, "rank_within_condition": 1},
        {"pert_id": "BRD-EXACT", "drug_name": "Drug A", "cell_id": "MCF7", "pert_type": "trt_cp", "dose": "10 uM", "time": "24 h", "n_signatures": 1, "WTCS_median": 0.2, "rank_within_condition": 2},
        {"pert_id": "BRD-NAME-ONLY", "drug_name": "Drug A", "cell_id": "MCF7", "pert_type": "trt_cp", "dose": "1 uM", "time": "24 h", "n_signatures": 1, "WTCS_median": -0.8, "rank_within_condition": 1},
    ])
    pert_info = root / "pert_info.tsv.gz"
    pert_rows = [
        {"pert_id": "BRD-EXACT", "canonical_smiles": "C", "inchi_key": "INCHI-A", "pert_iname": "Drug A", "pert_type": "trt_cp"},
        {"pert_id": "BRD-NAME-ONLY", "canonical_smiles": "", "inchi_key": "", "pert_iname": "Drug A", "pert_type": "trt_cp"},
    ]
    with gzip.open(pert_info, "wt", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(pert_rows[0]), delimiter="\t")
        writer.writeheader(); writer.writerows(pert_rows)
    config = {"project_id": "test-project", "project_slug": "test-project", "project_name": "软件验证项目", "disease_id": "MONDO:0000001", "analysis_run_id": "ANALYSIS_RUN:KG_BUNDLE:run-1", "s1_analysis_run_id": "ANALYSIS_RUN:S1:run-1", "s2_analysis_run_id": "ANALYSIS_RUN:S2:run-1", "enrichment_analysis_run_id": "ANALYSIS_RUN:S1_ENRICHMENT:run-1", "test_only": True, "s1_fdr_threshold": 0.05, "s1_table": str(s1), "s1_mapping_audit": str(mapping), "s2_conditions": str(conditions), "pert_info_path": str(pert_info), "enrichment_dir": str(enrichment), "public_kg_dir": str(public), "output_dir": str(root / "bundle")}

    manifest = build_bundle(config)
    nodes = {row["id"]: row for row in read_rows(root / "bundle" / "subgraph_nodes.csv")}
    edges = read_rows(root / "bundle" / "subgraph_edges.csv")
    mapping_rows = read_rows(root / "bundle" / "candidate_mapping_audit.csv")
    routes = read_rows(root / "bundle" / "candidate_target_pathway_routes.csv")

    assert manifest["status"] == "validated" and manifest["test_only"] is True
    assert {"python", "duckdb", "polars", "pyarrow", "biocypher"}.issubset(manifest["software_versions"])
    assert "kg/pyproject.toml" in manifest["input_hashes"] and "kg/uv.lock" in manifest["input_hashes"]
    assert manifest["counts"]["s2_condition_rows"] == 3
    assert manifest["counts"]["exact_inchikey_mapped_drugs"] == 1
    assert len([node for node in nodes.values() if node["type"] == "S2Condition"]) == 3
    assert nodes["CHEMBLTEST1"]["type"] == "Drug"
    assert nodes["GO:0000001"]["type"] == "Pathway"
    assert "test pathway" not in nodes  # description is a label, never a stable node ID
    assert [row["mapping_status"] for row in mapping_rows if row["pert_id"] == "BRD-NAME-ONLY"] == ["unmatched_no_exact_inchikey"]
    assert not [edge for edge in edges if edge["from"].endswith("BRD-NAME-ONLY") and edge["label"] == "PROJECT-REFERENCES_DRUG"]
    assert routes and routes[0]["pert_id"] == "BRD-EXACT"
    assert len(read_rows(root / "bundle" / "relation_conflicts.csv")) == 1
    assert json.loads(nodes[next(key for key in nodes if key.startswith("CANDIDATE:"))]["properties_json"])["condition_count"] == 2

    # Missing all gene crosswalks must fail closed instead of producing a
    # superficially validated bundle with no pathway-gene relationships.
    bad_enrichment = root / "enrichment-without-ensembl"
    bad_enrichment.mkdir()
    for filename in ["go_up.csv", "go_down.csv", "reactome_up.csv", "reactome_down.csv", "hallmark_gsea.csv"]:
        shutil.copy2(enrichment / filename, bad_enrichment / filename)
    write_rows(
        bad_enrichment / "pathway_gene_links.csv",
        ["analysis", "pathway_id", "pathway", "adjusted_p", "ENTREZID", "gene_symbol"],
        [{"analysis": "GO_UP", "pathway_id": "GO:0000001", "pathway": "test pathway", "adjusted_p": 0.01, "ENTREZID": "999999", "gene_symbol": "UNKNOWN"}],
    )
    with pytest.raises(ValueError, match="没有任何一条唯一映射到 Ensembl"):
        build_bundle({**config, "enrichment_dir": str(bad_enrichment), "output_dir": str(root / "bundle-no-pathway-map")})

    # Phase E architecture check: another disease gets isolated project/run
    # nodes while its public Drug/Gene/Pathway nodes keep the same stable IDs.
    first_bundle_hash = hashlib.sha256((root / "bundle" / "subgraph_nodes.csv").read_bytes()).hexdigest()
    second_config = {**config, "project_id": "test-lung-project", "project_slug": "test-lung-project", "project_name": "肺癌测试项目", "disease_id": "MONDO:0008903", "analysis_run_id": "ANALYSIS_RUN:KG_BUNDLE:run-lung", "s1_analysis_run_id": "ANALYSIS_RUN:S1:run-lung", "s2_analysis_run_id": "ANALYSIS_RUN:S2:run-lung", "enrichment_analysis_run_id": "ANALYSIS_RUN:S1_ENRICHMENT:run-lung", "output_dir": str(root / "bundle-lung")}
    second_manifest = build_bundle(second_config)
    second_rows = read_rows(root / "bundle-lung" / "subgraph_nodes.csv")
    second_nodes = {row["id"]: row for row in second_rows}
    assert second_manifest["status"] == "validated" and second_manifest["test_only"] is True
    assert "CHEMBLTEST1" in second_nodes and "ENSG00000000001" in second_nodes and "GO:0000001" in second_nodes
    assert second_nodes["CHEMBLTEST1"]["type"] == "Drug" and second_nodes["ENSG00000000001"]["type"] == "Gene"
    second_project_nodes = {key: row for key, row in second_nodes.items() if key.startswith(("CANDIDATE:test-lung-project", "DISEASE_CONTEXT:test-lung-project", "S2_CONDITION:test-lung-project"))}
    assert len(second_project_nodes) == 6  # two candidates, one context and three conditions
    assert not any(key.startswith(("CANDIDATE:test-project", "DISEASE_CONTEXT:test-project", "S2_CONDITION:test-project")) for key in second_nodes)
    second_context = next(row for row in second_rows if row["type"] == "DiseaseContext")
    second_context_props = json.loads(second_context["properties_json"])
    assert second_context_props["disease_id"] == "MONDO:0008903"
    assert second_context_props["s1_analysis_run_id"] == "ANALYSIS_RUN:S1:run-lung"
    second_edges = read_rows(root / "bundle-lung" / "subgraph_edges.csv")
    s2_edges = [row for row in second_edges if row["label"] in {"PROJECT-HAS_CANDIDATE", "PROJECT-REFERENCES_DRUG", "PROJECT-HAS_S2_CONDITION"}]
    assert s2_edges and all(json.loads(row["properties_json"]).get("analysis_run_id") == "ANALYSIS_RUN:S2:run-lung" for row in s2_edges)

    # Rebuilding an identical run in a fresh version directory is deterministic
    # and does not overwrite the first version's materialized artifacts.
    repeat_config = {**config, "output_dir": str(root / "bundle-repeat")}
    repeat_manifest = build_bundle(repeat_config)
    assert repeat_manifest["output_hashes"] == manifest["output_hashes"]
    assert hashlib.sha256((root / "bundle" / "subgraph_nodes.csv").read_bytes()).hexdigest() == first_bundle_hash
