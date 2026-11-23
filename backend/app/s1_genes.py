import csv
import math
from functools import lru_cache
from pathlib import Path


RESULTS_PATH = Path(__file__).resolve().parents[2] / "s1_初步_gse42568_limma" / "limma_all_genes.csv"


def _number(value: str | None) -> float | None:
    if value in (None, "", "NA", "NaN", "Inf", "-Inf"):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if result == result and abs(result) != float("inf") else None


@lru_cache(maxsize=1)
def _read_rows(path: Path = RESULTS_PATH) -> tuple[dict, ...]:
    if not path.is_file():
        raise FileNotFoundError(f"S1 limma result not found: {path.name}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        symbol_column = "gene_symbol" if "gene_symbol" in fields else "gene_id"
        required = {symbol_column, "logFC", "t", "adj.P.Val"}
        if not required.issubset(fields):
            raise ValueError(f"S1 limma table is missing required columns: {sorted(required - fields)}")
        rows = []
        for raw in reader:
            symbol = (raw.get(symbol_column) or "").strip()
            if not symbol:
                symbol = (raw.get("gene_id") or "").strip()
            log_fc = _number(raw.get("logFC"))
            statistic = _number(raw.get("t"))
            adjusted_p = _number(raw.get("adj.P.Val"))
            p_value = _number(raw.get("P.Value"))
            if not symbol or log_fc is None or statistic is None or adjusted_p is None:
                continue
            rows.append({
                "gene_symbol": symbol,
                "gene_id": (raw.get("gene_id") or symbol).strip(),
                "logFC": log_fc,
                "t": statistic,
                "P.Value": p_value,
                "adj.P.Val": adjusted_p,
                "direction": "up" if log_fc > 0 else "down" if log_fc < 0 else "unchanged",
            })
    return tuple(rows)


def volcano_points(path: Path = RESULTS_PATH, fdr_threshold: float = 0.05) -> dict:
    rows = _read_rows(path)
    points = [
        {
            "gene_symbol": row["gene_symbol"],
            "logFC": row["logFC"],
            "adj.P.Val": row["adj.P.Val"],
            "minus_log10_fdr": -math.log10(max(row["adj.P.Val"], 1e-300)),
            "direction": row["direction"] if row["adj.P.Val"] < fdr_threshold else "not_significant",
        }
        for row in rows
    ]
    return {"total": len(points), "fdr_threshold": fdr_threshold, "points": points}


def gene_items(direction: str = "all", limit: int = 50, offset: int = 0, significant_only: bool = True, path: Path = RESULTS_PATH, fdr_threshold: float = 0.05) -> dict:
    if direction not in {"all", "up", "down"}:
        raise ValueError("direction must be all, up, or down")
    rows = list(_read_rows(path))
    if significant_only:
        rows = [row for row in rows if row["adj.P.Val"] < fdr_threshold]
    if direction != "all":
        rows = [row for row in rows if row["direction"] == direction]
    rows.sort(key=lambda row: (row["adj.P.Val"], -abs(row["logFC"]), row["gene_symbol"].casefold()))
    return {"direction": direction, "significant_only": significant_only, "total": len(rows), "offset": offset, "limit": limit, "items": rows[offset:offset + limit]}
