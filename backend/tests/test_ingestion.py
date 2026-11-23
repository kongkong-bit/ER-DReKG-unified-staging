import hashlib

import pytest

from app.ingestion import copy_stream_and_hash, inspect_expression_file


def test_precomputed_deg_table_checks_required_limma_columns(tmp_path):
    path = tmp_path / "deg.csv"
    path.write_text("gene_symbol,logFC,adj.P.Val,t\nESR1,1.2,0.001,4.5\n", encoding="utf-8")
    result = inspect_expression_file(path, "precomputed_deg")
    assert result["row_count"] == 1
    assert result["column_count"] == 4
    assert result["numeric_cell_count"] == 3
    assert result["sample_annotation_required"] is False


def test_expression_and_sample_metadata_require_group_ready_shapes(tmp_path):
    expression = tmp_path / "matrix.csv"
    expression.write_text("gene_symbol,T1,N1\nESR1,4.2,3.8\n", encoding="utf-8")
    expression_result = inspect_expression_file(expression, "expression_matrix")
    assert expression_result["sample_count"] == 2
    assert expression_result["numeric_cell_count"] == 2

    expression.write_text("gene_symbol,T1,T1\nESR1,4.2,3.8\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate sample columns"):
        inspect_expression_file(expression, "expression_matrix")

    path = tmp_path / "bad_fdr.csv"
    path.write_text("gene_symbol,logFC,adj.P.Val,t\nESR1,1.2,1.5,4.5\n", encoding="utf-8")
    with pytest.raises(ValueError, match="FDR outside"):
        inspect_expression_file(path, "precomputed_deg")

    metadata = tmp_path / "samples.tsv"
    metadata.write_text("sample_id\tgroup\nT1\tTumor\nN1\tNormal\n", encoding="utf-8")
    assert inspect_expression_file(metadata, "sample_metadata")["group_count"] == 2

    metadata.write_text("sample_id\tgroup\nT1\tTumor\nN1\tTumor\n", encoding="utf-8")
    with pytest.raises(ValueError, match="two distinct groups"):
        inspect_expression_file(metadata, "sample_metadata")


def test_upload_stream_helper_hashes_and_enforces_size_limit(tmp_path):
    path = tmp_path / "upload.csv"
    payload = b"a,b\n1,2\n"
    size, digest = copy_stream_and_hash([payload[:3], payload[3:]], path, max_bytes=100)
    assert size == len(payload)
    assert digest == hashlib.sha256(payload).hexdigest()
    with pytest.raises(ValueError, match="exceeds configured limit"):
        copy_stream_and_hash([payload], tmp_path / "too-large.csv", max_bytes=2)
    assert not (tmp_path / "too-large.csv").exists()


def test_invalid_encoding_and_duplicate_sample_ids_are_rejected(tmp_path):
    invalid = tmp_path / "invalid.csv"
    invalid.write_bytes(b"gene,\xff\n")
    with pytest.raises(ValueError, match="valid UTF-8"):
        inspect_expression_file(invalid, "expression_matrix")

    metadata = tmp_path / "duplicate.csv"
    metadata.write_text("sample_id,group\nS1,Tumor\nS1,Normal\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate sample ID"):
        inspect_expression_file(metadata, "sample_metadata")
