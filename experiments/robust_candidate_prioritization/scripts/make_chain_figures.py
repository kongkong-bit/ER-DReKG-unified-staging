"""Generate one mechanism-chain figure per v4 A-list candidate."""
from __future__ import annotations

import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyArrowPatch

ROOT = Path(__file__).resolve().parents[3]
EXP = ROOT / "experiments/robust_candidate_prioritization"
OUT = EXP / "figures"
OUT.mkdir(parents=True, exist_ok=True)
BUNDLE = Path(
    r"D:\AAA\学习\大三上\生物医学信息学\ER-DReKG-KG-delivery-20261120"
    r"\ER-DReKG-KG-delivery-20261120\03_GraphBundle\e0421796-2aff-47e2-9228-d683eab05fa9"
)

DRUG_C = "#12406e"
TGT_C = "#b03a2e"
ER_C = "#2e7d32"
OTH_C = "#6b7280"
INK = "#1f2937"

top10 = pd.read_csv(EXP / "results/v4_mechanism_top10.csv")
chains = pd.read_csv(EXP / "results/v4_chains.csv")
links = pd.read_csv(ROOT / "experiments/s1_pathway_enrichment/pathway_gene_links.csv")
ev = pd.read_csv(BUNDLE / "evidence_records.csv", low_memory=False)

ev_index = {(r.subject_id, r.predicate, r.object_id): r.evidence_id for r in ev.itertuples()}


def is_er(name: str) -> bool:
    up = name.upper()
    return "ESTROGEN" in up or up.startswith("ESR-") or "ESR-MEDIATED" in up


def pick_pathways(gene: str, raw: str, er_flag: bool) -> list[tuple[str, float, str]]:
    names = [x.strip() for x in raw.split(";") if x.strip()]
    rows = []
    for name in names:
        sub = links[(links.gene_symbol.str.upper() == gene) & (links.pathway == name)]
        if len(sub) == 0:
            continue
        rows.append((name, float(sub.adjusted_p.iloc[0]), str(sub.analysis.iloc[0])))
    er_rows = [r for r in rows if is_er(r[0])]
    if er_flag and er_rows:
        chosen = sorted(er_rows, key=lambda r: r[1])[:2]
    else:
        chosen = sorted(rows, key=lambda r: r[1])[:2]
    return chosen


def wrap(name: str, width: int = 24) -> str:
    words, lines, cur = name.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return "\n".join(lines[:3]) + ("…" if len(lines) > 3 else "")


def slug(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()


for row in top10.sort_values("rank_mech").itertuples():
    sub = chains[chains.pert_id == row.pert_id].copy()
    if sub.empty:
        print("skip (no chains):", row.drug_name)
        continue
    blocks = []
    for ch in sub.itertuples():
        s, pred, obj = ch.evidence_keys.split("|")
        eid = ev_index.get((s, pred, obj), "")
        paths = pick_pathways(ch.target, str(ch.pathways), bool(ch.er_program))
        blocks.append({"target": ch.target, "relation": ch.relation, "logfc": float(ch.s1_logFC),
                       "eid": eid, "paths": paths, "er": bool(ch.er_program)})
    blocks.sort(key=lambda b: (0 if any(is_er(p[0]) for p in b["paths"]) else 1, -b["logfc"]))

    total_rows = sum(max(1, len(b["paths"])) for b in blocks)
    fig_h = max(3.8, 2.5 + 0.38 * total_rows)
    fig, ax = plt.subplots(figsize=(13.0, fig_h), dpi=300)
    ax.axis("off")
    ax.set_xlim(-0.45, 3.35)
    ax.set_ylim(-0.10, 1.26)

    def node(x, y, label, ec, fc="#ffffff", fs=8.3, lw=1.4):
        ax.text(x, y, label, ha="center", va="center", fontsize=fs, color=INK,
                bbox=dict(boxstyle="round,pad=0.38", fc=fc, ec=ec, lw=lw), zorder=3)

    def edge(p1, p2, color, label=None, lw=1.4, fs=6.8-0.6, ):
        ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=9, color=color,
                                     lw=lw, zorder=2, shrinkA=30, shrinkB=30))
        if label:
            ax.text((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2 + 0.012, label, ha="center",
                    va="bottom", fontsize=fs, color=color, zorder=4)

    # column headers
    for x, t in [(0.0, "Drug"), (1.10, "Direct target (S1 DEG)"), (2.50, "S1-enriched pathway")]:
        ax.text(x, 1.015, t, ha="center", va="bottom", fontsize=9.2, color="#6b7280", fontweight="bold")

    drug_y = 0.50
    y_cursor = 0.97
    for b in blocks:
        n = max(1, len(b["paths"]))
        ys = [y_cursor - (i + 0.5) * (0.90 / total_rows) for i in range(n)]
        y_cursor -= n * (0.90 / total_rows)
        ty = sum(ys) / len(ys)
        edge((0.0, drug_y), (1.10, ty), DRUG_C, b["relation"])
        node(1.10, ty, f"{b['target']}\nS1 logFC {b['logfc']:+.2f} (up)\nEV {b['eid'][:8]}", TGT_C, fs=7.6)
        for (pw, p, ana), py in zip(b["paths"], ys):
            color = ER_C if is_er(pw) else OTH_C
            tag = " · ER+" if is_er(pw) else ""
            edge((1.10, ty), (2.50, py), color, f"p={p:.1e}{tag}")
            node(2.50, py, wrap(pw), color, fs=7.4)

    node(0.0, drug_y, f"{row.drug_name}\n{row.pert_id}", DRUG_C, fs=8.6, lw=1.9)

    ax.set_title(f"{row.drug_name} — direction-coherent mechanism chains",
                 loc="left", x=0.0, y=1.215, fontsize=13.5, fontweight="bold", color=INK)
    ax.text(-0.45, 1.135,
            f"v4 A-list #{row.rank_mech}  ·  S_disc {row.S_disc:.3f}  ·  {row.n_chains} chain(s)  ·  "
            "PRISM: " + {"anti_er_positive": "anti-ER+", "support": "ER+ support",
                          "no_clear_direction": "no clear ER+ direction",
                          "missing": "no PRISM record"}.get(row.prism_status, row.prism_status),
            fontsize=8.0, color="#6b7280", ha="left", va="bottom")
    ax.text(-0.45, -0.055,
            "Reading: S1 logFC > 0 = gene up in ER+ tumour vs normal; an inhibitor of an up-regulated gene opposes the disease direction. "
            "Green = ER+ programme pathway; edge labels carry the relation and the evidence_id prefix.",
            fontsize=6.8, color="#4b5563", ha="left", va="top")

    fig.tight_layout()
    path = OUT / f"chain_{slug(row.drug_name)}.png"
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", path.name, f"({len(blocks)} targets)")


