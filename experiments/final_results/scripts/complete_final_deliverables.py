from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "experiments" / "final_results"
RESULT = OUT / "results"
MECH = OUT / "mechanism"
REPORT = OUT / "reports"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def split_ids(value: object) -> list[str]:
    if value is None or pd.isna(value):
        return []
    return [part.strip() for part in re.split(r"[;,]", str(value)) if part.strip()]


def json_load(value: object) -> dict:
    if value is None or pd.isna(value) or not str(value).strip():
        return {}
    try:
        parsed = json.loads(str(value))
        return parsed if isinstance(parsed, dict) else {}
    except (ValueError, TypeError):
        return {}


def clean(value: object) -> str:
    return "—" if value is None or pd.isna(value) or str(value) == "nan" else str(value)


def main() -> None:
    top = pd.read_csv(RESULT / "final_top10.csv")
    matrix = pd.read_csv(RESULT / "final_top10_evidence_matrix.csv")
    targets = pd.read_csv(MECH / "final_neo4j_direct_targets.csv")
    paths = pd.read_csv(MECH / "final_neo4j_s1_pathway_links.csv")
    derived_columns = [
        "Exp006_rank_A_historical", "Exp006_rank_B_historical", "Exp006_24h_Q2_dose_count", "Exp006_negative_dose_fraction",
        "Exp006_dose_stability", "Exp006_QC_sensitivity_range", "Exp006_stability_grade", "Exp006_stability_limitations",
        "empirical_pvalue_B200_historical", "BH_FDR_B200_historical", "permutation_count_B200_historical", "permutation_statistics_scope",
    ]
    derived_columns += [c for c in matrix.columns if str(c).startswith("Exp007_rank_")]
    matrix = matrix.drop(columns=[c for c in derived_columns if c in matrix.columns])

    # Join previously completed method/stability analyses without using them to change the S2 rank.
    stability = pd.read_csv(ROOT / "experiments" / "exp006_ranking_reliability" / "results" / "candidate_drugs_top50.csv")
    stability = stability[["pert_id", "rank_A", "rank_B", "n_available_doses", "negative_dose_fraction", "dose_stability", "qc_sensitivity_range", "stability_grade", "evidence_limitations"]].rename(columns={
        "rank_A": "Exp006_rank_A_historical", "rank_B": "Exp006_rank_B_historical", "n_available_doses": "Exp006_24h_Q2_dose_count",
        "negative_dose_fraction": "Exp006_negative_dose_fraction", "dose_stability": "Exp006_dose_stability",
        "qc_sensitivity_range": "Exp006_QC_sensitivity_range", "stability_grade": "Exp006_stability_grade",
        "evidence_limitations": "Exp006_stability_limitations",
    })
    matrix = matrix.merge(stability, on="pert_id", how="left", validate="one_to_one")

    qvalues = pd.read_csv(ROOT / "experiments" / "exp008_scoring_statistics" / "results" / "empirical_pvalues.csv")
    qvalues = qvalues[(qvalues.scheme == "B200") & (qvalues.cell_id == "MCF7") & (qvalues.pert_type.eq("trt_cp") if "pert_type" in qvalues.columns else True)]
    qvalues = qvalues[qvalues.dose.eq("10.0 um") & qvalues.time.eq("24 h")][["pert_id", "empirical_pvalue", "adjusted_pvalue", "permutation_count"]].rename(columns={
        "empirical_pvalue": "empirical_pvalue_B200_historical", "adjusted_pvalue": "BH_FDR_B200_historical",
        "permutation_count": "permutation_count_B200_historical",
    })
    matrix = matrix.merge(qvalues, on="pert_id", how="left", validate="one_to_one")
    matrix["permutation_statistics_scope"] = "Historical Exp008 B200 permutation table (2,000 permutations); NA means this pert_id-condition was not tested there; not recomputed for the corrected 5,861-signature set."

    rankings = pd.read_csv(ROOT / "experiments" / "exp007_signature_sensitivity" / "results" / "condition_rankings.csv")
    rankings = rankings[(rankings.cell_id == "MCF7") & (rankings.pert_type == "trt_cp") & (rankings.dose == "10.0 um") & (rankings.time == "24 h")]
    rank_schemes = rankings.pivot_table(index="pert_id", columns="scheme", values="rank_condition", aggfunc="first").reset_index()
    rank_schemes.columns.name = None
    rank_schemes = rank_schemes.rename(columns={c: f"Exp007_rank_{c}" for c in rank_schemes.columns if c != "pert_id"})
    matrix = matrix.merge(rank_schemes, on="pert_id", how="left", validate="one_to_one")
    matrix.to_csv(RESULT / "final_top10_evidence_matrix.csv", index=False)

    selection_lines = [
        "# Final02 修正后 Top 10 选择报告", "",
        "固定规则：GSE42568 BING Top100 UP/DOWN；GSE70138 MCF7 trt_cp、24 h、CC≥0.2；统一采用覆盖最多药物的 10 μM 条件；按 pert_id 聚合该条件下 WTCS 中位数，升序排序；按 pert_id 作确定性平局排序。图谱、文献、Exp010 和 PRISM 均不改变 S2 排名。", "",
        "稳定 ID 合并后，共有 5,861 条合格 signature、1,471 个药物；主剂量覆盖 1,032 个化合物。历史名称键漏掉 1,100 条真实可配对签名；Exp009 排序权重错配分数不用于本榜单。", "",
        "## 固定主规则下的 Top10", "",
        "| 排名 | 候选 | pert_id | WTCS | 签名数 | Exp008历史B200经验P | BH FDR |", "|---:|---|---|---:|---:|---:|---:|",
    ]
    for item in matrix.itertuples(index=False):
        p = getattr(item, "empirical_pvalue_B200_historical")
        q = getattr(item, "BH_FDR_B200_historical")
        selection_lines.append(f"| {int(item.rank)} | {item.drug_name} | `{item.pert_id}` | {item.WTCS_median:.4f} | {int(item.n_signatures)} | {clean(p)} | {clean(q)} |")
    selection_lines += [
        "", "经验 P 和 FDR 仅沿用 Exp008 的历史 B200、2,000 次随机基因集置换结果。只有 5/10 个候选在历史分析中存在同剂量记录；另外 5 个保留 NA。该旧置换表没有对新增 stable-ID signature 集重跑，因此不可将历史 FDR 描述成 5,861 条修正数据集的显著性。",
        "", "旧正式榜与修正稳定 ID 榜的 Top10 pert_id 重合 5/10。变化来自修正 ID 覆盖及 Exp009 排序权重 bug；不得解释成药物效应发生改变。Top10 每个候选在主条件均只有一条签名，稳定性有限。"
    ]
    (REPORT / "final_top10_selection_report.md").write_text("\n".join(selection_lines) + "\n", encoding="utf-8")

    # One path row per graph-supported target-to-S1 route; preserve assertion JSON and Evidence IDs.
    path_cols = [c for c in ["rank", "pert_id", "drug_name", "inchi_key", "graph_drug_id", "target_gene_id", "target_symbol",
                             "target_assertion_json", "target_evidence_ids", "s1_direction", "s1_logFC", "s1_FDR", "pathway_id",
                             "pathway_label", "gene_pathway_assertion_json", "gene_pathway_evidence_ids",
                             "disease_context_assertion_json", "disease_context_evidence_ids"] if c in paths.columns]
    top_paths = paths[paths.pert_id.isin(top.pert_id)][path_cols].copy()
    top_paths.to_csv(MECH / "top10_mechanism_paths.csv", index=False)

    citations: list[dict[str, object]] = []
    evidence_matrix = matrix.set_index("pert_id")
    for candidate in top.itertuples(index=False):
        row = evidence_matrix.loc[candidate.pert_id]
        drug_targets = targets[targets.pert_id.eq(candidate.pert_id)]
        drug_paths = paths[paths.pert_id.eq(candidate.pert_id)]
        # Citation rows for graph edges retain relation semantics, source assertions and auditable IDs.
        for target in drug_targets.itertuples(index=False):
            assertion = json_load(target.target_assertion_json)
            rels = assertion.get("relation_assertions") or []
            citations.append({"rank": int(candidate.rank), "pert_id": candidate.pert_id, "drug_name": candidate.drug_name,
                              "evidence_type": "drug_target_relation", "entity_or_claim": f"{target.target_symbol} ({target.target_gene_id})",
                              "relation_semantics": ";".join(str(rel.get("relation", "")) for rel in rels),
                              "source": ";".join(assertion.get("sources", {}).get("direct", []) or []),
                              "evidence_id": target.target_evidence_ids, "source_record_id": assertion.get("source_record_id", ""),
                              "source_url": ";".join(assertion.get("source_urls") or []), "assertion_json": target.target_assertion_json,
                              "interpretation_limit": "Graph relation is source-backed association; relation type does not itself establish therapeutic effect."})
        for path in drug_paths.itertuples(index=False):
            for evidence_type, ids_field, assertion_field in [
                ("target_to_S1_pathway", "gene_pathway_evidence_ids", "gene_pathway_assertion_json"),
                ("disease_context_pathway", "disease_context_evidence_ids", "disease_context_assertion_json"),
            ]:
                assertion_text = getattr(path, assertion_field, "")
                assertion = json_load(assertion_text)
                for evidence_id in split_ids(getattr(path, ids_field, "")):
                    citations.append({"rank": int(candidate.rank), "pert_id": candidate.pert_id, "drug_name": candidate.drug_name,
                                      "evidence_type": evidence_type,
                                      "entity_or_claim": f"{getattr(path, 'target_symbol', '')} → {getattr(path, 'pathway_label', '')} ({getattr(path, 'pathway_id', '')})",
                                      "relation_semantics": "gene-pathway or disease-context association; see assertion_json",
                                      "source": ";".join(assertion.get("sources", {}).get("direct", []) or []),
                                      "evidence_id": evidence_id, "source_record_id": assertion.get("source_record_id", ""),
                                      "source_url": ";".join(assertion.get("source_urls") or []), "assertion_json": assertion_text,
                                      "interpretation_limit": "Pathway overlap is association and does not prove causal mediation by the drug."})
        for url in split_ids(row.get("literature_links", "")):
            citations.append({"rank": int(candidate.rank), "pert_id": candidate.pert_id, "drug_name": candidate.drug_name,
                              "evidence_type": "external_pharmacology_literature", "entity_or_claim": "General pharmacology / target mechanism",
                              "relation_semantics": "literature context; not project-specific efficacy evidence", "source": "External literature or regulator label",
                              "evidence_id": "", "source_record_id": "", "source_url": url, "assertion_json": "",
                              "interpretation_limit": "Supports general mechanism only; it does not verify ER+ breast cancer activity."})
        citations.extend([
            {"rank": int(candidate.rank), "pert_id": candidate.pert_id, "drug_name": candidate.drug_name,
             "evidence_type": "independent_S1_validation", "entity_or_claim": "GSE139038 external S1 ranking",
             "relation_semantics": "independent cohort, same-condition rank", "source": "Exp010",
             "evidence_id": "", "source_record_id": "experiments/exp010_external_s1/results/external_s1_drug_ranking.csv",
             "source_url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE139038", "assertion_json": "",
             "interpretation_limit": f"Rank={clean(row.get('external_S1_same_condition_rank'))}; cohort has 14 paired ER+ patients and external Top10 overlap was 1/10."},
            {"rank": int(candidate.rank), "pert_id": candidate.pert_id, "drug_name": candidate.drug_name,
             "evidence_type": "PRISM_cell_sensitivity", "entity_or_claim": "PRISM ER+ breast cancer cell sensitivity",
             "relation_semantics": "in vitro viability endpoint; not expression reversal", "source": "Exp011 / DepMap PRISM Primary",
             "evidence_id": "", "source_record_id": "experiments/exp011_prism_validation/results/candidate_sensitivity_results.csv",
             "source_url": "https://depmap.org/repurposing/", "assertion_json": "",
             "interpretation_limit": f"ER+ mean sensitivity={clean(row.get('PRISM_ERpos_mean_sensitivity'))}; absent results are missing, not zero."},
        ])
    citations_df = pd.DataFrame(citations)
    citations_df.to_csv(MECH / "top10_evidence_citations.csv", index=False)

    # Add source-backed paths to the page payload so candidate details can drill into raw Evidence IDs.
    public_json = ROOT / "frontend" / "public" / "final-results.json"
    public_evidence_json = ROOT / "frontend" / "public" / "final-evidence-records.json"
    evidence_records: dict[str, dict] = {}
    for citation in citations:
        evidence_id = clean(citation.get("evidence_id"))
        if not evidence_id or evidence_id == "—" or evidence_id in evidence_records:
            continue
        evidence_records[evidence_id] = {
            "evidence_id": evidence_id,
            "source_release": "OptimusKG 3.2 / captured from read-only Neo4j GraphBuild query",
            "source_assertion": json_load(citation.get("assertion_json")),
            "source_url": citation.get("source_url") or None,
            "source_record_id": citation.get("source_record_id") or None,
            "graph_build_id": json.loads((MECH / "neo4j_query_manifest.json").read_text(encoding="utf-8")).get("graph_build_id"),
            "capture_note": "Snapshot comes from the read-only query CSV in this experiment; it is the fallback if the preview graph service does not contain this GraphBuild.",
        }
    public_evidence_json.write_text(json.dumps(evidence_records, ensure_ascii=False, indent=2), encoding="utf-8")
    page = json.loads(public_json.read_text(encoding="utf-8"))
    graph_build_id = json.loads((MECH / "neo4j_query_manifest.json").read_text(encoding="utf-8")).get("graph_build_id")
    for item in page.get("candidates", []):
        pid = item["pert_id"]
        p_rows = top_paths[top_paths.pert_id.eq(pid)]
        item["mechanism_paths"] = [
            {"target_symbol": clean(p.target_symbol), "target_gene_id": clean(p.target_gene_id),
             "pathway_id": clean(p.pathway_id), "pathway_label": clean(p.pathway_label),
             "s1_direction": clean(p.s1_direction), "s1_logFC": None if pd.isna(p.s1_logFC) else float(p.s1_logFC),
             "s1_FDR": None if pd.isna(p.s1_FDR) else float(p.s1_FDR),
             "target_evidence_ids": split_ids(p.target_evidence_ids),
             "pathway_evidence_ids": split_ids(p.gene_pathway_evidence_ids),
             "disease_context_evidence_ids": split_ids(p.disease_context_evidence_ids)}
            for p in p_rows.itertuples(index=False)
        ]
        item["target_evidence_ids_list"] = split_ids(item.get("target_evidence_ids", ""))
    page["graph_build_id"] = graph_build_id
    public_json.write_text(json.dumps(page, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    pd.DataFrame([{"pert_id": r["pert_id"], "drug_name": r["drug_name"], "mechanism_paths": r.get("mechanism_paths", [])} for r in page.get("candidates", [])]).to_json(
        ROOT / "frontend" / "public" / "final-pathways.json", orient="records", force_ascii=False, indent=2)

    report_dir = OUT / "top10_mechanism_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    candidate_notes = {
        "ponatinib": "图谱精确映射显示 ABL1、FGFR/KDR/KIT/SRC 等激酶靶点，其中 FGFR3、RET 在本 S1 上调，KDR、TEK、CYP3A5 在 S1 下调；这形成多靶点信号假设，但靶点方向不一，不能将整条路径解释为单向逆转。",
        "mocetinostat": "图谱记录 HDAC1/2/3/8/11 关联；HDAC1 在 S1 上调，相关 S1 路径涉及染色质调节和雌激素依赖基因表达。属于表观遗传机制假设，尚无 ER+ 乳腺癌因果验证。",
        "MK-2461": "外部原始研究将 MK-2461 描述为 c-MET/MET 激酶抑制剂；本项目 Neo4j 当前版本无精确结构映射，故没有可核验的项目内靶点—S1通路路径。",
        "doxorubicin": "图谱记录 TOP2A 等关系，并连接 DNA 复制、细胞周期路径；TOP2A 在 S1 上调。广谱细胞毒性和 DNA 损伤作用不能解释为 ER+ 特异或通过逆转 S1 起效。",
        "rebastinib": "外部文献描述 switch-control 多靶点激酶抑制机制（如 BCR-ABL1、FLT3/TIE2）；本项目图谱无精确映射，机制仅为外部药理背景。",
        "PHA-767491": "外部研究支持 CDC7 抑制并报告 CDK9 共靶作用，可联系 DNA 复制起始和转录调控；当前图谱未提供候选特异的靶点—S1路径。",
        "iniparib": "本图谱仅有 PARP1 一般 TARGET 关联，未记录抑制语义；外部研究对其完整细胞 PARP 抑制作用提出反证，故不将其解释为已验证 PARP 抑制剂。",
        "balaglitazone": "图谱记录 PPARG 部分激动作用，PPARG 在 S1 下调并关联代谢路径；激动作用并不能简单解释为表达逆转，机制方向存在不确定性。",
        "PFI-1": "外部研究将 PFI-1 作为 BET 溴结构域抑制剂，涉及乙酰化组蛋白读取和转录调节；当前图谱无精确映射，不能声称该作用连接到本项目 S1。",
        "JNJ-26481585": "又名 quisinostat，外部研究支持 HDAC 抑制和组蛋白乙酰化变化；当前图谱无精确映射，缺少项目内靶点和 S1 通路证据。",
    }
    for candidate in top.itertuples(index=False):
        row = evidence_matrix.loc[candidate.pert_id]
        drug_targets = targets[targets.pert_id.eq(candidate.pert_id)]
        drug_paths = top_paths[top_paths.pert_id.eq(candidate.pert_id)]
        sigs = pd.read_csv(RESULT / "final_signature_scores.csv")
        sigs = sigs[sigs.pert_id.eq(candidate.pert_id) & sigs.dose.eq("10.0 um") & sigs.time.eq("24 h")]
        lit = split_ids(row.get("literature_links", ""))
        target_lines = []
        for t in drug_targets.itertuples(index=False):
            assertion = json_load(t.target_assertion_json)
            semantics = ", ".join(str(x.get("relation", "")) for x in assertion.get("relation_assertions", [])) or "unspecified"
            target_lines.append(f"- {t.target_symbol} (`{t.target_gene_id}`): 关系语义 `{semantics}`，来源 `{'; '.join(assertion.get('sources', {}).get('direct', []) or [])}`，Evidence ID `{t.target_evidence_ids}`。S1 direction={clean(t.s1_direction)}; logFC={clean(t.s1_logFC)}; FDR={clean(t.s1_FDR)}。")
        pathway_lines = []
        for p in drug_paths.itertuples(index=False):
            pathway_lines.append(f"- `{p.target_symbol}` → {p.pathway_label} (`{p.pathway_id}`)，S1方向={clean(p.s1_direction)}，GO/Reactome/Hallmark证据 ID `{p.gene_pathway_evidence_ids}`；疾病通路关联 ID `{p.disease_context_evidence_ids}`。")
        candidate_md = f'''# {int(candidate.rank)}. {candidate.drug_name} EvidencePackage

## 候选与 S2 筛选依据

- LINCS perturbagen：`{candidate.pert_id}`；主条件：MCF7 / trt_cp / 10 μM / 24 h / distil_cc_q75≥0.2。
- WTCS={candidate.WTCS_median:.6f}；项目记号 reversal_score={-candidate.WTCS_median:.6f}；签名数={int(candidate.n_signatures)}；签名 ID：{', '.join(sigs.sig_id.astype(str)) if len(sigs) else '未找到'}。
- 历史 B200 置换经验 P={clean(row.get('empirical_pvalue_B200_historical'))}，BH FDR={clean(row.get('BH_FDR_B200_historical'))}，置换数={clean(row.get('permutation_count_B200_historical'))}。该检验只覆盖 Exp008 历史 B200 分析集；NA 表示未在该历史文件测试，不能当成不显著。它不是临床疗效概率。
- Exp006 历史稳定性：A rank={clean(row.get('Exp006_rank_A_historical'))}，B rank={clean(row.get('Exp006_rank_B_historical'))}，稳定性等级={clean(row.get('Exp006_stability_grade'))}；可用 24 h Q2 剂量数={clean(row.get('Exp006_24h_Q2_dose_count'))}，跨剂量负 WTCS 比例={clean(row.get('Exp006_negative_dose_fraction'))}；限制={clean(row.get('Exp006_stability_limitations'))}。
- S1 规模敏感性同条件排名：{'; '.join(f'{c.removeprefix("Exp007_rank_")}={clean(row.get(c))}' for c in row.index if str(c).startswith('Exp007_rank_'))}。全局结果显示 B100/B150/B200/B300 相对原始 A 的 Top10 重合分别为 8/10、7/10、4/10、3/10，故头部名单对 S1 规模敏感。

## 已知靶点和关系语义

精确 InChIKey 图谱映射：{clean(row.get('Neo4j_exact_InChIKey_status'))}；GraphBuild=`{json.loads((MECH / 'neo4j_query_manifest.json').read_text(encoding='utf-8')).get('graph_build_id')}`。仅报告当前构建中存在的关系：

{chr(10).join(target_lines) if target_lines else '- 当前 GraphBuild 无候选药物的精确药物节点/直接靶点关系。外部文献可作为背景，但不等于项目图谱证据。'}

## 靶点到疾病异常通路的证据路径

{chr(10).join(pathway_lines) if pathway_lines else '- 当前图谱未建立可审计的候选靶点到 S1 显著通路路径。'}

当前 S1 富集摘要：肿瘤上调侧突出 DNA replication、E2F/G2M 与 estrogen-response Hallmark；肿瘤下调侧突出氧化代谢、呼吸链/oxidative phosphorylation、脂肪酸代谢等。富集与路径重叠仅为注释关联，不是通路因果证明。

## 独立验证、机制假设与冲突证据

- Exp010 独立队列同条件排名：{clean(row.get('external_S1_same_condition_rank'))}；外部 S1 条件级排序与主排序总体 Spearman=0.544，Top10 重合仅 1/10。
- PRISM ER+ 平均敏感性：{clean(row.get('PRISM_ERpos_mean_sensitivity'))}，细胞系数={clean(row.get('PRISM_ERpos_cell_lines'))}；PRISM 相关性弱且没有显示 ER+ 选择性，不能作为 S2 药效确认。
- 候选机制摘要：{candidate_notes.get(candidate.drug_name, clean(row.get('mechanism_evidence_limit')))}
- 文献链接：{'；'.join(f'[{u}]({u})' for u in lit) if lit else '当前没有逐药外部机制文献登记'}。
- 本项目用确定性证据模板整理解释；未调用 LLM 生成本候选机制正文，因此不把模板内容标为 AI 输出。

## 局限

该药主条件仅由 {int(candidate.n_signatures)} 条 LINCS signature 支持。WTCS 是表达逆关联，不等同药效。靶点关系与机制文献可能来自一般药理，不代表在 ER 阳性乳腺癌中直接成立。当前图谱没有可审计 PPI 边；不推断一层 PPI 扩展。后续需要多签名/剂量的重复、ER+ 模型剂量反应、正常细胞对照和机制实验。

## 可追溯文件

- S2 原始评分：`results/final_signature_scores.csv`（signature ID 可检索）；候选证据：`results/final_top10_evidence_matrix.csv`。
- 图谱关系路径：`mechanism/top10_mechanism_paths.csv`；原始图谱查询结果：`mechanism/final_neo4j_direct_targets.csv`、`mechanism/final_neo4j_s1_pathway_links.csv`。
- 逐条引用登记：`mechanism/top10_evidence_citations.csv`。
'''
        (report_dir / f"{int(candidate.rank):02d}_{candidate.drug_name.replace('/', '_')}.md").write_text(candidate_md, encoding="utf-8")

    summary_lines = ["# Top10 机制证据摘要", "", "排名严格沿用 S2 WTCS 主排名；图谱/PRISM/文献未回调排序。", ""]
    for r in matrix.itertuples(index=False):
        summary_lines.append(f"{int(r.rank)}. **{r.drug_name}** (`{r.pert_id}`)：WTCS={r.WTCS_median:.4f}；KG={r.Neo4j_exact_InChIKey_status}；直接靶点={int(r.Neo4j_direct_target_count)}；S1路径={int(r.Neo4j_target_to_S1_pathway_rows)}行；Exp010 rank={clean(r.external_S1_same_condition_rank)}；PRISM ER+={clean(r.PRISM_ERpos_mean_sensitivity)}。解释：{r.mechanism_evidence_limit}。")
    summary_lines += ["", "## 共性限制", "", "所有 10 个主条件候选各只有一条合格 signature；独立 S1 Top10 重合为 1/10；PRISM 排名与 WTCS 关联弱且未显示 ER+ 选择性。图谱路径为关联证据，候选机制均属假设，未完成因果或疗效验证。"]
    (REPORT / "top10_mechanism_summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    audit = f'''# Final03 机制审计

## 审计范围

- Top10 候选数：{len(top)}；关系查询为只读 Neo4j，限定当前 GraphBuild `{json.loads((MECH / 'neo4j_query_manifest.json').read_text(encoding='utf-8')).get('graph_build_id')}`。
- 药物身份按 LINCS InChIKey 精确匹配；不按名称模糊匹配。10 个药物中 {int(matrix.Neo4j_exact_InChIKey_status.eq('exact InChIKey').sum())} 个精确映射。
- 5 个候选有当前构建直接靶点；5 个有靶点→S1 通路路径。其余是本构建覆盖缺口，不推论其无已知药理靶点。
- 关系语义保留原始断言 JSON 和来源；`TARGET`、`ENZYME`、`TRANSPORTER` 等不是统一的抑制关系。无方向断言时不推断药物抑制靶点。
- 当前关系类型审计未发现有来源支持的 PPI 关系；未做 PPI 扩展。
- 本轮机制正文由确定性模板生成，未调用 LLM。模型 API、prompt 及 LLM 输出因此不适用。

## 关系/机制风险核查

- Iniparib：当前图谱为 PARP1 一般 TARGET 关系；文献反证不支持将其写作已验证 PARP 抑制剂。
- Balaglitazone：PPARG 激动方向与将“PPARG 下调”简单解释为表达反转并不等价，不能称为已证实逆转。
- Doxorubicin：存在 TOP2A/细胞周期关联，但广谱细胞毒性不构成 ER+ 特异证据。
- LINCS COMPZ 目标基因是转录量描述，不是靶标结合/抑制测量。
- 其余候选外部文献机制是一般药理背景；如果项目图谱无精确节点，明确写作未图谱映射。

## 文件完整性

- `top10_mechanism_paths.csv`：所有能从当前图谱核验的候选靶点-S1 通路路径及 assertion/Evidence ID。
- `top10_evidence_citations.csv`：图谱和外部来源逐项登记。
- `top10_mechanism_reports/`：逐药 EvidencePackage 与限制说明。
'''
    (REPORT / "mechanism_audit.md").write_text(audit, encoding="utf-8")

    project_status = f'''# ER 阳性乳腺癌重定位项目状态

更新（UTC）：{datetime.now(timezone.utc).isoformat()}

| 阶段 | 状态 | 说明 |
|---|---|---|
| S1 差异表达与通路 | COMPLETE | GSE42568，limma；7,066 个 FDR<0.05 差异基因，独立通路富集结果已归档。 |
| S2 LINCS 初筛 | COMPLETE | GSE70138 Level 5，stable ID 修正后 5,861 条合格 MCF7 signatures 重算；正式主条件 24 h、10 μM、CC≥0.2。 |
| Exp006–Exp011 可靠性/外部核对 | COMPLETE_WITH_LIMITATIONS | S1 方案/评分法会改变头部；外部 S1 Top10 重合 1/10；PRISM 与 WTCS 排名关联较弱。详见第二轮报告。 |
| Final01 输入与算法审计 | PASS | 历史 ID 联结差异和 Exp009 权重配对 bug 已审计并修复；历史文件只读。 |
| Final02 固定规则 Top10 | PASS | 按 S2 WTCS 生成唯一化合物榜单，不用机制证据事后调排名。 |
| Final03 机制证据 | PARTIAL | 逐药报告、路径和来源均有交付；当前图谱精确覆盖 5/10，机制推断仍需实验验证。 |
| Final04 综合报告和页面 | PASS | React `/final-results` 已接入，候选详情含图谱路径与可点击 Evidence ID；生产构建和数据测试通过。 |
| 药物疗效/因果验证 | NOT_PERFORMED | 未执行新细胞、动物或临床干预实验。Top10 是初步候选，不能称为有效治疗药物。 |

## 当前交付核心

- 正式初步 Top10：`results/final_top10.csv`。
- 总报告：`reports/final_research_report.md`。
- 逐药机制说明：`top10_mechanism_reports/`。
- 路径和引用：`mechanism/top10_mechanism_paths.csv`、`mechanism/top10_evidence_citations.csv`。
- 数据/代码校验清单：`final_results_manifest.json`。

项目最关键的未完成科学工作，是在独立 ER+ 乳腺癌模型中复现候选的表达/生长效应，并检验靶点和机制因果链。
'''
    (REPORT / "final_project_status.md").write_text(project_status, encoding="utf-8")

    # Preserve pre-existing research report; append the mandatory sensitivity and counter-evidence results.
    final_report = REPORT / "final_research_report.md"
    content = final_report.read_text(encoding="utf-8")
    section = '''
## 与 Exp006–Exp011 的稳定性和反证核对

- S1 签名规模会改变 Top10：相对原始方案 A，B100/B150/B200/B300 的 Top10 重合分别为 8/10、7/10、4/10、3/10；本报告锁定 BING UP/DOWN 各 100 的 B200 命名方案作为主分析，不能称为唯一最佳方案。
- WTCS 和其他适配算法会改变头部名单：WTCS 与 Classic KS Top10 重合 3/10；XSum 0/10，Zhang signed-rank 5/10。Exp008 的 Zhang/XSum 是 COMPZ 输入适配，不是原论文 raw logFC 的严格复刻；NCS/Tau 因缺合格官方参考未计算。
- Exp006 中原 B200 Top50 稳定性等级：low 41、medium 7、high 1、insufficient 1。Top10 主剂量每个候选只有一条 signature；这比药物整体排序相关性更能说明个体候选的重复支持有限。
- Exp010 的 14 对外部 ER+ 患者队列：双方显著的 333 个共同基因中 97.3% 方向一致，但全共同基因 logFC Spearman=0.314；外部 S1 下药物排序 Spearman=0.544，Top10 仅重合 1 个。
- Exp011 中 Top50 的 S2 排名与 PRISM ER+ 敏感性排序 Spearman=0.260（95% CI -0.105 至 0.573）；跨 0，排名关系不明确。候选与随机组的整体体外敏感性对照也不能证明 ER+ 选择性；候选 ER+ 减 TNBC 敏感性差为 -0.327（95% CI -0.517 至 -0.145），方向并不支持 ER+ 更敏感。
- 因此最终 Top10 是表达签名筛选结果，不是经过稳定性、外部数据或体外药效共同确认的疗效榜单。支持和冲突证据均在逐药矩阵与报告中保留。
'''
    if "## 与 Exp006–Exp011 的稳定性和反证核对" not in content:
        final_report.write_text(content.rstrip() + "\n\n" + section, encoding="utf-8")

    # Requested final names coexist with the underlying data manifest/status.
    manifest = json.loads((OUT / "final_data_manifest.json").read_text(encoding="utf-8"))
    manifest["mechanism_deliverables"] = {
        "individual_reports": [str(p.relative_to(ROOT)) for p in sorted(report_dir.glob("*.md"))],
        "paths_csv": str((MECH / "top10_mechanism_paths.csv").relative_to(ROOT)),
        "citations_csv": str((MECH / "top10_evidence_citations.csv").relative_to(ROOT)),
        "mechanism_audit": str((REPORT / "mechanism_audit.md").relative_to(ROOT)),
        "mechanism_summary": str((REPORT / "top10_mechanism_summary.md").relative_to(ROOT)),
        "llm_status": "not used; deterministic evidence template",
    }
    manifest["requested_final_artifacts"] = {
        "final_research_report": str(final_report.relative_to(ROOT)) if final_report.exists() else str((REPORT / "final_research_report.md").relative_to(ROOT)),
        "final_project_status": str((REPORT / "final_project_status.md").relative_to(ROOT)),
        "final_results_manifest_alias": str((OUT / "final_results_manifest.json").relative_to(ROOT)),
        "frontend_route": "/final-results",
        "frontend_payload": str(public_json.relative_to(ROOT)),
        "frontend_evidence_fallback": str(public_evidence_json.relative_to(ROOT)),
        "pathway_payload": str((ROOT / "frontend" / "public" / "final-pathways.json").relative_to(ROOT)),
    }
    manifest["final_acceptance"]["extended_evidence_matrix_sha256"] = sha(RESULT / "final_top10_evidence_matrix.csv")
    manifest["final_acceptance"]["mechanism_artifact_sha256"] = {
        str(path.relative_to(ROOT)): sha(path)
        for path in [MECH / "top10_mechanism_paths.csv", MECH / "top10_evidence_citations.csv",
                     REPORT / "mechanism_audit.md", REPORT / "top10_mechanism_summary.md", REPORT / "final_project_status.md", final_report,
                     public_json, public_evidence_json, ROOT / "frontend" / "public" / "final-pathways.json"]
    }
    code_to_hash = {
        "frontend/src/App.tsx": ROOT / "frontend" / "src" / "App.tsx",
        "frontend/src/pages/FinalResultsPage.tsx": ROOT / "frontend" / "src" / "pages" / "FinalResultsPage.tsx",
        "experiments/final_results/scripts/complete_final_deliverables.py": Path(__file__).resolve(),
        "experiments/final_results/tests/test_final_results.py": OUT / "tests" / "test_final_results.py",
    }
    manifest.setdefault("code_sha256", {}).update({name: sha(path) for name, path in code_to_hash.items() if path.is_file()})
    manifest.setdefault("final_acceptance", {}).setdefault("deliverable_sha256", {})[
        "experiments/final_results/reports/final_top10_selection_report.md"
    ] = sha(REPORT / "final_top10_selection_report.md")
    (OUT / "final_data_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (RESULT / "final_data_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "final_results_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "mechanism_path_rows": len(top_paths), "citation_rows": len(citations_df),
                      "individual_reports": len(list(report_dir.glob('*.md'))), "empirical_p_available": int(matrix.empirical_pvalue_B200_historical.notna().sum()),
                      "top10": len(top)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
