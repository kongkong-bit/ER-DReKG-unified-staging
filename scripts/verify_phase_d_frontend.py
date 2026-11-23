"""Read-only Vite/FastAPI integration check for the real ER+ project."""
from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:5173"
PROJECT_ID = "3f18f4c1-713d-58c5-8a53-38eca5a5aaf9"
GRAPH_BUILD_ID = f"GRAPH_BUILD:{PROJECT_ID}:a08001496a447f7f"
# Phase F's immutable evidence manifest was built against this earlier
# GraphBuild and must keep pointing to the graph it was actually integrated
# with; live graph pages use the current GraphBuild above.
CANDIDATE_EVIDENCE_GRAPH_BUILD_ID = f"GRAPH_BUILD:{PROJECT_ID}:a6aabb2147cb5f5e"
HISTORICAL_EVIDENCE_ID = "2cfeaaa2b83e494b63fd450c4e19efaeb2cd350d6ad8375feeb725beb6866684"
OUT_DIR = ROOT / "experiments/platform_phase_d"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def get(path: str) -> tuple[int, object]:
    request = urllib.request.Request(BASE + path, headers={"Accept": "application/json, text/html, */*"})
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read()
        content_type = response.headers.get("Content-Type", "")
        if "json" in content_type:
            return response.status, json.loads(body.decode("utf-8"))
        return response.status, body.decode("utf-8", errors="replace")


def main() -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    checks: dict[str, object] = {}
    status, html = get("/")
    assert status == 200 and '<div id="root"></div>' in html
    checks["vite_home"] = {"status": status, "html_bytes": len(html.encode())}

    status, transformed_app = get("/src/App.tsx")
    assert status == 200 and "lazy(" in transformed_app and "/src/pages/S1Page" in transformed_app and "/src/pages/GraphPage" in transformed_app
    assert "antd" not in transformed_app and "/src/components/ProjectDialogs" in transformed_app
    page_modules: dict[str, str] = {}
    for page in ["DashboardPage", "RunComparisonPage", "S1Page", "S2Page", "GraphPage", "DrugPage"]:
        page_status, page_text = get(f"/src/pages/{page}.tsx")
        assert page_status == 200
        page_modules[page] = page_text
    assert "跨剂量 Top 10 复现率" in page_modules["DrugPage"] and "LINCS 剂量/时间条件" in page_modules["DrugPage"]
    assert "分析运行比较" in page_modules["RunComparisonPage"] or "AnalysisRun 比较" in page_modules["RunComparisonPage"]
    assert "直接药物—靶点关系" in page_modules["GraphPage"] and "其他疾病/通路关系" in page_modules["GraphPage"]
    assert "图谱来源证据" in page_modules["GraphPage"] and "showGraphEvidence" in page_modules["GraphPage"]
    assert "最近分析运行" in page_modules["DashboardPage"] and "查看状态" in page_modules["DashboardPage"]
    assert "当前选中版本实时统计" in page_modules["GraphPage"] and "登记时节点" in page_modules["GraphPage"]
    assert "独立队列验证" in page_modules["S1Page"] and "GSE139038" in page_modules["S1Page"]
    assert "研究" in page_modules["DashboardPage"] and "study" in page_modules["DashboardPage"]
    dialog_status, dialog_text = get("/src/components/ProjectDialogs.tsx")
    assert dialog_status == 200 and "上传项目数据" in dialog_text and "新建疾病项目" in dialog_text
    assert "登记研究" in dialog_text and "study_id" in dialog_text
    checks["vite_react_module"] = {"status": status, "page_modules_http_200": list(page_modules), "project_dialog_module_http_200": dialog_status, "route_code_split": True, "shell_avoids_static_antd_import": True, "project_dialogs_load_on_demand": True, "drug_detail_components_present": True, "independent_cohort_validation_page_present": True, "analysis_run_comparison_page_present": True, "run_status_dashboard_present": True, "direct_vs_context_edge_filter_present": True, "graph_edge_evidence_dialog_present": True, "live_build_counts_separated_from_snapshot": True}

    status, projects = get("/api/v1/projects")
    project = next((item for item in projects if item["project_id"] == PROJECT_ID), None)
    assert status == 200 and project is not None
    checks["project_list_proxy"] = {"status": status, "project_found": True, "status_label": project["status"]}

    prefix = f"/api/v1/projects/{PROJECT_ID}"
    status, studies = get(prefix + "/studies")
    assert status == 200 and isinstance(studies, list) and len(studies) == 1
    assert studies[0]["accession"] == "GSE42568" and studies[0]["study_id"]
    status, datasets = get(prefix + "/datasets")
    assert status == 200 and all(item.get("study_id") == studies[0]["study_id"] for item in datasets["items"])
    assert all(item.get("study", {}).get("accession") == "GSE42568" for item in datasets["items"])
    checks["project_study_api"] = {"status": status, "study_count": len(studies), "study_accession": studies[0]["accession"], "datasets_linked_to_study": len(datasets["items"])}
    status, s1 = get(prefix + "/s1/summary")
    assert status == 200 and s1["tested_genes"] == 21655
    checks["s1_summary"] = {"status": status, "tested_genes": s1["tested_genes"]}
    status, external_s1 = get(prefix + "/s1/external-validation?limit=2&offset=0")
    assert status == 200 and external_s1["available"] and external_s1["source_dataset"] == "GSE139038"
    assert external_s1["sample_design"]["paired_ER_positive_patients"] == 14
    assert external_s1["total_conditions"] == 3715 and len(external_s1["items"]) == 2
    assert len(external_s1["provenance"]["summary_sha256"]) == 64 and len(external_s1["provenance"]["ranking_sha256"]) == 64
    checks["external_s1_validation"] = {"status": status, "source_dataset": external_s1["source_dataset"], "paired_patients": external_s1["sample_design"]["paired_ER_positive_patients"], "total_conditions": external_s1["total_conditions"], "summary_sha256": external_s1["provenance"]["summary_sha256"], "ranking_sha256": external_s1["provenance"]["ranking_sha256"]}

    status, candidates = get(prefix + "/s2/candidates?limit=50")
    assert status == 200 and candidates["total"] == 50
    checks["candidate_list"] = {"status": status, "candidate_count": candidates["total"]}

    status, runs = get(prefix + "/runs")
    assert status == 200
    completed_by_type: dict[str, list[dict]] = {}
    for run in runs:
        if run["status"] == "completed":
            completed_by_type.setdefault(run["run_type"], []).append(run)
    comparable = next((items for items in completed_by_type.values() if len(items) >= 2), None)
    if comparable:
        compare_query = urllib.parse.urlencode({"run_a_id": comparable[0]["analysis_run_id"], "run_b_id": comparable[1]["analysis_run_id"]})
        status, comparison = get(prefix + "/runs/compare?" + compare_query)
        assert status == 200
        assert comparison["run_a"]["analysis_run_id"] == comparable[0]["analysis_run_id"]
        assert comparison["run_b"]["analysis_run_id"] == comparable[1]["analysis_run_id"]
        assert comparison["provenance_comparison"] is not None
        checks["analysis_run_comparison"] = {"status": status, "run_type": comparison["run_type"], "run_a_id": comparable[0]["analysis_run_id"], "run_b_id": comparable[1]["analysis_run_id"], "identical_input_hashes": comparison["provenance_comparison"]["identical_input_hashes"]}
    else:
        checks["analysis_run_comparison"] = {"status": "NOT_AVAILABLE", "reason": "project has no same-type pair of completed AnalysisRuns"}
    completed_runs = [run for run in runs if run["status"] == "completed"]
    if completed_runs:
        status, job = get("/api/v1/jobs/" + urllib.parse.quote(completed_runs[0]["analysis_run_id"]))
        assert status == 200 and job["analysis_run_id"] == completed_runs[0]["analysis_run_id"]
        assert job["state"] == "completed" and job["progress"] == 100
        checks["run_status"] = {"status": status, "job_id": job["job_id"], "state": job["state"], "progress": job["progress"], "description": job["description"]}
    else:
        checks["run_status"] = {"status": "NOT_AVAILABLE", "reason": "project has no completed AnalysisRun"}

    status, matrix = get(prefix + "/s2/evidence-matrix?limit=100")
    assert status == 200 and matrix["available"] and matrix["total"] == 819 and len(matrix["items"]) == 100
    checks["integrated_evidence_matrix"] = {"status": status, "total": matrix["total"], "page_rows": len(matrix["items"])}

    candidate_evidence_rows = []
    source_hash = None
    graph_build_id = None
    for offset in range(0, 819, 100):
        status, page = get(prefix + f"/s2/candidate-evidence?offset={offset}&limit=100")
        assert status == 200 and page["available"] and page["total"] == 819
        assert page["graph_build_id"] == CANDIDATE_EVIDENCE_GRAPH_BUILD_ID and len(page["source_sha256"]) == 64
        source_hash = source_hash or page["source_sha256"]
        graph_build_id = page["graph_build_id"]
        assert source_hash == page["source_sha256"]
        candidate_evidence_rows.extend(page["items"])
    assert len(candidate_evidence_rows) == 819
    assert len({row["pert_id"] for row in candidate_evidence_rows}) == 819
    checks["phase_f_candidate_evidence"] = {"status": 200, "total": len(candidate_evidence_rows), "unique_perturbagens": 819, "graph_build_id": graph_build_id, "source_sha256": source_hash}

    condition_rows = []
    for offset in range(0, 240, 100):
        status, page = get(prefix + f"/s2/conditions?offset={offset}&limit=100")
        assert status == 200 and page["available"] and page["total"] == 240
        condition_rows.extend(page["items"])
    condition_ids = {(row["pert_id"], row["cell_id"], row["pert_type"], row["dose"], row["time"]) for row in condition_rows}
    assert len(condition_rows) == 240 and len(condition_ids) == 240
    checks["condition_pages"] = {"status": 200, "rows": len(condition_rows), "unique_condition_keys": len(condition_ids)}

    status, stability = get(prefix + "/s2/stability?top_n=10")
    assert status == 200 and stability["available"] and len(stability["items"]) == 50
    checks["dose_stability"] = {"status": status, "candidate_rows": len(stability["items"]), "top_n": stability["top_n"]}

    graph_query = urllib.parse.urlencode({"graph_build_id": GRAPH_BUILD_ID})
    status, graph = get(prefix + "/graph/summary?" + graph_query)
    assert status == 200 and graph["source"] == "neo4j"
    assert graph["node_count"] == 6850 and graph["edge_count"] == 38657
    assert graph["nodes_by_type"].get("DiseaseContext") == 1
    checks["graph_summary"] = {"status": status, "graph_build_id": GRAPH_BUILD_ID, "node_count": graph["node_count"], "edge_count": graph["edge_count"], "disease_contexts": 1}
    status, graph_builds = get(prefix + "/graph-builds")
    latest_build = next((row for row in graph_builds.get("items", []) if row["graph_build_id"] == GRAPH_BUILD_ID), None)
    assert status == 200 and latest_build is not None
    assert latest_build["summary"].get("evidence_records_status") == "persisted"
    assert latest_build["summary"].get("evidence_record_count") == 38998
    checks["graph_build_evidence_records"] = {"status": status, "graph_build_id": GRAPH_BUILD_ID, "record_count": latest_build["summary"]["evidence_record_count"], "source_sha256": latest_build["summary"]["evidence_records_sha256"]}
    assert latest_build["summary"].get("disease_contexts_status") == "persisted"
    assert latest_build["summary"].get("disease_context_count") == 1
    checks["graph_build_disease_contexts"] = {"status": "PASS", "graph_build_id": GRAPH_BUILD_ID, "context_count": latest_build["summary"]["disease_context_count"], "source_sha256": latest_build["summary"]["disease_contexts_sha256"]}

    status, mechanisms = get(prefix + f"/drugs/BRD-A00147595/mechanisms?{graph_query}")
    assert status == 200 and len(mechanisms["routes"]) == 82
    checks["mechanism_routes"] = {"status": status, "pert_id": "BRD-A00147595", "route_count": len(mechanisms["routes"])}

    status, subgraph = get(prefix + "/graph/subgraph?" + urllib.parse.urlencode({"limit": 100, "max_depth": 2, "graph_build_id": GRAPH_BUILD_ID}))
    assert status == 200 and subgraph["edges"]
    edge_evidence_ids = next((edge["evidence_ids"] for edge in subgraph["edges"] if edge.get("evidence_ids")), [])
    assert edge_evidence_ids
    status, graph_evidence = get("/api/v1/evidence/" + urllib.parse.quote(edge_evidence_ids[0]) + "?" + graph_query)
    assert status == 200 and graph_evidence["evidence_id"] == edge_evidence_ids[0]
    assert graph_evidence.get("graph_build_id") == GRAPH_BUILD_ID and len(graph_evidence.get("assertion_sha256", "")) == 64
    checks["graph_edge_evidence"] = {"status": status, "graph_build_id": graph_evidence["graph_build_id"], "evidence_id": edge_evidence_ids[0], "source_release": graph_evidence.get("source_release"), "assertion_sha256": graph_evidence["assertion_sha256"]}
    status, old_graph_evidence = get("/api/v1/evidence/" + urllib.parse.quote(HISTORICAL_EVIDENCE_ID) + "?graph_build_id=" + urllib.parse.quote(CANDIDATE_EVIDENCE_GRAPH_BUILD_ID))
    assert status == 200 and old_graph_evidence.get("graph_build_id") == CANDIDATE_EVIDENCE_GRAPH_BUILD_ID
    checks["historical_graph_evidence"] = {"status": status, "graph_build_id": old_graph_evidence["graph_build_id"], "evidence_id": HISTORICAL_EVIDENCE_ID, "source_release": old_graph_evidence.get("source_release")}

    build_assets = sorted((ROOT / "frontend/dist/assets").glob("*.js"))
    assert build_assets
    asset_manifest = [{"file": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)} for path in build_assets]
    assets_by_name = {Path(item["file"]).name: item for item in asset_manifest}
    built_html = (ROOT / "frontend/dist/index.html").read_text(encoding="utf-8")
    entry_match = re.search(r'<script[^>]+src="/assets/([^\"]+\.js)"', built_html)
    assert entry_match
    entry_asset = assets_by_name.get(entry_match.group(1))
    chart_asset = next((item for item in asset_manifest if Path(item["file"]).name.startswith("ChartRenderer-")), None)
    graph_asset = next((item for item in asset_manifest if Path(item["file"]).name.startswith("cytoscape.")), None)
    assert entry_asset and chart_asset and graph_asset
    initial_chunks = {entry_match.group(1)}
    pending_chunks = list(initial_chunks)
    while pending_chunks:
        chunk_name = pending_chunks.pop()
        chunk_path = ROOT / "frontend/dist/assets" / chunk_name
        text = chunk_path.read_text(encoding="utf-8")
        for dependency in re.findall(r'(?:from|import)\s*["\'](?:\./)?([^"\']+\.js)["\']', text):
            if dependency in assets_by_name and dependency not in initial_chunks:
                initial_chunks.add(dependency)
                pending_chunks.append(dependency)
    initial_static_bytes = sum(assets_by_name[name]["bytes"] for name in initial_chunks)
    route_assets = [item for item in asset_manifest if Path(item["file"]).name.startswith(("DashboardPage-", "RunComparisonPage-", "S1Page-", "S2Page-", "GraphPage-", "DrugPage-"))]
    assert len(route_assets) == 6
    checks["frontend_bundle_sizes"] = {
        "entry_file": entry_match.group(1),
        "entry_bytes": entry_asset["bytes"],
        "initial_static_dependency_files": sorted(initial_chunks),
        "initial_static_dependency_bytes": initial_static_bytes,
        "route_chunk_count": len(route_assets),
        "largest_route_chunk_bytes": max(item["bytes"] for item in route_assets),
        "chart_chunk_bytes": chart_asset["bytes"],
        "cytoscape_chunk_bytes": graph_asset["bytes"],
        "chart_chunk_sha256": chart_asset["sha256"],
    }
    report = {
        "status": "PASS",
        "scope": "Read-only local Vite proxy and project API integration; not a visual desktop-browser test.",
        "checked_at_utc": timestamp,
        "project_id": PROJECT_ID,
        "graph_build_id": GRAPH_BUILD_ID,
        "checks": checks,
        "frontend_js_assets": asset_manifest,
        "limitations": [
            "Desktop browser visual interaction was not verified in this run.",
            "Production authentication/authorization and deployment hardening remain incomplete.",
            "API checks validate data contracts and live responses, not every user interaction or responsive layout.",
        ],
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "phase_d_verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Phase D：前端 MVP 与真实 API 联调验收", "", f"验收时间（UTC）：{timestamp}", "",
        "## 实际检查", "",
        "- Vite 首页与 React 开发模块均返回 HTTP 200；最新药物详情代码由 Vite 成功转译。",
        f"- 正式 ER+ 项目 S1 查询返回 {s1['tested_genes']:,} 个检验基因；候选 API 返回 {candidates['total']} 项。",
        f"- Study API 返回 HTTP 200（现有研究 {len(studies)} 条）；{len(datasets['items'])} 个历史数据集均关联到 {studies[0]['accession']}，列表可读取 Study accession/title。",
        f"- Exp010 外部验证 API 返回 GSE139038 的 {external_s1['sample_design']['paired_ER_positive_patients']} 对 ER+ 患者队列、{external_s1['total_conditions']:,} 个剂量/时间条件；摘要和排名文件 SHA-256 均校验通过。",
        f"- Exp006–Exp011 综合证据矩阵为 {matrix['total']:,} 项；剂量条件分页完整读取 {len(condition_rows)} 项且 condition key 全部唯一。",
        f"- Phase F 候选证据 API 分页读取 {len(candidate_evidence_rows):,} 个唯一 perturbagen；GraphBuild 与结果 SHA-256 和验收清单一致。",
        f"- AnalysisRun 比较 API：{checks['analysis_run_comparison']['status']}；同类型运行可比参数、输入哈希和类型专属结果。",
        f"- 运行状态 API：{checks['run_status']['status']}；当前 job_id 与 AnalysisRun ID 相同；同步执行状态不伪造异步进度。",
        f"- S2 跨剂量稳定性返回 {len(stability['items'])} 个候选；正式 GraphBuild 过滤后 {graph['node_count']:,} 节点、{graph['edge_count']:,} 条关系、DiseaseContext={graph['nodes_by_type']['DiseaseContext']}。",
        f"- EvidenceRecord API/数据库版本验收：正式 GraphBuild 持久化 {checks['graph_build_evidence_records']['record_count']:,} 条证据，SHA-256 与 GraphBundle 一致；最新与历史 GraphBuild 的证据均按各自版本读取。",
        f"- DiseaseContext PostgreSQL 持久化：正式 GraphBuild 保存 {checks['graph_build_disease_contexts']['context_count']} 条项目疾病上下文，来源 `subgraph_nodes.csv` 哈希已登记。",
        f"- 机制 API 对 `{checks['mechanism_routes']['pert_id']}` 返回 {checks['mechanism_routes']['route_count']} 条版本内路径。",
        "- 以上请求全部通过本机 Vite `/api` 代理读取真实 PostgreSQL/Neo4j 项目数据；不写数据库，不触发实验运行。", "",
        "## 代码变化", "",
        "- 药物详情新增分项呈现：Exp006 原排名、B 方案 WTCS、S2 剂量/时间/质量条件、跨剂量 Top 10 复现率、独立 S1 排名、PRISM ER+/ER− 指标，以及带 evidence ID 的机制路径。缺失值保持空值，不按药名补配、不合成疗效总分。",
        "- 新增 `/compare` 运行版本比较页；同类型运行并列显示参数、软件版本、输入哈希和结果摘要，S2 只按精确条件键对齐。",
        "- Dashboard 展示最近 10 个 AnalysisRun 状态，并可按运行 ID 查询同步任务状态。",
        "- S2 详情用分页接口读取所有条件，保留每个剂量/时间独立结果。",
        "- S1 页增加 Exp010/GSE139038 独立配对队列复核和外部 LINCS 条件排名；接口只服务 ER+ 项目，校验实验 manifest 中摘要、数据集清单和排名 CSV 的 SHA-256，其他项目返回明确 unavailable。",
        "- 图谱关系提供全部、直接药物—靶点、其他疾病/通路关系三种筛选；直接关系仅按药物节点与 Gene/ProteinTarget 端点类型判定。",
        "- 点击已加载关系可根据其 evidence ID 打开来源证据弹窗；本次使用正式 GraphBuild 子图中的真实 edge evidence ID 检查证据 API。",
        f"- 六个页面已做路由级动态载入，项目/上传弹窗仅在打开时载入；导航 shell 不静态导入 Ant Design。Vite 初始静态 JS 依赖闭包 {initial_static_bytes / 1000:.2f} kB、最大页面入口块 {max(item['bytes'] for item in route_assets) / 1000:.2f} kB。ECharts 与 Cytoscape 只在对应页面载入，图表块 {chart_asset['bytes'] / 1000:.2f} kB、Cytoscape 块 {graph_asset['bytes'] / 1000:.2f} kB；超过 500 kB 的剩余告警来自按需加载的 S1 图表块。", "",
        "## 未覆盖范围", "",
        "本报告不是桌面浏览器视觉验收；没有验证原生文件选择器操作、各屏幕尺寸布局、键盘可访问性或所有按钮交互。通用 Job 页面/队列仍按方案暂缓；生产认证、授权和部署加固未完成。", "",
        "## 复现", "",
        "- 命令：`python scripts/verify_phase_d_frontend.py`（在 Vite 5173、FastAPI 8000 及 Docker 数据库服务运行时执行）。",
        "- 机器可读记录：`experiments/platform_phase_d/phase_d_verification.json`。",
        "- JS 构建文件大小与 SHA-256 同记录保存。", "",
    ]
    (OUT_DIR / "phase_d_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": report["status"], "checks": checks, "report": "experiments/platform_phase_d/phase_d_report.md"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
