import json

from app.kg07 import _retained_citations_verified, _validate_claims, interpret, rule_template


def test_invalid_citations_are_removed_and_claim_dropped():
    data = {"known_targets": [{"text": "claimed target", "evidence_ids": ["fake"], "path_ids": ["bad"]}], "associated_pathways": [{"text": "real path", "evidence_ids": ["e1"], "path_ids": ["p1"]}]}
    result, issues = _validate_claims(data, {"e1"}, {"p1"})
    assert result["known_targets"] == []
    assert result["associated_pathways"][0]["evidence_ids"] == ["e1"]
    assert result["associated_pathways"][0]["path_ids"] == ["p1"]
    assert len(issues) == 2


def test_retained_citation_status_is_separate_from_dropped_model_claims():
    explanation = {
        "known_targets": [{"text": "supported", "evidence_ids": ["e1"], "path_ids": ["p1"]}],
        "insufficient_evidence": [{"text": "coverage gap", "evidence_ids": [], "path_ids": [], "citation_reference_status": "verified_coverage_gap_from_EvidencePackage"}],
    }
    assert _retained_citations_verified(explanation, {"e1"}, {"p1"}, "kg_llm")
    assert not _retained_citations_verified({"known_targets": [{"text": "uncited", "evidence_ids": [], "path_ids": []}]}, {"e1"}, {"p1"}, "kg_llm")
    assert not _retained_citations_verified(explanation, {"other"}, {"p1"}, "kg_llm")
    assert not _retained_citations_verified(explanation, {"e1"}, {"p1"}, "direct_llm")


def test_causal_claim_is_downgraded_and_direction_must_match_path():
    data = {"known_targets": [{"text": "drug causes tumor regression", "relation": "causal", "evidence_ids": ["e1"], "path_ids": ["p1"]}, {"text": "drug inhibits target", "relation": "inhibition", "evidence_ids": ["e1"], "path_ids": ["p2"]}]}
    result, issues = _validate_claims(data, {"e1"}, {"p1", "p2"}, allowed_path_relations={"p1": "association", "p2": "association"})
    claims = result["known_targets"]
    assert claims[0]["relation"] == "association" and "未验证" in claims[0]["text"]
    assert claims[1]["relation"] == "association" and "来源未确认" in claims[1]["text"]
    assert len(issues) == 2


def test_kg07_rejects_cross_section_citations_and_unbound_target_genes():
    package = {
        "paths": [
            {"path_id": "target-path", "route_type": "direct_target", "target_gene_id": "ENSG1", "evidence_ids": ["target-evidence"], "nodes": [{"id": "ENSG1", "type": "Gene", "label": "ABL1"}], "edges": []},
            {"path_id": "pathway-path", "route_type": "s1_enrichment_overlap", "target_gene_id": "ENSG1", "pathway_id": "HALLMARK-X", "evidence_ids": ["pathway-evidence"], "nodes": [{"id": "ENSG1", "type": "Gene", "label": "ABL1"}], "edges": []},
        ],
        "screening_evidence": {"s2_conditions": [{"evidence_ids": ["s2-evidence"]}]},
    }
    raw = {
        "screening_basis": [{"text": "不当引用图谱路径", "evidence_ids": ["target-evidence"], "path_ids": ["target-path"]}],
        "known_targets": [
            {"text": "CDK1 是该药物的直接靶点", "evidence_ids": ["target-evidence"], "path_ids": ["target-path"], "relation": "association", "genes": [{"gene_id": "ENSG1", "symbol": "ABL1"}]},
            {"text": "ABL1 有直接靶点注释", "evidence_ids": ["target-evidence"], "path_ids": ["target-path"], "relation": "association", "genes": [{"gene_id": "ENSG1", "symbol": "ABL1"}]},
        ],
        "associated_pathways": [{"text": "靶点有关联", "evidence_ids": ["target-evidence"], "path_ids": ["target-path"]}],
        "independent_validation": [{"text": "已独立验证", "evidence_ids": ["s2-evidence"], "path_ids": []}],
    }

    clean, issues = _validate_claims(raw, {"target-evidence", "pathway-evidence", "s2-evidence"}, {"target-path", "pathway-path"}, package=package)

    assert clean["screening_basis"] == []
    assert len(clean["known_targets"]) == 1
    assert clean["known_targets"][0]["genes"] == [{"gene_id": "ENSG1", "symbol": "ABL1"}]
    assert clean["associated_pathways"] == []
    assert clean["independent_validation"] == []
    assert len(issues) == 4


def test_rule_template_reports_unknown_direction_as_association():
    package = {"candidate": {"pert_id": "BRD-X"}, "project_id": "proj", "graph_build_id": "build", "provenance": {"evidence_input_sha256": "abc"}, "screening_evidence": {"s2_candidate": {"condition_count": 1}}, "paths": [{"path_id": "p1", "route_type": "direct_target", "target_gene_id": "ENSG1", "evidence_ids": ["e1"], "edges": [{"reported_actions": []}]}], "evidence_gaps": []}
    output = rule_template(package)
    assert output["explanation"]["known_targets"][0]["relation"] == "association"
    assert output["explanation"]["known_targets"][0]["path_ids"] == ["p1"]


def test_kg_interpretation_requires_configured_key(monkeypatch, tmp_path):
    from app import kg07

    monkeypatch.setattr(kg07.settings, "zhipu_api_key", "")
    monkeypatch.delenv("ZHIPU_API_KEY", raising=False)
    monkeypatch.setattr(kg07, "CACHE_DIR", tmp_path)
    package = {"candidate": {}, "project_id": "p", "graph_build_id": "b", "provenance": {"evidence_input_sha256": "x"}, "screening_evidence": {}, "paths": []}
    try:
        interpret(package)
    except RuntimeError as error:
        assert "not configured" in str(error)
    else:
        raise AssertionError("expected missing-key configuration failure")


def test_kg_interpretation_caches_and_validates_mocked_provider(monkeypatch, tmp_path):
    from app import kg07

    monkeypatch.setattr(kg07.settings, "zhipu_api_key", "test-only-never-sent")
    monkeypatch.setattr(kg07, "CACHE_DIR", tmp_path)
    calls = []

    def fake_provider(messages, *, max_tokens=1200):
        calls.append(messages)
        return ({"model": "test-model", "choices": [{"message": {"content": '{"known_targets":[{"text":"supported","evidence_ids":["e1"],"path_ids":["p1"]},{"text":"unsupported","evidence_ids":["bad"],"path_ids":[]}],"limitations":[]}'}}], "usage": {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20}}, 0.01)

    monkeypatch.setattr(kg07, "_post_chat", fake_provider)
    package = {
        "candidate": {"pert_id": "BRD-X"}, "project_id": "project", "graph_build_id": "build",
        "provenance": {"evidence_input_sha256": "input-hash"}, "screening_evidence": {},
        "paths": [{"path_id": "p1", "route_type": "direct_target", "evidence_ids": ["e1"], "edges": []}],
        "v4_ranking_context": {"mechanism_rank": 1, "rank_v4": 3, "context_sha256": "v4-context-a"},
    }
    result = kg07.interpret(package)
    cached = kg07.interpret(package)
    assert result["citation_validation_pass"] is False
    assert len(result["explanation"]["known_targets"]) == 1
    assert result["citation_validation_issues"]
    assert cached["cached"] is True
    assert len(calls) == 1
    payload = json.loads(calls[0][1]["content"])
    assert payload["v4_ranking_context"]["rank_v4"] == 3

    changed_context = {**package, "v4_ranking_context": {"mechanism_rank": 1, "rank_v4": 4, "context_sha256": "v4-context-b"}}
    regenerated = kg07.interpret(changed_context)
    assert regenerated["cached"] is False
    assert regenerated["v4_ranking_context"]["rank_v4"] == 4
    assert len(calls) == 2
