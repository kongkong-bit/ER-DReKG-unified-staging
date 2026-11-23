import csv
import json
from functools import lru_cache
from pathlib import Path


PATHWAY_DIR = Path(__file__).resolve().parents[2] / "experiments" / "s1_pathway_enrichment"
COLLECTIONS = {"go_up", "go_down", "reactome_up", "reactome_down", "hallmark_gsea"}


@lru_cache(maxsize=5)
def _read_collection(collection: str) -> tuple[dict, ...]:
    if collection not in COLLECTIONS:
        raise ValueError("unknown pathway collection")
    path = PATHWAY_DIR / f"{collection}.csv"
    if not path.is_file():
        return ()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        for key in ("p.adjust", "padj", "adjusted_p", "NES", "Count"):
            if row.get(key) not in (None, "", "NA"):
                try:
                    row[key] = int(row[key]) if key == "Count" else float(row[key])
                except ValueError:
                    row[key] = None
    return tuple(rows)


def pathway_items(collection: str, limit: int = 20, offset: int = 0, significant_only: bool = True, result_dir: Path | None = None) -> dict:
    if collection not in COLLECTIONS:
        raise ValueError("unknown pathway collection")
    if result_dir is None:
        rows = list(_read_collection(collection))
    else:
        path = result_dir / f"{collection}.csv"
        if not path.is_file():
            rows = []
        else:
            with path.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            for row in rows:
                for key in ("p.adjust", "padj", "adjusted_p", "NES", "Count"):
                    if row.get(key) not in (None, "", "NA"):
                        try:
                            row[key] = int(row[key]) if key == "Count" else float(row[key])
                        except ValueError:
                            row[key] = None
    if significant_only:
        if collection == "hallmark_gsea":
            rows = [r for r in rows if isinstance(r.get("padj"), (float, int)) and r["padj"] < 0.05]
        else:
            rows = [r for r in rows if str(r.get("significant", "")).lower() == "true" or (isinstance(r.get("p.adjust"), (float, int)) and r["p.adjust"] < 0.05)]
    p_key = "padj" if collection == "hallmark_gsea" else "p.adjust"
    rows.sort(key=lambda r: (r.get(p_key) is None, r.get(p_key) or 1.0, str(r.get("ID", r.get("pathway", "")))))
    return {"collection": collection, "total": len(rows), "offset": offset, "limit": limit, "items": rows[offset:offset + limit]}


def pathway_summary() -> dict:
    manifest_path = PATHWAY_DIR / "environment_manifest.json"
    required = [PATHWAY_DIR / f"{name}.csv" for name in COLLECTIONS]
    if not manifest_path.is_file() or not all(path.is_file() for path in required):
        return {"available": False, "counts": {}}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {
        "available": True,
        "counts": {
            "go_up": int(manifest["GO_UP_sig"]),
            "go_down": int(manifest["GO_DOWN_sig"]),
            "reactome_up": int(manifest["Reactome_UP_sig"]),
            "reactome_down": int(manifest["Reactome_DOWN_sig"]),
            "hallmark_gsea": int(manifest["Hallmark_sig"]),
        },
        "mapped_universe": int(manifest["mapped_entrez_universe"]),
        "input_sha256": manifest.get("input_sha256"),
    }
