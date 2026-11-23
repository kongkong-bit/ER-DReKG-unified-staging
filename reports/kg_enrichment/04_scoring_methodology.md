# Phase 4 reasoning and scoring methodology

## Path classes

`candidate_mechanism_paths` is reserved for directed `REGULATES` edges with source assertion IDs from SIGNOR/OmniPath. Search is bounded to at most four regulatory edges; the current Top10 observed paths are one edge each. Unknown or conflicting signs, or incompatible contexts, propagate as unknown. There are 349 candidate-to-S1 gene connection paths across 9/10 candidates. This is coverage only, not a validated causal drug-to-disease mechanism, and no aggregate candidate score is emitted.

`candidate_context_paths` stores exact-match ChEMBL direct mechanism → human UniProt component → Reactome 98 protein participation routes. These are context/annotation trails. They are not regulatory paths, do not support sign propagation and are not ER+ efficacy evidence. Current counts are reported in `03_top10_subgraph_summary.csv`.

## Evidence dimensions

Each drug dossier reports separate fields for EvidenceQuality, DirectionConsistency, DiseaseRelevance, DrugPerturbationSupport, ContextMatch, PathSpecificity and ContradictionPenalty. Missing evidence is marked with `missing=true` or `not_assessable`; no aggregate score is emitted because direction, pathway specificity and independent path validation are unavailable. WTCS remains drug-level reversal evidence; gene-level expression change does not stand in for protein activity.

## Evaluation limitations

DrugMechDB 2.0.1 is used only as an external reference: exact drug-name matching yields one breast-neoplasm MeSH path for doxorubicin and the direct target TOP2A overlaps the project pharmacology target. This single broad indication is not ER+ truth or full-path validation; overall recall remains unassessable. There is no blind expert path review. Context-route counts are not mechanism coverage. Independent S1 and PRISM records remain separate in each dossier.
