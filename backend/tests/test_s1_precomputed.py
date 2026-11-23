import csv

import pytest

from app.s1_genes import gene_items, volcano_points
from app.s1_precomputed import standardize_precomputed_deg


def test_precomputed_deg_is_canonicalized_and_duplicate_is_audited(tmp_path):
    source = tmp_path / "deg.csv"
    source.write_text(
        "Gene Symbol,logFC,adj.P.Val,t,P.Value\n"
        "TP53,1.2,0.01,4.1,0.002\n"
        "TP53,1.8,0.01,4.8,0.001\n"
        "ESR1,-2.0,0.2,-3.2,0.04\n",
        encoding="utf-8",
    )
    destination = tmp_path / "canonical" / "limma_all_genes.csv"

    summary = standardize_precomputed_deg(source, destination, positive_group="Tumor", negative_group="Normal")

    assert summary["input_rows"] == 3
    assert summary["unique_genes"] == 2
    assert summary["duplicate_rows_removed"] == 1
    assert summary["significant_genes"] == summary["up"] == 1
    assert summary["down"] == 0
    assert summary["contrast"] == "Tumor - Normal"
    genes = gene_items("up", path=destination)
    assert genes["total"] == 1 and genes["items"][0]["gene_symbol"] == "TP53"
    assert genes["items"][0]["logFC"] == 1.8
    volcano = volcano_points(destination)
    assert volcano["total"] == 2 and volcano["points"][0]["direction"] == "up"


def test_precomputed_deg_rejects_invalid_fdr_and_ambiguous_contrast(tmp_path):
    source = tmp_path / "bad.tsv"
    source.write_text("symbol\tlogFC\tadj.P.Val\tt\nA\t1\t1.2\t2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="调整后 P 值"):
        standardize_precomputed_deg(source, tmp_path / "out.csv", positive_group="A", negative_group="B")
    with pytest.raises(ValueError, match="两个不同"):
        standardize_precomputed_deg(source, tmp_path / "out.csv", positive_group="A", negative_group="A")


def test_precomputed_deg_does_not_overwrite_result_on_validation_failure(tmp_path):
    source = tmp_path / "bad.csv"
    source.write_text("Gene,logFC,adj.P.Val,t\nA,not-number,0.01,3\n", encoding="utf-8")
    destination = tmp_path / "canonical.csv"
    with pytest.raises(ValueError, match="不是数值"):
        standardize_precomputed_deg(source, destination, positive_group="Case", negative_group="Control")
    assert not destination.exists()
