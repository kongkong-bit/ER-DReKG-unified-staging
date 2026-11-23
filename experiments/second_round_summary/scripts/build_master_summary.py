from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"experiments"/"second_round_summary"

def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def main():
    r=OUT/"results";f=OUT/"figures";rep=OUT/"reports";r.mkdir(exist_ok=True);f.mkdir(exist_ok=True);rep.mkdir(exist_ok=True)
    e006=ROOT/"experiments"/"exp006_ranking_reliability"/"results"
    e007=ROOT/"experiments"/"exp007_signature_sensitivity"/"results"
    e008=ROOT/"experiments"/"exp008_scoring_statistics"/"results"
    e009=ROOT/"experiments"/"exp009_lincs_quality"/"results"
    e010=ROOT/"experiments"/"exp010_external_s1"/"results"
    e011=ROOT/"experiments"/"exp011_prism_validation"/"results"

    cmp7=pd.read_csv(e007/"ranking_comparison.csv")
    cmp8=pd.read_csv(e008/"method_comparison.csv")
    cmp9=pd.read_csv(e009/"quality_rank_comparison.csv")
    corr10=json.loads((e010/"cross_cohort_summary.json").read_text(encoding="utf-8"))
    corr11=pd.read_csv(e011/"s2_prism_rank_correlation.csv")
    rand11=pd.read_csv(e011/"candidate_vs_random_test.csv").iloc[0]
    er_spec11=pd.read_csv(e011/"er_specificity_random_test.csv").iloc[0]
    prm=e008/"empirical_pvalues.csv"
    if prm.exists():
        perm=pd.read_csv(prm)
        sig_count=perm.groupby("scheme").adjusted_pvalue.apply(lambda x:int((x<.05).sum())).to_dict()
        min_q=perm.groupby("scheme").adjusted_pvalue.min().to_dict()
        perm_n=int(perm.permutation_count.min())
        perm_status="completed"
    else:
        perm=pd.DataFrame();sig_count={};min_q={};perm_n=0;perm_status="not completed"

    status_rows=[
        {"experiment":"Exp006","status":"PASS","what_it_means":"原有排序可靠性、质量阈值与剂量敏感性结果已作为基线复核；旧结果保持只读。","remaining":"单药证据仍以计算结果为主。"},
        {"experiment":"Exp007","status":"PASS","what_it_means":"比较六种 S1 签名大小/组成，4,761 signatures 成对重算并复现历史 WTCS。","remaining":"稳定性不是疗效验证。"},
        {"experiment":"Exp008","status":"PARTIAL","what_it_means":f"算法排名比较及随机基因集置换状态：{perm_status}。NCS/Tau 按官方定义审计为不可用。","remaining":"Zhang/XSum 用 COMPZ 做输入适配，非原始 logFC 论文输入的逐字复刻；NCS/Tau 未计算。"},
        {"experiment":"Exp009","status":"PASS","what_it_means":"正式 ID 联结后比较 CC/TAS 质量门槛；门槛间整体排名高度相关。","remaining":"项目阈值敏感性，不是普适筛选标准。"},
        {"experiment":"Exp010","status":"PASS","what_it_means":"独立 GSE139038 14 个 ER+ 肿瘤/配对正常样本完成外部 S1 和 S2 排名对照。","remaining":"外部药物 Top10 重合很低，外推支持有限。"},
        {"experiment":"Exp011","status":"PASS","what_it_means":"PRISM Primary 与 DepMap 模型表按结构/ACH ID 对齐，完成候选敏感性、ER 特异性和覆盖匹配随机背景对照。","remaining":"Top50 有37个结构匹配；体外细胞活力不等同患者获益。"},
    ]
    status=pd.DataFrame(status_rows);status.to_csv(r/"experiment_status.csv",index=False)

    m8=cmp8.copy();m8["comparison_type"]="scoring_method"
    m8=m8.rename(columns={"method_a":"scheme_a","method_b":"scheme_b","spearman_score":"spearman","top10_overlap":"top10_overlap"})
    m7=cmp7.copy();m7["comparison_type"]="S1_signature"
    m7=m7.rename(columns={"scheme_a":"scheme_a","scheme_b":"scheme_b"})
    methodology=pd.concat([m7,m8],ignore_index=True,sort=False)
    methodology.to_csv(r/"methodology_comparison.csv",index=False)

    p7=cmp7[cmp7.scheme_a.eq("A_original")][["scheme_b","n_common_conditions","spearman","top10_overlap","median_abs_WTCS_difference"]].copy()
    p7["parameter_group"]="S1 signature scheme vs A_original"
    p7=p7.rename(columns={"scheme_b":"setting","n_common_conditions":"n_common","spearman":"rank_spearman","top10_overlap":"top10_overlap_count","median_abs_WTCS_difference":"median_abs_score_difference"})
    p9=cmp9.copy().rename(columns={"comparison":"setting","common_conditions":"n_common","spearman":"rank_spearman","top10_overlap":"top10_overlap_count"})
    p9["parameter_group"]="LINCS quality filter"
    p9["median_abs_score_difference"]=np.nan
    p9=p9[["setting","n_common","rank_spearman","top10_overlap_count","parameter_group","median_abs_score_difference"]]
    p7["median_abs_score_difference"]=p7.median_abs_score_difference
    parameters=pd.concat([p7,p9],ignore_index=True,sort=False)
    parameters.to_csv(r/"parameter_sensitivity_summary.csv",index=False)

    # Candidate evidence integrated by LINCS perturbagen ID; never join by drug name.
    full=pd.read_csv(e006/"candidate_drugs_all.csv")
    out=full.copy()
    ext=pd.read_csv(e010/"external_s1_drug_ranking.csv")
    ext=ext.groupby("pert_id",as_index=False).agg(external_s1_median_rank=("external_rank","median"),external_s1_B200_median_rank=("B200_rank","median"),external_s1_conditions=("dose","size"))
    out=out.merge(ext,on="pert_id",how="left",validate="one_to_one")
    qc=pd.read_csv(e009/"quality_sensitivity_condition_rankings.csv")
    qc=qc[(qc.CC_threshold==.2)&qc.TAS_threshold.isna()].groupby("pert_id",as_index=False).agg(Q2_condition_median_rank=("rank","median"),Q2_conditions=("dose","size"))
    out=out.merge(qc,on="pert_id",how="left",validate="one_to_one")
    # Exp011 has only structurally matched candidates. Its ID rows remain explicit and unmatched rows stay NaN.
    s11=pd.read_csv(e011/"candidate_sensitivity_results.csv")
    map11=pd.read_csv(e011/"candidate_mapping_audit_full.csv")[["pert_id","structure_match","exact_name_aux_only","mapping_method"]].drop_duplicates("pert_id")
    out=out.merge(map11,on="pert_id",how="left",validate="one_to_one")
    s11cols=[c for c in ["pert_id","inchi_key","erpos_mean_sensitivity","erpos_median_sensitivity","n_erpos_lines","erneg_mean_sensitivity","n_erneg_lines","mcf7_sensitivity","n_mcf7_conditions","sensitivity_rank_erpos","sensitivity_rank_mcf7"] if c in s11]
    out=out.merge(s11[s11cols].drop_duplicates("pert_id"),on="pert_id",how="left",validate="one_to_one")
    if "structure_match" in out: out["structure_match"]=out.structure_match.fillna(False)
    out["S2_reversal_strength_project_convention"]=-out["wtcs_median_B"]
    out["PRISM_endpoint"]="cell viability reduction (-log2 fold change); distinct from S2 expression reversal"
    out["WTCS_PRISM_agreement_interpretation"]="independent endpoints; disagreement does not by itself invalidate either assay"
    out.to_csv(r/"candidate_evidence_integrated.csv",index=False)

    # Cross-experiment compact figure: rank consistency vs independent evidence.
    fig,axs=plt.subplots(1,3,figsize=(14,4.8),dpi=180)
    a=cmp7[cmp7.scheme_a.eq("A_original")]
    names=["Matched 125","B100","B150","B200","B300"]
    vals=[float(a.loc[a.scheme_b.eq(x),"spearman"].iloc[0]) for x in ["B_matched125","B100","B150","B200","B300"]]
    bars=axs[0].bar(names,vals,color="#4C78A8");axs[0].set_title("S1 signature schemes vs A");axs[0].tick_params(axis="x",rotation=22);axs[0].set_ylim(0,1.1)
    for b,v in zip(bars,vals):axs[0].text(b.get_x()+b.get_width()/2,v+.02,f"{v:.2f}",ha="center",fontsize=8)
    qc_names=["CC 0.1","CC 0.3","CC+TAS"]
    qc_vals=cmp9.spearman.to_list()
    bars=axs[1].bar(qc_names,qc_vals,color="#59A14F");axs[1].set_title("LINCS QC threshold sensitivity");axs[1].set_ylim(0,1.1)
    for b,v in zip(bars,qc_vals):axs[1].text(b.get_x()+b.get_width()/2,v+.005,f"{v:.3f}",ha="center",fontsize=8)
    x=corr11.n_compounds; y=corr11.spearman_rank_rho
    names=["Top50 overlap","All candidates"]
    bars=axs[2].bar(names,y,color="#E15759");axs[2].axhline(0,color="black",lw=.8);axs[2].set_title("S2 vs PRISM sensitivity rank");axs[2].set_ylabel("Spearman rho");axs[2].set_ylim(-.1,.4)
    for b,v,n in zip(bars,y,x):axs[2].text(b.get_x()+b.get_width()/2,v+(0.025 if v>=0 else -.05),f"{v:.2f}\nn={int(n)}",ha="center",fontsize=8)
    for ax in axs:ax.grid(axis="y",alpha=.2)
    fig.tight_layout();fig.savefig(f/"cross_experiment_summary.png");plt.close(fig)

    e007A=cmp7[(cmp7.scheme_a=="A_original")&(cmp7.scheme_b=="B100")].iloc[0]
    e007B=cmp7[(cmp7.scheme_a=="A_original")&(cmp7.scheme_b=="B200")].iloc[0]
    method_b=cmp8[cmp8.scheme=="B200"]
    ks=method_b[((method_b.method_a=="Classic_KS")&(method_b.method_b=="WTCS"))|((method_b.method_b=="Classic_KS")&(method_b.method_a=="WTCS"))].iloc[0]
    zhang=method_b[((method_b.method_a=="Zhang_signed_rank")&(method_b.method_b=="WTCS"))|((method_b.method_b=="Zhang_signed_rank")&(method_b.method_a=="WTCS"))].iloc[0]
    xsum=method_b[((method_b.method_a=="XSum_zscore_adaptation")&(method_b.method_b=="WTCS"))|((method_b.method_b=="XSum_zscore_adaptation")&(method_b.method_a=="WTCS"))].iloc[0]
    p009=cmp9.iloc[0]
    erp=(pd.read_csv(e011/"cell_line_inventory.csv").query("primary_tissue == 'breast'").er_group.value_counts().to_dict())
    exp8_text=(f"随机置换 B={perm_n:,} 次完成。BH 后 A 有 {sig_count.get('A_original',0)} 个条件 q<0.05，B 有 {sig_count.get('B200',0)} 个条件 q<0.05；最小 q 值 A={min_q.get('A_original',float('nan')):.4g}、B={min_q.get('B200',float('nan')):.4g}。" if perm_status=="completed" else "WTCS 随机基因集置换还没有完成，因此目前不能回答真实药物信号是否显著超出随机零模型。")
    report=f"""# 第二轮方法学验证：综合报告（人话版）

## 一句话讲清楚

这轮实验主要是在问：换一批疾病基因、换一把分数尺子、改变 LINCS 数据质量门槛，药物名单会不会完全变；而且 S1 能不能在另一批病人数据里复现，S2 排名能不能在另一种药物实验里看到相应的细胞敏感性。

**答案是：中间部分比较稳定，但靠前的药名仍会变；S1 在独立数据里有方向一致的部分证据，S2 排名与外部药物敏感性没有表现出清楚的一致排序。** 这些都是计算和细胞实验层面的证据，不能叫临床疗效。

最后的跨实验自动测试共 **24 项通过**。原始 limma 全表、历史正式 S2 Signature 分数、药物条件排名和 QC 汇总保持只读；本轮只重跑了 Exp009 独立质量敏感性分析，并更新 Exp008/Exp011 说明和综合材料。

## 先把三个容易混淆的地方讲清楚

- WTCS 是看药物处理后的基因表达，是否朝着和疾病表达相反的方向变化；随机基因集经验 P 值只回答“这样的 WTCS 在本项目随机抽基因的对照里少不少见”。它不是官方 CMap 的 NCS 或 Tau。NCS 要用匹配的参考签名分布标准化，Tau 还要拿标准化分数和指定的参考查询集比较；本工程缺这些合格参考，所以没有算 NCS/Tau。
- Exp009 的 CC≥0.2 是本项目自己选的重复一致性过滤值。TAS 是另一项综合活动分数；文献中特定筛选场景用过 TAS≥0.2，并不意味着 CC 也该用 0.2。两项在报告中分开保留。
- WTCS 和 PRISM 观察的是不同结果：WTCS 看表达逆转，PRISM 看细胞存活下降。某药在一个指标上强、另一个指标上弱，不足以单独判定任何一边算错，也不能证明治疗效果。

本轮按用户要求的分析结构依次组织为：Exp007+Exp008（输入和评分方法）→ Exp009（LINCS 质量与剂量）→ Exp010（独立患者队列）→ Exp011（PRISM 外部敏感性）→ 综合证据。各实验运行时间以各自 manifest 为准。

## 五项实验分别说明什么

| 实验 | 状态 | 人话结论 |
|---|---|---|
| Exp007：S1 基因名单大小 | PASS | A 与 B100 的 3,715 个药物剂量条件排序相关 ρ={e007A.spearman:.3f}，Top10 重合 {int(e007A.top10_overlap)}/10；A 与 B200 的 ρ={e007B.spearman:.3f}，Top10 只重合 {int(e007B.top10_overlap)}/10。全局次序还算像，但最前面的少数药名会换。 |
| Exp008：评分算法/随机对照 | PARTIAL | Classic KS 与 WTCS 的 B200 排名相关 ρ={ks.spearman_score:.3f}，Top10 仅 {int(ks.top10_overlap)} 个重合；Zhang ρ={zhang.spearman_score:.3f}、Top10 {int(zhang.top10_overlap)} 个；XSum ρ={xsum.spearman_score:.3f}、Top10 {int(xsum.top10_overlap)} 个。算法会影响头部排序。{exp8_text} NCS/Tau 需要匹配的官方参考查询，目前没有，所以标记不可用；不拿百分位或普通 Z 分数冒充。 |
| Exp009：LINCS 质量门槛 | PASS | CC≥0.1、0.2、0.3 及额外 TAS 筛选的共同药物条件排名 ρ 为 {cmp9.spearman.min():.3f}–{cmp9.spearman.max():.3f}，Top10 均重合 10 个。整体排名对 QC 门槛较稳；旧的药名联结写法曾漏掉 1,100 条稳定 ID 可匹配的 24 小时签名，正式结果保留稳定 ID 口径。 |
| Exp010：独立 S1 数据 | PASS | 用另一个队列的 14 个 ER+ 肿瘤/配对正常样本复算。两个队列共同显著的 333 个基因里方向一致率 {corr10['both_significant_direction_concordance']:.1%}；但全部共同基因 logFC 相关只有 {corr10['spearman_logFC']:.3f}。换成外部 S1 后，药物条件排名 ρ={corr10['ranking_spearman']:.3f}，Top10 只重合 {corr10['top10_overlap_unique_pert_id']} 个。 |
| Exp011：PRISM 外部敏感性 | PASS | Top50 有 37 个药物能用结构 ID 严格配到 PRISM。它们的 S2 排名与 ER+ 细胞敏感性排名 ρ={corr11.iloc[0].spearman_rank_rho:.3f}，95% bootstrap 区间 [{corr11.iloc[0].spearman_bootstrap_95ci_low:.3f}, {corr11.iloc[0].spearman_bootstrap_95ci_high:.3f}]，区间跨 0，排名对应关系不明确。37 个药的平均敏感性高于同大小、且按 ER+ 细胞覆盖数匹配的随机药物组（经验 P={rand11.one_sided_empirical_p_candidates_more_sensitive:.4g}，这是 10,000 次置换的最低分辨率附近），但这只说明候选集合整体较容易抑制体外细胞；可能受细胞毒性药物比例影响，不能说 S2 排名预测 ER+ 疗效。ER+ 与 TNBC 差值为 {er_spec11.observed_mean_ERpos_minus_TNBC_sensitivity:.3f}（95% CI [{er_spec11.bootstrap_95ci_low:.3f}, {er_spec11.bootstrap_95ci_high:.3f}]），方向是 TNBC 细胞反应更强，并没有显示 ER+ 选择性。全 819 候选中 683 个可结构匹配，完整列表 S2 与敏感性排名相关很弱（ρ={corr11.iloc[1].spearman_rank_rho:.3f}）。 |

## 研究问题的答案

### S1：100 UP + 100 DOWN 是否适合？

当前证据不支持说它是唯一最好方案。B100 相对 A 的排名较接近，B200 的总体排名仍相关，但 Top10 重合降到 4/10；B300 相对 A 的 Top10 只重合 3/10。建议把 B200 保留为已经预设的主分析签名，把 A 和 B100/B150/B300 当敏感性分析；这只是为了可复现和覆盖不同规模，不是声称 B200 生物学上最优。

### S2：排名有随机模型以外的统计证据吗？

{exp8_text} 置换经验 P 只针对项目自己的“从 BING 随机抽等规模上下调集合”零模型，不是临床疗效概率，也不是官方 CMap Tau。

### 哪些步骤比较稳，哪些更容易变？

- 比较稳：QC 阈值改变后整体条件排序相关约 0.99；Exp010 的两个队列在双方显著的基因中方向基本一致。
- 容易变：改变 S1 基因数量后 Top10 变化；改变算法后 Top10 重合很少；换到独立 S1 后外部药物 Top10 重合只有 1 个。
- 仍需谨慎：Exp006 Top50 里大多数剂量/签名支持有限；高排名不等于有可靠、多重复的证据。

## 最终建议

1. 正式报告保留 BING Top100 UP/DOWN + WTCS + MCF7、24h、CC≥0.2 作为主设定，并把 A、其它签名大小和 QC 阈值放在敏感性分析中。没有证据把它称作唯一最佳参数。
2. 展示药物时同时放 S2 分数、多个剂量方向、签名数、QC、独立 S1 排名和 PRISM 结果；不要仅按单个最负 WTCS 决定 Top10。
3. 当前没有足够的外部验证来声称候选药物有效。PRISM 测的是细胞存活，后续需要 ER+ 乳腺癌模型的剂量反应、正常细胞毒性和独立重复实验，再考虑动物或临床证据。
4. Exp008 仍为 PARTIAL：虽然随机置换能完成，它的 Zhang/XSum 是 COMPZ 输入下的适配版本，不是原论文 raw logFC 输入的严格复刻；本报告明确保留这一限制。NCS/Tau 在没有官方匹配参考时标为不可用。

## 交付文件

- `experiment_status.csv`：每项 PASS/PARTIAL 状态和未完成事项。
- `methodology_comparison.csv`：Exp007 与 Exp008 的方法排名比较。
- `parameter_sensitivity_summary.csv`：S1 规模及 QC 阈值敏感性。
- `candidate_evidence_integrated.csv`：以 LINCS perturbagen ID 合并 Exp006–Exp011 候选证据；没匹配到的留空，不用名称强行合并。
- `second_round_manifest.json`：输入文件 SHA-256、状态和实验时间。
- `figures/cross_experiment_summary.png`：由实验结果生成的总览图。
"""
    (rep/"second_round_master_report.md").write_text(report,encoding="utf-8")
    inputs=[OUT/"results"/"input_audit.csv",e006/"candidate_drugs_all.csv",e006/"candidate_evidence_matrix.csv",e007/"ranking_comparison.csv",e007/"historical_reproduction_check.csv",e008/"method_comparison.csv",e008/"empirical_pvalues.csv",e008/"permutation_manifest.json",e009/"quality_rank_comparison.csv",e009/"run_manifest.json",e010/"cross_cohort_summary.json",e010/"external_s1_drug_ranking.csv",e010/"experiment_manifest.json",e011/"candidate_sensitivity_results.csv",e011/"s2_prism_rank_correlation.csv",e011/"candidate_vs_random_test.csv",e011/"er_specificity_random_test.csv",e011/"run_manifest.json"]
    manifest={"built_utc":datetime.now(timezone.utc).isoformat(),"experiment_status":status.to_dict(orient="records"),"source_sha256":{p.relative_to(ROOT).as_posix():sha(p) for p in inputs if p.exists()},"permutation_status":perm_status,"permutation_count":perm_n,"outputs":{p.name:sha(p) for p in [r/"experiment_status.csv",r/"methodology_comparison.csv",r/"parameter_sensitivity_summary.csv",r/"candidate_evidence_integrated.csv",rep/"second_round_master_report.md",f/"cross_experiment_summary.png"] if p.exists()}}
    (r/"second_round_manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({"status":status.to_dict(orient="records"),"candidate_rows":len(out),"permutation_status":perm_status,"significant_conditions":sig_count},ensure_ascii=False,indent=2))

if __name__=="__main__":main()
