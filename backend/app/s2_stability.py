from collections import defaultdict
from typing import Iterable, Mapping


def summarize_condition_stability(
    rows: Iterable[Mapping[str, object]], *, top_n: int = 10
) -> list[dict[str, object]]:
    """Describe rank recurrence across doses without combining WTCS scores."""
    if top_n < 1:
        raise ValueError("top_n must be positive")

    groups: dict[tuple[str, str, str, str], list[dict[str, object]]] = defaultdict(list)
    for source in rows:
        row = dict(source)
        pert_id = str(row.get("pert_id") or "").strip()
        if not pert_id:
            continue
        key = (
            str(row.get("cell_id") or ""),
            str(row.get("pert_type") or ""),
            str(row.get("time") or ""),
            pert_id,
        )
        try:
            rank = float(row.get("rank_within_condition"))
        except (TypeError, ValueError):
            continue
        row["_rank"] = rank
        groups[key].append(row)

    summaries = []
    for (cell_id, pert_type, time, pert_id), conditions in sorted(groups.items()):
        ranks = [float(row["_rank"]) for row in conditions]
        top_n_count = sum(rank <= top_n for rank in ranks)
        summaries.append({
            "pert_id": pert_id,
            "drug_name": str(conditions[0].get("drug_name") or pert_id),
            "cell_id": cell_id,
            "pert_type": pert_type,
            "time": time,
            "dose_count": len({str(row.get("dose") or "") for row in conditions}),
            "condition_count": len(conditions),
            "top_n": top_n,
            "top_n_condition_count": top_n_count,
            "top_n_condition_fraction": top_n_count / len(conditions),
            "best_condition_rank": min(ranks),
            "worst_condition_rank": max(ranks),
            "rank_range_across_conditions": max(ranks) - min(ranks),
            "interpretation": "跨剂量条件排名复现率；不合并 WTCS，不代表药效总排名",
        })
    return summaries
