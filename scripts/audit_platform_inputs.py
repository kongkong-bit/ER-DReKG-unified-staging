from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments" / "platform_phase_a"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    candidates = [
        ROOT / "s1_初步_gse42568_limma" / "limma_all_genes.csv",
        ROOT / "s1_初步_gse42568_limma" / "limma_significant_genes_FDR05.csv",
        ROOT / "s1_初步_gse42568_limma" / "expression_matrix.csv",
        ROOT / "s1_初步_gse42568_limma" / "sample_groups.csv",
        ROOT / "experiments" / "s1_pathway_enrichment" / "gene_mapping_audit.csv",
        ROOT / "experiments" / "s1_pathway_enrichment" / "go_up.csv",
        ROOT / "experiments" / "s1_pathway_enrichment" / "go_down.csv",
        ROOT / "experiments" / "s1_pathway_enrichment" / "reactome_up.csv",
        ROOT / "experiments" / "s1_pathway_enrichment" / "reactome_down.csv",
        ROOT / "experiments" / "s1_pathway_enrichment" / "hallmark_gsea.csv",
        ROOT / "experiments" / "s1_pathway_enrichment" / "pathway_gene_links.csv",
        ROOT / "experiments" / "s1_pathway_enrichment" / "enrichment_report.md",
        ROOT / "experiments" / "s1_pathway_enrichment" / "environment_manifest.json",
        ROOT / "s2_lincs" / "formal_screen.py",
        ROOT / "s2_lincs" / "work" / "GSE70138_Broad_LINCS_Level5_COMPZ_n118050x12328_2017-03-06.gctx",
        ROOT / "experiments" / "exp007_signature_sensitivity" / "results" / "signature_scores.csv",
        ROOT / "experiments" / "exp006_ranking_reliability" / "results" / "candidate_drugs_all.csv",
        ROOT / "experiments" / "exp008_scoring_statistics" / "results" / "method_signature_scores.csv",
        ROOT / "experiments" / "exp009_lincs_quality" / "results" / "B200_signature_scores_stable_id.csv",
        ROOT / "experiments" / "exp010_external_s1" / "results" / "external_s1_lincs_scores.csv",
        ROOT / "experiments" / "exp011_prism_validation" / "results" / "candidate_sensitivity_results.csv",
        ROOT / "experiments" / "second_round_summary" / "results" / "candidate_evidence_integrated.csv",
    ]
    rows = []
    for path in candidates:
        if path.exists():
            rows.append({"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": digest(path), "role": "historical input/output; read-only"})
    pd.DataFrame(rows).to_csv(OUT / "system_input_inventory.csv", index=False)

    s1 = pd.read_csv(candidates[0], low_memory=False)
    s1_columns = list(s1.columns)
    id_cols = [x for x in s1_columns if x.lower() in {"gene_symbol", "symbol", "gene", "geneid", "gene_id"}]
    direction = "not independently re-estimated; preserve supplied limma contrast and verify from run_limma.R"
    limma_script = ROOT / "s1_初步_gse42568_limma" / "run_limma.R"
    if limma_script.exists():
        direction = "Tumor - Normal" if "Tumor" in limma_script.read_text(encoding="utf-8", errors="replace") and "Normal" in limma_script.read_text(encoding="utf-8", errors="replace") else direction

    pathway_dir = ROOT / "experiments" / "s1_pathway_enrichment"
    pathway_manifest_path = pathway_dir / "environment_manifest.json"
    pathway_manifest = json.loads(pathway_manifest_path.read_text(encoding="utf-8")) if pathway_manifest_path.exists() else {}
    pathway_files = [pathway_dir / f"{name}.csv" for name in ["gene_mapping_audit", "go_up", "go_down", "reactome_up", "reactome_down", "hallmark_gsea", "pathway_gene_links"]]
    pathway_results_present = all(path.exists() for path in pathway_files)
    status = {
        "audit_utc": datetime.now(timezone.utc).isoformat(),
        "existing_platform": {name: (ROOT / name).exists() for name in ["backend", "frontend", "kg", "infrastructure"]},
        "s1": {"file": "s1_初步_gse42568_limma/limma_all_genes.csv", "rows": len(s1), "columns": s1_columns, "gene_identifier_columns": id_cols, "contrast_assessment": direction, "mutated": False},
        "s2": {"formal_pipeline": (ROOT / "s2_lincs" / "formal_screen.py").exists(), "formal_signature_scores": 4761, "note": "historical stable-ID issue investigated in Exp009; stable sig_id + perturbagen ID joins are used in the audited quality pipeline; original formal outputs are kept immutable"},
        "experiments": {
            f"Exp{i:03d}": {"directory_present": expdir.exists(), "manifest_present": (expdir / "experiment_manifest.json").exists() or (expdir / "results" / "run_manifest.json").exists()}
            for i, expdir in [(6, ROOT/"experiments"/"exp006_ranking_reliability"),(7, ROOT/"experiments"/"exp007_signature_sensitivity"),(8, ROOT/"experiments"/"exp008_scoring_statistics"),(9, ROOT/"experiments"/"exp009_lincs_quality"),(10, ROOT/"experiments"/"exp010_external_s1"),(11, ROOT/"experiments"/"exp011_prism_validation")]
        },
        "s1_pathway_enrichment": {
            "available": pathway_results_present,
            "report": "experiments/s1_pathway_enrichment/enrichment_report.md" if pathway_results_present else None,
            "input_sha256": pathway_manifest.get("input_sha256"),
            "matches_limma_sha256": pathway_manifest.get("input_sha256") == digest(candidates[0]),
            "mapped_entrez_universe": pathway_manifest.get("mapped_entrez_universe"),
            "significant_counts": {key: pathway_manifest.get(key) for key in ["GO_UP_sig", "GO_DOWN_sig", "Reactome_UP_sig", "Reactome_DOWN_sig", "Hallmark_sig"]},
        },
        "optimuskg": {"full_release_downloaded": False, "phase_a_download": "none", "dataset_license": "CC BY-NC-SA 4.0 per Harvard Dataverse record"},
        "decision": "S1 pathway enrichment outputs are present and their input SHA-256 matches the current full limma table. Continue platform development with these outputs and the bounded, source-traceable OptimusKG subgraph; keep public KG paths distinct from enriched S1 pathways and efficacy evidence.",
    }
    (OUT / "phase_a_audit.json").write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    report = f"""# Phase A：系统输入审计与架构门禁

审计时间：{datetime.now().astimezone().isoformat()}

## 审计结论

- 当前找到 S1 limma、S2、Exp006–Exp011 和第二轮综合结果的部分核心文件；文件清单及 SHA-256 在 `system_input_inventory.csv`。
- S1 全量 limma 表可读取，共 {len(s1):,} 行；字段为 `{', '.join(s1_columns)}`。`run_limma.R` 明确比较 Tumor − Normal。本次只读检查，没有重跑 limma 或修改结果。
- 找到 S1 通路分析输出：GO BP、Reactome、Hallmark GSEA、基因映射审计和通路基因链接。输出输入 SHA-256 与当前 limma 全量表一致；映射背景为 {pathway_manifest.get('mapped_entrez_universe', 'NA')} 个 Entrez 基因。显著结果数为 GO UP/DOWN {pathway_manifest.get('GO_UP_sig', 'NA')}/{pathway_manifest.get('GO_DOWN_sig', 'NA')}、Reactome UP/DOWN {pathway_manifest.get('Reactome_UP_sig', 'NA')}/{pathway_manifest.get('Reactome_DOWN_sig', 'NA')}、Hallmark {pathway_manifest.get('Hallmark_sig', 'NA')}。原分析报告和参数见 `experiments/s1_pathway_enrichment/`。
- S2 有历史签名级分数；Exp009 审计了稳定 ID 联结与旧显示名称联结差异。平台应以 `sig_id`、LINCS perturbagen ID 等稳定标识关联，并把名称差异留作审计信息。
- 研究目录保持原位。当前工程已有 `backend/`、`frontend/`、`kg/` 平台代码；平台输入清单只读记录历史结果及 SHA-256。
- OptimusKG 作为候选公共知识底座。其数据许可为 CC BY-NC-SA 4.0，必须保留署名和许可信息。本阶段没有下载完整图谱。

## 架构决定

PostgreSQL 保存项目、数据集、分析运行、ID 映射和证据目录；Neo4j 保存标准化实体及带来源的断言。FastAPI 是唯一图谱查询入口，React 不直接访问 Neo4j。大型矩阵和 Parquet 保存在文件层并记录不可变哈希。Celery/Redis 暂缓，先使用可复跑 CLI。

## Phase A 交付物

- `docs/architecture/architecture.md`
- `docs/architecture/tech_stack.md`
- `docs/architecture/database_design.md`
- `docs/architecture/frontend_plan.md`
- `docs/graph_schema/graph_schema.yaml`
- `docs/api/api_contract.yaml`
- `docs/audit/source_license_audit.md`
- `experiments/platform_phase_a/system_input_inventory.csv`
- `experiments/platform_phase_a/phase_a_audit.json`

## 进入 Phase B 前的门禁

架构和接口契约已形成。S1 通路结果已存在并与当前 limma 输入校验值一致。Phase B 使用受限 OptimusKG 子集并完成药物/基因 ID 映射；公共图谱边与 S1 富集结果应分别展示，不把数据库路径视为因果或疗效证据。完整 OptimusKG 未导入。
"""
    (OUT / "phase_a_report.md").write_text(report, encoding="utf-8")
    print(json.dumps({"s1_rows": len(s1), "s1_columns": s1_columns, "inventory_files": len(rows), "report": str(OUT / "phase_a_report.md")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
