"""v4 discovery run.

Implements reports/protocol_v4_discovery.md exactly: four-algorithm median-rank
aggregation (no weights), dose gates identical to v2, a 3-of-4 consensus gate,
1,000-replicate dose bootstrap, and a direction-coherent mechanism chain gate.
External S1 and PRISM never enter the ranking.

Outputs are written only if the pre-registered protocol file already exists.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mechanism import MechanismScorer  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
EXP = Path(__file__).resolve().parents[1]
OUT = EXP / "results"
ALGOS = ["WTCS", "Classic_KS", "Zhang_signed_rank", "XSum_zscore_adaptation"]
N_BOOT = 1000
SEED = 20261120
CONSENSUS_MIN = 3
CONSENSUS_P = 0.70
STABILITY_LADDER = [0.70, 0.60, 0.50, None]
TOP_N = 20


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pct_against(value: float, ref_sorted: np.ndarray) -> float:
    """Reversal percentile against a frozen reference distribution."""
    n = len(ref_sorted)
    if n <= 1:
        return 1.0
    less = np.searchsorted(ref_sorted, value, side="left")
    equal = np.searchsorted(ref_sorted, value, side="right") - less
    rank = less + (equal + 1) / 2.0
    return float(1.0 - (rank - 1.0) / (n - 1.0))


def main() -> int:
    spec = EXP / "reports/protocol_v4_discovery.md"
    if not spec.exists():
        raise RuntimeError("v4 protocol must be written before execution")

    # Use the exact method score snapshot that produced the validated v4
    # baseline. Other project branches may contain same-shaped, but different,
    # scores and would produce a distinct ranking.
    exp008 = pd.read_csv(EXP / "inputs/method_signature_scores.csv")
    exp008 = exp008[(exp008.scheme == "B200") & (exp008.dose != "0.0 um")]
    pivot = exp008.pivot_table(index=["sig_id", "pert_id", "dose"], columns="method",
                               values="score", aggfunc="first").reset_index()
    missing = [a for a in ALGOS if a not in pivot.columns]
    if missing:
        raise RuntimeError(f"missing algorithms: {missing}")

    doses = (pivot.groupby(["pert_id", "dose"], as_index=False)
             .agg({a: "median" for a in ALGOS}))
    n_doses = doses.groupby("pert_id").size()
    structural_ids = set(n_doses[n_doses >= 3].index)
    doses = doses[doses.pert_id.isin(structural_ids)].copy()
    if len(structural_ids) != 652:
        raise RuntimeError(f"structural pool is {len(structural_ids)}, protocol expects 652")

    drug = doses.groupby("pert_id", as_index=False).agg(
        n_dose_conditions=("dose", "nunique"),
        **{f"{a}_dose_median": (a, "median") for a in ALGOS},
        **{f"{a}_neg_frac": (a, lambda v: float((v < 0).mean())) for a in ALGOS},
        WTCS_dose_min=("WTCS", "min"),
        WTCS_dose_max=("WTCS", "max"),
        WTCS_dose_iqr=("WTCS", lambda v: float(np.percentile(v, 75) - np.percentile(v, 25))),
    )
    drug["strong_flip"] = ((drug.WTCS_dose_max >= 0.20) & (drug.WTCS_dose_min <= -0.20)).astype(int)

    gates = {
        "dose_ge_3": drug.n_dose_conditions.ge(3),
        "wtcs_neg_frac": drug.WTCS_neg_frac.ge(0.6),
        "ks_neg_frac": drug.Classic_KS_neg_frac.ge(0.6),
        "wtcs_neg_median": drug.WTCS_dose_median.lt(0),
        "ks_neg_median": drug.Classic_KS_dose_median.lt(0),
        "no_strong_flip": drug.strong_flip.eq(0),
    }
    for name, values in gates.items():
        drug[f"gate_{name}"] = values.astype(bool)
    gate_cols = [c for c in drug.columns if c.startswith("gate_")]
    drug["dose_gates_passed"] = drug[gate_cols].all(axis=1)

    refs = {a: np.sort(drug[f"{a}_dose_median"].to_numpy(dtype=float)) for a in ALGOS}
    for a in ALGOS:
        drug[f"p_{a}"] = [pct_against(v, refs[a]) for v in drug[f"{a}_dose_median"]]
    pcols = [f"p_{a}" for a in ALGOS]
    drug["S_disc"] = drug[pcols].median(axis=1)
    drug["algorithm_consensus"] = (drug[pcols] >= CONSENSUS_P).sum(axis=1).ge(CONSENSUS_MIN)

    names = (pd.read_csv(ROOT / "experiments/final_results/results/final_signature_scores.csv")[["pert_id", "drug_name"]]
             .drop_duplicates("pert_id"))
    drug = drug.merge(names, on="pert_id", how="left")
    eligible = drug[drug.dose_gates_passed & drug.algorithm_consensus].copy().reset_index(drop=True)
    if len(eligible) == 0:
        raise RuntimeError("no eligible drugs; check the consensus gate")

    # ---- dose bootstrap ----
    rng = np.random.default_rng(SEED)
    dose_groups = {pid: grp for pid, grp in doses.groupby("pert_id")}
    elig_ids = eligible.pert_id.tolist()
    counts = {pid: 0 for pid in elig_ids}
    k = min(TOP_N, len(elig_ids))
    for _ in range(N_BOOT):
        scores = np.empty(len(elig_ids))
        for i, pid in enumerate(elig_ids):
            grp = dose_groups[pid]
            idx = rng.integers(0, len(grp), len(grp))
            sample = grp.iloc[idx]
            ps = [pct_against(float(np.median(sample[a])), refs[a]) for a in ALGOS]
            scores[i] = float(np.median(ps))
        order = np.argsort(-scores, kind="stable")[:k]
        for i in order:
            counts[elig_ids[i]] += 1
    eligible["stability_top20"] = eligible.pert_id.map(lambda p: counts[p] / N_BOOT)

    ladder_counts: dict[str, int] = {}
    chosen = None
    pool = None
    for rung in STABILITY_LADDER:
        sub = eligible if rung is None else eligible[eligible.stability_top20.ge(rung)]
        ladder_counts["no_gate" if rung is None else f"{rung:.2f}"] = int(len(sub))
        if chosen is None and len(sub) >= TOP_N:
            chosen = rung
            pool = sub
    if pool is None:
        pool = eligible
    used_rung = "no_gate" if chosen is None else f"{chosen:.2f}"

    ranked = pool.sort_values(["S_disc", "stability_top20", "WTCS_dose_median", "pert_id"],
                              ascending=[False, False, True, True], kind="stable").reset_index(drop=True)
    ranked["rank_v4"] = np.arange(1, len(ranked) + 1)
    top20 = ranked.head(TOP_N).copy()

    # ---- mechanism chains ----
    scorer = MechanismScorer(ROOT)
    chain_rows: list[dict[str, object]] = []
    drug_flags = []
    for pid in ranked.pert_id:
        r = scorer.score(pid)
        chains = scorer.chains(pid)
        chain_rows.extend(chains)
        drug_flags.append({
            "pert_id": pid,
            "prism_status": r.prism_status,
            "prism_delta": r.prism_delta,
            "n_chains": len(chains),
            "n_er_chains": sum(1 for c in chains if c["er_program"]),
            "chain_targets": "; ".join(sorted({str(c["target"]) for c in chains})),
            "chain_pathways": "; ".join(sorted({p for c in chains for p in str(c["pathways"]).split("; ")})),
            "in_graph": bool(r.graph_drug_id),
            "inchi_key": r.inchi_key,
        })
    flags = pd.DataFrame(drug_flags)
    ranked = ranked.merge(flags, on="pert_id", how="left", validate="one_to_one")
    top20 = ranked.head(TOP_N).copy()

    chains = pd.DataFrame(chain_rows)

    # ---- mechanism Top10 (A) ----
    with_chain = ranked[ranked.n_chains > 0].sort_values(
        ["S_disc", "stability_top20", "pert_id"], ascending=[False, False, True], kind="stable"
    ).reset_index(drop=True)
    mech_top10 = with_chain.head(10).copy()
    mech_top10["rank_mech"] = np.arange(1, len(mech_top10) + 1)
    mech_top10["from_top20"] = mech_top10.rank_v4.le(TOP_N)

    # ---- core C: chain + PRISM not anti ----
    core_c = ranked[(ranked.n_chains > 0) & (ranked.prism_status != "anti_er_positive")].sort_values(
        "S_disc", ascending=False, kind="stable").reset_index(drop=True)
    core_c["rank_core_c"] = np.arange(1, len(core_c) + 1)

    drug.to_csv(OUT / "v4_drug_scores.csv", index=False)
    eligible.to_csv(OUT / "v4_eligible.csv", index=False)
    ranked.to_csv(OUT / "v4_ranked_pool.csv", index=False)
    top20.to_csv(OUT / "v4_top20.csv", index=False)
    mech_top10.to_csv(OUT / "v4_mechanism_top10.csv", index=False)
    core_c.to_csv(OUT / "v4_core_c.csv", index=False)
    chains.to_csv(OUT / "v4_chains.csv", index=False)

    input_paths = {
        "method_signature_scores.csv": EXP / "inputs/method_signature_scores.csv",
        "final_signature_scores.csv": ROOT / "experiments/final_results/results/final_signature_scores.csv",
        "candidate_sensitivity_results.csv": ROOT / "experiments/exp011_prism_validation/results/candidate_sensitivity_results.csv",
        "limma_significant_genes_FDR05.csv": ROOT / "s1_初步_gse42568_limma/limma_significant_genes_FDR05.csv",
        "limma_all_genes.csv": ROOT / "s1_初步_gse42568_limma/limma_all_genes.csv",
        "pathway_gene_links.csv": ROOT / "experiments/s1_pathway_enrichment/pathway_gene_links.csv",
        "graph_bundle_manifest.json": ROOT / "data/processed/projects/3f18f4c1-713d-58c5-8a53-38eca5a5aaf9/graph_bundle/runs/e0421796-2aff-47e2-9228-d683eab05fa9/bundle_manifest.json",
        "graph_subgraph_nodes.csv": ROOT / "data/processed/projects/3f18f4c1-713d-58c5-8a53-38eca5a5aaf9/graph_bundle/runs/e0421796-2aff-47e2-9228-d683eab05fa9/subgraph_nodes.csv",
        "graph_subgraph_edges.csv": ROOT / "data/processed/projects/3f18f4c1-713d-58c5-8a53-38eca5a5aaf9/graph_bundle/runs/e0421796-2aff-47e2-9228-d683eab05fa9/subgraph_edges.csv",
        "graph_evidence_records.csv": ROOT / "data/processed/projects/3f18f4c1-713d-58c5-8a53-38eca5a5aaf9/graph_bundle/runs/e0421796-2aff-47e2-9228-d683eab05fa9/evidence_records.csv",
        "graph_candidate_mapping_audit.csv": ROOT / "data/processed/projects/3f18f4c1-713d-58c5-8a53-38eca5a5aaf9/graph_bundle/runs/e0421796-2aff-47e2-9228-d683eab05fa9/candidate_mapping_audit.csv",
    }
    missing_inputs = [name for name, path in input_paths.items() if not path.is_file()]
    if missing_inputs:
        raise FileNotFoundError(f"v4 required inputs missing: {missing_inputs}")

    manifest = {
        "status": "PASS",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": "v4 discovery (reports/protocol_v4_discovery.md)",
        "spec_sha256": sha256(spec),
        "input_sha256": {name: sha256(path) for name, path in input_paths.items()},
        "algorithms": ALGOS,
        "seed": SEED,
        "bootstrap_replicates": N_BOOT,
        "stability_rung_used": used_rung,
        "stability_ladder_counts": ladder_counts,
        "counts": {
            "discovery_queue": int(pd.read_csv(ROOT / "experiments/final_results/results/final_signature_scores.csv")["pert_id"].nunique()),
            "four_algorithm_coverage": int(exp008["pert_id"].nunique()),
            "structural_pool": int(len(structural_ids)),
            "dose_gates_passed": int(drug.dose_gates_passed.sum()),
            "eligible_after_consensus": int(len(eligible)),
            "ranked_pool": int(len(ranked)),
            "top20": int(len(top20)),
            "with_chain_top20": int((top20.n_chains > 0).sum()),
            "mechanism_top10": int(len(mech_top10)),
            "core_c": int(len(core_c)),
        },
        "outputs": {name: sha256(OUT / name) for name in [
            "v4_drug_scores.csv", "v4_eligible.csv", "v4_ranked_pool.csv",
            "v4_top20.csv", "v4_mechanism_top10.csv", "v4_core_c.csv", "v4_chains.csv",
        ]},
    }
    (OUT / "v4_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# v4 发现版结果\n",
        f"- 预注册规则：`protocol_v4_discovery.md`（SHA-256 `{manifest['spec_sha256'][:16]}…`）。",
        f"- 结构池 {len(structural_ids)} 个药物；过剂量门槛 {int(drug.dose_gates_passed.sum())} 个；"
        f"再过「3/4 算法 ≥0.70」共识门槛 **{len(eligible)}** 个。",
        f"- 免权重发现分：`S_disc = median(p_WTCS, p_ClassicKS, p_Zhang, p_XSum)`。",
        f"- 剂量 bootstrap（{N_BOOT} 次，种子 {SEED}）后，稳定性门槛使用 **{used_rung}**；"
        f"各级存活数：{ladder_counts}。",
        f"- 稳定性分布：≥0.70 的 {int(eligible.stability_top20.ge(0.70).sum())} 个、"
        f"0.50–0.70 的 {int(((eligible.stability_top20 >= 0.50) & (eligible.stability_top20 < 0.70)).sum())} 个、"
        f"<0.50 的 {int(eligible.stability_top20.lt(0.50).sum())} 个。",
        f"- v4 Top20 中**有方向一致机制链的只有 {int((top20.n_chains > 0).sum())} 个**。",
        f"- 机制可解释 Top10（A 方案）输出 **{len(mech_top10)}** 个（其中 {int(mech_top10.from_top20.sum())} 个来自 Top20，"
        f"{int((~mech_top10.from_top20).sum())} 个为按协议扩展自 Top20 之外）；高置信核心集（C 方案）**{len(core_c)}** 个。\n",
        "## 四算法一致性\n",
        f"- 四种算法的药物级中位数两两 Spearman：见 `v4_drug_scores.csv`；`S_disc` 与 WTCS 单独排序的秩相关 = "
        f"{ranked[['S_disc','p_WTCS']].corr(method='spearman').iloc[0,1]:.3f}。",
        f"- 共识门槛（≥3/4 算法前 30%）淘汰了 {int((drug.dose_gates_passed & ~drug.algorithm_consensus).sum())} 个已过剂量门槛的药物。\n",
        "## v4 Top20\n",
        "| # | 药物 | `S_disc` | 稳定性 | 链数 | ER+ 链 | PRISM |",
        "| ---: | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in top20.itertuples():
        lines.append(f"| {row.rank_v4} | {row.drug_name} | {row.S_disc:.3f} | {row.stability_top20:.2f} | "
                     f"{row.n_chains} | {row.n_er_chains} | {row.prism_status} |")
    lines += [
        "\n## 机制可解释 Top10（A 方案）\n",
        "| # | 药物 | v4 名次 | `S_disc` | 链数 | ER+ 链 | PRISM 方向 | 链靶点 |",
        "| ---: | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in mech_top10.itertuples():
        lines.append(f"| {row.rank_mech} | {row.drug_name} | {row.rank_v4} | {row.S_disc:.3f} | {row.n_chains} | "
                     f"{row.n_er_chains} | {row.prism_status} | {row.chain_targets} |")
    lines += [
        "\n## 高置信核心集（C 方案）\n",
        "| # | 药物 | v4 名次 | `S_disc` | 链数 | ER+ 链 | PRISM 差值 |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in core_c.itertuples():
        lines.append(f"| {row.rank_core_c} | {row.drug_name} | {row.rank_v4} | {row.S_disc:.3f} | {row.n_chains} | "
                     f"{row.n_er_chains} | {getattr(row, 'prism_delta', float('nan')):.3f} |")
    lines += [
        "\n## 与 v3 交付版的关系\n",
        "- v4 不使用外部 S1 与 PRISM 排序，因此这两项在 v4 中只是标签；v3 用它们做过资格门槛。",
        "- v4 的机制层是「方向一致链」门槛，不是注释密度打分；因此机制 Top10 与 v3 的名单会明显不同。",
        "- 所有结果仍是计算优先级，不是疗效或临床结论；没有链的候选是知识覆盖不足，不是无效。",
    ]
    (EXP / "reports" / "v4_report.md").write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        "status": "PASS",
        "counts": manifest["counts"],
        "stability_rung": used_rung,
        "top20": top20[["rank_v4", "pert_id", "S_disc", "stability_top20", "n_chains", "prism_status"]].round(3).to_dict("records"),
        "mech_top10": mech_top10[["rank_mech", "pert_id", "rank_v4", "S_disc", "n_chains", "n_er_chains"]].round(3).to_dict("records"),
        "core_c": core_c[["rank_core_c", "pert_id", "S_disc", "n_chains", "prism_status"]].round(3).to_dict("records"),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

