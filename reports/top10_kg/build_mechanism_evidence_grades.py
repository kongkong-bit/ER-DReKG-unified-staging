"""Build a hash-pinned, human-curated mechanism evidence grade table for frozen Top 10."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports" / "top10_kg"
EVIDENCE = ROOT / "data" / "top10_kg" / "evidence"
FROZEN_PATH = REPORTS / "02_top10_frozen_manifest.json"
GRADE_PATH = REPORTS / "mechanism_evidence_grade.csv"
MANIFEST_PATH = REPORTS / "mechanism_evidence_grade_manifest.json"

# Grades synthesize candidate target evidence and the reviewed disease-context record.
# They are manual assessments; they are never inferred from relation counts.
ASSESSMENTS = {
    "BRD-K44227013": ("A", "OptimusKG source-supported kinase target assertions intersect the FGFR1-amplified ER-positive breast model reported for ponatinib.", "ER-positive cell/model evidence only; no clinical efficacy claim or proof that the frozen LINCS condition engaged FGFR1."),
    "BRD-K16485616": ("A", "ChEMBL reports direct HDAC1/2/3/8/11 inhibitory mechanisms with linked PMID records; reviewed work reports ER-positive endocrine-resistant models and PDX.", "Preclinical and combination-context evidence; not a clinical indication or efficacy estimate."),
    "BRD-K56405753": ("B", "ChEMBL reports direct MET inhibition and primary studies support MET pharmacology; disease-context review found target biology but no ER-positive-specific result.", "Target pharmacology is stronger than the disease-context link; do not infer ER-positive therapeutic benefit."),
    "BRD-K92093830": ("A", "Established breast-cancer pharmacology and source-supported TOP2A target evidence are accompanied by ER-positive cell-model studies.", "Doxorubicin is an existing breast-cancer treatment, not a newly discovered therapy; reviewed estrogen-response evidence is mixed and does not establish the frozen dose mechanism."),
    "BRD-K76694128": ("B", "ChEMBL reports a direct ABL inhibitory mechanism and a phase Ib study provides breast-cancer clinical pharmacodynamic context.", "The study included mixed HER2-negative subtypes; it does not establish ER-positive-specific efficacy."),
    "BRD-K50000283": ("B", "External primary-source claims support CDC7/CDK9 inhibitor pharmacology and target assertions; breast-cancer evidence exists in TNBC models.", "Subtype differs from the ER-positive project; this is not evidence of ER-positive efficacy or a validated ER-positive path."),
    "BRD-K11153516": ("C", "PARP1 association and historical PARP-related claims are counterbalanced by mechanism-revision literature and a phase III trial that missed prespecified coprimary endpoints.", "Do not label iniparib a validated PARP inhibitor; the negative/mixed clinical context does not itself prove absence of every possible mechanism."),
    "BRD-A00147595": ("B", "ChEMBL reports a direct PPAR-gamma partial-agonist mechanism and the graph contains S1 pathway intersections.", "Focused search found no compound-specific ER-positive breast-cancer study; S1 intersections are statistical context, not drug-pathway causal evidence."),
    "BRD-K13094524": ("B", "SGC/IUPHAR source records support exact PFI-1 identity and BET bromodomain probe pharmacology; BRD2/BRD4 target claims are source-linked.", "Available primary context is not ER-positive breast cancer; biochemical binding does not establish target engagement at the frozen dose."),
    "BRD-K83837640": ("B", "ChEMBL reports an HDAC inhibitory mechanism and primary sources support pan-HDAC pharmacology with non-subtype preclinical tumor context.", "No ER-positive-specific efficacy evidence in the focused review; broad target pharmacology is not a treatment-effect claim."),
}

GRADE_DEFINITIONS = {
    "A": "较强机制证据：可信药理机制或直接实验支持，且存在相关疾病背景研究；仍须限定模型、条件和研究设计。",
    "B": "部分机制证据：有来源支持的药物靶点/药理证据，但疾病或通路连接不完整。",
    "C": "间接/争议机制线索：主要依据关联、亚型外推、计算或存在重要机制争议，缺少适用于本疾病背景的直接验证。",
    "U": "暂无足够证据建立可信机制解释。",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    frozen_manifest = json.loads(FROZEN_PATH.read_text(encoding="utf-8"))
    source_path = ROOT / frozen_manifest["source_file"]
    if sha256(source_path) != frozen_manifest["source_sha256"]:
        raise SystemExit("Frozen Top 10 source SHA mismatch")
    disease_manifest = json.loads((REPORTS / "external_disease_evidence_manifest.json").read_text(encoding="utf-8"))
    disease_path = ROOT / disease_manifest["source_file"]
    if sha256(disease_path) != disease_manifest["source_sha256"]:
        raise SystemExit("Disease evidence source SHA mismatch")
    source_manifest_path = EVIDENCE / "top10_source_evidence_manifest.json"
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    mechanism_path = EVIDENCE / "chembl_mechanisms.csv"
    mechanism_manifest_key = next((key for key in source_manifest["outputs_sha256"] if Path(key).name == mechanism_path.name), None)
    if not mechanism_manifest_key or sha256(mechanism_path) != source_manifest["outputs_sha256"][mechanism_manifest_key]:
        raise SystemExit("ChEMBL mechanism source SHA mismatch")
    target_report = REPORTS / "03_drug_target_report.md"
    bundle_manifest = REPORTS / "top10_graph_bundle" / "3928c54d_external_v1" / "bundle_manifest.json"
    external_claims = REPORTS / "external_identity_and_mechanism_evidence.csv"
    for path in (target_report, bundle_manifest, external_claims):
        if not path.is_file():
            raise SystemExit(f"Required evidence input missing: {path}")

    frozen = json.loads(FROZEN_PATH.read_text(encoding="utf-8"))
    disease_rows = {row["pert_id"]: row for row in read_csv(disease_path)}
    mechanisms: dict[str, list[dict[str, str]]] = {}
    for row in read_csv(mechanism_path):
        mechanisms.setdefault(row["pert_id"], []).append(row)
    external_claim_rows = read_csv(external_claims)
    fields = ["rank", "pert_id", "drug_name", "grade", "grade_label", "grade_rationale", "target_evidence_basis", "target_evidence_ids", "target_source_records", "target_source_urls", "disease_evidence_scope", "disease_evidence_summary", "disease_source_id", "disease_source_url", "limitations", "mechanism_source_refs", "assessment_type"]
    output: list[dict[str, str]] = []
    for item in frozen["items"]:
        pert_id = item["pert_id"]
        if pert_id not in ASSESSMENTS or pert_id not in disease_rows:
            raise SystemExit(f"Missing manual assessment or disease evidence for {pert_id}")
        grade, rationale, limits = ASSESSMENTS[pert_id]
        disease = disease_rows[pert_id]
        source_refs: list[str] = []
        for mechanism in mechanisms.get(pert_id, []):
            try:
                refs = json.loads(mechanism.get("mechanism_refs", "[]"))
            except json.JSONDecodeError:
                refs = []
            source_refs.extend(str(ref.get("ref_id")) for ref in refs if ref.get("ref_id"))
        dossier_candidates = sorted((REPORTS / "drugs").glob(f"{int(item['rank']):02d}_*.md"))
        if len(dossier_candidates) != 1:
            raise SystemExit(f"Expected exactly one dossier for rank {item['rank']}")
        dossier_text = dossier_candidates[0].read_text(encoding="utf-8")
        target_ids = re.findall(r"Evidence `([^`]+)`", dossier_text)
        target_records = re.findall(r"source record `([^`]+)`", dossier_text)
        candidate_claims = [row for row in external_claim_rows if row.get("pert_id") == pert_id and row.get("external_target_claim")]
        target_sources = [row.get("evidence_source", "") for row in candidate_claims]
        target_urls = [row.get("evidence_url", "") for row in candidate_claims]
        output.append({
            "rank": str(item["rank"]),
            "pert_id": pert_id,
            "drug_name": item["pert_iname"],
            "grade": grade,
            "grade_label": {"A": "较强", "B": "部分", "C": "间接/争议", "U": "证据不足"}[grade],
            "grade_rationale": rationale,
            "target_evidence_basis": "审阅 03_drug_target_report.md、冻结 bundle 与 external identity/mechanism claims；未按关系条数打分。",
            "target_evidence_ids": "; ".join(dict.fromkeys(target_ids)),
            "target_source_records": "; ".join(dict.fromkeys([*target_records, *target_sources])),
            "target_source_urls": "; ".join(dict.fromkeys(url for url in target_urls if url)),
            "disease_evidence_scope": disease["evidence_scope"],
            "disease_evidence_summary": disease["curated_finding"],
            "disease_source_id": disease["source_id"],
            "disease_source_url": disease["source_url"],
            "limitations": f"{limits} 定向检索不是系统综述；等级描述机制证据，不表示疗效概率。原始疾病记录限制：{disease['limitations']}",
            "mechanism_source_refs": "; ".join(dict.fromkeys(source_refs)),
            "assessment_type": "human_curated_focused_review_v1",
        })
    if len(output) != 10 or {row["pert_id"] for row in output} != {item["pert_id"] for item in frozen["items"]}:
        raise SystemExit("Grade table does not exactly cover frozen Top 10")
    with GRADE_PATH.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)
    inputs = {
        "02_top10_frozen_manifest.json": sha256(FROZEN_PATH),
        "formal_top10_source": frozen_manifest["source_sha256"],
        "external_disease_evidence_manifest.json": sha256(REPORTS / "external_disease_evidence_manifest.json"),
        "external_disease_evidence.csv": sha256(disease_path),
        "top10_source_evidence_manifest.json": sha256(source_manifest_path),
        "chembl_mechanisms.csv": sha256(mechanism_path),
        "03_drug_target_report.md": sha256(target_report),
        "parent_external_bundle_manifest.json": sha256(bundle_manifest),
        "external_identity_and_mechanism_evidence.csv": sha256(external_claims),
        "drug_dossiers_sha256": {path.name: sha256(path) for path in sorted((REPORTS / "drugs").glob("*.md"))},
    }
    manifest = {
        "manifest_version": 1,
        "status": "human_curated_focused_review",
        "assessment_date": "2026-11-21",
        "assessment_type": "human_curated_focused_review_v1",
        "grade_definitions": GRADE_DEFINITIONS,
        "grading_policy": "Manual synthesis of source-supported drug pharmacology/target and disease-context evidence. Relation counts are not used. A grade is not efficacy probability. Focused search is not a systematic review.",
        "source_file": "reports/top10_kg/mechanism_evidence_grade.csv",
        "source_sha256": sha256(GRADE_PATH),
        "frozen_top10_sha256": frozen_manifest["source_sha256"],
        "record_count": len(output),
        "grade_counts": {grade: sum(row["grade"] == grade for row in output) for grade in ("A", "B", "C", "U")},
        "input_sha256": inputs,
        "limitations": ["Provisional focused evidence assessment; systematic review not performed.", "Do not interpret as treatment efficacy or probability.", "Disease evidence scope and contradictory context remain visible per candidate."],
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(GRADE_PATH), "sha256": manifest["source_sha256"], "grade_counts": manifest["grade_counts"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
