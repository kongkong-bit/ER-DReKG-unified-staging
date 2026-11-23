import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "s2_lincs"))

from exp007_core import weighted_es_from_hits, wtcs_from_rank_positions  # noqa: E402
from smoke import weighted_es as historical_weighted_es, wtcs as historical_wtcs  # noqa: E402


def test_weighted_es_matches_historical_implementation_for_reference_case():
    ranked = ["u1", "u2", "x1", "x2", "d1", "d2"]
    values = np.array([6.0, 4.0, 2.0, -2.0, -4.0, -6.0])
    fast = weighted_es_from_hits([0, 1], [6, 4], len(ranked))
    assert fast == pytest.approx(historical_weighted_es(ranked, dict(zip(ranked, values)), {"u1", "u2"}))
    assert fast == pytest.approx(1.0)


def test_wtcs_reference_orientation_and_exact_extremes():
    # Gene index order is the input vector order; rank_position gives its ranked position.
    rank_position = np.arange(6, dtype=np.int32)
    values = np.array([6.0, 4.0, 2.0, -2.0, -4.0, -6.0])
    up = np.array([0, 1]); down = np.array([4, 5])
    assert wtcs_from_rank_positions(rank_position, values, up, down) == pytest.approx((1.0, -1.0, 1.0))
    reverse = rank_position[::-1].copy()
    assert wtcs_from_rank_positions(reverse, values, up, down) == pytest.approx((-1.0, 1.0, -1.0))


def test_wtcs_matches_historical_implementation_for_seeded_rankings():
    rng = np.random.default_rng(42)
    genes = [f"g{i}" for i in range(250)]
    up = set(genes[:35]); down = set(genes[70:105])
    values = rng.normal(size=len(genes))
    order = np.lexsort((np.asarray(genes), -values))
    ranked = [genes[i] for i in order]
    ranked_values = values[order]
    rank_position = np.empty(len(genes), dtype=np.int32); rank_position[order] = np.arange(len(genes))
    indices = {g:i for i,g in enumerate(genes)}
    fast = wtcs_from_rank_positions(rank_position, values, np.array([indices[g] for g in up]), np.array([indices[g] for g in down]))
    slow = historical_wtcs(ranked, dict(zip(ranked, ranked_values)), up, down)
    assert fast == pytest.approx(slow, abs=1e-12)


def test_empty_or_full_query_gene_set_is_nan_and_overlap_is_rejected():
    assert np.isnan(weighted_es_from_hits([], [], 6))
    assert np.isnan(weighted_es_from_hits(range(6), np.ones(6), 6))
    with pytest.raises(ValueError, match="overlap"):
        wtcs_from_rank_positions(np.arange(6), np.ones(6), np.array([0, 1]), np.array([1, 2]))

