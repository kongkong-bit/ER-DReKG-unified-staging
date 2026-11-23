import pytest

from smoke import wtcs as legacy_wtcs
from scoring import wtcs


def test_reversal_is_negative():
    genes = ["d1", "d2", "x", "y", "u1", "u2"]
    weights = dict(zip(genes, [6, 5, 0.1, -0.1, -5, -6]))
    es_up, es_down, score = wtcs(genes, weights, {"u1", "u2"}, {"d1", "d2"})
    assert es_up < 0 and es_down > 0 and score < 0


def test_same_direction_is_positive():
    genes = ["u1", "u2", "x", "y", "d1", "d2"]
    weights = dict(zip(genes, [6, 5, 0.1, -0.1, -5, -6]))
    es_up, es_down, score = wtcs(genes, weights, {"u1", "u2"}, {"d1", "d2"})
    assert es_up > 0 and es_down < 0 and score > 0


def test_same_sign_es_returns_zero():
    genes = ["u1", "d1", "u2", "d2", "x", "y"]
    weights = dict(zip(genes, [6, 5, 4, 3, 0.1, -6]))
    assert wtcs(genes, weights, {"u1", "u2"}, {"d1", "d2"})[2] == 0


def test_overlap_rejected():
    with pytest.raises(ValueError, match="overlap"):
        wtcs(["a", "b"], {"a": 1, "b": -1}, {"a"}, {"a"})


def test_repeatable_and_missing_query_gene_is_ignored():
    args = (["a", "b", "c"], {"a": 3, "b": -3, "c": 0.1}, {"a", "missing"}, {"b"})
    assert wtcs(*args) == wtcs(*args)


def test_reference_values_and_rank_orientation():
    # Hand-checkable weighted-KS fixture: both hits at one end give ES +/-1.
    ranked = ["u1", "u2", "x1", "x2", "d1", "d2"]
    weights = dict(zip(ranked, [6.0, 4.0, 2.0, -2.0, -4.0, -6.0]))
    assert wtcs(ranked, weights, {"u1", "u2"}, {"d1", "d2"}) == (1.0, -1.0, 1.0)
    reverse = list(reversed(ranked))
    reverse_weights = {gene: weights[gene] for gene in reverse}
    assert wtcs(reverse, reverse_weights, {"u1", "u2"}, {"d1", "d2"}) == (-1.0, 1.0, -1.0)


def test_project_scoring_matches_existing_smoke_implementation():
    ranked = ["u1", "u2", "x", "d1", "d2"]
    weights = dict(zip(ranked, [5.0, 3.0, 0.2, -3.0, -5.0]))
    up, down = {"u1", "u2"}, {"d1", "d2"}
    assert wtcs(ranked, weights, up, down) == legacy_wtcs(ranked, weights, up, down)
