"""Exercise KG06->KG07 rule-template API on five real coverage patterns."""
from __future__ import annotations

import hashlib
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT_ID = "3f18f4c1-713d-58c5-8a53-38eca5a5aaf9"
GRAPH_BUILD_ID = "GRAPH_BUILD:3f18f4c1-713d-58c5-8a53-38eca5a5aaf9:a08001496a447f7f"
BASE_URL = os.environ.get("KG06_BASE_URL", "http://127.0.0.1:8000")
PACKAGE_DIR = ROOT / "experiments" / "kg06_mechanism_evidence" / "results" / "evidence_packages_v2"
OUT = ROOT / "experiments" / "kg07_mechanism_interpretation" / "rule_pilot"
PILOT_IDS = ["BRD-K44227013", "BRD-K13390322", "BRD-K28822270", "BRD-K79090631", "BRD-A00147595"]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for pert_id in PILOT_IDS:
        package_path = PACKAGE_DIR / f"{pert_id}.json"
        package = json.loads(package_path.read_text(encoding="utf-8"))
        url = f"{BASE_URL}/api/v1/projects/{PROJECT_ID}/kg07/interpret/{pert_id}?mode=kg_rule&graph_build_id={GRAPH_BUILD_ID}"
        request = urllib.request.Request(url, data=b"", headers={"Content-Length": "0"}, method="POST")
        with urllib.request.urlopen(request, timeout=120) as response:
            if response.status != 200:
                raise RuntimeError(f"KG07 rule API returned HTTP {response.status} for {pert_id}")
            result = json.load(response)
        if result.get("project_id") != PROJECT_ID or result.get("graph_build_id") != GRAPH_BUILD_ID or result.get("candidate", {}).get("candidate_id") != package.get("candidate", {}).get("candidate_id"):
            raise RuntimeError(f"project/build/candidate mismatch for {pert_id}")
        file_path = OUT / f"{pert_id}.json"
        file_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        claims = [claim for section in ("screening_basis", "known_targets", "associated_pathways") for claim in result["explanation"].get(section, [])]
        package_path_ids = {path["path_id"] for path in package.get("paths", [])}
        package_eids = {eid for path in package.get("paths", []) for eid in path.get("evidence_ids", [])} | {eid for condition in package.get("screening_evidence", {}).get("s2_conditions", []) for eid in condition.get("evidence_ids", [])}
        all_refs_match = all(set(claim.get("path_ids", [])) <= package_path_ids and set(claim.get("evidence_ids", [])) <= package_eids for claim in claims)
        if not all_refs_match:
            raise RuntimeError(f"claim citation does not match package for {pert_id}")
        results.append({"pert_id": pert_id, "drug_name": result["candidate"].get("drug_name"), "http_status": 200, "path_count": len(package.get("paths", [])), "s2_condition_count": len(package.get("screening_evidence", {}).get("s2_conditions", [])), "target_claims": len(result["explanation"].get("known_targets", [])), "pathway_claims": len(result["explanation"].get("associated_pathways", [])), "screening_claims": len(result["explanation"].get("screening_basis", [])), "citation_reference_validation_pass": result.get("citation_reference_validation_pass"), "all_refs_match_package": all_refs_match, "evidence_gaps": result.get("evidence_gaps", []), "input_sha256": package.get("provenance", {}).get("evidence_input_sha256"), "output_sha256": hashlib.sha256(file_path.read_bytes()).hexdigest()})
    manifest = {"status": "PASS" if len(results) == len(PILOT_IDS) and all(row["citation_reference_validation_pass"] and row["all_refs_match_package"] for row in results) else "FAIL", "created_at_utc": datetime.now(timezone.utc).isoformat(), "project_id": PROJECT_ID, "graph_build_id": GRAPH_BUILD_ID, "n_candidates": len(results), "model_calls": 0, "external_data_sent": False, "cases": results}
    (OUT / "rule_pilot_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    report = ["# KG06 → KG07 真实候选规则模板 Pilot", "", f"状态：**{manifest['status']}**。本轮只调用本机 API，不调用外部 LLM；候选 {len(results)} 个。", "", "| 扰动 ID | 药物 | 路径数 | S2 条件数 | 靶点结论 | 通路结论 | 引用核验 |", "|---|---|---:|---:|---:|---:|---|"]
    report.extend(f"| {r['pert_id']} | {r['drug_name']} | {r['path_count']} | {r['s2_condition_count']} | {r['target_claims']} | {r['pathway_claims']} | {'PASS' if r['citation_reference_validation_pass'] and r['all_refs_match_package'] else 'FAIL'} |" for r in results)
    report.extend(["", "引用 ID/Path ID 与该候选对应 EvidencePackage 逐项核对；该检查不判断句子是否被证据语义支持。所有输出均要求人工生物学审核。无路径候选的机制解释保持为空/证据不足。", ""])
    (OUT / "rule_pilot_report.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "n_candidates": len(results), "citation_reference_validation_pass": sum(bool(row["citation_reference_validation_pass"]) for row in results)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
