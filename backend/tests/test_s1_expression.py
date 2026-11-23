import csv
import json
from pathlib import Path

import pytest

from app.s1_expression import limma_runtime, run_limma_microarray, run_rnaseq_edger_voom


def test_limma_microarray_smoke_uses_explicit_contrast_and_writes_auditable_table(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[2]
    try:
        limma_runtime(repo_root)
    except RuntimeError as error:
        pytest.skip(str(error))

    expression = tmp_path / "matrix.csv"
    samples = tmp_path / "samples.csv"
    output = tmp_path / "limma_all_genes.csv"
    expression.write_text(
        "gene_id,S1,S2,S3,S4\nG1,1.0,1.1,3.0,3.1\nG2,2.0,2.1,1.0,1.2\nG3,1.5,1.4,1.6,1.5\n",
        encoding="utf-8",
    )
    samples.write_text(
        "sample_id,group\nS1,Normal\nS2,Normal\nS3,Tumor\nS4,Tumor\n",
        encoding="utf-8",
    )

    summary = run_limma_microarray(repo_root, expression, samples, output, "Tumor", "Normal", "symbol", 0.05)
    with output.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    table = {row["gene_id"]: row for row in rows}

    assert summary["contrast"] == "Tumor - Normal"
    assert summary["tested_features"] == 3
    assert summary["up"] == 1 and summary["down"] == 1
    assert float(table["G1"]["logFC"]) > 0
    assert float(table["G2"]["logFC"]) < 0
    assert {"gene_symbol", "logFC", "t", "P.Value", "adj.P.Val"}.issubset(table["G1"])
    assert json.loads(Path(str(output) + ".summary.json").read_text(encoding="utf-8"))["limma"] == summary["limma"]


def test_limma_microarray_rejects_sample_id_mismatch(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[2]
    try:
        limma_runtime(repo_root)
    except RuntimeError as error:
        pytest.skip(str(error))
    expression = tmp_path / "matrix.csv"
    samples = tmp_path / "samples.csv"
    expression.write_text("gene_id,S1,S2,S3,S4\nG1,1,1.1,3,3.1\n", encoding="utf-8")
    samples.write_text("sample_id,group\nX1,Normal\nS2,Normal\nS3,Tumor\nS4,Tumor\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="样本注释和表达矩阵样本不一致"):
        run_limma_microarray(repo_root, expression, samples, tmp_path / "out.csv", "Tumor", "Normal", "symbol", 0.05)


def test_rnaseq_edger_voom_filters_normalizes_and_preserves_contrast(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[2]
    try:
        limma_runtime(repo_root, ("limma", "edgeR"))
    except RuntimeError as error:
        pytest.skip(str(error))
    expression = tmp_path / "counts.csv"
    samples = tmp_path / "samples.csv"
    output = tmp_path / "rnaseq_limma_all_genes.csv"
    sample_ids = ["N1", "N2", "N3", "T1", "T2", "T3"]
    with expression.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["gene_id", *sample_ids])
        writer.writerow(["UP", 10, 11, 9, 400, 420, 380])
        writer.writerow(["DOWN", 500, 520, 480, 20, 22, 18])
        for index in range(178):
            baseline = 80 + index % 30
            writer.writerow([f"G{index:03d}", baseline, baseline + 2, baseline - 2, baseline + 1, baseline - 1, baseline + 3])
        for index in range(20):
            writer.writerow([f"LOW{index:03d}", 0, 0, 0, 0, 0, 0])
    samples.write_text(
        "sample_id,group\nN1,Normal\nN2,Normal\nN3,Normal\nT1,Tumor\nT2,Tumor\nT3,Tumor\n",
        encoding="utf-8",
    )

    summary = run_rnaseq_edger_voom(repo_root, expression, samples, output, "Tumor", "Normal", "symbol", 0.05)
    with output.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    table = {row["gene_id"]: row for row in rows}

    assert summary["contrast"] == "Tumor - Normal"
    assert summary["input_features"] == 200
    assert summary["tested_features"] > 0 and summary["filtered_features"] > 0
    assert "TMM normalization" in summary["method"]
    assert float(table["UP"]["logFC"]) > 0
    assert float(table["DOWN"]["logFC"]) < 0
    assert summary["edgeR"] == "4.4.2"


def test_rnaseq_edger_voom_rejects_normalized_fractional_values(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[2]
    try:
        limma_runtime(repo_root, ("limma", "edgeR"))
    except RuntimeError as error:
        pytest.skip(str(error))
    counts = tmp_path / "normalized.csv"
    samples = tmp_path / "samples.csv"
    counts.write_text("gene_id,N1,N2,T1,T2\nG1,0.5,1.5,2.5,3.5\nG2,2.5,3.5,0.5,1.5\n", encoding="utf-8")
    samples.write_text("sample_id,group\nN1,Normal\nN2,Normal\nT1,Tumor\nT2,Tumor\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="原始整数 read counts"):
        run_rnaseq_edger_voom(repo_root, counts, samples, tmp_path / "out.csv", "Tumor", "Normal", "symbol", 0.05)

