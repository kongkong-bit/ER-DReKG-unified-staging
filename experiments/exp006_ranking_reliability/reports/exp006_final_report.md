# Exp006 ranking reliability assessment

## Executive result
The formal S2 data support a reproducible ranked candidate set at the condition level, but evidence is uneven for individual drugs. A single global dose-mixed WTCS ranking is not justified. We selected the primary dose mechanically as the exact dose with the greatest unique-drug coverage in Q2, without inspecting score direction: **10.0 um**, 819 drug-condition rows covering 819 drugs. The primary candidate file is dose-specific. This is computational evidence for knowledge-graph prioritization, not efficacy evidence.

## Phase 0 audit
Verified input formal scores: 9,522 rows, 4,761 unique signatures with one A and one B score each. Condition file: 7,430 rows, 3,715 per scheme, unique on scheme + pert_id + cell + dose + time. Recomputed condition medians matched stored medians. Perturbagen IDs and names were non-empty. No pert_id mapped to multiple names in the scored data. Doses retain the source `um` unit and time is 24 h. Historical result files were read only. See `00_formal_data_audit.md` and `00_condition_coverage.csv`.

## E01 A/B stability
Across 3715 paired exact dose/time conditions, Spearman=0.894; Kendall=0.788. Compound overlap of condition-level Top K selections: Top10 4/10 (40%), Top20 11/20 (55%), Top50 28/50 (56%). At primary 10 um, B Top50 has 8/50 also within A Top50. Whole-list association is strong, yet top-10 membership and individual ranks are less stable.

## E02 dose stability
Scheme B has 879 drugs with at least two quality-passing doses, 652 with at least three, and 338 with a sign flip across dose-condition medians. A sign flip or single-dose-only evidence is retained as a stability limitation. Dose trends are descriptive and are not inhibition curves. Potential cytotoxicity/stress response remains unassessed.

## E03 QC sensitivity
Q1 >=0.1 retained 7768 signatures, 1427 compounds and 6577 conditions. Q2 >=0.2 retained 4761, 1191 compounds and 3715 conditions. Q3 >=0.3 retained 2973, 761 compounds and 2050 conditions. For B condition Top50, Q1 vs Q2 shared 25/50 compounds; Q3 vs Q2 shared 28/50. Q1 scores for absent signatures were computed incrementally from real GCTX rows. Thresholds are project sensitivity settings, not official CMap mandates.

## E04 candidate ranking and stability grade
Primary dose selection used maximum Q2 unique compound coverage. All candidate rows preserve A/B condition medians, ranks, number of signatures, number of available doses, negative-dose fraction, QC threshold range, and limitations. Grade rules were fixed in code: high requires >=3 signatures at primary condition, >=3 doses, >=75% negative dose conditions, no direction flip, QC-range <0.15 and A rank <=50; medium requires >=2 signatures, >=2 doses, >=50% negative conditions and A rank <=100; low denotes one signature or fewer than two doses; remaining records are insufficient. Among the Top50 B candidates, grades were {'low': 41, 'medium': 7, 'high': 1, 'insufficient': 1}. Most high-ranking rows have only one signature at the selected dose, so their individual condition median is a single observation and stability is low.

Top candidate examples are in `candidate_drugs_top50.csv`. They remain preliminary. Negative WTCS indicates inverse connectivity according to the scoring metric, not clinical effect. Drug identity is supported by LINCS perturbagen IDs/names; salt forms, stereoisomers, and synonym normalization beyond this ID level were not externally adjudicated.

## Recommendation
A condition-level BING Top100 candidate set is suitable as input for knowledge-graph mechanism exploration with evidence grades and condition metadata attached. Use the high/medium stability labels to prioritize computational follow-up, while treating low/insufficient candidates as exploratory. Do not interpret the current ranking as therapeutic validation.

## Reproducibility outputs
All Exp006 outputs are in this experiment directory. Q1 incremental scores and threshold aggregates are preserved. Scripts and test logs accompany the CSVs.
