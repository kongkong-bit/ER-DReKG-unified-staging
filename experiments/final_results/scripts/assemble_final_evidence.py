from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parents[1]

LITERATURE = {
    "ponatinib": ["https://www.accessdata.fda.gov/drugsatfda_docs/label/2020/203469s032lbl.pdf"],
    "mocetinostat": ["https://pubmed.ncbi.nlm.nih.gov/28276480/", "https://pubmed.ncbi.nlm.nih.gov/18413790/"],
    "MK-2461": ["https://pubmed.ncbi.nlm.nih.gov/21608528/"],
    "doxorubicin": ["https://www.accessdata.fda.gov/drugsatfda_docs/label/2024/050629Orig1s033Correctedlbl.pdf"],
    "rebastinib": ["https://pubmed.ncbi.nlm.nih.gov/21505103/", "https://pubmed.ncbi.nlm.nih.gov/27927766/"],
    "PHA-767491": ["https://pubmed.ncbi.nlm.nih.gov/18469809/", "https://pubmed.ncbi.nlm.nih.gov/21768328/"],
    "iniparib": ["https://pubmed.ncbi.nlm.nih.gov/22291137/"],
    "balaglitazone": ["https://pubmed.ncbi.nlm.nih.gov/22372600/"],
    "PFI-1": ["https://pubmed.ncbi.nlm.nih.gov/23576556/"],
    "JNJ-26481585": ["https://pubmed.ncbi.nlm.nih.gov/27423454/", "https://aacrjournals.org/clincancerres/article/15/22/6841/74560/JNJ-26481585-a-Novel-Second-Generation-Oral"],
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def join_values(values: pd.Series, max_items: int = 30) -> str:
    return "; ".join(sorted(set(str(value) for value in values.dropna() if str(value).strip()))[:max_items])


def main() -> None:
    result = OUT / "results"
    mechanism = OUT / "mechanism"
    figures = OUT / "figures"
    top = pd.read_csv(result / "final_top10.csv")
    mapping = pd.read_csv(mechanism / "final_neo4j_drug_mapping.csv")
    targets = pd.read_csv(mechanism / "final_neo4j_direct_targets.csv")
    paths = pd.read_csv(mechanism / "final_neo4j_s1_pathway_links.csv")
    s2_target = pd.read_csv(mechanism / "final_top10_target_s2_expression.csv")
    mapping_by = mapping.set_index("pert_id")

    rows = []
    for candidate in top.itertuples(index=False):
        drug_targets = targets[targets.pert_id.eq(candidate.pert_id)]
        significant_targets = drug_targets[drug_targets.s1_FDR.lt(0.05)] if not drug_targets.empty else drug_targets
        drug_paths = paths[paths.pert_id.eq(candidate.pert_id)]
        pathway_summary = (drug_paths.groupby(["pathway_id", "pathway_label"], dropna=False)
                           .agg(unique_target_genes=("target_gene_id", "nunique"), evidence_ids=("gene_pathway_evidence_ids", join_values))
                           .reset_index().sort_values(["unique_target_genes", "pathway_label"], ascending=[False, True])) if not drug_paths.empty else pd.DataFrame()
        target_expr = s2_target[s2_target.pert_id.eq(candidate.pert_id)]
        map_row = mapping_by.loc[candidate.pert_id] if candidate.pert_id in mapping_by.index else None
        rows.append({
            "rank": int(candidate.rank), "pert_id": candidate.pert_id, "drug_name": candidate.drug_name,
            "main_condition": f"{candidate.cell_id} {candidate.pert_type} {candidate.dose} {candidate.time}",
            "WTCS_median": candidate.WTCS_median, "reversal_score_project_convention": -candidate.WTCS_median,
            "n_signatures": int(candidate.n_signatures), "CC_median": candidate.CC_median, "TAS_median": candidate.TAS_median,
            "n_24h_dose_conditions": int(candidate.n_24h_dose_conditions), "negative_dose_fraction": candidate.negative_dose_fraction,
            "external_S1_same_condition_rank": candidate.external_rank, "external_S1_same_condition_WTCS": candidate.WTCS_median_external,
            "PRISM_ERpos_mean_sensitivity": candidate.erpos_mean_sensitivity, "PRISM_ERpos_median_sensitivity": candidate.erpos_median_sensitivity,
            "PRISM_ERpos_cell_lines": candidate.n_erpos_lines, "PRISM_ERneg_mean_sensitivity": candidate.erneg_mean_sensitivity,
            "PRISM_ERneg_cell_lines": candidate.n_erneg_lines, "PRISM_MCF7_sensitivity": candidate.mcf7_sensitivity,
            "PRISM_ERpos_rank": candidate.sensitivity_rank_erpos,
            "Neo4j_exact_InChIKey_status": map_row.neo4j_mapping if map_row is not None else "not queried",
            "Neo4j_graph_drug_id": map_row.graph_drug_ids if map_row is not None and hasattr(map_row, "graph_drug_ids") else "",
            "Neo4j_direct_target_count": int(drug_targets.target_gene_id.nunique()) if not drug_targets.empty else 0,
            "Neo4j_target_genes": join_values(drug_targets.target_symbol) if not drug_targets.empty else "",
            "S1_DEG_direct_target_count": int(significant_targets.target_gene_id.nunique()) if not significant_targets.empty else 0,
            "S1_UP_direct_targets": join_values(significant_targets.loc[significant_targets.s1_direction.eq("UP"), "target_symbol"]) if not significant_targets.empty else "",
            "S1_DOWN_direct_targets": join_values(significant_targets.loc[significant_targets.s1_direction.eq("DOWN"), "target_symbol"]) if not significant_targets.empty else "",
            "Neo4j_target_to_S1_pathway_rows": int(len(drug_paths)),
            "Neo4j_S1_pathways": join_values(pathway_summary.pathway_label, 12) if not pathway_summary.empty else "",
            "target_S2_compz_measured": int(target_expr.mapping_status.eq("mapped by exact LINCS gene symbol").sum()),
            "target_S2_opposite_direction_count": int(target_expr.S2_directional_relation.eq("opposite expression direction (descriptive)").sum()),
            "target_S2_same_direction_count": int(target_expr.S2_directional_relation.eq("same expression direction (descriptive)").sum()),
            "target_evidence_ids": join_values(drug_targets.target_evidence_ids, 50) if not drug_targets.empty else "",
            "mechanism_evidence_limit": ("Current graph has no exact InChIKey node" if map_row is None or map_row.neo4j_mapping != "exact InChIKey" else "Graph routes are curated associations, not proof of causality or therapeutic effect"),
            "target_expression_caveat": "LINCS COMPZ target transcript direction is descriptive, not direct target engagement or activity",
            "literature_links": ";".join(LITERATURE.get(str(candidate.drug_name), [])),
        })
    matrix = pd.DataFrame(rows)
    matrix.to_csv(result / "final_top10_evidence_matrix.csv", index=False)

    evidence_priority = matrix.copy()
    evidence_priority["evidence_coverage_only_order"] = np.arange(1, len(evidence_priority) + 1)
    evidence_priority = evidence_priority.sort_values(
        ["Neo4j_target_to_S1_pathway_rows", "Neo4j_direct_target_count", "external_S1_same_condition_rank"],
        ascending=[False, False, True], na_position="last", kind="stable",
    ).reset_index(drop=True)
    evidence_priority["evidence_coverage_only_order"] = np.arange(1, len(evidence_priority) + 1)
    evidence_priority["priority_interpretation"] = "mechanism evidence completeness ordering only; does not change S2 candidate rank or imply drug efficacy"
    evidence_priority.to_csv(result / "evidence_priority_candidates.csv", index=False)

    # Figure 1: actual corrected WTCS values.
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=200)
    ordered = matrix.sort_values("rank", ascending=False)
    colors = ["#bf6b54" if x < 0 else "#4a8b83" for x in ordered.WTCS_median]
    ax.barh(ordered.drug_name, ordered.WTCS_median, color=colors)
    ax.axvline(0, color="#5d6773", lw=0.8)
    for y, (_, r) in enumerate(ordered.iterrows()):
        ax.text(r.WTCS_median + 0.012, y, f"{r.WTCS_median:.3f}  ·  n={int(r.n_signatures)}", va="center", ha="left", color="white", fontsize=8)
    ax.set_xlabel("Median WTCS (negative = inverse expression association)")
    ax.set_title("Final Top 10 · MCF7, 24 h, 10 μM, CC ≥ 0.2")
    ax.grid(axis="x", alpha=0.18)
    fig.tight_layout()
    fig.savefig(figures / "final_top10_wtcs.png", bbox_inches="tight")
    plt.close(fig)

    # Figure 2: separate observed dose conditions to show sign stability.
    condition = pd.read_csv(result / "final_drug_condition_summary.csv")
    condition = condition[condition.pert_id.isin(top.pert_id)]
    heat = condition.pivot_table(index="drug_name", columns="dose", values="WTCS_median", aggfunc="first")
    numeric_cols = sorted(heat.columns, key=lambda value: float(str(value).split()[0]))
    heat = heat[numeric_cols].reindex(matrix.sort_values("rank").drug_name)
    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=200)
    values = np.ma.masked_invalid(heat.to_numpy(dtype=float))
    dose_cmap = plt.get_cmap("RdBu_r").copy()
    dose_cmap.set_bad("#e7ebef")
    image = ax.imshow(values, aspect="auto", cmap=dose_cmap, vmin=-0.6, vmax=0.6)
    ax.set_xticks(range(len(numeric_cols)), numeric_cols, rotation=35, ha="right")
    ax.set_yticks(range(len(heat.index)), heat.index)
    ax.set_title("Top 10 · 24 h WTCS by dose (separate conditions; blank = no QC-passed signature)")
    fig.colorbar(image, ax=ax, label="Median WTCS")
    fig.tight_layout()
    fig.savefig(figures / "final_top10_dose_sensitivity.png", bbox_inches="tight")
    plt.close(fig)

    # Figure 3: availability only; not a score and not used for ranking.
    availability_cols = {
        "Exp010 external S1": matrix.external_S1_same_condition_rank.notna(),
        "PRISM ER+": matrix.PRISM_ERpos_mean_sensitivity.notna(),
        "Neo4j exact drug": matrix.Neo4j_exact_InChIKey_status.eq("exact InChIKey"),
        "direct targets": matrix.Neo4j_direct_target_count.gt(0),
        "target-S1 pathways": matrix.Neo4j_target_to_S1_pathway_rows.gt(0),
        "target COMPZ": matrix.target_S2_compz_measured.gt(0),
    }
    availability = np.column_stack([availability_cols[k].astype(int) for k in availability_cols])
    fig, ax = plt.subplots(figsize=(9, 5.4), dpi=200)
    ax.imshow(availability, cmap=plt.matplotlib.colors.ListedColormap(["#e7ebef", "#568a83"]), aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(len(availability_cols)), list(availability_cols), rotation=30, ha="right")
    ax.set_yticks(range(len(matrix)), [f"{r.rank}. {r.drug_name}" for r in matrix.itertuples(index=False)])
    for i in range(availability.shape[0]):
        for j in range(availability.shape[1]):
            ax.text(j, i, "Y" if availability[i, j] else "—", ha="center", va="center", color="white" if availability[i, j] else "#6f7881", fontsize=8)
    ax.set_title("Evidence availability for ranked candidates (coverage only)")
    fig.tight_layout()
    fig.savefig(figures / "final_evidence_coverage.png", bbox_inches="tight")
    plt.close(fig)

    candidate_notes = {
        "ponatinib": "Neo4j 精确 InChIKey 匹配；ABL1、FGFR/KDR/KIT/SRC 等直接靶点中有 S1 差异基因，部分靶点连接到 S1 Hallmark/富集路径。可提出多靶点激酶信号假设；不同靶点的 S1 方向并不一致。",
        "mocetinostat": "Neo4j 精确匹配；HDAC1/2/3 等靶点连接染色质调控、雌激素依赖基因表达等路径；HDAC1 在 S1 上调。与表观遗传调控相关的机制假设可追踪，但不能据此断定乳腺癌治疗作用。",
        "MK-2461": "当前 Neo4j 无精确 InChIKey 映射，故该图谱不提供此候选的直接靶点或 S1 路径证据。外部原始研究报告其为 c-MET/MET 激酶抑制剂；这是一般药理依据，不是本项目 ER+ 证据。",
        "doxorubicin": "Neo4j 精确匹配；图谱记录 TOP2A 及多种代谢/转运关系，并连接 DNA 复制、细胞周期等 S1 富集路径。TOP2A 在 S1 上调。它的普遍细胞毒性不能解释为 ER+ 特异机制。",
        "rebastinib": "当前 Neo4j 无精确 InChIKey 映射。文献支持其为 switch-control 多靶点激酶抑制剂，涉及 BCR-ABL1、FLT3/TIE2 等；只能作为外部药理机制背景，未在当前图谱与 S1 建立可审计路径。",
        "PHA-767491": "当前 Neo4j 无精确 InChIKey 映射。文献支持 CDC7 抑制和 CDK9 共靶作用，分别联系 DNA 复制起始和转录/MCL1 调控；当前工程没有候选特异的图谱路径或靶点表达证据。",
        "iniparib": "Neo4j 仅记录 PARP1 的一般 TARGET 关系，没有 INHIBITOR 断言。PARP1 在 S1 上调；但原始研究指出 iniparib 在完整细胞中缺乏有力 PARP 抑制证据。因此不能将此候选解释为已验证的 PARP 抑制逆转机制。",
        "balaglitazone": "Neo4j 精确匹配，记录 PPARG 部分激动作用；PPARG 在 S1 下调，关联脂质代谢/脂肪生成路径。S1 方向相反并不证明激动剂能逆转疾病状态，需作为机制假设而非支持性疗效证据。",
        "PFI-1": "当前 Neo4j 无精确 InChIKey 映射。文献支持其抑制 BET 溴结构域与乙酰化组蛋白相互作用、改变转录及细胞周期；此为外部机制背景，未与本工程 S1 建立直接 KG 路径。",
        "JNJ-26481585": "当前 Neo4j 无精确 InChIKey 映射。其又名 quisinostat，外部研究支持 HDAC 抑制和组蛋白乙酰化变化；缺少本项目的精确图谱靶点及 S1 通路证据。",
    }
    report_lines = [
        "# Final03 Top 10 机制证据包", "",
        "## 解读边界", "",
        "Top 10 顺序来自修正后的 S2 WTCS 主实验；本报告不按图谱覆盖度、文献数量或 PRISM 结果调整顺序。WTCS 是表达逆关联，不代表药效。Neo4j 靶点/通路是来源数据库关系与本项目 S1 的可追溯交汇；对无精确结构映射的药物，只记录外部文献机制，不把名称相似视为图谱映射。",
        "直接靶点 COMPZ 是 LINCS 目标基因转录量方向的描述，不证明药物与靶点结合或抑制。当前 Neo4j 没有可审计 PPI 关系，未扩展 PPI 层。",
        "",
        "## 按 S2 排名逐药解释", "",
    ]
    for r in matrix.itertuples(index=False):
        links = LITERATURE.get(str(r.drug_name), [])
        link_text = "；".join(f"[机制文献 {i+1}]({u})" for i, u in enumerate(links)) if links else "无已登记机制文献链接"
        report_lines += [
            f"### {r.rank}. {r.drug_name}（{r.pert_id}）", "",
            f"- S2：WTCS={r.WTCS_median:.4f}，{int(r.n_signatures)} 条签名；24 h 合格剂量中 {int(r.n_24h_dose_conditions)} 个条件，{r.negative_dose_fraction:.0%} 条件 WTCS<0。",
            f"- 独立证据：Exp010 同剂量排名 {r.external_S1_same_condition_rank if pd.notna(r.external_S1_same_condition_rank) else 'NA'}；PRISM ER+ 平均敏感性 {r.PRISM_ERpos_mean_sensitivity if pd.notna(r.PRISM_ERpos_mean_sensitivity) else 'NA'}（{int(r.PRISM_ERpos_cell_lines) if pd.notna(r.PRISM_ERpos_cell_lines) else 0} 个 ER+ 细胞系）。PRISM 与 WTCS 是不同终点。",
            f"- 图谱证据：{r.Neo4j_exact_InChIKey_status}；直接靶点 {int(r.Neo4j_direct_target_count)} 个；与 S1 显著差异基因相交 {int(r.S1_DEG_direct_target_count)} 个；target→S1 pathway 关系 {int(r.Neo4j_target_to_S1_pathway_rows)} 行。",
            f"- 潜在机制/证据边界：{candidate_notes.get(str(r.drug_name), '当前未形成可审计的候选特异机制路径。')}",
            f"- 外部机制来源：{link_text}。这些来源解释的是药物一般药理机制，不证明在 ER+ 乳腺癌中有效。",
            f"- 可追溯 Neo4j Evidence ID：{r.target_evidence_ids if r.target_evidence_ids else '当前 GraphBuild 无直接靶点 Evidence ID'}。",
            "",
        ]
    report_lines += [
        "## 汇总", "",
        f"Top10 中 {int(mapping.neo4j_mapping.eq('exact InChIKey').sum())}/10 个药物在当前 Neo4j 有精确 InChIKey 药物节点；其中 {int(targets.pert_id.nunique())}/10 有当前 GraphBuild 的直接靶点关系，{int(paths.pert_id.nunique())}/10 有靶点到本项目 S1 富集通路的关系。未匹配表示当前图谱构建未覆盖，不等于该药物没有已知靶点。",
        "多数 Top10 条目仅由单条合格 signature 支持，且不同剂量可改变 WTCS 方向；优先视作需进一步实验验证的筛选命中。没有细胞/动物/临床因果验证时，不能称为推荐治疗药物。",
        "",
        "## 关键来源链接", "",
        "- GSE70138 / LINCS Level 5 与本项目所有参数、文件 hash：`final_data_manifest.json`。",
        "- Neo4j 精确映射、靶点、S1 pathway link 和原始 source_assertion / Evidence ID：`mechanism/` 目录下三张 CSV。",
        "- PRISM 终点和实验设计：Exp011 报告与其原始结果；外部 S1：Exp010 报告。",
        "- 逐药主分数、剂量稳定性和外部证据表：`results/final_top10_evidence_matrix.csv`。",
    ]
    (OUT / "reports" / "final_top10_mechanism_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    # Machine-readable page data, generated from the same final evidence table.
    page = {"project_id": "3f18f4c1-713d-58c5-8a53-38eca5a5aaf9", "generated_utc": datetime.now(timezone.utc).isoformat(),
            "status": "PASS", "protocol": "BING Top100 UP/DOWN; MCF7 trt_cp; 24 h; CC≥0.2; maximum-coverage dose; WTCS median per pert_id/condition",
            "ranking_caveat": "WTCS<0 is inverse expression association, not drug efficacy; graph/PRISM/external evidence do not affect rank",
            "candidates": [dict(row, mechanism_summary=candidate_notes.get(str(row["drug_name"]), "当前未形成可审计的候选特异机制路径。"))
                           for row in matrix.astype(object).where(pd.notna(matrix), None).to_dict(orient="records")],
            "evidence_priority": evidence_priority[["rank", "pert_id", "drug_name", "evidence_coverage_only_order", "Neo4j_direct_target_count", "Neo4j_target_to_S1_pathway_rows"]].astype(object).where(pd.notna(evidence_priority[["rank", "pert_id", "drug_name", "evidence_coverage_only_order", "Neo4j_direct_target_count", "Neo4j_target_to_S1_pathway_rows"]]), None).to_dict(orient="records")}
    public = ROOT / "frontend" / "public"
    public.mkdir(exist_ok=True)
    (public / "final-results.json").write_text(json.dumps(page, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    shutil.copy2(result / "final_top10.csv", public / "final-top10.csv")
    shutil.copy2(result / "final_top10_evidence_matrix.csv", public / "final-evidence-matrix.csv")
    for name in ("final_top10_wtcs.png", "final_top10_dose_sensitivity.png", "final_evidence_coverage.png"):
        shutil.copy2(figures / name, public / name)

    inputs = [result / "final_top10.csv", result / "final_signature_scores.csv", result / "final_drug_condition_summary.csv",
              ROOT / "experiments" / "exp010_external_s1" / "results" / "external_s1_drug_ranking.csv",
              ROOT / "experiments" / "exp011_prism_validation" / "results" / "candidate_sensitivity_results.csv",
              mechanism / "final_neo4j_drug_mapping.csv", mechanism / "final_neo4j_direct_targets.csv",
              mechanism / "final_neo4j_s1_pathway_links.csv", mechanism / "final_top10_target_s2_expression.csv"]
    outputs = [result / "final_top10_evidence_matrix.csv", result / "evidence_priority_candidates.csv",
               OUT / "reports" / "final_top10_mechanism_report.md", figures / "final_top10_wtcs.png",
               figures / "final_top10_dose_sensitivity.png", figures / "final_evidence_coverage.png", public / "final-results.json",
               public / "final-top10.csv", public / "final-evidence-matrix.csv", public / "final_top10_wtcs.png",
               public / "final_top10_dose_sensitivity.png", public / "final_evidence_coverage.png"]
    manifest = json.loads((result / "final_data_manifest.json").read_text(encoding="utf-8"))
    manifest["mechanism_query"] = json.loads((mechanism / "neo4j_query_manifest.json").read_text(encoding="utf-8"))
    manifest["final_evidence_counts"] = {"top10": len(matrix), "neo4j_exact_drug_nodes": int(mapping.neo4j_mapping.eq("exact InChIKey").sum()),
                                         "top10_with_direct_targets": int(targets.pert_id.nunique()), "top10_with_s1_pathways": int(paths.pert_id.nunique()),
                                         "prism_with_ERpos_result": int(matrix.PRISM_ERpos_mean_sensitivity.notna().sum()),
                                         "external_s1_rank_available": int(matrix.external_S1_same_condition_rank.notna().sum())}
    manifest["supplemental_input_sha256"] = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    manifest["final_output_sha256"] = {str(p.relative_to(ROOT)): sha(p) for p in outputs}
    (OUT / "final_data_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (result / "final_data_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "top10": len(matrix), "neo4j_exact": manifest["final_evidence_counts"]["neo4j_exact_drug_nodes"],
                      "targets": manifest["final_evidence_counts"]["top10_with_direct_targets"], "s1_pathways": manifest["final_evidence_counts"]["top10_with_s1_pathways"],
                      "prism": manifest["final_evidence_counts"]["prism_with_ERpos_result"], "external_s1": manifest["final_evidence_counts"]["external_s1_rank_available"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
