"""Shared mechanism-scoring primitives for the robust candidate prioritization.

Both the frozen v2 stage 5 and the v3 deliverable Top10 use this module, so the
two deliverables cannot drift apart in how a mechanism score is computed.

Rules implemented here combine the frozen v4 protocol
(`reports/protocol_v4_discovery.md`: direction-coherent chain definition) with
the 10-point scoring items frozen in `archive/v2/selection_protocol.json`:

  2 pt  exact InChIKey match to a graph Drug node
  2 pt  at least one traceable direct target (drug->gene edge with an evidence record)
  1 pt  at least one direct target is an S1 differentially expressed gene
  2 pt  at least one direct target sits in an S1 enriched pathway
  0 pt  item 5 (external authority / literature) has no machine-readable source here
  2 pt  ER+ background or PRISM support without an obvious anti-ER+ direction

No name matching, no fuzzy matching, no inference from drug fame.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

GRAPH_BUNDLE_RELATIVE = Path(
    "data/processed/projects/3f18f4c1-713d-58c5-8a53-38eca5a5aaf9"
    "/graph_bundle/runs/e0421796-2aff-47e2-9228-d683eab05fa9"
)
PRISM_ANTI_ERPLUS_MARGIN = 0.1

# Directional relation vocabulary, frozen in reports/protocol_v4_discovery.md.
INHIBITS = {"INHIBITOR", "ANTAGONIST", "BLOCKER", "INVERSE_AGONIST", "NEGATIVE_ALLOSTERIC_MODULATOR"}
ACTIVATES = {"AGONIST", "ACTIVATOR", "PARTIAL_AGONIST", "POSITIVE_ALLOSTERIC_MODULATOR",
             "OPENER", "POSITIVE_MODULATOR"}
ESTROGEN_PATHWAY_MARKERS = ("ESTROGEN",)


@dataclass
class MechanismResult:
    inchi_key: str
    inchi_key_source: str
    graph_drug_id: str
    targets: list[str] = field(default_factory=list)
    targets_in_s1_deg: list[str] = field(default_factory=list)
    targets_in_s1_pathway: list[str] = field(default_factory=list)
    n_evidence_records: int = 0
    prism_erpos_mean: float = float("nan")
    prism_erneg_mean: float = float("nan")
    prism_delta: float = float("nan")
    prism_status: str = "missing"
    points: dict[str, int] = field(default_factory=dict)
    flags: list[str] = field(default_factory=list)

    @property
    def score(self) -> int:
        return int(sum(self.points.values()))


def _norm(value: object) -> str:
    if value is None or (isinstance(value, float) and value != value):
        return ""
    return str(value).strip().upper()


class MechanismScorer:
    def __init__(self, root: Path):
        graph_bundle = root / GRAPH_BUNDLE_RELATIVE
        self.nodes = pd.read_csv(graph_bundle / "subgraph_nodes.csv")
        self.edges = pd.read_csv(graph_bundle / "subgraph_edges.csv")
        self.evidence = pd.read_csv(graph_bundle / "evidence_records.csv", low_memory=False)
        self.audit = pd.read_csv(graph_bundle / "candidate_mapping_audit.csv")
        self.prism = pd.read_csv(root / "experiments/exp011_prism_validation/results/candidate_sensitivity_results.csv")
        deg = pd.read_csv(root / "s1_初步_gse42568_limma/limma_significant_genes_FDR05.csv")
        links = pd.read_csv(root / "experiments/s1_pathway_enrichment/pathway_gene_links.csv")

        drug_nodes = self.nodes[self.nodes.type == "Drug"].copy()
        drug_nodes["ik"] = drug_nodes.properties_json.map(
            lambda s: _norm(json.loads(s).get("inchi_key"))
        )
        self.node_by_ik = {ik: node_id for ik, node_id in zip(drug_nodes.ik, drug_nodes.id) if ik}

        self.evidence_keys = set(zip(self.evidence.subject_id, self.evidence.predicate, self.evidence.object_id))
        self.drug_gene = self.edges[self.edges.label == "DRG-GEN"].copy()
        gene_of = dict(zip(self.nodes.loc[self.nodes.type == "Gene", "id"], self.nodes.loc[self.nodes.type == "Gene", "label"]))
        self.drug_gene["gene"] = self.drug_gene["to"].map(gene_of).map(lambda v: v if isinstance(v, str) else None)

        self.deg_genes = set(deg.gene_symbol.astype(str).str.upper())
        self.pathway_genes = set(links.loc[links.adjusted_p < 0.05, "gene_symbol"].astype(str).str.upper())

        # Direction-aware chain inputs (v4 protocol): S1 logFC per gene and the
        # significant pathways each gene belongs to.
        all_genes = pd.read_csv(root / "s1_初步_gse42568_limma/limma_all_genes.csv")
        sig = all_genes[(all_genes["adj.P.Val"] < 0.05) & all_genes.gene_symbol.notna()].copy()
        sig["sym"] = sig.gene_symbol.astype(str).str.upper()
        self.log_fc = dict(zip(sig.sym, sig.logFC))
        sig_links = links[links.adjusted_p < 0.05]
        self.gene_pathways: dict[str, list[tuple[str, str, float]]] = {}
        for row in sig_links.itertuples():
            gene = str(row.gene_symbol).upper()
            self.gene_pathways.setdefault(gene, []).append((row.pathway, row.analysis, float(row.adjusted_p)))

        self.ik_source: dict[str, tuple[str, str]] = {}
        for row in self.audit.itertuples():
            if isinstance(row.inchi_key, str) and row.inchi_key.strip():
                self.ik_source.setdefault(row.pert_id, ("graph_bundle_audit", _norm(row.inchi_key)))
        for row in self.prism.itertuples():
            if isinstance(row.inchi_key, str) and row.inchi_key.strip():
                self.ik_source.setdefault(row.pert_id, ("prism_compound_map", _norm(row.inchi_key)))
        self.prism_by_pert = {row.pert_id: row for row in self.prism.itertuples()}

    def score(self, pert_id: str) -> MechanismResult:
        source, ik = self.ik_source.get(pert_id, ("missing", ""))
        node_id = self.node_by_ik.get(ik) if ik else None

        traced: list[str] = []
        n_evidence = 0
        if node_id:
            sub = self.drug_gene[self.drug_gene["from"] == node_id]
            for row in sub.itertuples():
                if (row._1, row.relation, row.to) in self.evidence_keys:
                    n_evidence += 1
                    if row.gene:
                        traced.append(row.gene.upper())
        traced = sorted(set(traced))

        result = MechanismResult(
            inchi_key=ik,
            inchi_key_source=source,
            graph_drug_id=node_id or "",
            targets=traced,
            targets_in_s1_deg=sorted(set(traced) & self.deg_genes),
            targets_in_s1_pathway=sorted(set(traced) & self.pathway_genes),
            n_evidence_records=n_evidence,
        )

        prism_row = self.prism_by_pert.get(pert_id)
        if prism_row is not None and pd.notna(getattr(prism_row, "erpos_mean_sensitivity", None)):
            erpos = float(prism_row.erpos_mean_sensitivity)
            erneg = float(prism_row.erneg_mean_sensitivity)
            delta = erpos - erneg
            result.prism_erpos_mean, result.prism_erneg_mean, result.prism_delta = erpos, erneg, delta
            # Symmetric margins: "support" needs a positive delta of at least the
            # same 0.1 used to call a negative delta an anti-ER+ direction. A delta
            # inside +/-0.1 means PRISM carries no ER+ selectivity information.
            result.prism_status = (
                "support" if delta >= PRISM_ANTI_ERPLUS_MARGIN
                else ("anti_er_positive" if delta < -PRISM_ANTI_ERPLUS_MARGIN else "no_clear_direction")
            )

        result.points = {
            "exact_InChIKey_graph_match": 2 if node_id else 0,
            "auditable_direct_target": 2 if traced else 0,
            "direct_target_is_S1_DEG": 1 if result.targets_in_s1_deg else 0,
            "target_to_S1_pathway_route": 2 if result.targets_in_s1_pathway else 0,
            "external_target_breast_cancer_evidence": 0,
            "ERplus_background_or_PRISM_support": 2 if result.prism_status in {"support", "no_clear_direction"} else 0,
        }

        flags: list[str] = []
        if not ik:
            flags.append("inchikey_unavailable")
        elif not node_id:
            flags.append("no_exact_graph_drug_node")
        if node_id and not traced:
            flags.append("no_traceable_direct_target")
        if not result.targets_in_s1_deg:
            flags.append("no_direct_target_in_S1_DEG")
        if not result.targets_in_s1_pathway:
            flags.append("no_direct_target_in_S1_enriched_pathway")
        flags.append("literature_evidence_source_not_available")
        if result.prism_status == "missing":
            flags.append("prism_record_missing")
        elif result.prism_status == "anti_er_positive":
            flags.append("prism_anti_er_positive_direction")
        result.flags = flags
        return result

    def chains(self, pert_id: str) -> list[dict[str, object]]:
        """Direction-coherent mechanism chains for one drug.

        A chain is kept only when the drug->gene edge carries an evidence record,
        the gene is an S1 DEG, the drug's direction opposes the gene's S1 change,
        and the gene sits in an S1 significant pathway.
        """
        source, ik = self.ik_source.get(pert_id, ("missing", ""))
        node_id = self.node_by_ik.get(ik) if ik else None
        if not node_id:
            return []
        sub = self.drug_gene[self.drug_gene["from"] == node_id]
        rows: list[dict[str, object]] = []
        for edge in sub.itertuples():
            gene = edge.gene
            if not gene or gene not in self.log_fc:
                continue
            if (edge._1, edge.relation, edge.to) not in self.evidence_keys:
                continue
            action = 1 if edge.relation in INHIBITS else (-1 if edge.relation in ACTIVATES else 0)
            if action == 0:
                continue
            logfc = float(self.log_fc[gene])
            coherent = (action == 1 and logfc > 0) or (action == -1 and logfc < 0)
            if not coherent:
                continue
            pathways = self.gene_pathways.get(gene, [])
            if not pathways:
                continue
            er = [p for p, _, _ in pathways if any(m in p.upper() for m in ESTROGEN_PATHWAY_MARKERS)]
            rows.append({
                "pert_id": pert_id,
                "graph_drug_id": node_id,
                "target": gene,
                "relation": edge.relation,
                "drug_direction": "inhibits" if action == 1 else "activates",
                "s1_logFC": logfc,
                "n_pathways": len(pathways),
                "pathways": "; ".join(sorted({p for p, _, _ in pathways})),
                "best_pathway_adjusted_p": min(p for _, _, p in pathways),
                "er_program": bool(er),
                "evidence_keys": f"{edge._1}|{edge.relation}|{edge.to}",
            })
        return rows
