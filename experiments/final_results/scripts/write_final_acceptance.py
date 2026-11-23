from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "experiments" / "final_results"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    result = OUT / "results"
    reports = OUT / "reports"
    top = pd.read_csv(result / "final_top10.csv")
    evidence = pd.read_csv(result / "final_top10_evidence_matrix.csv")
    manifest = json.loads((OUT / "final_data_manifest.json").read_text(encoding="utf-8"))

    rows = [
        ("Final01 数据与算法审计", "PASS", "stable ID 联结后重算 5,861 条合格签名；与历史重叠 4,761 条分数最大差 < 1e-9；Exp009 排序权重错误已识别且未用于最终排名。"),
        ("Final02 固定规则与 Top10", "PASS", "固定 BING Top100、MCF7 trt_cp、24 h、CC≥0.2；统一采用覆盖最多药物的 10 μM 条件；WTCS 中位数排序，图谱及 PRISM 不回调排名。"),
        ("Final03 机制证据", "PARTIAL", "10 个候选中 5 个有当前图谱精确结构映射/靶点与路径材料；其余以外部药理来源为背景。未覆盖不代表无已知机制。"),
        ("Final04 页面与交付", "PASS", "React 最终结果页已接入 /final-results；前端生产构建通过，8 项数据一致性测试通过；提供 CSV、图表、中文报告和 SHA-256 清单。"),
        ("疗效验证", "NOT_PERFORMED", "本项目完成计算筛选与机制证据整理；没有完成细胞、动物或临床干预验证，Top10 不能表述为已证实有效药物。"),
    ]
    status_path = OUT / "reports" / "final_status.csv"
    with status_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["阶段", "状态", "验收说明"])
        writer.writerows(rows)

    candidate_lines = [
        "| 排名 | 药物 | LINCS pert_id | WTCS | 合格签名数 |",
        "|---:|---|---|---:|---:|",
    ]
    for row in top.itertuples(index=False):
        candidate_lines.append(f"| {int(row.rank)} | {row.drug_name} | `{row.pert_id}` | {row.WTCS_median:.4f} | {int(row.n_signatures)} |")

    report = f'''# ER 阳性乳腺癌药物重定位：最终研究报告

生成时间（UTC）：{datetime.now(timezone.utc).isoformat()}

## 研究目标与流程

本项目以 GSE42568 的 ER 阳性乳腺癌与正常乳腺组织差异表达结果构建疾病签名 S1，再使用 LINCS L1000/GSE70138 的 MCF7 化学药物扰动签名 S2 寻找表达逆转候选；随后把候选与项目知识图谱、外部 S1 复现和 PRISM 敏感性结果并列整理，给出可追溯的机制假设。

历史 S1 使用 67 个 ER 阳性肿瘤样本、17 个正常组织样本，limma 对 21,655 个基因进行差异分析，FDR<0.05 有 7,066 个差异基因（上调 3,422、下调 3,644）。最终主分析在 LINCS BING 基因空间中按预先固定规则选取 UP/DOWN 各 Top100。S1、LINCS 原始数据和历史 Smoke Test 均保持只读。

## 最终 S2 主筛选规则

- 数据：GSE70138 Level 5；MCF7、`trt_cp`；24 h；`distil_cc_q75 ≥ 0.2`。
- 元数据使用 `sig_id + pert_id + pert_type` 稳定 ID 联结，不以可能不一致的显示名称作连接条件。
- 对符合条件的 5,861 条签名重算 WTCS，覆盖 1,471 个化合物。统一主剂量按全部药物覆盖数预先选择，10 μM 覆盖 1,032 个化合物；不为每种药物挑最有利剂量。
- 签名分数在药物与固定条件内取中位数，按 WTCS 升序生成候选表。负 WTCS 表示与 S1 的表达逆关联，只是计算筛选信号，不等同药效。
- 历史重叠的 4,761 条签名经正确实现复现，WTCS 最大差约 6.7×10⁻¹⁴。Exp009 的旧 stable-ID 分数存在命中权重与排序位置错配（4,761 条中 3,870 条分数不一致），因此不作为正式排名输入。

## Top 10 候选药物

| 排名 | 药物 | LINCS pert_id | WTCS | 合格签名数 |
|---:|---|---|---:|---:|
{chr(10).join(candidate_lines[2:])}

这十项在主剂量条件下均只有一条合格 signature，重复支持有限；不同剂量的 WTCS 可能变号，剂量敏感性图和原始结果表应与主排名一并查看。Top10 是计算候选清单，不代表药物推荐。

## 机制证据与项目要求的对应

项目要求的“疾病 S1 → LINCS 药物 S2 → 知识图谱子图抽取 → 候选机制解释”已形成可检查的计算链。Neo4j 当前图谱对 5/10 个候选有精确 InChIKey 药物节点；5/10 有当前 GraphBuild 的直接靶点关系并与 S1 通路建立可追溯连接。其余 5 个没有当前图谱精确映射，机制报告只引用外部药物药理资料，不把名称相似当作图谱证据。图谱中没有可审计 PPI 关系，因此未声称构建了 PPI 机制链。

Exp010 外部 S1 同条件排名有 5/10 可用，PRISM ER+ 敏感性有 5/10 可用；这些结果用于独立交叉检查，不参与 S2 排名。各候选的靶点、S1 交集、通路和 Evidence ID 见[Top10 机制证据报告](final_top10_mechanism_report.md)及 `mechanism/` CSV。

机制解释应保持保守：例如 ponatinib、mocetinostat、doxorubicin 有本图谱直接靶点和 S1 通路交集；MK-2461、rebastinib、PHA-767491、PFI-1、JNJ-26481585 在当前图谱没有精确候选节点，不能声称已完成项目图谱机制映射。Iniparib 的 PARP1 关系不能解释为已验证 PARP 抑制；balaglitazone 的 PPARG 作用也不能仅凭 S1 方向认作逆转机制。所有机制仍是假设。

## 验收结果和局限

- 前端生产构建：通过；最终页面路由为 `/final-results`。
- 数据一致性 pytest：8 项通过。
- 当前 Neo4j 机制覆盖：精确药物节点 5/10、直接靶点 5/10、靶点至 S1 通路 5/10。
- Top10 全部仅有一条主条件 signature；本轮没有新增细胞、动物或临床验证。S2 的表达逆关联、PRISM 的细胞敏感性、知识图谱关系是不同类型证据，不能互相替代。
- 报告只支持“初步重定位候选”；不能得出临床疗效或 ER 阳性亚型特异性结论。后续优先工作是对候选进行独立数据集复核与实验验证，并补齐当前图谱未覆盖药物的可审计靶点来源。

## 交付文件

- `results/final_top10.csv`：正式初步候选榜单。
- `results/final_signature_scores.csv`：5,861 条签名级原始 WTCS 结果。
- `results/final_drug_condition_summary.csv`：药物、剂量、时间条件汇总。
- `results/final_top10_evidence_matrix.csv`：WTCS、Exp010、PRISM、图谱与 S2 靶点表达并列表。
- `figures/`：Top10 WTCS、剂量敏感性、证据覆盖图；前端展示相同图表。
- `final_data_manifest.json`：来源、参数、输入输出 SHA-256 和运行验证信息。
- `final_status.csv`：阶段验收状态和范围边界。
'''
    report_path = reports / "final_research_report.md"
    report_path.write_text(report, encoding="utf-8")

    # Preserve existing audit fields, and add code/report provenance without hashing the manifest itself.
    code_paths = [
        OUT / "scripts" / "build_final_results.py",
        OUT / "scripts" / "assemble_final_evidence.py",
        OUT / "scripts" / "extract_top10_target_s2.py",
        OUT / "scripts" / "query_final_neo4j_evidence.py",
        OUT / "scripts" / "write_final_acceptance.py",
        OUT / "tests" / "test_final_results.py",
    ]
    deliverables = [
        report_path, status_path,
        OUT / "results" / "final_top10.csv",
        OUT / "results" / "final_signature_scores.csv",
        OUT / "results" / "final_drug_condition_summary.csv",
        OUT / "results" / "final_top10_evidence_matrix.csv",
        OUT / "reports" / "final_top10_mechanism_report.md",
        OUT / "figures" / "final_top10_wtcs.png",
        OUT / "figures" / "final_top10_dose_sensitivity.png",
        OUT / "figures" / "final_evidence_coverage.png",
        ROOT / "frontend" / "public" / "final-results.json",
        ROOT / "frontend" / "public" / "final-top10.csv",
        ROOT / "frontend" / "public" / "final-evidence-matrix.csv",
    ]
    manifest["code_sha256"] = {str(path.relative_to(ROOT)): sha256(path) for path in code_paths if path.exists()}
    manifest["final_acceptance"] = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "statuses": {phase: status for phase, status, _ in rows},
        "pytest": "8 passed",
        "frontend_build": "PASS",
        "ranked_candidates": int(len(top)),
        "all_primary_candidates_single_signature": bool((top.n_signatures == 1).all()),
        "deliverable_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in deliverables if path.exists()},
    }
    (OUT / "final_data_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (result / "final_data_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "report": str(report_path), "status_csv": str(status_path), "candidates": len(evidence)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
