import gzip

import h5py
import numpy as np
import pandas as pd
from uuid import uuid4

import project_screen


def _write_tsv_gz(path, frame):
    with gzip.open(path, "wt", encoding="utf-8", newline="") as stream:
        frame.to_csv(stream, sep="\t", index=False)


def test_project_screen_extracts_real_shaped_rows_and_keeps_dose_strata(tmp_path, monkeypatch):
    data = tmp_path / "data"
    work = tmp_path / "work"
    out = tmp_path / "results"
    data.mkdir(); work.mkdir()
    genes = pd.DataFrame({
        "pr_gene_id": ["101", "102", "103", "104"],
        "pr_gene_symbol": ["UPG", "DNG", "BG1", "BG2"],
        "pr_is_bing": [1, 1, 1, 1],
    })
    _write_tsv_gz(data / "tiny_gene_info.txt.gz", genes)
    sig_rows = [
        ("A10_R1", "CP-A", "Drug A", "24 h", "10 uM"),
        ("A10_R2", "CP-A", "Drug A", "24 h", "10 uM"),
        ("A1_R1", "CP-A", "Drug A", "24 h", "1 uM"),
        ("A6_R1", "CP-A", "Drug A", "6 h", "10 uM"),
        ("LOW_R1", "CP-A", "Drug A", "24 h", "10 uM"),
        ("NO_GCTX", "CP-B", "Drug B", "24 h", "10 uM"),
    ]
    sig_info = pd.DataFrame([{"sig_id": sid, "pert_id": pert, "pert_iname": name, "pert_type": "trt_cp", "cell_id": "MCF7", "pert_idose": dose, "pert_itime": time} for sid, pert, name, time, dose in sig_rows])
    metrics = pd.DataFrame([{"sig_id": sid, "distil_cc_q75": (0.1 if sid == "LOW_R1" else 0.6), "distil_ss": 5, "tas": 0.5, "distil_nsample": 3} for sid, *_ in sig_rows])
    _write_tsv_gz(data / "tiny_sig_info.txt.gz", sig_info)
    _write_tsv_gz(data / "tiny_sig_metrics.txt.gz", metrics)
    gctx_sig_ids = ["A10_R1", "A10_R2", "A1_R1", "A6_R1", "LOW_R1"]
    scores = np.asarray([[-4, 4, 2, -2]] * len(gctx_sig_ids), dtype=np.float32)
    with h5py.File(work / "tiny.gctx", "w") as handle:
        row = handle.create_group("0/META/ROW")
        col = handle.create_group("0/META/COL")
        dtype = h5py.string_dtype(encoding="utf-8")
        row.create_dataset("id", data=np.asarray(["101", "102", "103", "104"], dtype=object), dtype=dtype)
        col.create_dataset("id", data=np.asarray(gctx_sig_ids, dtype=object), dtype=dtype)
        handle.create_dataset("0/DATA/0/matrix", data=scores, chunks=(1, 4))
    s1 = tmp_path / "s1.csv"
    s1.write_text("gene_id,logFC,adj.P.Val,t\nUPG,1.5,0.01,4\nDNG,-1.5,0.02,-4\n", encoding="utf-8")
    monkeypatch.setattr(project_screen, "DATA", data)
    monkeypatch.setattr(project_screen, "WORK", work)

    preallocated_run_id = f"ANALYSIS_RUN:S2_LINCS:{uuid4()}"
    manifest = project_screen.screen_project(s1_path=s1, identifier_type="symbol", output_dir=out, top_n=1, test_only=True, analysis_run_id=preallocated_run_id)

    assert manifest["status"] == "completed" and manifest["test_only"] is True
    assert manifest["analysis_run_id"] == preallocated_run_id
    assert manifest["qc_summary"]["mcf7_trt_cp_signatures"] == 6
    assert manifest["qc_summary"]["requested_time_signatures"] == 5
    assert manifest["qc_summary"]["quality_pass_signatures"] == 4
    assert manifest["qc_summary"]["scored_signatures"] == 3
    assert manifest["qc_summary"]["dose_time_condition_rows"] == 2
    assert manifest["qc_summary"]["s1_up_measured_in_gctx"] == 1
    result = pd.read_csv(out / "signature_scores.csv")
    condition = pd.read_csv(out / "drug_condition_summary.csv")
    assert len(result) == 3 and result.WTCS.lt(0).all()
    assert set(condition.dose) == {"1 uM", "10 uM"}
    assert condition.n_signatures.sum() == 3
    assert (out / "s1_gene_mapping_audit.csv").is_file()


def test_unsupported_ensembl_mapping_emits_audit_and_blocks_scoring(tmp_path, monkeypatch):
    data = tmp_path / "data"
    data.mkdir()
    genes = pd.DataFrame({"pr_gene_id": ["101", "102"], "pr_gene_symbol": ["UPG", "DNG"], "pr_is_bing": [1, 1]})
    _write_tsv_gz(data / "tiny_gene_info.txt.gz", genes)
    s1 = tmp_path / "s1.csv"
    s1.write_text("gene_id,logFC,adj.P.Val,t\nENSG000001,1,0.01,3\nENSG000002,-1,0.01,-3\n", encoding="utf-8")
    out = tmp_path / "blocked"
    monkeypatch.setattr(project_screen, "DATA", data)

    manifest = project_screen.screen_project(s1_path=s1, identifier_type="ensembl", output_dir=out, top_n=1, test_only=True)

    assert manifest["status"] == "BLOCKED"
    assert (out / "s1_gene_mapping_audit.csv").is_file()
    audit = pd.read_csv(out / "s1_gene_mapping_audit.csv")
    assert audit.mapping_status.str.startswith("unsupported_identifier_type_ensembl").all()
    assert not (out / "signature_scores.csv").exists()
