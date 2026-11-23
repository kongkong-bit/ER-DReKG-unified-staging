"""Project-scoped ingestion of already computed differential-expression tables."""
from __future__ import annotations

import csv
import math
import re
from pathlib import Path


ALIASES = {
    "gene_id": {"gene", "gene_symbol", "genesymbol", "symbol", "geneid", "gene_id", "entrez", "entrez_id", "ensembl", "ensembl_id"},
    "logFC": {"logfc", "log2fc", "log_fold_change", "logfoldchange"},
    "adj.P.Val": {"adjpval", "adj.p.val", "padj", "fdr", "adjustedpvalue", "adjusted_p_value"},
    "t": {"t", "tstat", "t_stat", "tstatistic", "t_statistic"},
    "P.Value": {"pvalue", "p.value", "p_value", "pval"},
}


def _key(value: str) -> str:
    return re.sub(r"[^a-z0-9.]", "", value.strip().lower())


def _number(raw: str | None, row_number: int, column: str, *, allow_missing: bool = False) -> float | None:
    if raw is None or not raw.strip() or raw.strip().lower() in {"na", "nan", "null"}:
        if allow_missing:
            return None
        raise ValueError(f"第 {row_number} 行的 {column} 为空")
    try:
        value = float(raw)
    except ValueError as error:
        raise ValueError(f"第 {row_number} 行的 {column} 不是数值") from error
    if not math.isfinite(value):
        raise ValueError(f"第 {row_number} 行的 {column} 不是有限数值")
    return value


def standardize_precomputed_deg(
    source: Path,
    destination: Path,
    *,
    positive_group: str,
    negative_group: str,
    fdr_threshold: float = 0.05,
) -> dict:
    """Write a canonical per-project table and return an audit summary.

    Duplicate identifiers retain the row with lowest adjusted p value, then
    largest absolute logFC. Original row number and source fields are retained.
    """
    if not positive_group.strip() or not negative_group.strip() or positive_group.strip() == negative_group.strip():
        raise ValueError("比较组必须是两个不同的非空名称")
    if not math.isfinite(fdr_threshold) or not 0 < fdr_threshold <= 1:
        raise ValueError("FDR 阈值必须在 (0, 1] 范围内")
    delimiter = "\t" if source.suffix.lower() == ".tsv" else ","
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        original_headers = reader.fieldnames or []
        normalized = {_key(name): name for name in original_headers}
        indexes: dict[str, str] = {}
        for canonical, aliases in ALIASES.items():
            found = next((normalized[_key(alias)] for alias in aliases if _key(alias) in normalized), None)
            if found:
                indexes[canonical] = found
        missing = [field for field in ("gene_id", "logFC", "adj.P.Val", "t") if field not in indexes]
        if missing:
            raise ValueError("差异表缺少必需字段：" + ", ".join(missing))
        rows_by_id: dict[str, dict] = {}
        input_rows = duplicate_rows = 0
        for line_number, raw in enumerate(reader, start=2):
            if not raw or all(value is None or not value.strip() for value in raw.values()):
                continue
            input_rows += 1
            identifier = (raw.get(indexes["gene_id"]) or "").strip()
            if not identifier:
                raise ValueError(f"第 {line_number} 行的基因标识为空")
            log_fc = _number(raw.get(indexes["logFC"]), line_number, indexes["logFC"])
            adjusted_p = _number(raw.get(indexes["adj.P.Val"]), line_number, indexes["adj.P.Val"])
            statistic = _number(raw.get(indexes["t"]), line_number, indexes["t"])
            p_value = _number(raw.get(indexes["P.Value"]), line_number, indexes["P.Value"], allow_missing=True) if "P.Value" in indexes else None
            if not 0 <= adjusted_p <= 1:
                raise ValueError(f"第 {line_number} 行的调整后 P 值不在 [0, 1] 范围")
            candidate = {
                "gene_id": identifier,
                "logFC": log_fc,
                "adj.P.Val": adjusted_p,
                "t": statistic,
                "P.Value": p_value,
                "source_row": line_number,
                "direction": "up" if log_fc > 0 else "down" if log_fc < 0 else "unchanged",
            }
            previous = rows_by_id.get(identifier.casefold())
            if previous is not None:
                duplicate_rows += 1
                if (adjusted_p, -abs(log_fc), line_number) >= (previous["adj.P.Val"], -abs(previous["logFC"]), previous["source_row"]):
                    continue
            rows_by_id[identifier.casefold()] = candidate
    rows = sorted(rows_by_id.values(), key=lambda row: (row["adj.P.Val"], -abs(row["logFC"]), row["gene_id"].casefold()))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["gene_id", "logFC", "adj.P.Val", "t", "P.Value", "source_row", "direction"])
        writer.writeheader()
        writer.writerows(rows)
    significant = [row for row in rows if row["adj.P.Val"] < fdr_threshold]
    return {
        "input_rows": input_rows,
        "unique_genes": len(rows),
        "duplicate_rows_removed": duplicate_rows,
        "significant_genes": len(significant),
        "up": sum(row["direction"] == "up" and row["adj.P.Val"] < fdr_threshold for row in rows),
        "down": sum(row["direction"] == "down" and row["adj.P.Val"] < fdr_threshold for row in rows),
        "unchanged_significant": sum(row["direction"] == "unchanged" and row["adj.P.Val"] < fdr_threshold for row in rows),
        "fdr_threshold": fdr_threshold,
        "contrast": f"{positive_group.strip()} - {negative_group.strip()}",
        "positive_group": positive_group.strip(),
        "negative_group": negative_group.strip(),
        "gene_identifier_column": indexes["gene_id"],
        "source_columns": original_headers,
        "duplicate_policy": "retain lowest adj.P.Val; ties retain largest absolute logFC; final ties retain first input row",
    }
