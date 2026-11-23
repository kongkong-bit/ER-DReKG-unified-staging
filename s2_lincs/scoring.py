"""Shared CMap-style weighted connectivity score primitives."""
from __future__ import annotations

import numpy as np


def weighted_es(ranked: list[str], weights: dict[str, float], genes: set[str], p: float = 1.0) -> float:
    hits = [i for i, gene in enumerate(ranked) if gene in genes]
    if not hits or len(hits) == len(ranked):
        return float("nan")
    hit_weights = np.array([abs(weights[ranked[i]]) ** p for i in hits], dtype=float)
    if hit_weights.sum() == 0:
        hit_weights[:] = 1.0
    hit_weights /= hit_weights.sum()
    hit_map = dict(zip(hits, hit_weights))
    miss_step = 1.0 / (len(ranked) - len(hits))
    running = 0.0
    maximum = -np.inf
    minimum = np.inf
    for i in range(len(ranked)):
        running += hit_map[i] if i in hit_map else -miss_step
        maximum = max(maximum, running)
        minimum = min(minimum, running)
    return float(maximum if abs(maximum) >= abs(minimum) else minimum)


def wtcs(ranked: list[str], weights: dict[str, float], up: set[str], down: set[str]) -> tuple[float, float, float]:
    if up & down:
        raise ValueError("UP and DOWN sets overlap")
    es_up = weighted_es(ranked, weights, up)
    es_down = weighted_es(ranked, weights, down)
    if np.sign(es_up) == np.sign(es_down):
        score = 0.0
    else:
        score = (es_up - es_down) / 2.0
    return es_up, es_down, score
