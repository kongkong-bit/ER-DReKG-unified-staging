import json
import os
from pathlib import Path
import subprocess


def limma_runtime(repo_root: Path, required_packages: tuple[str, ...] = ("limma",)) -> tuple[Path, dict[str, str]]:
    configured = os.environ.get("DISEASEGRAPH_R_ENV")
    env_root = Path(configured).resolve() if configured else repo_root / "experiments" / "s1_pathway_enrichment" / "r-env"
    r_home = env_root / "lib" / "R"
    rscript = env_root / "Scripts" / "Rscript.exe"
    missing = [package for package in required_packages if not (r_home / "library" / package).is_dir()]
    if not rscript.is_file() or missing:
        detail = ", ".join(missing) if missing else "Rscript"
        raise RuntimeError(f"项目 R 环境缺少 {detail}；请按环境说明配置 DISEASEGRAPH_R_ENV")
    env = os.environ.copy()
    env["R_HOME"] = str(r_home)
    env["LC_ALL"] = "C"
    env["LANG"] = "C"
    env["LANGUAGE"] = "C"
    paths = [env_root / "Library" / "bin", env_root / "Library" / "usr" / "bin", env_root / "Scripts", r_home / "bin", r_home / "bin" / "x64"]
    env["PATH"] = os.pathsep.join([str(path) for path in paths] + [env.get("PATH", "")])
    return rscript, env


def run_limma_microarray(
    repo_root: Path,
    expression_path: Path,
    sample_metadata_path: Path,
    output_path: Path,
    positive_group: str,
    negative_group: str,
    identifier_type: str,
    fdr_threshold: float,
) -> dict:
    script = Path(__file__).parent / "pipelines" / "limma_microarray.R"
    if not script.is_file():
        raise RuntimeError("limma microarray 插件脚本缺失")
    rscript, env = limma_runtime(repo_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [str(rscript), str(script), str(expression_path), str(sample_metadata_path), str(output_path), positive_group, negative_group, identifier_type, str(fdr_threshold)]
    try:
        result = subprocess.run(command, cwd=repo_root, env=env, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=1800, check=False)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("limma 分析超过 30 分钟运行上限") from error
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "未知 R 错误")[-4000:]
        raise RuntimeError(f"limma 分析失败：{detail}")
    summary_path = Path(str(output_path) + ".summary.json")
    if not output_path.is_file() or not summary_path.is_file():
        raise RuntimeError("limma 未生成完整的结果表和运行摘要")
    try:
        return json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("limma 运行摘要无法解析") from error


def run_rnaseq_edger_voom(
    repo_root: Path,
    counts_path: Path,
    sample_metadata_path: Path,
    output_path: Path,
    positive_group: str,
    negative_group: str,
    identifier_type: str,
    fdr_threshold: float,
) -> dict:
    script = Path(__file__).parent / "pipelines" / "rnaseq_edger_voom.R"
    if not script.is_file():
        raise RuntimeError("edgeR-voom RNA-seq 插件脚本缺失")
    rscript, env = limma_runtime(repo_root, ("limma", "edgeR"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [str(rscript), str(script), str(counts_path), str(sample_metadata_path), str(output_path), positive_group, negative_group, identifier_type, str(fdr_threshold)]
    try:
        result = subprocess.run(command, cwd=repo_root, env=env, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=1800, check=False)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("RNA-seq 差异分析超过 30 分钟运行上限") from error
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "未知 R 错误")[-4000:]
        raise RuntimeError(f"edgeR-voom 分析失败：{detail}")
    summary_path = Path(str(output_path) + ".summary.json")
    if not output_path.is_file() or not summary_path.is_file():
        raise RuntimeError("edgeR-voom 未生成完整的结果表和运行摘要")
    try:
        return json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("edgeR-voom 运行摘要无法解析") from error


def run_project_s1_enrichment(repo_root: Path, s1_path: Path, output_dir: Path, identifier_type: str, contrast: str, fdr_threshold: float) -> dict:
    """Run project-scoped GO BP, Reactome ORA, and Hallmark GSEA on a completed S1 table."""
    script = Path(__file__).parent / "pipelines" / "project_s1_enrichment.R"
    if not script.is_file():
        raise RuntimeError("项目级 S1 富集分析脚本缺失")
    if not s1_path.is_file():
        raise RuntimeError("登记的 S1 结果文件缺失")
    packages = ("clusterProfiler", "ReactomePA", "org.Hs.eg.db", "fgsea", "ggplot2", "dplyr", "readr", "tidyr", "jsonlite", "AnnotationDbi")
    rscript, env = limma_runtime(repo_root, packages)
    env["DISEASEGRAPH_REPO_ROOT"] = str(repo_root.resolve())
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [str(rscript), str(script), str(s1_path), str(output_dir), identifier_type, contrast, str(fdr_threshold)]
    try:
        result = subprocess.run(command, cwd=repo_root, env=env, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=1800, check=False)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("S1 通路富集分析超过 30 分钟运行上限") from error
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "未知 R 错误")[-5000:]
        raise RuntimeError(f"S1 通路富集分析失败：{detail}")
    summary_path = output_dir / "summary.json"
    required = [output_dir / f"{name}.csv" for name in ("gene_mapping_audit", "go_up", "go_down", "reactome_up", "reactome_down", "hallmark_gsea", "pathway_gene_links")]
    if not summary_path.is_file() or not all(path.is_file() for path in required):
        raise RuntimeError("S1 通路富集分析未生成全部必需结果表和摘要")
    try:
        return json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("S1 通路富集分析摘要无法解析") from error
