import hashlib
import json

import pytest

from app import robust_v4


def _write_artifacts(directory, csv_text: str):
    csv_path = directory / "v4_mechanism_top10.csv"
    csv_path.write_text(csv_text, encoding="utf-8")
    manifest = {
        "status": "PASS",
        "protocol": "v4 protocol fixture",
        "spec_sha256": "protocol-hash",
        "outputs": {csv_path.name: hashlib.sha256(csv_path.read_bytes()).hexdigest()},
    }
    manifest_path = directory / "v4_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path, csv_path


def test_load_v4_mechanism_candidate_verifies_manifest_and_selects_allowlisted_fields(tmp_path, monkeypatch):
    manifest_path, csv_path = _write_artifacts(
        tmp_path,
        "pert_id,drug_name,rank_mech,rank_v4,S_disc,n_dose_conditions,WTCS_dose_median,WTCS_neg_frac,algorithm_consensus,stability_top20,n_chains,n_er_chains,chain_targets\n"
        "BRD-X,example drug,2,5,0.91,4,-0.42,0.75,True,0.8,3,1,CDK1; CDK9\n",
    )
    monkeypatch.setattr(robust_v4, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(robust_v4, "MECHANISM_TOP10_PATH", csv_path)

    candidate = robust_v4.load_mechanism_candidate("BRD-X")

    assert candidate["mechanism_rank"] == 2
    assert candidate["rank_v4"] == 5
    assert candidate["algorithm_consensus"] is True
    assert candidate["target_symbols"] == ["CDK1", "CDK9"]
    assert len(candidate["context_sha256"]) == 64
    assert robust_v4.load_mechanism_candidate("BRD-Y") is None


def test_load_v4_mechanism_candidate_rejects_hash_mismatch(tmp_path, monkeypatch):
    manifest_path, csv_path = _write_artifacts(
        tmp_path,
        "pert_id,drug_name,rank_mech,rank_v4,S_disc,n_dose_conditions,WTCS_dose_median,WTCS_neg_frac,algorithm_consensus,stability_top20,n_chains,n_er_chains,chain_targets\n"
        "BRD-X,example drug,2,5,0.91,4,-0.42,0.75,True,0.8,3,1,CDK1\n",
    )
    csv_path.write_text(csv_path.read_text(encoding="utf-8") + "BRD-Y,tampered\n", encoding="utf-8")
    monkeypatch.setattr(robust_v4, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(robust_v4, "MECHANISM_TOP10_PATH", csv_path)

    with pytest.raises(robust_v4.RobustV4ArtifactError, match="hash"):
        robust_v4.load_mechanism_candidate("BRD-X")
