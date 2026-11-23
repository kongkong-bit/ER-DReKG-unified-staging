import csv
import hashlib
import json
from pathlib import Path
from uuid import UUID, uuid5

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import AnalysisRun, Candidate, Dataset, Project

NAMESPACE = UUID("10f85342-3f82-4d9c-b00a-3183f7d34e49")
PROJECT_SLUG = "erpos-gse42568"
RUN_ID = "PHASEB_OPTIMUSKG32_20261113"


def seed_historical_project(db: Session) -> None:
    project = db.scalar(select(Project).where(Project.slug == PROJECT_SLUG))
    if project is None:
        project = Project(project_id=str(uuid5(NAMESPACE, PROJECT_SLUG)), slug=PROJECT_SLUG, name="ER-positive breast cancer drug repositioning", disease_id="MONDO:0007254", status="active")
        db.add(project); db.flush()
    run = db.get(AnalysisRun, RUN_ID)
    phaseb_dir = Path(settings.graph_data_dir).resolve()
    manifest_path = phaseb_dir / "phase_b_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    if run is None:
        run = AnalysisRun(
            analysis_run_id=RUN_ID, project_id=project.project_id, run_type="knowledge_graph_seed_subgraph",
            status="completed", parameters={"source_release": "OptimusKG 3.2", "disease_context": "GSE42568 ER-positive, Tumor - Normal", "max_graph_depth": 2},
            software_versions={"pipeline": "DiseaseGraph Lab Phase B"}, input_hashes=manifest.get("input_sha256", {}),
        )
        db.add(run); db.flush()
    dataset = db.scalar(select(Dataset).where(Dataset.project_id == project.project_id, Dataset.source == "GSE42568"))
    if dataset is None:
        limma_path = Path(__file__).resolve().parents[2] / "s1_初步_gse42568_limma" / "limma_significant_genes_FDR05.csv"
        sha = hashlib.sha256(limma_path.read_bytes()).hexdigest() if limma_path.exists() else ""
        db.add(Dataset(project_id=project.project_id, source="GSE42568", release="local limma output", source_url="https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE42568", sha256=sha, license_status="GEO terms; review before redistribution", state="validated", metadata_json={"contrast": "Tumor - Normal", "significant_gene_count": 7066}))
    candidate_path = Path(__file__).resolve().parents[2] / "experiments" / "exp006_ranking_reliability" / "results" / "candidate_drugs_top50.csv"
    existing = db.scalar(select(Candidate.candidate_id).where(Candidate.project_id == project.project_id, Candidate.analysis_run_id == RUN_ID).limit(1))
    if existing is None and candidate_path.exists():
        with candidate_path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                db.add(Candidate(candidate_id=f"{project.project_id}:{RUN_ID}:{row['pert_id']}", project_id=project.project_id, analysis_run_id=RUN_ID, pert_id=row["pert_id"], drug_name=row["drug_name"], rank=int(float(row["rank"])), score_name="WTCS median B", score_value=row.get("wtcs_median_B", ""), evidence_json={"dose": row.get("primary_dose"), "time": row.get("pert_time"), "stability_grade": row.get("stability_grade"), "evidence_limitations": row.get("evidence_limitations")}))
    db.commit()
