from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
FINAL = ROOT / "experiments" / "final_results"
RESULTS = FINAL / "results"
MECH = FINAL / "mechanism"
LINCS = ROOT / "s2_lincs" / "data"
OUT = FINAL / "final05_scientific_audit"
OUT_RESULTS = OUT / "results"
OUT_REPORTS = OUT / "reports"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def split_ids(value: object) -> list[str]:
    if pd.isna(value) or not str(value).strip():
        return []
    return [v for v in str(value).split("|") if v]


def main() -> None:
    OUT_RESULTS.mkdir(parents=True, exist_ok=True)
    OUT_REPORTS.mkdir(parents=True, exist_ok=True)

    top = pd.read_csv(RESULTS / "final_top10.csv")
    scores = pd.read_csv(RESULTS / "final_signature_scores.csv")
    summary = pd.read_csv(RESULTS / "final_drug_condition_summary.csv")
    sig_path = LINCS / "GSE70138_Broad_LINCS_sig_info_2017-03-06.txt.gz"
    met_path = LINCS / "GSE70138_Broad_LINCS_sig_metrics_2017-03-06.txt.gz"
    inst_path = LINCS / "GSE70138_Broad_LINCS_inst_info_2017-03-06.txt.gz"
    pert_path = LINCS / "GSE70138_Broad_LINCS_pert_info_2017-03-06.txt.gz"
    sig_info = pd.read_csv(sig_path, sep="\t", low_memory=False)
    metrics = pd.read_csv(met_path, sep="\t", low_memory=False).drop(columns=["Unnamed: 0"], errors="ignore")
    inst_info = pd.read_csv(inst_path, sep="\t", low_memory=False)
    pert_info = pd.read_csv(pert_path, sep="\t", low_memory=False)
    sig_info = sig_info.merge(metrics, on=["sig_id", "pert_id", "pert_type"], how="left", suffixes=("", "_metric"), validate="one_to_one")

    # Top10 are frozen. Validate the scored subset against all raw same-condition metadata,
    # including signatures excluded by QC before scoring.
    score_candidates = scores[scores.pert_id.isin(top.pert_id)].copy()
    current_primary = score_candidates[score_candidates.dose.astype(str).str.strip().eq("10.0 um") &
                                       score_candidates.time.astype(str).str.strip().eq("24 h")]
    primary_meta = sig_info[(sig_info.pert_id.isin(top.pert_id)) & (sig_info.cell_id == "MCF7") &
                            (sig_info.pert_type == "trt_cp") & (sig_info.pert_idose.astype(str).str.strip() == "10.0 um") &
                            (sig_info.pert_itime.astype(str).str.strip() == "24 h")].copy()
    primary = primary_meta.merge(current_primary[["sig_id", "pert_id", "WTCS", "reversal_score"]],
                                 on=["sig_id", "pert_id"], how="left", validate="one_to_one")
    inst_lookup = inst_info.set_index("inst_id", drop=False)

    primary_rows = []
    for _, row in top.sort_values("rank").iterrows():
        sigs = primary[primary.pert_id.eq(row.pert_id)]
        scored = sigs[sigs.WTCS.notna()]
        assert len(scored) == int(row.n_signatures), f"Scored primary count mismatch for {row.drug_name}"
        for _, sig in sigs.iterrows():
            iid = split_ids(sig.distil_id)
            resolved = [x for x in iid if x in inst_lookup.index]
            insts = inst_lookup.loc[resolved] if resolved else inst_info.iloc[0:0]
            primary_rows.append({
                "rank_frozen": int(row["rank"]), "drug_name": row.drug_name, "pert_id": row.pert_id,
                "sig_id": sig.sig_id, "cell_id": sig.cell_id, "pert_type": sig.pert_type,
                "dose": sig.pert_idose, "time": sig.pert_itime,
                "included_in_formal_scoring_after_QC": bool(pd.notna(sig.WTCS)),
                "QC_exclusion_reason": "" if pd.notna(sig.WTCS) else ("distil_cc_q75 < 0.2" if pd.notna(sig.distil_cc_q75) and sig.distil_cc_q75 < 0.2 else "not present in formal score input; see QC manifest"),
                "WTCS": float(sig.WTCS) if pd.notna(sig.WTCS) else np.nan,
                "reversal_score_project_convention": float(sig.reversal_score) if pd.notna(sig.reversal_score) else np.nan,
                "distil_cc_q75": sig.distil_cc_q75, "distil_ss": sig.distil_ss, "tas": sig.tas,
                "distil_nsample_reported": sig.distil_nsample,
                "distil_id_instance_count": len(iid), "inst_info_resolved_instance_count": len(resolved),
                "underlying_inst_ids": "|".join(iid),
                "underlying_det_plates": "|".join(sorted(set(insts.det_plate.dropna().astype(str)))) if len(insts) else "",
                "underlying_distinct_plate_count": int(insts.det_plate.nunique()) if len(insts) else 0,
                "level5_consensus_signature_count_in_raw_metadata": len(sigs),
                "formal_scored_consensus_signature_count_for_primary_condition": len(scored),
                "interpretation": "One Level 5 consensus signature; distil instances are underlying L1000 replicate profiles, not independent cohorts.",
            })
    sig_audit = pd.DataFrame(primary_rows)
    assert len(sig_audit) == 11 and sig_audit.sig_id.nunique() == 11
    sig_audit.to_csv(OUT_RESULTS / "signature_level_audit.csv", index=False)

    # Exact dose/time support from the existing fixed-method signature scoring run.
    dose_rows = []
    for _, tr in top.sort_values("rank").iterrows():
        d = score_candidates[(score_candidates.pert_id == tr.pert_id) & (score_candidates.time == "24 h")].copy()
        # Include the already-computed condition-level summaries, which preserve within-condition aggregation.
        sumd = summary[(summary.pert_id == tr.pert_id) & (summary.cell_id == "MCF7") &
                       (summary.pert_type == "trt_cp") & (summary.time == "24 h")]
        for _, c in sumd.iterrows():
            selected = d[d.dose == c.dose]
            dose_rows.append({
                "rank_frozen": int(tr["rank"]), "drug_name": tr.drug_name, "pert_id": tr.pert_id,
                "cell_id": c.cell_id, "pert_type": c.pert_type, "dose": c.dose, "time": c.time,
                "n_level5_consensus_signatures": int(c.n_signatures),
                "underlying_instance_replicates_total": int(selected.distil_nsample.fillna(0).sum()),
                "WTCS_median": float(c.WTCS_median), "WTCS_mean": float(c.WTCS_mean) if pd.notna(c.WTCS_mean) else np.nan,
                "CC_median": float(c.CC_median) if pd.notna(c.CC_median) else np.nan,
                "TAS_median": float(c.TAS_median) if pd.notna(c.TAS_median) else np.nan,
                "direction_negative": bool(c.WTCS_median < 0),
                "n_signatures_with_current_WTCS": int(len(selected)),
                "other_time_metadata_signatures_exist": int(((sig_info.pert_id == tr.pert_id) & (sig_info.cell_id == "MCF7") &
                    (sig_info.pert_type == "trt_cp") & (sig_info.pert_itime.astype(str) != "24 h")).sum()),
            })
    dose = pd.DataFrame(dose_rows)
    dose.to_csv(OUT_RESULTS / "dose_batch_support.csv", index=False)

    # Compare every raw Level 5 metadata row per dose with signatures passing formal score QC.
    raw24 = sig_info[(sig_info.pert_id.isin(top.pert_id)) & (sig_info.cell_id == "MCF7") &
                     (sig_info.pert_type == "trt_cp") & (sig_info.pert_itime.astype(str).str.strip() == "24 h")].copy()
    scored_ids = set(score_candidates.loc[score_candidates.time == "24 h", "sig_id"].astype(str))
    raw_dose_rows = []
    for (pert_id, dose_label), g in raw24.groupby(["pert_id", "pert_idose"], dropna=False):
        tr = top[top.pert_id.eq(pert_id)].iloc[0]
        ids = g.sig_id.astype(str).tolist()
        included = [x for x in ids if x in scored_ids]
        excluded = g[~g.sig_id.astype(str).isin(scored_ids)]
        all_iids = [iid for value in g.distil_id for iid in split_ids(value)]
        resolved_iids = [iid for iid in all_iids if iid in inst_lookup.index]
        insts = inst_lookup.loc[resolved_iids] if resolved_iids else inst_info.iloc[0:0]
        w = score_candidates[(score_candidates.pert_id == pert_id) & score_candidates.sig_id.isin(included)]
        raw_dose_rows.append({
            "rank_frozen": int(tr["rank"]), "drug_name": tr.drug_name, "pert_id": pert_id,
            "dose": dose_label, "time": "24 h", "raw_level5_metadata_signatures": len(ids),
            "formal_scored_signatures": len(included), "QC_excluded_signatures": len(excluded),
            "raw_instance_profiles_total": len(all_iids), "resolved_instance_profiles": len(resolved_iids),
            "raw_sig_ids": "|".join(ids), "formal_scored_sig_ids": "|".join(included),
            "excluded_sig_ids": "|".join(excluded.sig_id.astype(str)),
            "excluded_CC_q75": "|".join(excluded.distil_cc_q75.dropna().astype(str)),
            "underlying_distinct_det_plates": int(insts.det_plate.nunique()) if len(insts) else 0,
            "experiment_series": "|".join(sorted({str(x).split(":")[0].replace("_MCF7_24H", "") for x in ids})),
            "formal_WTCS_median": float(w.WTCS.median()) if len(w) else np.nan,
            "formal_WTCS_all_negative": bool((w.WTCS < 0).all()) if len(w) else None,
        })
    raw_dose_audit = pd.DataFrame(raw_dose_rows)
    raw_dose_audit.to_csv(OUT_RESULTS / "dose_metadata_qc_audit.csv", index=False)

    all_score_rows = score_candidates[score_candidates.time == "24 h"][["sig_id", "pert_id", "WTCS", "reversal_score"]]
    all_sig = raw24.merge(all_score_rows, on=["sig_id", "pert_id"], how="left", validate="one_to_one")
    all_signature_rows = []
    for _, sig in all_sig.iterrows():
        iids = split_ids(sig.distil_id)
        resolved = [x for x in iids if x in inst_lookup.index]
        insts = inst_lookup.loc[resolved] if resolved else inst_info.iloc[0:0]
        all_signature_rows.append({
            "drug_name": sig.pert_iname, "pert_id": sig.pert_id, "sig_id": sig.sig_id,
            "experiment_series": str(sig.sig_id).split(":")[0].replace("_MCF7_24H", ""),
            "cell_id": sig.cell_id, "pert_type": sig.pert_type, "dose": sig.pert_idose, "time": sig.pert_itime,
            "distil_cc_q75": sig.distil_cc_q75, "distil_ss": sig.distil_ss, "tas": sig.tas,
            "distil_nsample": sig.distil_nsample, "instance_ids": sig.distil_id,
            "instance_count_from_distil_id": len(iids), "resolved_instance_count_in_inst_info": len(resolved),
            "distinct_detection_plates": int(insts.det_plate.nunique()) if len(insts) else 0,
            "included_in_formal_scoring": bool(pd.notna(sig.WTCS)),
            "QC_exclusion_reason": "" if pd.notna(sig.WTCS) else ("distil_cc_q75 < 0.2" if pd.notna(sig.distil_cc_q75) and sig.distil_cc_q75 < 0.2 else "absent from formal score file"),
            "WTCS": float(sig.WTCS) if pd.notna(sig.WTCS) else np.nan,
            "reversal_score": float(sig.reversal_score) if pd.notna(sig.reversal_score) else np.nan,
        })
    all_signature_audit = pd.DataFrame(all_signature_rows)
    all_signature_audit.to_csv(OUT_RESULTS / "all_candidate_signature_audit.csv", index=False)

    # Metadata proves whether other exposure times were present, but their WTCS is not recalculated here.
    time_rows = []
    for _, tr in top.sort_values("rank").iterrows():
        all_sig = sig_info[(sig_info.pert_id == tr.pert_id) & (sig_info.cell_id == "MCF7") & (sig_info.pert_type == "trt_cp")]
        for tval, g in all_sig.groupby("pert_itime", dropna=False):
            time_rows.append({"rank_frozen": int(tr["rank"]), "drug_name": tr.drug_name, "pert_id": tr.pert_id,
                              "pert_itime": tval, "level5_consensus_signature_count": int(g.sig_id.nunique()),
                              "instance_replicates_total": int(g.distil_nsample.fillna(0).sum()),
                              "distinct_dose_conditions": int(g.pert_idose.nunique()),
                              "sig_ids": "|".join(g.sig_id.astype(str).tolist()),
                              "WTCS_recalculated_in_this_audit": False})
    timecov = pd.DataFrame(time_rows)
    timecov.to_csv(OUT_RESULTS / "time_metadata_coverage.csv", index=False)

    # Historical empirical p/FDR are surfaced only as historical statistics; compare their observed score.
    perm = pd.read_csv(ROOT / "experiments" / "exp008_scoring_statistics" / "results" / "empirical_pvalues.csv")
    perm = perm[(perm.scheme == "B200") & (perm.cell_id == "MCF7") & (perm.time == "24 h")]
    perm = perm[perm.pert_id.isin(top.pert_id)].copy()
    perm = perm.rename(columns={"observed_WTCS": "historical_B200_observed_WTCS", "empirical_pvalue": "historical_B200_empirical_pvalue", "adjusted_pvalue": "historical_B200_BH_FDR"})
    perm = perm.merge(dose[dose.dose.eq("10.0 um")][["pert_id", "WTCS_median"]].rename(columns={"WTCS_median":"current_final_WTCS_median"}), on="pert_id", how="left")
    perm["historical_vs_current_delta"] = perm.historical_B200_observed_WTCS - perm.current_final_WTCS_median
    perm["same_score_within_1e-6"] = perm.historical_vs_current_delta.abs().le(1e-6)
    perm["scope_note"] = "Exp008 historical 2,000-permutation B200 result; not recomputed against this corrected final run. Do not treat as definitive current-set significance when score mismatch is nonzero."
    perm.to_csv(OUT_RESULTS / "historical_permutation_crosswalk.csv", index=False)

    # Exact LINCS structure identifiers for the 5 compounds missing from the existing graph mapping.
    expected = {
        "BRD-K56405753": ("MK-2461", "JGEBLDKNWBUGRZ-HXUWFJFHSA-N", "44137946", "CHEMBL1802916", "https://pubchem.ncbi.nlm.nih.gov/summary/summary.cgi?cid=44137946"),
        "BRD-K76694128": ("rebastinib", "WVXNSAVVKYZVOE-UHFFFAOYSA-N", "25066467", "CHEMBL1738757", "https://pubchem.ncbi.nlm.nih.gov/compound/25066467"),
        "BRD-K50000283": ("PHA-767491", "DKXHSOUZPMHNIZ-UHFFFAOYSA-N", "11715767", "CHEMBL225519", "https://pubchem.ncbi.nlm.nih.gov/compound/11715767"),
        "BRD-K13094524": ("PFI-1", "TXZPMHLMPKIUGK-UHFFFAOYSA-N", "71271629", "CHEMBL2179387", "https://pubchem.ncbi.nlm.nih.gov/summary/summary.cgi?cid=71271629"),
        "BRD-K83837640": ("JNJ-26481585 / quisinostat", "PAWIYAYFNXQGAP-UHFFFAOYSA-N", "11538455", "CHEMBL2105763", "https://pubchem.ncbi.nlm.nih.gov/compound/11538455"),
    }
    graph_map = pd.read_csv(MECH / "final_neo4j_drug_mapping.csv")
    id_rows = []
    for pert, (name, inchikey, cid, chembl, url) in expected.items():
        pi = pert_info[pert_info.pert_id.eq(pert)]
        graph = graph_map[graph_map.pert_id.eq(pert)]
        lin_key = str(pi.iloc[0].inchi_key) if len(pi) else ""
        graph_status = str(graph.iloc[0].neo4j_mapping) if len(graph) else "not mapped"
        id_rows.append({"drug_name": name, "LINCS_pert_id": pert, "LINCS_pert_info_inchi_key": lin_key,
                        "external_PubChem_CID": cid, "external_ChEMBL_ID": chembl, "external_InChIKey": inchikey,
                        "exact_InChIKey_match": lin_key == inchikey, "existing_graph_mapping_status": graph_status,
                        "resolution": "Identity crosswalk independently resolved by exact structure key; current KG unchanged.",
                        "evidence_source_url": url, "LINCS_source_file": pert_path.name})
    id_audit = pd.DataFrame(id_rows)
    assert id_audit.exact_InChIKey_match.all()
    id_audit.to_csv(OUT_RESULTS / "unmapped_drug_identifier_audit.csv", index=False)

    # Candidate-level pharmacology/indication audit: sources are explicit and not interpreted as ER+ efficacy.
    mech = [
        ("ponatinib", "Multikinase inhibitor including BCR::ABL1", "FDA-approved for specified Ph+ ALL/CML settings; no breast cancer indication in cited label", "No approved breast cancer use", "Candidate breast cancer mechanism remains hypothetical; label carries serious vascular, cardiac and hepatic warnings", "https://www.accessdata.fda.gov/drugsatfda_docs/label/2025/203469s038lbl.pdf"),
        ("mocetinostat", "Class I HDAC1/2/3 inhibitor; exact antitumor mechanism not fully defined", "Investigational/clinical study agent; not an approved breast cancer treatment", "No approved breast cancer use", "Epigenetic mechanism is a hypothesis and was not validated in this ER-positive project", "https://www.cancer.gov/publications/dictionaries/cancer-drug/def/mocetinostat"),
        ("MK-2461", "Multikinase inhibitor with preference for activated/phosphorylated c-MET", "Investigational compound tested in first-in-human phase I advanced solid tumor studies; no approved breast cancer use", "No approved breast cancer use", "Requires evidence of MET dependence/activation; WTCS cannot establish target dependence", "https://ascopubs.org/doi/10.1200/jco.2008.26.15_suppl.14657; https://pubmed.ncbi.nlm.nih.gov/20145145/"),
        ("doxorubicin", "Anthracycline DNA intercalator / topoisomerase II inhibitor", "Used in adjuvant and metastatic breast cancer treatment", "Established breast cancer treatment; not a novel breast cancer repositioning discovery", "Expression reversal may reflect broad cytotoxic stress; ranking is not ER-positive-specific efficacy evidence", "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=36924f82-6c05-4989-9f41-a398c0ad48e6"),
        ("rebastinib", "Multikinase inhibitor (BCR-ABL, SRC family, TIE2, VEGFR2, among others)", "Investigational/development agent; no approved breast cancer indication", "No approved breast cancer use; preclinical breast cancer models do not establish clinical efficacy", "Angiogenesis/kinase mechanisms require target and model validation", "https://www.cancer.gov/publications/dictionaries/cancer-drug/def/rebastinib-tosylate"),
        ("PHA-767491", "CDC7 inhibitor with additional CDK9 inhibitory activity", "Research/preclinical compound; no approved breast cancer indication", "No approved breast cancer use", "Replication-initiation/transcription mechanism is biologically testable, but current S2 stability is weak", "https://pubmed.ncbi.nlm.nih.gov/21768328/"),
        ("iniparib", "Should not be interpreted as a bona fide PARP inhibitor; studies report little/no intact-cell PARP inhibition and possible nonspecific reactivity", "Developed and trialed under a PARP inhibitor premise; phase III metastatic TNBC trial did not meet coprimary PFS/OS endpoints", "No approved breast cancer use; prior TNBC clinical development is not approval or proof of efficacy", "If KG shows a PARP1-drug edge, it does not prove PARP inhibition; mark as mechanistically contradicted/uncertain", "https://pubmed.ncbi.nlm.nih.gov/22291137/; https://pubmed.ncbi.nlm.nih.gov/25349301/"),
        ("balaglitazone", "PPAR-gamma partial agonist", "Investigational glucose-lowering candidate studied in type 2 diabetes", "No approved breast cancer use", "PPAR-gamma/breast cancer relationship is a testable hypothesis, not validated here", "https://pubmed.ncbi.nlm.nih.gov/21328517/"),
        ("PFI-1", "Selective BET bromodomain chemical probe/inhibitor", "Research chemical probe; not an approved anticancer medicine", "No approved breast cancer use", "BET transcriptional regulation is a hypothesis; target engagement and cell dependence remain to be tested", "https://pubmed.ncbi.nlm.nih.gov/23576556/"),
        ("JNJ-26481585", "Pan-HDAC inhibitor (quisinostat)", "Investigational/clinical-study agent; PubChem summary lists lymphoma, MDS and other studies", "No approved breast cancer use", "HDAC inhibition and expression reversal do not establish an ER-positive-specific mechanism", "https://pubchem.ncbi.nlm.nih.gov/compound/11538455"),
    ]
    known = pd.DataFrame(mech, columns=["drug_name", "known_mechanism_or_class", "clinical_status_or_indication", "breast_cancer_context", "audit_caveat", "source_url"])
    known = top[["rank", "drug_name", "pert_id", "WTCS_median", "negative_dose_fraction"]].merge(known, on="drug_name", how="left", validate="one_to_one")
    known.to_csv(OUT_RESULTS / "drug_mechanism_indication_audit.csv", index=False)

    # Evidence dimensions are categorical; no composite probability is computed.
    prism = pd.read_csv(ROOT / "experiments" / "exp011_prism_validation" / "results" / "candidate_sensitivity_results.csv")
    prism_er = prism[prism.er_group.eq("ER-positive")][["pert_id", "erpos_mean_sensitivity", "erpos_median_sensitivity", "n_erpos_lines"]]
    graph_drugs = pd.read_csv(MECH / "final_neo4j_drug_mapping.csv")
    direct = pd.read_csv(MECH / "final_neo4j_direct_targets.csv")
    paths = pd.read_csv(MECH / "final_neo4j_s1_pathway_links.csv")
    evidence_rows = []
    for _, t in top.sort_values("rank").iterrows():
        da = dose[dose.pert_id.eq(t.pert_id)]
        p = prism_er[prism_er.pert_id.eq(t.pert_id)]
        gm = graph_drugs[graph_drugs.pert_id.eq(t.pert_id)]
        dt = direct[direct.pert_id.eq(t.pert_id)]
        pl = paths[paths.pert_id.eq(t.pert_id)]
        exact = bool(len(gm) and str(gm.iloc[0].neo4j_mapping).lower().startswith("exact"))
        neg_fraction = float(da.direction_negative.mean()) if len(da) else np.nan
        has_prism = len(p) > 0
        evidence_rows.append({
            "rank_frozen": int(t["rank"]), "drug_name": t.drug_name, "pert_id": t.pert_id,
            "expression_reversal_evidence": "single Level5 consensus; primary WTCS %.4f; %d/ %d 24h doses negative; empirical stats historical only" % (float(t.WTCS_median), int(da.direction_negative.sum()), len(da)),
            "expression_reversal_grade": "weak-to-moderate computational; low replication/stability" if neg_fraction < .8 else "moderate computational; single consensus, dose stability not equivalent to replication",
            "independent_S1_cross_cohort_evidence": ("Exp010 external S1 rank=%d; WTCS=%.4f; n=%d signature" % (int(t.external_rank), float(t.WTCS_median_external), int(t.n_signatures_external))) if pd.notna(t.external_rank) else "No exact-structure external S1 candidate score available",
            "independent_S1_grade": "limited; one signature and external Top10 overlap only 1/10 overall" if pd.notna(t.external_rank) else "missing",
            "independent_sensitivity_evidence": ("PRISM ER+ n=%d; mean %.3f; panel association is not efficacy" % (int(p.iloc[0].n_erpos_lines), float(p.iloc[0].erpos_mean_sensitivity))) if has_prism else "No matching PRISM ER+ observation in current exact-structure table",
            "independent_sensitivity_grade": "available, nonconfirmatory" if has_prism else "missing",
            "known_target_evidence": ("Exact KG compound map; %d direct target assertions; target relation does not prove inhibition/engagement" % len(dt)) if exact else "No exact current KG compound node; external identifier resolved separately for 5 drugs",
            "known_target_grade": "database association; requires relation/source interpretation" if exact else "unavailable in current KG",
            "disease_pathway_evidence": ("%d KG target-to-S1 pathway rows; path count is not independent evidence count" % len(pl)) if len(pl) else "No current KG target-to-S1 pathway route",
            "disease_pathway_grade": "indirect hypothesis only" if len(pl) else "missing",
            "mechanism_hypothesis_status": "Unvalidated in ER+ disease models; see drug-specific mechanism audit",
            "overall_interpretation": "Do not sum dimensions or interpret as probability of clinical benefit.",
        })
    ev = pd.DataFrame(evidence_rows)
    ev.to_csv(OUT_RESULTS / "evidence_grade_matrix.csv", index=False)

    # Small frontend payload; raw tables and the full Chinese report remain downloadable separately.
    frontend = []
    for _, t in top.sort_values("rank").iterrows():
        pr = primary[primary.pert_id.eq(t.pert_id)]
        primary_sig = sig_audit[(sig_audit.pert_id == t.pert_id) & sig_audit.included_in_formal_scoring_after_QC].iloc[0]
        dd = dose[dose.pert_id.eq(t.pert_id)]
        pp = perm[(perm.pert_id == t.pert_id) & (perm.dose == "10.0 um")]
        pp = pp.iloc[0] if len(pp) else None
        prr = prism_er[prism_er.pert_id.eq(t.pert_id)]
        gm = graph_drugs[graph_drugs.pert_id.eq(t.pert_id)]
        direct_count = int((direct.pert_id == t.pert_id).sum())
        path_count = int((paths.pert_id == t.pert_id).sum())
        frontend.append({
            "rank": int(t["rank"]), "drug_name": t.drug_name, "pert_id": t.pert_id,
            "sig_id": str(primary_sig.sig_id), "WTCS": float(primary_sig.WTCS),
            "distil_cc_q75": float(primary_sig.distil_cc_q75), "tas": float(primary_sig.tas),
            "level5_consensus_signatures": int(sig_audit.pert_id.eq(t.pert_id).sum()),
            "formal_scored_consensus_signatures": int(len(pr)), "replicate_instances": int(primary_sig.distil_nsample_reported),
            "distinct_plates": int(sig_audit.loc[sig_audit.pert_id.eq(t.pert_id), "underlying_distinct_plate_count"].iloc[0]),
            "dose_conditions": int(len(dd)), "negative_dose_count": int(dd.direction_negative.sum()),
            "negative_dose_fraction": float(dd.direction_negative.mean()),
            "historical_B200_p": None if pp is None else float(pp.historical_B200_empirical_pvalue),
            "historical_B200_fdr": None if pp is None else float(pp.historical_B200_BH_FDR),
            "historical_B200_score_matches_current": False if pp is None else bool(pp["same_score_within_1e-6"]),
            "PRISM_ERpos_mean": None if len(prr) == 0 else float(prr.iloc[0].erpos_mean_sensitivity),
            "PRISM_ERpos_lines": None if len(prr) == 0 else int(prr.iloc[0].n_erpos_lines),
            "exact_graph_mapping": bool(len(gm) and str(gm.iloc[0].neo4j_mapping).lower().startswith("exact")),
            "graph_direct_target_assertions": direct_count, "graph_target_to_S1_path_rows": path_count,
        })
    frontend_payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "title": "Final05 candidate reliability audit",
        "frozen_top10": frontend,
        "primary_condition": "MCF7 trt_cp, 10.0 um, 24 h; BING Top100 UP/DOWN",
        "historical_permutation_note": "Exp008 B200 2,000-permutation statistics are historical. Only rows with exact observed WTCS match current final were shown as matching; absence is NA.",
        "validation_priorities": [
            {"drug_name": "mocetinostat", "role": "Exploratory mechanism validation priority; dose consistency and independent S1/PRISM evidence remain limited."},
            {"drug_name": "JNJ-26481585", "role": "Expression-stability follow-up; negative WTCS in all 6 observed 24h dose conditions, but no exact KG or PRISM support and only one scored consensus per condition."},
            {"drug_name": "ponatinib", "role": "Secondary hypothesis validation; highest frozen S2 rank but negative WTCS occurs at only 1 of 5 24h doses."},
            {"drug_name": "doxorubicin", "role": "Use as known breast-cancer cytotoxic comparator/assay control, not as novel repositioning."},
        ],
        "special_cautions": [
            "Doxorubicin already has established breast-cancer use; this result is not a new breast-cancer indication.",
            "Iniparib should not be called a bona fide PARP inhibitor; intact-cell studies found little or no PARP inhibition.",
            "One Level 5 consensus signature aggregates underlying replicate profiles and is not an independent patient or cohort replication.",
            "No evidence dimensions are summed into a probability of therapeutic efficacy.",
        ],
    }
    frontend_path = ROOT / "frontend" / "public" / "final05-audit.json"
    frontend_path.write_text(json.dumps(frontend_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # Source- and hash-aware audit manifest.
    inputs = [RESULTS / "final_top10.csv", RESULTS / "final_signature_scores.csv", RESULTS / "final_drug_condition_summary.csv",
              sig_path, met_path, inst_path, pert_path,
              ROOT / "experiments" / "exp008_scoring_statistics" / "results" / "empirical_pvalues.csv",
              ROOT / "experiments" / "exp011_prism_validation" / "results" / "candidate_sensitivity_results.csv",
              MECH / "final_neo4j_drug_mapping.csv", MECH / "final_neo4j_direct_targets.csv", MECH / "final_neo4j_s1_pathway_links.csv"]
    sources = {
        "ponatinib": "https://www.accessdata.fda.gov/drugsatfda_docs/label/2025/203469s038lbl.pdf",
        "mocetinostat": "https://www.cancer.gov/publications/dictionaries/cancer-drug/def/mocetinostat",
        "MK-2461": "https://pubmed.ncbi.nlm.nih.gov/20145145/",
        "doxorubicin": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=36924f82-6c05-4989-9f41-a398c0ad48e6",
        "rebastinib": "https://www.cancer.gov/publications/dictionaries/cancer-drug/def/rebastinib-tosylate",
        "PHA-767491": "https://pubmed.ncbi.nlm.nih.gov/21768328/",
        "iniparib": "https://pubmed.ncbi.nlm.nih.gov/22291137/",
        "balaglitazone": "https://pubmed.ncbi.nlm.nih.gov/21328517/",
        "PFI-1": "https://pubmed.ncbi.nlm.nih.gov/23576556/",
        "quisinostat": "https://pubchem.ncbi.nlm.nih.gov/compound/11538455",
        "unmapped_identifiers": [r.evidence_source_url for r in id_audit.itertuples()],
    }

    def md_table(headers: list[str], rows: list[list[object]]) -> str:
        def cell(value: object) -> str:
            if value is None or (isinstance(value, float) and np.isnan(value)):
                return "—"
            return str(value).replace("|", "\\|").replace("\n", " ")
        return "| " + " | ".join(headers) + " |\n| " + " | ".join(["---"] * len(headers)) + " |\n" + "\n".join("| " + " | ".join(cell(v) for v in row) + " |" for row in rows)

    z = lambda s: s  # Chinese text below is encoded as Unicode escapes to keep this script portable on Windows shells.
    sig_table = md_table(
        ["\u6392\u540d", "\u836f\u7269", "sig_id", "WTCS", "CC q75", "TAS", "\u5e95\u5c42\u5b9e\u4f8b", "\u5e73\u53f0\u677f\u6570", "\u662f\u5426\u901a\u8fc7\u6b63\u5f0f\u8bc4\u5206"],
        [[int(r.rank_frozen), r.drug_name, r.sig_id, f"{r.WTCS:.6f}" if pd.notna(r.WTCS) else "NA (QC excluded)",
          r.distil_cc_q75, r.tas, int(r.distil_nsample_reported), int(r.underlying_distinct_plate_count),
          "\u662f" if r.included_in_formal_scoring_after_QC else "\u5426\uff1aCC q75 < 0.2"] for r in sig_audit.itertuples()]
    )
    dose_agg = dose.groupby(["rank_frozen", "drug_name", "pert_id"]).agg(
        n_dose=("dose", "nunique"), neg=("direction_negative", "sum"), total=("direction_negative", "count"),
        wtcs_min=("WTCS_median", "min"), wtcs_max=("WTCS_median", "max")).reset_index()
    dose_table = md_table(["\u6392\u540d", "\u836f\u7269", "24h\u5242\u91cf\u6761\u4ef6\u6570", "WTCS<0 \u6761\u4ef6", "\u5206\u6570\u8303\u56f4"],
        [[int(r.rank_frozen), r.drug_name, int(r.n_dose), f"{int(r.neg)}/{int(r.total)}", f"{r.wtcs_min:.3f} to {r.wtcs_max:.3f}"] for r in dose_agg.itertuples()])
    raw_signature_total = len(raw24)
    scored_signature_total = int(raw_dose_audit.formal_scored_signatures.sum())
    excluded_signature_total = int(raw_dose_audit.QC_excluded_signatures.sum())
    duplicate_batch_conditions = int(raw_dose_audit.experiment_series.str.contains("\\|").sum())
    p_primary = perm[perm.dose.eq("10.0 um")].copy()
    p_rows = []
    for _, tr in top.sort_values("rank").iterrows():
        p = p_primary[p_primary.pert_id.eq(tr.pert_id)]
        if len(p) and bool(p.iloc[0]["same_score_within_1e-6"]):
            p_rows.append([int(tr["rank"]), tr.drug_name, f"{p.iloc[0].historical_B200_empirical_pvalue:.6g}",
                           f"{p.iloc[0].historical_B200_BH_FDR:.6g}", "\u5386\u53f2 B200\uff1b\u5f53\u524d WTCS \u4e00\u81f4"])
        else:
            p_rows.append([int(tr["rank"]), tr.drug_name, "NA", "NA", "\u672a\u627e\u5230\u53ef\u6bd4\u5386\u53f2\u7f6e\u6362\u7ed3\u679c"])
    perm_table = md_table(["\u6392\u540d", "\u836f\u7269", "empirical p", "BH FDR", "\u8303\u56f4"], p_rows)
    id_table = md_table(["\u836f\u7269", "LINCS pert_id", "PubChem CID", "ChEMBL", "InChIKey \u7cbe\u786e\u4e00\u81f4", "\u73b0\u6709 KG \u6620\u5c04", "\u5916\u90e8\u6765\u6e90"],
        [[r.drug_name, r.LINCS_pert_id, r.external_PubChem_CID, r.external_ChEMBL_ID,
          "\u662f" if r.exact_InChIKey_match else "\u5426", r.existing_graph_mapping_status, f"[PubChem]({r.evidence_source_url})"] for r in id_audit.itertuples()])
    mech_table = md_table(["\u836f\u7269", "\u4f5c\u7528\u7c7b\u578b", "\u9002\u5e94\u8bc1 / \u7814\u7a76\u72b6\u6001", "\u672c\u9879\u76ee\u89e3\u91ca\u9650\u5236", "\u6765\u6e90"],
        [[r.drug_name, r.known_mechanism_or_class, r.clinical_status_or_indication, r.audit_caveat,
          " ".join(f"[\u6765\u6e90 {i+1}]({url.strip()})" for i, url in enumerate(r.source_url.split(";")))] for r in known.itertuples()])
    report = """# Final05：Top 10 候选药物科研可靠性审计

## 审计结论

正式 Top 10 顺序保持 Final01–04 冻结版本不变。本轮没有重建知识图谱，没有改写 S1/S2 或原始数据。审计确认：主条件下正式纳入每个候选的计分结果均来自一条 Level 5 共识 Signature；其底层通常由 3 个 L1000 实例、3 个检测板整合而成。它们是同一处理条件下的重复表达谱，不是 3 个独立患者队列或独立研究。

原始元数据中 Top 10 主条件共检出 11 条 Level 5 记录：Iniparib 有两条，其中一条的 `distil_cc_q75=0.18`，低于正式门槛 0.2，未进入正式计分；另一条 `distil_cc_q75=0.42` 纳入。其余候选各有一条主条件记录。10 个正式纳入的主条件签名均与冻结分数表的 sig_id、pert_id、WTCS 对齐。

各候选 24 小时可评分剂量条件共 51 个。只有 doxorubicin 5/6、mocetinostat 4/6、JNJ-26481585 6/6 的条件 WTCS 为负；ponatinib 仅 1/5。其余候选也存在符号变化或零分。剂量间变化说明排序依赖处理条件，不构成独立批次重复。对这 10 个扰动药物，GSE70138 MCF7 trt_cp 元数据仅见 24 小时；本轮没有替其他时间重算 WTCS，因此不把时间外推当作支持证据。

## 主条件 Signature 与 QC

主条件：MCF7、`trt_cp`、24 h、10.0 μM；评分输入为现有 BING Top100 UP/DOWN 正式结果。`distil_nsample` 与 `distil_id` 均用于核对底层实例，并与 `inst_info` 中实例/检测板对齐。

""" + sig_table + """

说明：Iniparib 的 QC 未通过记录仍保留在表中，WTCS 留空表示未进入正式评分，并非零分。其余数值只代表表达逆转关联。WTCS 更负不等于临床疗效更强。

## 跨剂量和处理条件支持

""" + dose_table + f"""

没有把不同剂量简单平均，也没有为每个药物挑选最有利剂量。主排名沿用固定统一条件。跨剂量统计是稳定性描述，不是重复实验显著性。原始 24 h 元数据共有 {raw_signature_total} 条候选签名，其中 {scored_signature_total} 条进入正式评分，{excluded_signature_total} 条未纳入；{duplicate_batch_conditions} 个药物剂量条件出现多个实验系列记录。多系列记录均来自 Iniparib 的 LJP008 与 REP.A005 两组：0.37 μM 和 3.33 μM 两组均有通过 QC 的 Signature，但 WTCS 方向彼此相反；10.0 μM 中 LJP008 记录因 CC q75=0.18 被排除，REP.A005 记录进入主评分。该批次对照显示其逆转信号并不一致。逐剂量 QC 排除和系列信息见 `results/dose_metadata_qc_audit.csv`；逐条真实签名分数见 `results/all_candidate_signature_audit.csv`。详细逐剂量汇总见 `results/dose_batch_support.csv` 和 `results/time_metadata_coverage.csv`。

## 经验 P 值与多重检验

旧 Exp008 B200 输出进行过 2,000 次置换。本次逐项与当前冻结 WTCS 对齐后，仅 5 个药物的主条件有相同观察分数并可报告其历史经验 P/FDR；其余药物为 NA，不能补造。历史可对齐的 5 项经验 p 均为 0.0005、BH FDR 均为 0.003933，p 值受 2,000 次置换分辨率限制。这些数值来自旧实验文件，不是本轮针对全体最终候选重新计算的统计检验；不能当作对全部 Top 10 的统一显著性证明。

""" + perm_table + """

## 五个原图谱未精确映射药物的身份复核

使用 LINCS `pert_id` 对应的原始 `pert_info` InChIKey，与 PubChem 结构记录逐项比较；5/5 InChIKey 精确相同，并记录 PubChem CID、ChEMBL ID 和来源 URL。没有使用模糊名称匹配。这解决的是化合物身份交叉引用，不会自动创建或修改 Neo4j Drug 节点；当前图谱映射仍未覆盖这 5 个实体。

""" + id_table + """

逐项来源链接见 `results/unmapped_drug_identifier_audit.csv`。尤其 MK-2461 PubChem 同义词记录还包含 LINCS BRD 编号，其他候选也以原始 LINCS InChIKey 与 PubChem InChIKey 作结构级核对。

## 药理机制、适应证与反证

""" + mech_table + """

**Doxorubicin** 已有乳腺癌辅助及转移性治疗用途，因此应作为已知治疗药/实验阳性比较对象，不应描述成项目新发现的乳腺癌药物。它的强逆转分数可能包含广谱细胞毒与应激成分，也不提供 ER 阳性特异性证据。

**Iniparib** 不应继续标注成确证的 PARP 抑制剂。研究显示其在完整细胞中对 PARP 活性几乎没有抑制，且高浓度细胞杀伤不支持 PARP 抑制机制。图谱中的 PARP1 关联（如有）只是一条数据库断言，不能自动解释为药物抑制 PARP1。

其余候选的药理类别与来源链接在 CSV 中逐药记录。图谱中的 Drug–Gene 断言不总是抑制关系，数量多也不等同于更强机制证据；路径行数可能来自共享通路/多条证据，不作为独立实验重复计数。

## 分项证据等级（不合并成疗效概率）

| 证据维度 | 本轮判定 |
|---|---|
| 表达逆转 | 主条件有强负 WTCS 的计算信号，但每个药物只有一个纳入的共识签名；剂量稳定性总体有限。 |
| 独立 S1 队列 | Exp010 外部 S1 同条件结果仅 5/10 可用，整体排序 Spearman=0.544，Top10 只重合 1/10；单候选外部也只有一条 Signature。 |
| 独立药物敏感性 | Exp011 PRISM ER+ 结果只覆盖 5/10。已有 Top50 S2–PRISM 秩相关为 rho=0.260，95% CI [-0.105, 0.573]，未显示明确相关；PRISM 是细胞活力观察，不是临床获益。 |
| 已知靶点 | 现有 KG 对 5/10 有精确化合物映射。断言仍需区分抑制、结合、转运或其他关系类型。另 5 个外部化合物身份已精确核实，但未改图谱。 |
| 疾病相关通路 | 5 个已映射药物具有图谱靶点到 S1 通路关联；这属于间接机制线索，不证明因果。 |
| 机制假设 | 全部尚未在 ER+ 乳腺癌实验模型中验证，不构成治疗机制或疗效结论。 |

每个候选的分项描述见 `results/evidence_grade_matrix.csv`。这些维度不相加，不换算成未经验证的“有效概率”。

## 建议后续优先验证

正式 Top10 不变。若进入实验验证，建议将 **mocetinostat** 作为探索性机制验证优先项（仍需靶点占有、剂量重复和 ER+ 模型验证）；**JNJ-26481585 / quisinostat** 可作为表达稳定性追踪候选（观察到的 6/6 个 24 h 剂量条件 WTCS 为负），但缺少当前 KG 与 PRISM 支持，且每条件仍只有一个合格共识签名；**ponatinib** 可作为次级假设，但主条件虽排第 1，只有 1/5 的 24 h 剂量条件 WTCS 为负。**Doxorubicin** 更适合作为已知乳腺癌药物的实验比较/阳性对照，不能作为新重定位发现。此建议是透明的验证顺序，不是重新排名或药效判断。

## 尚缺证据与局限

1. Top10 的正式主条件几乎都是单个 Level 5 共识 Signature；重复实例有助于形成共识质量，但不能代替独立实验批次、独立细胞模型或患者样本重复。
2. 历史置换统计只在部分候选上与当前 WTCS 精确对齐，其他候选没有当前版本统一重算的经验 P/FDR。
3. PRISM 覆盖不足且整体相关性未证明表达逆转分数可以预测细胞敏感性；PRISM 也不等同于乳腺癌患者结局。
4. 对没有精确图谱实体的 5 个候选，身份映射已解决但图谱机制覆盖仍缺失；这轮遵循要求未重建图谱。
5. 没有对候选在 ER+ 乳腺癌模型中做靶点结合、功能扰动、剂量反应、细胞选择性或动物实验。因此 Top10 仍是待验证计算候选，而不是药物推荐。

## 复现与文件

审计脚本：`scripts/run_final05_audit.py`。原始输入与输出 SHA-256、固定条件、来源链接记录在 `final05_manifest.json`。逐签名、逐剂量、身份映射、机制与分项证据 CSV 均保存在 `results/`。正式 `results/final_top10.csv` 未修改。
"""
    report_path = OUT_REPORTS / "final05_scientific_audit_report.md"
    report_path.write_text(report, encoding="utf-8")
    public_report = ROOT / "frontend" / "public" / "final05-scientific-audit-report.md"
    shutil.copyfile(report_path, public_report)
    public_downloads = {
        "final05-evidence-grade.csv": OUT_RESULTS / "evidence_grade_matrix.csv",
        "final05-dose-support.csv": OUT_RESULTS / "dose_batch_support.csv",
        "final05-dose-metadata-qc.csv": OUT_RESULTS / "dose_metadata_qc_audit.csv",
        "final05-all-signatures.csv": OUT_RESULTS / "all_candidate_signature_audit.csv",
        "final05-identifier-audit.csv": OUT_RESULTS / "unmapped_drug_identifier_audit.csv",
    }
    for name, source_path in public_downloads.items():
        shutil.copyfile(source_path, ROOT / "frontend" / "public" / name)
    final_report_path = FINAL / "reports" / "final_research_report.md"
    old_report = final_report_path.read_text(encoding="utf-8")
    marker = "\n## Final05 \u79d1\u7814\u53ef\u9760\u6027\u5ba1\u8ba1\n"
    if marker in old_report:
        old_report = old_report.split(marker)[0]
    final_report_path.write_text(old_report.rstrip() + marker + report[report.index("## \u5ba1\u8ba1\u7ed3\u8bba"):], encoding="utf-8")

    manifest = {
        "audit": "Final05 scientific reliability audit", "generated_utc": datetime.now(timezone.utc).isoformat(),
        "top10_invariant": top[["rank", "drug_name", "pert_id"]].to_dict(orient="records"),
        "method": {"primary_condition": "MCF7 trt_cp 10.0 um 24 h", "fixed_scoring_input": "BING Top100 UP/DOWN; existing corrected 5,861 signature score run",
                   "replicate_definition": "distil_nsample and sig_info.distil_id list of underlying instance profiles; not independent cohorts",
                   "historical_permutation": "Exp008 B200, 2,000 permutations, reported as historical only and crosswalked against current score"},
        "input_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in inputs},
        "external_sources": sources,
        "outputs": {p.name: sha256(p) for p in OUT_RESULTS.glob("*.csv")},
        "frontend_payload_sha256": sha256(frontend_path),
        "frontend_report_sha256": sha256(public_report),
        "frontend_download_sha256": {name: sha256(ROOT / "frontend" / "public" / name) for name in public_downloads},
        "report_sha256": sha256(report_path),
    }
    (OUT / "final05_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"primary_signatures": len(sig_audit), "dose_rows": len(dose), "identifier_matches": int(id_audit.exact_InChIKey_match.sum()),
                      "historical_permutation_rows": len(perm), "top10_unchanged": top[["rank", "drug_name", "pert_id"]].to_dict(orient="records")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
