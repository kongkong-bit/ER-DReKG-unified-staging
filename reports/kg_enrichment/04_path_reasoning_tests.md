# Path reasoning validation

`kg/tests/test_kg_enrichment.py` contains deterministic fixtures for source-specific parsing, sign propagation, unknown/conflicting signs, context compatibility, UniProt-gene mapping evidence, bounded directed path enumeration and a pinned DrugMechDB reference check. All 17 KG enrichment/schema tests passed on 2026-11-22. Against the real frozen Top 10, the offline subgraphs contain 349 one-hop signed regulatory paths across 9/10 candidates (SIGNOR and OmniPath). These are graph-supported candidate-to-S1 connections, not biologically validated mechanisms; repeated edges and candidate seed mapping contribute coverage, so path count is not an independent evidence count. Opposing/unknown-context source assertions do not produce a confident propagated sign.

Run from repository root: `$env:PYTHONPATH='D:\CLASS\syh'; uv run --project kg --group test pytest kg/tests/test_kg_enrichment.py kg/tests/test_top10_mechanism_schema.py -q`.
