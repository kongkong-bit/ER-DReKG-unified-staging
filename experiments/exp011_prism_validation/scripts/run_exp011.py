from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from rdkit import Chem, rdBase
from rdkit.Chem import inchi
from rdkit import RDLogger
from scipy.stats import kendalltau, spearmanr


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
REPORTS = ROOT / "reports"
SEED = 20261112
N_PERM = 10_000
N_BOOT = 5_000
RDLogger.DisableLog("rdApp.*")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inchikey(smiles) -> str | None:
    if pd.isna(smiles) or not str(smiles).strip():
        return None
    raw=str(smiles).strip()
    mol=Chem.MolFromSmiles(raw)
    if mol is not None:
        return inchi.MolToInchiKey(mol)
    # PRISM's collapsed treatment file can store a comma-delimited list of equivalent SMILES.
    keys=set()
    for part in raw.split(","):
        part=part.strip()
        if not part: continue
        mol=Chem.MolFromSmiles(part)
        if mol is not None: keys.add(inchi.MolToInchiKey(mol))
    return next(iter(keys)) if len(keys)==1 else None


def name_key(x) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(x).lower())


def bootstrap_corr(x: np.ndarray, y: np.ndarray, seed: int) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    vals = []
    n = len(x)
    for _ in range(N_BOOT):
        ix = rng.integers(0, n, n)
        if len(np.unique(x[ix])) > 1 and len(np.unique(y[ix])) > 1:
            v = spearmanr(x[ix], y[ix]).statistic
            if np.isfinite(v):
                vals.append(v)
    return tuple(np.quantile(vals, [0.025, 0.975])) if vals else (np.nan, np.nan)


def main() -> None:
    for p in (RESULTS, FIGURES, REPORTS):
        p.mkdir(parents=True, exist_ok=True)

    cell_path = DATA / "primary-screen-cell-line-info.csv"
    matrix_path = DATA / "primary-screen-replicate-collapsed-logfold-change.csv"
    tx_path = DATA / "primary-screen-replicate-collapsed-treatment-info.csv"
    readme_path = DATA / "primary-screen-readme.txt"
    model_path = DATA / "DepMap_Model_24Q4.csv"
    top_path = Path(__file__).resolve().parents[2] / "exp006_ranking_reliability" / "results" / "candidate_drugs_top50.csv"
    all_path = top_path.with_name("candidate_drugs_all.csv")
    pert_path = Path(__file__).resolve().parents[3] / "s2_lincs" / "data" / "GSE70138_Broad_LINCS_pert_info_2017-03-06.txt.gz"

    cells = pd.read_csv(cell_path)
    model = pd.read_csv(model_path, low_memory=False)
    tx = pd.read_csv(tx_path)
    matrix = pd.read_csv(matrix_path, index_col=0, low_memory=False)
    top = pd.read_csv(top_path)
    all_candidates = pd.read_csv(all_path)
    pert = pd.read_csv(pert_path, sep="\t", low_memory=False)

    # Integrity gate: condition columns and IDs must be one-to-one before scoring.
    tx = tx.drop_duplicates("column_name", keep="first")
    matrix.columns = matrix.columns.astype(str)
    assert set(tx.column_name).issubset(set(matrix.columns)), "PRISM treatment columns do not align to the viability matrix"
    assert matrix.index.is_unique, "PRISM cell-line row IDs are not unique"
    cells = cells.drop_duplicates("row_name", keep="first")
    assert set(matrix.index).issubset(set(cells.row_name)), "Unannotated PRISM matrix rows"

    # ModelSubtypeFeatures is an explicit DepMap field; only explicit ER+ and TNBC labels are classified.
    cell_meta = cells.merge(model, left_on="depmap_id", right_on="ModelID", how="left", validate="many_to_one")
    feat = cell_meta["ModelSubtypeFeatures"].fillna("").astype(str).str.lower()
    explicit_er_positive = feat.str.contains(r"\ber\b", regex=True) & ~feat.str.contains(r"\ber\s*-|\btnbc\b", regex=True)
    explicit_er_negative = feat.str.contains(r"\ber\s*-|\btnbc\b", regex=True)
    cell_meta["er_group"] = np.select(
        [explicit_er_positive, explicit_er_negative],
        ["ER-positive", "ER-negative (ER-/TNBC label)"], default="ER-unknown"
    )
    cell_meta["er_annotation_source"] = np.where(cell_meta.ModelID.notna(), "DepMap Public 24Q4 Model.csv: ModelSubtypeFeatures", "No ACH ID match in DepMap 24Q4")
    cell_meta.to_csv(RESULTS / "cell_line_inventory.csv", index=False)

    # Map candidate perturbagens to PRISM only by structure-derived InChIKey.
    pert = pert.drop_duplicates("pert_id", keep="first")
    tx["inchi_key"] = tx.smiles.map(inchikey)
    tx["name_aux_key"] = tx.name.map(name_key)
    pert["name_aux_key"] = pert.pert_iname.map(name_key)
    tx_key_map = tx.dropna(subset="inchi_key")[ ["inchi_key", "broad_id", "name", "dose", "screen_id", "column_name", "smiles"] ].copy()
    tx_key_map = tx_key_map.drop_duplicates(["inchi_key", "column_name"])
    prism_keys = set(tx_key_map.inchi_key)

    def map_candidates(df: pd.DataFrame, cohort: str) -> pd.DataFrame:
        x = df.merge(pert[["pert_id", "canonical_smiles", "inchi_key", "pert_iname"]], on="pert_id", how="left", validate="many_to_one")
        x["prism_exact_broad_id"] = x.pert_id.isin(set(tx.broad_id))
        x["structure_match"] = x.inchi_key.isin(prism_keys)
        name_counts = tx.groupby("name_aux_key").name.nunique()
        aux_names = set(tx.name_aux_key)
        x["exact_name_aux_only"] = x.drug_name.map(name_key).isin(aux_names) & ~x.structure_match
        x["mapping_method"] = np.select(
            [x.prism_exact_broad_id, x.structure_match, x.exact_name_aux_only],
            ["exact Broad ID", "exact InChIKey from SMILES", "exact normalized name only (not accepted)"], default="unmatched"
        )
        x["prism_name_matches_by_aux_key"] = x.drug_name.map(name_key).map(name_counts).fillna(0).astype(int)
        x["candidate_cohort"] = cohort
        return x

    map_top = map_candidates(top, "Exp006 Top50")
    map_all = map_candidates(all_candidates, "Exp006 full 819")
    # Top50 mapping table is the primary audit; full list mapping is also retained.
    map_top.to_csv(RESULTS / "candidate_mapping_audit_top50.csv", index=False)
    map_all.to_csv(RESULTS / "candidate_mapping_audit_full.csv", index=False)

    # Restrict to compounds that map by exact structural identity (or exact Broad ID).
    valid_top = map_top[map_top.structure_match | map_top.prism_exact_broad_id].copy()
    valid_all = map_all[map_all.structure_match | map_all.prism_exact_broad_id].copy()
    # Stable chemical identity is the InChIKey. Treat any multiple PRISM batch/dose records as repeated assays.
    candidate_key_rows = valid_all.dropna(subset="inchi_key").drop_duplicates(["pert_id", "inchi_key"])
    cand_inchis = set(candidate_key_rows.inchi_key)
    controls = tx[tx.name_aux_key.str.contains(r"tamoxifen|fulvestrant|faslodex|raloxifene|4.?hydroxy.?tamoxifen|endoxifen", regex=True, na=False)].copy()
    control_keys = set(controls.inchi_key.dropna())
    target_tx = tx_key_map[tx_key_map.inchi_key.isin(cand_inchis | control_keys)].copy()
    target_tx[target_tx.inchi_key.isin(cand_inchis)].to_csv(RESULTS / "candidate_prism_condition_map.csv", index=False)
    target_tx[target_tx.inchi_key.isin(control_keys)].to_csv(RESULTS / "positive_control_condition_map.csv", index=False)

    # Select the same condition columns from the matrix, then take median logFC over doses/screens per cell × compound.
    cols = target_tx.column_name.drop_duplicates().tolist()
    mat = matrix.loc[:, cols].apply(pd.to_numeric, errors="coerce")
    mat.index.name = "row_name"
    long = mat.reset_index().melt(id_vars="row_name", var_name="column_name", value_name="logfold_change")
    long = long.merge(target_tx[["column_name", "inchi_key"]], on="column_name", how="inner", validate="many_to_one")
    long = long.groupby(["row_name", "inchi_key"], as_index=False).logfold_change.median()
    long["sensitivity"] = -long.logfold_change
    long = long.merge(cell_meta[["row_name", "depmap_id", "ccle_name", "primary_tissue", "ModelID", "CellLineName", "ModelSubtypeFeatures", "er_group", "er_annotation_source"]], on="row_name", how="left", validate="many_to_one")
    long.to_csv(RESULTS / "candidate_sensitivity_matrix.csv", index=False)

    # Candidate structure-to-score mapping. A single InChIKey can have multiple LINCS IDs; median rank aggregates them.
    top_keys = set(valid_top.inchi_key.dropna())
    sensitivity_summary = long.groupby(["inchi_key", "er_group"], dropna=False).agg(
        n_cell_lines=("sensitivity", "count"), mean_sensitivity=("sensitivity", "mean"), median_sensitivity=("sensitivity", "median")
    ).reset_index()
    erpos = sensitivity_summary[sensitivity_summary.er_group.eq("ER-positive")].rename(columns={"n_cell_lines":"n_erpos_lines", "mean_sensitivity":"erpos_mean_sensitivity", "median_sensitivity":"erpos_median_sensitivity"})
    erneg = sensitivity_summary[sensitivity_summary.er_group.eq("ER-negative (ER-/TNBC label)")].rename(columns={"n_cell_lines":"n_erneg_lines", "mean_sensitivity":"erneg_mean_sensitivity", "median_sensitivity":"erneg_median_sensitivity"})
    summary = erpos.merge(erneg[["inchi_key","n_erneg_lines","erneg_mean_sensitivity","erneg_median_sensitivity"]], on="inchi_key", how="outer")
    mcf = long[long.ccle_name.astype(str).str.upper().eq("MCF7_BREAST")].groupby("inchi_key").sensitivity.agg(mcf7_sensitivity="median", n_mcf7_conditions="count").reset_index()
    labels = candidate_key_rows[["inchi_key", "pert_id", "drug_name", "rank"]].sort_values("rank").drop_duplicates("inchi_key").rename(columns={"rank": "s2_rank"})
    summary = labels.merge(summary, on="inchi_key", how="left").merge(mcf, on="inchi_key", how="left")
    summary["sensitivity_rank_erpos"] = summary.erpos_mean_sensitivity.rank(ascending=False, method="average")
    summary["sensitivity_rank_mcf7"] = summary.mcf7_sensitivity.rank(ascending=False, method="average")
    summary.to_csv(RESULTS / "candidate_sensitivity_results.csv", index=False)
    ctrl_long=long[long.inchi_key.isin(control_keys)].copy()
    ctrl_er=ctrl_long[ctrl_long.er_group.eq("ER-positive")].groupby("inchi_key").sensitivity.agg(erpos_mean_sensitivity="mean",erpos_median_sensitivity="median",n_erpos_lines="count").reset_index()
    ctrl_mcf=ctrl_long[ctrl_long.ccle_name.astype(str).str.upper().eq("MCF7_BREAST")].groupby("inchi_key").sensitivity.agg(mcf7_sensitivity="median",n_mcf7_conditions="count").reset_index()
    ctrl_labels=controls.dropna(subset="inchi_key")[["inchi_key","broad_id","name","moa","target"]].drop_duplicates()
    ctrl_results=ctrl_labels.merge(ctrl_er,on="inchi_key",how="left").merge(ctrl_mcf,on="inchi_key",how="left")
    ctrl_results.to_csv(RESULTS / "positive_control_sensitivity.csv",index=False)

    # Formal rank concordance: higher sensitivity = more inhibited; compare like-ranked lists (1 is best).
    corr_rows = []
    top_summary = summary[summary.inchi_key.isin(top_keys)].dropna(subset=["s2_rank", "sensitivity_rank_erpos"])
    for cohort, frame in [("Top50 exact structure overlap", top_summary), ("Full-list exact structure overlap", summary.dropna(subset=["s2_rank", "sensitivity_rank_erpos"]))]:
        if len(frame) >= 3:
            x = frame.s2_rank.to_numpy(float)
            y = frame.sensitivity_rank_erpos.to_numpy(float)
            rho = float(spearmanr(x, y).statistic)
            tau = float(kendalltau(x, y).statistic)
            lo, hi = bootstrap_corr(x, y, SEED + len(frame))
        else:
            rho = tau = lo = hi = np.nan
        corr_rows.append({"cohort":cohort,"n_compounds":len(frame),"spearman_rank_rho":rho,"spearman_bootstrap_95ci_low":lo,"spearman_bootstrap_95ci_high":hi,"kendall_tau":tau,"rank_note":"S2 rank 1 = stronger reversal; PRISM sensitivity rank 1 = stronger viability reduction"})
    pd.DataFrame(corr_rows).to_csv(RESULTS / "s2_prism_rank_correlation.csv", index=False)

    # Same-size random compound-set test among all structurally identified PRISM molecules assayed in ER+ lines.
    er_scores = long[long.er_group.eq("ER-positive")].groupby("inchi_key").sensitivity.agg(["mean",lambda x:x.notna().sum()]).dropna()
    er_scores.columns=["mean_sensitivity","n_erpos_lines"]
    mapped_top_scores = summary[summary.inchi_key.isin(top_keys)].set_index("inchi_key").erpos_mean_sensitivity.dropna()
    observed = float(mapped_top_scores.mean()) if len(mapped_top_scores) else np.nan
    candidate_coverage=summary[summary.inchi_key.isin(mapped_top_scores.index)].set_index("inchi_key").n_erpos_lines.astype(int)
    background=er_scores.drop(index=mapped_top_scores.index.intersection(er_scores.index), errors="ignore")
    target_counts={int(k):int(v) for k,v in candidate_coverage.value_counts().to_dict().items()}
    coverage_pools={int(k):g.mean_sensitivity.to_numpy() for k,g in background.groupby("n_erpos_lines")}
    if any(int(k) not in coverage_pools or len(coverage_pools[int(k)])<int(v) for k,v in target_counts.items()):
        raise ValueError("Cannot form assay-coverage-matched random compounds for candidate set")
    rng = np.random.default_rng(SEED)
    null = np.array([np.concatenate([rng.choice(coverage_pools[int(k)],size=int(v),replace=False) for k,v in target_counts.items()]).mean() for _ in range(N_PERM)]) if len(mapped_top_scores)>0 else np.array([])
    p_emp = float((1 + np.sum(null >= observed)) / (1 + len(null))) if len(null) else np.nan
    pd.DataFrame([{"candidate_set":"Exp006 Top50 exact structure overlap","n_candidates":len(mapped_top_scores),"background_pool_unique_structures":len(background),"matched_erpos_line_coverage_counts":json.dumps(target_counts),"statistic":"mean sensitivity (-logFC), ER-positive PRISM lines","observed_mean_sensitivity":observed,"randomization_replicates":len(null),"seed":SEED,"one_sided_empirical_p_candidates_more_sensitive":p_emp,"null_mean":float(np.mean(null)) if len(null) else np.nan,"null_95ci_low":float(np.quantile(null,.025)) if len(null) else np.nan,"null_95ci_high":float(np.quantile(null,.975)) if len(null) else np.nan}]).to_csv(RESULTS / "candidate_vs_random_test.csv", index=False)
    if len(null):
        pd.DataFrame({"random_mean_sensitivity":null}).to_csv(RESULTS / "candidate_vs_random_null.csv", index=False)

    # ER specificity is descriptive, with strict labels only; no inferred ER status from tissue alone.
    er_specific = summary.dropna(subset=["erpos_mean_sensitivity","erneg_mean_sensitivity"]).copy()
    er_specific["erpos_minus_erneg_sensitivity"] = er_specific.erpos_mean_sensitivity-er_specific.erneg_mean_sensitivity
    er_specific.to_csv(RESULTS / "er_specificity_candidate_summary.csv", index=False)
    top_specific=er_specific[er_specific.inchi_key.isin(top_keys)].copy()
    top_deltas=top_specific.erpos_minus_erneg_sensitivity.dropna().to_numpy(float)
    obs_delta=float(top_deltas.mean()) if len(top_deltas) else np.nan
    rng_spec=np.random.default_rng(SEED+1)
    coverage_cols=["n_erpos_lines","n_erneg_lines"]
    top_specific[coverage_cols]=top_specific[coverage_cols].astype(int)
    background_specific=er_specific[~er_specific.inchi_key.isin(top_keys)].dropna(subset=["erpos_minus_erneg_sensitivity"]).copy()
    background_specific[coverage_cols]=background_specific[coverage_cols].astype(int)
    spec_counts={tuple(map(int,k)):int(v) for k,v in top_specific.groupby(coverage_cols).size().to_dict().items()}
    spec_pools={tuple(map(int,k)):g.erpos_minus_erneg_sensitivity.to_numpy(float) for k,g in background_specific.groupby(coverage_cols)}
    if any(k not in spec_pools or len(spec_pools[k])<v for k,v in spec_counts.items()):
        raise ValueError("Cannot form ER-specificity coverage-matched random background")
    null_spec=np.array([np.concatenate([rng_spec.choice(spec_pools[k],size=v,replace=False) for k,v in spec_counts.items()]).mean() for _ in range(N_PERM)])
    boot_spec=np.array([rng_spec.choice(top_deltas,size=len(top_deltas),replace=True).mean() for _ in range(N_BOOT)]) if len(top_deltas) else np.array([])
    ci_spec=np.quantile(boot_spec,[.025,.975]) if len(boot_spec) else [np.nan,np.nan]
    p_spec=float((1+np.sum(null_spec>=obs_delta))/(1+len(null_spec))) if len(null_spec) else np.nan
    breast_erpos_n=int((cell_meta.primary_tissue.astype(str).str.lower().eq("breast")&cell_meta.er_group.eq("ER-positive")).sum())
    breast_tnbc_n=int((cell_meta.primary_tissue.astype(str).str.lower().eq("breast")&cell_meta.er_group.eq("ER-negative (ER-/TNBC label)")).sum())
    pd.DataFrame([{"candidate_set":"Exp006 Top50 exact structure overlap","n_compounds":len(top_deltas),"ER_positive_cell_lines":breast_erpos_n,"ER_negative_TNBC_lines":breast_tnbc_n,"observed_mean_ERpos_minus_TNBC_sensitivity":obs_delta,"bootstrap_95ci_low":float(ci_spec[0]),"bootstrap_95ci_high":float(ci_spec[1]),"matched_line_coverage_strata":json.dumps({str(k):v for k,v in spec_counts.items()}),"randomization_replicates":len(null_spec),"one_sided_empirical_p_candidate_more_ERpos_selective":p_spec}]).to_csv(RESULTS / "er_specificity_random_test.csv",index=False)
    pd.DataFrame({"random_mean_ERpos_minus_TNBC_sensitivity":null_spec}).to_csv(RESULTS / "er_specificity_random_null.csv",index=False)

    # Search named endocrine controls in the observed PRISM screening collection, but report rather than force-map them.
    controls["er_group_coverage"] = "see candidate_sensitivity_matrix / DepMap cell inventory"
    controls.to_csv(RESULTS / "positive_control_inventory.csv", index=False)

    # Figures based on real files.
    fig, ax = plt.subplots(figsize=(7, 5), dpi=180)
    scatter = top_summary.dropna(subset=["s2_rank", "erpos_mean_sensitivity"])
    ax.scatter(scatter.s2_rank, scatter.erpos_mean_sensitivity, s=55, alpha=.8, color="#2878B5")
    for _, r in scatter.iterrows():
        ax.annotate(str(r.drug_name), (r.s2_rank, r.erpos_mean_sensitivity), fontsize=6, xytext=(3,3), textcoords="offset points")
    ax.set_xlabel("S2 reversal rank (1 = strongest predicted reversal)")
    ax.set_ylabel("PRISM ER+ mean sensitivity (−log fold change)")
    ax.set_title(f"S2–PRISM comparison: exact structure matches (n={len(scatter)})")
    ax.grid(alpha=.2); fig.tight_layout(); fig.savefig(FIGURES / "s2_prism_rank_scatter.png"); plt.close(fig)
    if len(null):
        fig, ax = plt.subplots(figsize=(7,4.5), dpi=180)
        ax.hist(null, bins=35, color="#9BB7D4", edgecolor="white")
        ax.axvline(observed, color="#B23A48", lw=2, label="Observed candidate set")
        ax.set_xlabel("Mean PRISM sensitivity across candidate set")
        ax.set_ylabel("Random sets")
        ax.set_title(f"Top50 vs same-size random PRISM compounds (n={len(mapped_top_scores)})")
        ax.legend(); fig.tight_layout(); fig.savefig(FIGURES / "candidate_vs_random.png"); plt.close(fig)
    spec_plot=summary.dropna(subset=["erpos_mean_sensitivity","erneg_mean_sensitivity"])
    fig,ax=plt.subplots(figsize=(6.5,5.2),dpi=180)
    is_top=spec_plot.inchi_key.isin(top_keys)
    ax.scatter(spec_plot.loc[~is_top,"erpos_mean_sensitivity"],spec_plot.loc[~is_top,"erneg_mean_sensitivity"],s=16,alpha=.35,color="#9AA0A6",label="Other exact-structure candidates")
    ax.scatter(spec_plot.loc[is_top,"erpos_mean_sensitivity"],spec_plot.loc[is_top,"erneg_mean_sensitivity"],s=38,alpha=.85,color="#D55E00",label="Exp006 Top50")
    low=float(min(spec_plot.erpos_mean_sensitivity.min(),spec_plot.erneg_mean_sensitivity.min()));high=float(max(spec_plot.erpos_mean_sensitivity.max(),spec_plot.erneg_mean_sensitivity.max()))
    ax.plot([low,high],[low,high],color="black",lw=1,ls="--");ax.set_xlabel("Mean sensitivity in ER+ lines (−LFC)");ax.set_ylabel("Mean sensitivity in ER−/TNBC lines (−LFC)");ax.set_title("PRISM ER specificity: above diagonal = greater TNBC sensitivity");ax.legend(fontsize=7);fig.tight_layout();fig.savefig(FIGURES/"er_specificity_scatter.png");plt.close(fig)

    breast_meta = cell_meta[cell_meta.primary_tissue.astype(str).str.lower().eq("breast")]
    er_counts = breast_meta.er_group.value_counts().to_dict()
    model_cell_count = int(cell_meta.ModelID.notna().sum())
    top_mapped = int(map_top.structure_match.sum())
    all_mapped = int(map_all.structure_match.sum())
    corr = pd.DataFrame(corr_rows)
    q2 = int((corr.iloc[0].n_compounds if len(corr) else 0))
    input_hashes = {p.name: sha256(p) for p in [cell_path,matrix_path,tx_path,readme_path,model_path,top_path,all_path,pert_path]}
    manifest = {
        "experiment":"Exp011 PRISM external drug-sensitivity validation",
        "run_utc":datetime.now(timezone.utc).isoformat(),"seed":SEED,"randomization_replicates":N_PERM,"bootstrap_replicates":N_BOOT,
        "rdkit_version":rdBase.rdkitVersion,"depmap_annotation_release":"DepMap Public 24Q4 Model.csv",
        "mapping_policy":"Exact Broad ID or exact InChIKey derived from valid LINCS/PRISM SMILES; exact normalized names retained for audit only and never used to assign identity; no fuzzy matching. PRISM comma-delimited equivalent SMILES are accepted only if valid parses yield one unique InChIKey.",
        "sensitivity_definition":"-PRISM log2 fold change; larger means more viability reduction. Dose and screen records collapsed by median per cell line and InChIKey.",
        "input_sha256":input_hashes,
        "dimensions":{"prism_matrix_cell_lines":matrix.shape[0],"cell_line_metadata_rows":len(cells),"model_cell_lines_joined_to_depmapping":model_cell_count,"matrix_conditions":matrix.shape[1],"treatment_metadata_rows":len(tx),"breast_cell_lines":len(breast_meta),"candidate_top50_exact_structure_matches":top_mapped,"full_candidates_exact_structure_matches":all_mapped,"breast_cell_er_groups":er_counts},
        "formal_status":"PASS" if set(matrix.index).issubset(set(cells.row_name)) and set(tx.column_name).issubset(set(matrix.columns)) and top_mapped > 0 else "FAIL",
    }
    report = f"""# Exp011：S2 候选药物的 PRISM 外部敏感性验证

## 用通俗的话说

S2 根据 LINCS 细胞实验推测哪些药物能把乳腺癌异常表达往反方向推；PRISM 则是在很多癌细胞系里实际测药物处理后细胞存活变化。本实验把两边能用化学结构确认是同一种药的药物配起来，检查 S2 排名和 PRISM 敏感性是否有一致趋势。它是细胞系层面的外部对照，不等于临床疗效。

## 数据与匹配

- 来源版本：Broad/DepMap PRISM Repurposing **Primary**；官方页面描述该 release 为 4,518 compounds、约 578/562 cell lines。本地 replicate-collapsed 文件实读到 {matrix.shape[1]} 个 condition columns，其中同药多剂量/不同 screen 会分别占列。PRISM 官方页：[depmap.org/repurposing](https://depmap.org/repurposing/)；该页面提供 README、细胞注释、replicate-collapsed LFC 与 treatment metadata。受体注释使用 DepMap Public 24Q4 `Model.csv`（[下载地址](https://ndownloader.figshare.com/files/51065297)），不是把 PRISM 细胞来源当作受体状态。
- 授权审计：本次下载的 PRISM README 和官方数据页列出数据来源及引用信息，但没有随文件提供单独 LICENSE 文件，也没有在所审页面显示逐文件许可条款；后续公开使用应按 PRISM/DepMap 页面提供的原始研究与数据集引用方式注明来源。
- PRISM Primary：矩阵包含 {matrix.shape[0]} 个细胞系和 {matrix.shape[1]} 个药物剂量/筛选条件；细胞系 ID 注释表有 {len(cells)} 行，其中 {model_cell_count} 个模型可按 ACH ID 连入 DepMap Public 24Q4。矩阵不含控制条码行，未能连入的行不纳入 ER 分型。
- 按 PRISM 注释识别乳腺癌细胞系 {len(breast_meta)} 个；DepMap Public 24Q4 `ModelSubtypeFeatures` 中标为 ER+ {er_counts.get('ER-positive',0)} 个，标为 ER−/TNBC {er_counts.get('ER-negative (ER-/TNBC label)',0)} 个，受体亚型未知 {er_counts.get('ER-unknown',0)} 个。MCF7 单独保留。
- 药物身份只接受 Broad ID 完全相同或由有效 SMILES 推导出的 InChIKey 完全相同。候选药物名称只用于核查，不用于药物身份归并；未做模糊匹配。
- Exp006 Top50 中有 {top_mapped}/50 个通过结构标识匹配；Exp006 全部 819 个候选中有 {all_mapped}/819 个通过结构标识匹配。其余未匹配条目保留在 mapping audit，不能据此解释为实验没有测过。
- PRISM 每个药物的剂量/屏幕记录先在每个细胞系内取中位数，不挑最有利剂量。敏感性定义为 `−log2 fold change`，越大表示细胞存活下降越强。

## 主要结果

见 `candidate_sensitivity_results.csv`、`s2_prism_rank_correlation.csv` 与 `candidate_vs_random_test.csv`。Top50 结构匹配药物数为 {q2}；相关性及置信区间仅对同时有 S2 排名和 ER+ PRISM 结果的化合物计算。候选组与随机组比较是从有 ER+ PRISM 记录的其他结构唯一化合物中抽取同样大小集合，固定种子 {SEED}，重复 {N_PERM:,} 次。

`candidate_vs_random_test.csv` 给出单侧经验 P 值（候选组是否较随机组更敏感）；随机化合物还按每个药物有 PRISM 结果的 ER+ 细胞系数量分层匹配（{json.dumps(target_counts)}）。经验 P 值的最小分辨率是 1/10,001；若观测值达到这个下限，应读作“≤约 0.0001”，不是无限精确的概率。若 P 值不小，或区间/样本数不足，就不能说候选整体更有效。ER− TNBC 和 MCF7 的结果分别保存在逐药/逐细胞结果中；ER status 未明确的乳腺细胞不并入 ER−组。

ER 特异性另作比较：在 {len(top_deltas)} 个结构匹配 Top50 候选中，ER+ 平均敏感性减去 TNBC 平均敏感性的均值为 {obs_delta:.3f}（bootstrap 95% CI {ci_spec[0]:.3f} 至 {ci_spec[1]:.3f}）；按 ER+ 与 TNBC 可用细胞系数量匹配的随机药物集单侧 P={p_spec:.4g}。该差值若为正才表示更偏向 ER+；结果按实际方向解释，不预设候选有 ER+ 选择性。

## 结果边界

WTCS 与 PRISM 是两个不同终点：WTCS 看药物引起的表达变化是否与疾病表达相反；PRISM 看药物是否让细胞生长/存活下降。WTCS 很负但 PRISM 杀伤不明显，不代表 WTCS 算错；PRISM 杀伤很强也不能证明它通过表达逆转机制起效。

1. PRISM 测的是体外细胞存活，不测患者疗效，也不直接测 ER+ 乳腺癌患者获益。
2. PRISM 主要筛选数据是多药剂量/批次的细胞活力实验；本报告在单细胞系内对剂量/屏幕取中位数，以减少挑选最有利剂量造成的偏差。
3. Top50 结构匹配数有限时，相关性和随机集合检验只能作探索性结果，不外推到未匹配药物或最终 Top10。
4. DepMap 24Q4 受体亚型注释与 PRISM 文件中的模型 ID 通过 ACH ID 连接；只接受明确含 ER 或 TNBC 标注的字段，其他标为未知。非乳腺细胞及控制条码不用于乳腺亚型统计。
5. PRISM SMILES 中不能解析的记录不参与结构匹配；数据字典提供了 SMILES 字段，但具体文件含空值/非 SMILES 占位值。
6. Fulvestrant、tamoxifen 和 raloxifene 在 PRISM 中有药物记录，逐药 ER+ / MCF7 敏感性结果见 `positive_control_sensitivity.csv`；它们用于核对 assay 是否覆盖已知内分泌药，不作为候选集有效性的证明。

## 文件

- `results/candidate_mapping_audit_top50.csv`、`candidate_mapping_audit_full.csv`：逐药标识映射审计。
- `results/cell_line_inventory.csv`：PRISM 细胞注释与 ER 分组来源。
- `results/candidate_prism_condition_map.csv`：通过结构映射的剂量/屏幕条件。
- `results/candidate_sensitivity_matrix.csv`：按 cell line × InChIKey 聚合的真实 PRISM LFC 与 sensitivity。
- `results/candidate_sensitivity_results.csv`：候选层汇总、S2 排名与 PRISM 敏感性。
- `results/s2_prism_rank_correlation.csv`：Spearman、Kendall 与 bootstrap 95%区间。
- `results/candidate_vs_random_test.csv` / `candidate_vs_random_null.csv`：同大小随机对照。
- `results/er_specificity_candidate_summary.csv`、`er_specificity_random_test.csv`、`positive_control_inventory.csv`：ER 分组逐药敏感性、覆盖数匹配随机检验和内分泌阳性对照清单。
- `results/positive_control_sensitivity.csv`：fulvestrant、tamoxifen、raloxifene 在 ER+ 组及 MCF7 的 PRISM 敏感性。
- `results/run_manifest.json`：来源、参数及输入 SHA-256。
- `figures/s2_prism_rank_scatter.png`、`candidate_vs_random.png`、`er_specificity_scatter.png`：由实际结果生成。

## 可复现信息

随机种子 {SEED}；随机对照 {N_PERM:,} 次；Spearman bootstrap {N_BOOT:,} 次；RDKit {rdBase.rdkitVersion}。DepMap model 元数据：Public 24Q4。输入哈希保存在 manifest。
"""
    (REPORTS / "exp011_report.md").write_text(report, encoding="utf-8")
    # Stable, descriptive filenames for downstream integration and review.
    map_all.to_csv(RESULTS / "candidate_compound_mapping.csv", index=False)
    map_all.to_csv(RESULTS / "compound_mapping_audit.csv", index=False)
    cell_meta.to_csv(RESULTS / "prism_cell_line_inventory.csv", index=False)
    cell_meta.loc[cell_meta.primary_tissue.eq("breast")].to_csv(RESULTS / "er_status_audit.csv", index=False)
    pd.read_csv(RESULTS / "candidate_sensitivity_matrix.csv", low_memory=False).to_csv(RESULTS / "drug_sensitivity_matrix.csv", index=False)
    pd.read_csv(RESULTS / "s2_prism_rank_correlation.csv").to_csv(RESULTS / "s2_sensitivity_correlation.csv", index=False)
    manifest["output_sha256"]={p.relative_to(ROOT).as_posix():sha256(p) for folder in [RESULTS,FIGURES,REPORTS] for p in folder.iterdir() if p.is_file() and p.name not in {"run_manifest.json"}}
    (RESULTS / "run_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (ROOT / "experiment_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status":manifest["formal_status"],"matrix":matrix.shape,"mapped_top50":top_mapped,"mapped_full":all_mapped,"cell_er_groups":er_counts,"correlations":corr_rows,"observed_random_test":observed,"empirical_p":p_emp}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
