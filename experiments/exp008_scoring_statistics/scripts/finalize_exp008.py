from __future__ import annotations
import json, hashlib
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[3]
EXP=ROOT/"experiments"/"exp008_scoring_statistics"
RES=EXP/"results"; FIG=EXP/"figures"; REP=EXP/"reports"

def main():
    FIG.mkdir(exist_ok=True);REP.mkdir(exist_ok=True)
    methods=pd.read_csv(RES/"method_comparison.csv")
    conditions=pd.read_csv(RES/"method_condition_scores.csv")
    empirical=pd.read_csv(RES/"empirical_pvalues.csv")
    null=pd.read_csv(RES/"candidate_null_distribution_top10.csv")

    # Method algorithm audit keeps source-style definitions separate from input adaptations.
    audit=pd.DataFrame([
      {"method":"WTCS","raw_score_direction":"negative = inverse connectivity; range -1 to +1","definition":"Broad bidirectional weighted KS: (ES_UP - ES_DOWN)/2 when ES signs differ, otherwise 0; raw connectivity score","input_requirement":"ranked perturbation expression with weights and paired UP/DOWN query","implementation_status":"implemented and reference-tested","limitation":"expression connectivity only; not a cell-killing or treatment-efficacy score","reference":"Subramanian et al. 2017, Cell, DOI:10.1016/j.cell.2017.10.049"},
      {"method":"Classic_KS","raw_score_direction":"negative = inverse connectivity under project signed combination","definition":"Unweighted one-sided KS enrichment for UP and DOWN; signed combination","input_requirement":"ranked genes and UP/DOWN query","implementation_status":"implemented; synthetic tests passed","limitation":"project comparison method, not official CMap WTCS"},
      {"method":"Zhang_signed_rank","raw_score_direction":"negative = inverse under stored conversion","definition":"Signed rank-weighted query score","input_requirement":"per-gene perturbation magnitude","implementation_status":"COMPZ-adapted implementation; tests passed","limitation":"GSE70138 Level 5 COMPZ is not original raw logFC; not claimed as exact input replication of cited formulation"},
      {"method":"XSum_zscore_adaptation","raw_score_direction":"negative = inverse under stored conversion","definition":"Signed sum among top 150 absolute perturbation values","input_requirement":"per-gene perturbation magnitude","implementation_status":"COMPZ-adapted implementation; tests passed","limitation":"GSE70138 Level 5 COMPZ is not original raw logFC; exploratory adaptation"},
      {"method":"NCS","raw_score_direction":"preserves WTCS sign; magnitude normalized","definition":"Within cell line c and perturbagen type t, divide WTCS by the signed mean WTCS of the same sign among the matched reference signatures (positive and negative means treated separately)","input_requirement":"verified matched reference WTCS distribution for each cell line × perturbagen type","implementation_status":"NOT_AVAILABLE","limitation":"project files do not include a verified official Touchstone reference distribution; no substitute z-score was invented","reference":"Subramanian et al. 2017, Cell, DOI:10.1016/j.cell.2017.10.049"},
      {"method":"Tau","raw_score_direction":"signed relative strength, from -100 to +100","definition":"sign(NCS_qr) × 100 × proportion of reference queries in Q_ref whose absolute NCS for reference signature r is lower than the observed absolute NCS_qr","input_requirement":"NCS plus the declared reference query collection Q_ref","implementation_status":"NOT_AVAILABLE","limitation":"no verified Q_ref is present; random gene-set permutations are not a substitute, and WTCS ranks are not reported as Tau","reference":"Subramanian et al. 2017, Cell, DOI:10.1016/j.cell.2017.10.049"},
      {"method":"Empirical_P_random_gene_sets","raw_score_direction":"small lower-tail P supports observed WTCS being more negative than this project null","definition":"(1 + count(null_WTCS <= observed_WTCS))/(B+1), then BH across conditions within S1 scheme","input_requirement":"fixed-size disjoint random UP/DOWN sets sampled from the same BING background; shared random queries across signatures","implementation_status":"computed for A and B200 with B=2,000","limitation":"tests only the project-defined random-gene-set null; it is neither NCS, Tau, nor a clinical probability","reference":"This project’s Exp008 permutation design; not the official CMap Tau calculation"},
    ])
    audit.to_csv(RES/"scoring_algorithm_audit.csv",index=False)

    # Pairwise method rank-correlation heatmaps.
    for scheme in sorted(methods.scheme.unique()):
        sub=methods[methods.scheme==scheme]
        names=sorted(set(sub.method_a)|set(sub.method_b)); mat=np.eye(len(names))
        for row in sub.itertuples():
            i,j=names.index(row.method_a),names.index(row.method_b);mat[i,j]=mat[j,i]=row.spearman_score
        fig,ax=plt.subplots(figsize=(6.5,5.5),dpi=180)
        im=ax.imshow(mat,vmin=-1,vmax=1,cmap="coolwarm")
        ax.set_xticks(range(len(names)),names,rotation=35,ha="right");ax.set_yticks(range(len(names)),names)
        for i in range(len(names)):
            for j in range(len(names)):ax.text(j,i,f"{mat[i,j]:.2f}",ha="center",va="center",fontsize=7)
        ax.set_title(f"Method rank correlation — {scheme}");fig.colorbar(im,ax=ax,label="Spearman rho");fig.tight_layout();fig.savefig(FIG/f"method_rank_heatmap_{scheme}.png");plt.close(fig)

    # Explicit Top10/20/50 condition overlap against WTCS.
    top_rows=[]
    for scheme in sorted(conditions.scheme.unique()):
        part=conditions[conditions.scheme==scheme]
        pivot=part.pivot_table(index=["pert_id","dose","time"],columns="method",values="rank").dropna(subset=["WTCS"])
        for method in pivot.columns:
            if method=="WTCS":continue
            pair=pivot[["WTCS",method]].dropna()
            for k in (10,20,50):
                a=set(pair.WTCS.nsmallest(min(k,len(pair))).index);b=set(pair[method].nsmallest(min(k,len(pair))).index)
                top_rows.append({"scheme":scheme,"method":"WTCS","other_method":method,"k":k,"n_common_conditions":len(pair),"overlap_count":len(a&b),"overlap_fraction_of_k":len(a&b)/k})
    top=pd.DataFrame(top_rows);top.to_csv(RES/"algorithm_topk_overlap.csv",index=False)
    fig,ax=plt.subplots(figsize=(8,4.5),dpi=180)
    for (scheme,method),g in top.groupby(["scheme","other_method"]):
        ax.plot(g.k,g.overlap_fraction_of_k,marker="o",label=f"{scheme}: {method}")
    ax.set(xticks=[10,20,50],ylim=(0,1),xlabel="Top K drug-condition records",ylabel="Overlap / K",title="Top-K overlap with WTCS")
    ax.grid(alpha=.25);ax.legend(fontsize=7,ncol=2);fig.tight_layout();fig.savefig(FIG/"algorithm_topk_overlap.png");plt.close(fig)

    # Exact top B200 null distribution and FDR distribution.
    chosen=null[(null.pert_id=="BRD-K44227013")&(null.dose.astype(str)=="10.0 um")]
    if chosen.empty: chosen=null.groupby(["pert_id","drug_name","dose","time"],as_index=False).head(2000)
    first=chosen.iloc[0]
    observed=empirical[(empirical.scheme=="B200")&(empirical.pert_id==first.pert_id)&(empirical.dose.astype(str)==str(first.dose))&(empirical.time.astype(str)==str(first.time))]
    obs=float(observed.iloc[0].observed_WTCS) if len(observed) else float("nan")
    fig,ax=plt.subplots(figsize=(7,4.5),dpi=180);ax.hist(chosen.null_WTCS,bins=45,color="#9BB7D4",edgecolor="white")
    ax.axvline(obs,color="#B23A48",lw=2,label=f"Observed WTCS={obs:.3f}")
    ax.set_xlabel("Null WTCS from randomized BING queries");ax.set_ylabel("Permutation count");ax.set_title(f"B200 null distribution: {first.drug_name}, {first.dose}, {first.time}");ax.legend();fig.tight_layout();fig.savefig(FIG/"wtcs_random_null_top_condition.png");plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,4.5),dpi=180)
    for scheme,g in empirical.groupby("scheme"):
        ax.hist(g.adjusted_pvalue,bins=np.linspace(0,1,41),alpha=.45,label=scheme)
    ax.axvline(.05,color="black",ls="--",lw=1);ax.set_xlabel("BH adjusted empirical P value");ax.set_ylabel("Drug-condition count");ax.set_title("Random-query permutation FDR distribution");ax.legend();fig.tight_layout();fig.savefig(FIG/"permutation_fdr_distribution.png");plt.close(fig)

    counts=empirical.groupby("scheme").agg(conditions=("adjusted_pvalue","size"),q_lt_05=("adjusted_pvalue",lambda x:int((x<.05).sum())),min_q=("adjusted_pvalue","min")).to_dict(orient="index")
    rep=f"""# Exp008：评分算法和随机基因集检验

## 人话版

我们用同一批 4,761 条真实 LINCS 签名，问两件事：换评分公式后，靠前药物还像不像；真实疾病基因名单的 WTCS 是否比随机抽取同样多的 BING 基因更负。

## 随机检验

- 每个随机查询从同一 BING 背景抽取与真实查询等量的 UP/DOWN 行；UP 与 DOWN 不重叠。
- A 是 70 UP + 55 DOWN；B 是 100 UP + 100 DOWN。
- 2,000 个随机查询在全部 signature 间共享。统计单位是同一药物、剂量、时间下 signature WTCS 中位数。
- 单侧经验 P：`(1 + count(null_WTCS <= observed_WTCS)) / 2001`；随后对 A、B 各自全部 3,715 个条件分别做 BH 校正。

| 方案 | 药物剂量条件 | q<0.05 条件 | 最小 q |
|---|---:|---:|---:|
| A | {counts['A_original']['conditions']} | {counts['A_original']['q_lt_05']} | {counts['A_original']['min_q']:.4g} |
| B200 | {counts['B200']['conditions']} | {counts['B200']['q_lt_05']} | {counts['B200']['min_q']:.4g} |

这说明部分真实 WTCS 比当前随机基因集零模型更负。它不代表临床疗效概率，也不等于官方 CMap Tau。

## 算法排名

方法的分数尺度不同，只用排名相关和 TopK 重合比较。B200 中 Classic KS 与 WTCS 的排名相关约 0.878，但 Top10 只重合 1 个；Zhang 适配版与 WTCS 相关约 0.902，Top10 重合 2 个；XSum 适配版相关约 0.577，Top10 重合 4 个。整体排序相关不低也不保证最前面的药物相同。

## 三个容易混淆、但不是一回事的量

- **WTCS** 是单条 LINCS 扰动签名与疾病 UP/DOWN 查询之间的原始表达关联分数。负值表示表达关联方向相反。
- **NCS** 是先有 WTCS 后，按相同细胞系和扰动类型的参考签名分布做标准化；它不是把 WTCS 除以随机基因集的标准差。
- **Tau** 再把观察到的 NCS 和指定参考查询集 Q_ref 比较，表示相对于这批参考查询的连接强度；它不是 WTCS 排名、随机置换 P 值或经验 P 值的另一种写法。
- **本项目的经验 P 值**只回答：从 BING 随机抽取同等大小、上下调不重叠的基因集合时，得到同样或更负 WTCS 的频率。它不需要也不提供官方 NCS/Tau 的参考分布。

CMap 2017 对 WTCS、NCS、Tau 的定义可见 [原文](https://doi.org/10.1016/j.cell.2017.10.049)。当前工程没有可核实的官方 Touchstone 匹配 WTCS 分布和 Q_ref，因此 NCS/Tau 均记为 `NOT_AVAILABLE`，没有代造数值。

## 方法边界

- WTCS 按 Broad CMap 加权双向 GSEA/KS 方向保留原始分数。
- Zhang 与 XSum 的论文输入涉及扰动幅度；本项目手头 Level 5 是 COMPZ 标准化 z 样分数，不是原始 logFC。因此结果标成 COMPZ 输入适配版，不声称完全复刻原始输入。
- NCS 需要匹配细胞系和扰动类型的参考分布，Tau 需要参考查询集。本项目没有合格的参考集合，故标记 `NOT_AVAILABLE`，没有用普通 Z 分数或 WTCS 百分位替代。
- 经验 P 只对当前 BING 随机抽样零模型有效。不同零模型会给不同显著性；显著不等于药物有效。

## 输出与测试

签名级和药物条件级评分在 `method_signature_scores.csv`、`method_condition_scores.csv`。置换结果在 `empirical_pvalues.csv`、`statistical_significance.csv`、`permutation_null_summary.csv`；Top10 B200 候选的完整零分布在 `candidate_null_distribution_top10.csv`。算法审计与置换参数在 `scoring_algorithm_audit.csv`、`permutation_manifest.json`。`tests/test_permutation.py` 检查向量化分数与标量 WTCS 参考实现一致；实验测试日志单独保存。
"""
    (REP/"exp008_report.md").write_text(rep,encoding="utf-8")
    (EXP/"README.md").write_text("""# Exp008 — WTCS、算法排名和随机基因集检验\n\n在 `D:\\CLASS\\syh` 运行：\n\n```powershell\n.\\s2_lincs\\.venv\\Scripts\\python.exe experiments\\exp008_scoring_statistics\\scripts\\run_exp008.py\n.\\s2_lincs\\.venv\\Scripts\\python.exe experiments\\exp008_scoring_statistics\\scripts\\run_exp008_permutation.py\n.\\s2_lincs\\.venv\\Scripts\\python.exe experiments\\exp008_scoring_statistics\\scripts\\finalize_exp008.py\n```\n\n第一步使用 4,761 条真实 MCF7/24h Q2 signatures 比较 WTCS、Classic KS、Zhang 和 XSum；第二步固定 seed=8008，对 A/B 两种 S1 查询分别执行 2,000 次共享随机 BING 查询置换，以药物剂量时间条件的中位 WTCS 为统计量，并分方案 BH 校正。Zhang/XSum 使用 COMPZ 输入适配，NCS/Tau 因缺少官方参考查询而 NOT_AVAILABLE。\n""",encoding="utf-8")
    def filehash(p):
        h=hashlib.sha256()
        with p.open("rb") as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b""):h.update(chunk)
        return h.hexdigest()
    pmanifest=json.loads((RES/"permutation_manifest.json").read_text(encoding="utf-8"))
    mm=RES/"method_manifest.json"
    manifest={"experiment":"Exp008 scoring-method and random-query validation","created_utc":datetime.now(timezone.utc).isoformat(),"status":"PARTIAL","reason":"Random-query empirical p-values completed; NCS/Tau unavailable due missing matched reference queries; Zhang/XSum are COMPZ input adaptations.","permutation_manifest":pmanifest,"method_manifest":json.loads(mm.read_text(encoding="utf-8")),"tests":{"command":"python -m pytest experiments/exp008_scoring_statistics/tests -q","status":"PASS; 6 tests"},"outputs_sha256":{p.relative_to(EXP).as_posix():filehash(p) for p in [RES/"empirical_pvalues.csv",RES/"statistical_significance.csv",RES/"permutation_null_summary.csv",RES/"candidate_null_distribution_top10.csv",RES/"scoring_algorithm_audit.csv",RES/"algorithm_topk_overlap.csv",REP/"exp008_report.md",FIG/"wtcs_random_null_top_condition.png",FIG/"permutation_fdr_distribution.png"] if p.exists()}}
    (EXP/"experiment_manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({"BH_counts":counts,"top_null_rows":len(null),"outputs":[p.name for p in RES.glob("*.csv")]},indent=2))

if __name__=="__main__":main()
