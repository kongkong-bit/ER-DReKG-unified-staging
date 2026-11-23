from __future__ import annotations

from typing import Iterable

import numpy as np


def weighted_es_from_hits(positions: Iterable[int], abs_weights: Iterable[float], n_genes: int) -> float:
    """CMap weighted one-sided KS ES, evaluated at hit positions only."""
    pos = np.asarray(list(positions), dtype=np.int64)
    weights = np.asarray(list(abs_weights), dtype=np.float64)
    if pos.size == 0 or pos.size >= n_genes:
        return float("nan")
    order = np.argsort(pos, kind="stable")
    pos = pos[order]
    weights = np.abs(weights[order])
    total = float(weights.sum())
    if total <= 0:
        weights = np.ones_like(weights)
        total = float(weights.sum())
    hit_cum = np.cumsum(weights) / total
    miss_before = (pos - np.arange(pos.size)) / float(n_genes - pos.size)
    before = np.r_[0.0, hit_cum[:-1]] - miss_before
    after = hit_cum - miss_before
    maximum = max(0.0, float(after.max()))
    minimum = min(0.0, float(before.min()))
    return maximum if abs(maximum) >= abs(minimum) else minimum


def weighted_es(ranked_symbols: list[str], ranked_values: np.ndarray, query: set[str]) -> float:
    positions = [i for i, symbol in enumerate(ranked_symbols) if symbol in query]
    hit_weights = [abs(float(ranked_values[i])) for i in positions]
    return weighted_es_from_hits(positions, hit_weights, len(ranked_symbols))


def wtcs_from_rank_positions(
    rank_position: np.ndarray,
    values_by_gene: np.ndarray,
    up_gene_indices: np.ndarray,
    down_gene_indices: np.ndarray,
) -> tuple[float, float, float]:
    """WTCS from a per-signature BING rank map; query order is immaterial."""
    if set(up_gene_indices.tolist()) & set(down_gene_indices.tolist()):
        raise ValueError("UP and DOWN sets overlap")
    es_up = weighted_es_from_hits(rank_position[up_gene_indices], values_by_gene[up_gene_indices], len(rank_position))
    es_down = weighted_es_from_hits(rank_position[down_gene_indices], values_by_gene[down_gene_indices], len(rank_position))
    if not np.isfinite(es_up) or not np.isfinite(es_down):
        return es_up, es_down, float("nan")
    wtcs = 0.0 if np.sign(es_up) == np.sign(es_down) else (es_up - es_down) / 2.0
    return es_up, es_down, float(wtcs)


def condition_key_frame(frame):
    return frame["pert_id"].astype(str) + "|" + frame["cell_id"].astype(str) + "|" + frame["dose"].astype(str) + "|" + frame["time"].astype(str)

