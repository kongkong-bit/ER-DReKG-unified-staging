import csv
import hashlib
import math
from pathlib import Path

import anyio


PRECOMPUTED_COLUMNS = {
    "gene": {"gene", "gene_symbol", "genesymbol", "symbol", "geneid", "gene_id"},
    "logfc": {"logfc"},
    "fdr": {"adjpval", "adj.p.val", "padj", "fdr", "adjustedpvalue"},
    "t": {"t", "tstat", "tstatistic"},
}


class UploadHasher:
    def __init__(self, max_bytes: int):
        self.max_bytes = max_bytes
        self.total = 0
        self.digest = hashlib.sha256()

    def update(self, chunk: bytes) -> None:
        self.total += len(chunk)
        if self.total > self.max_bytes:
            raise ValueError(f"upload exceeds configured limit of {self.max_bytes} bytes")
        self.digest.update(chunk)

    def finish(self) -> tuple[int, str]:
        if self.total == 0:
            raise ValueError("uploaded file is empty")
        return self.total, self.digest.hexdigest()


def inspect_expression_file(path: Path, dataset_type: str) -> dict:
    try:
        return _inspect_expression_file(path, dataset_type)
    except (UnicodeDecodeError, csv.Error) as error:
        raise ValueError("file must be a valid UTF-8 CSV/TSV table") from error


def _inspect_expression_file(path: Path, dataset_type: str) -> dict:
    if dataset_type not in {"expression_matrix", "precomputed_deg", "sample_metadata"}:
        raise ValueError("unsupported dataset_type")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        first_line = handle.readline()
        if not first_line:
            raise ValueError("uploaded file is empty")
        delimiter = "\t" if path.suffix.lower() == ".tsv" or first_line.count("\t") > first_line.count(",") else ","
        handle.seek(0)
        reader = csv.reader(handle, delimiter=delimiter)
        header = next(reader, [])
        normalized = [column.strip().lower().replace(" ", "") for column in header]
        if len(header) < 2 or any(not column.strip() for column in header):
            raise ValueError("the header must contain at least two named columns")
        if dataset_type == "precomputed_deg":
            missing = [key for key, aliases in PRECOMPUTED_COLUMNS.items() if not any(name in aliases for name in normalized)]
            if missing:
                raise ValueError("precomputed DEG table is missing required columns: " + ", ".join(missing))
            column_indices = {key: next(i for i, name in enumerate(normalized) if name in aliases) for key, aliases in PRECOMPUTED_COLUMNS.items()}
            numeric_columns = [column_indices[key] for key in ("logfc", "fdr", "t")]
            gene_column = column_indices["gene"]
        elif len(header) < 3:
            if dataset_type == "expression_matrix":
                raise ValueError("an expression matrix needs a gene identifier column and at least two samples")
        if dataset_type == "expression_matrix":
            sample_names = [name.casefold() for name in header[1:]]
            if len(sample_names) != len(set(sample_names)):
                raise ValueError("expression matrix contains duplicate sample columns")
            gene_column = 0
            numeric_columns = list(range(1, len(header)))
        elif dataset_type == "sample_metadata":
            gene_column = None
            numeric_columns = []
        if dataset_type == "sample_metadata":
            sample_column = next((i for i, name in enumerate(normalized) if name in {"sample", "sampleid", "sample_id", "geo_accession", "gsm"}), None)
            group_column = next((i for i, name in enumerate(normalized) if name in {"group", "condition", "tissue", "phenotype"}), None)
            if sample_column is None or group_column is None:
                raise ValueError("sample metadata must include sample_id and group/condition columns")
        else:
            sample_column = group_column = None

        row_count = 0
        numeric_cell_count = 0
        missing_numeric_count = 0
        groups = set()
        sample_ids = set()
        for row in reader:
            if not row or all(not value.strip() for value in row):
                continue
            if len(row) != len(header):
                raise ValueError(f"row {row_count + 2} has {len(row)} fields; expected {len(header)}")
            if gene_column is not None and not row[gene_column].strip():
                raise ValueError(f"row {row_count + 2} has a blank gene identifier")
            for column_index in numeric_columns:
                value = row[column_index].strip()
                if value.lower() in {"", "na", "nan", "null"}:
                    missing_numeric_count += 1
                    continue
                try:
                    number = float(value)
                except ValueError as error:
                    raise ValueError(f"row {row_count + 2}, column {header[column_index]} is not numeric") from error
                if not math.isfinite(number):
                    raise ValueError(f"row {row_count + 2}, column {header[column_index]} is not finite")
                if dataset_type == "precomputed_deg" and column_index == column_indices["fdr"] and not 0 <= number <= 1:
                    raise ValueError(f"row {row_count + 2} has an FDR outside [0, 1]")
                numeric_cell_count += 1
            if sample_column is not None and group_column is not None:
                sample_id = row[sample_column].strip()
                group = row[group_column].strip()
                if not sample_id or not group:
                    raise ValueError(f"sample metadata row {row_count + 2} has a blank sample ID or group")
                if sample_id in sample_ids:
                    raise ValueError(f"duplicate sample ID: {sample_id}")
                sample_ids.add(sample_id)
                groups.add(group)
            row_count += 1
        if row_count == 0:
            raise ValueError("the file contains a header but no data rows")
        if dataset_type == "sample_metadata" and len(groups) < 2:
            raise ValueError("sample metadata must describe at least two distinct groups")
    return {
        "detected_format": "tsv" if delimiter == "\t" else "csv",
        "header": header,
        "column_count": len(header),
        "row_count": row_count,
        "numeric_cell_count": numeric_cell_count,
        "missing_numeric_count": missing_numeric_count,
        "dataset_type": dataset_type,
        "sample_count": len(header) - 1 if dataset_type == "expression_matrix" else row_count if dataset_type == "sample_metadata" else None,
        "group_count": len(groups) if dataset_type == "sample_metadata" else None,
        "sample_annotation_required": dataset_type == "expression_matrix",
    }


def copy_stream_and_hash(chunks, output_path: Path, max_bytes: int) -> tuple[int, str]:
    hasher = UploadHasher(max_bytes)
    try:
        with output_path.open("wb") as output:
            for chunk in chunks:
                if not chunk:
                    continue
                hasher.update(chunk)
                output.write(chunk)
        return hasher.finish()
    except Exception:
        output_path.unlink(missing_ok=True)
        raise


async def write_request_stream(request, output_path: Path, max_bytes: int) -> tuple[int, str]:
    hasher = UploadHasher(max_bytes)
    try:
        async with await anyio.open_file(output_path, "wb") as output:
            async for chunk in request.stream():
                if not chunk:
                    continue
                hasher.update(chunk)
                await output.write(chunk)
        return hasher.finish()
    except Exception:
        output_path.unlink(missing_ok=True)
        raise
