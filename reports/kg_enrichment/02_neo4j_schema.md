# Phase 2 Schema and evidence model (offline design)

## Reuse and additions

The repository already defines BioCypher entity/relation types in `kg/config/biocypher_schema.yaml` and produces source-linked GraphBundles with separate node, edge and evidence-record tables. The enrichment artifacts preserve that model instead of replacing the graph with a second ontology. Existing `Drug`, `Gene`, `Protein` and `Pathway` nodes are reused by their exact IDs where available. New offline node IDs use `CHEMBL_TARGET:<target_chembl_id>`, `UNIPROT:<accession>` and `REACT:<stable_id>`; edge labels retain relation semantics (`HAS_DIRECT_TARGET`, `HAS_COMPONENT`, `PARTICIPATES_IN`, `SUBPATHWAY_OF`).

Every imported or derived edge carries an assertion ID, source release and source record ID. SIGNOR/OmniPath `REGULATES` assertions preserve source sign, cell/tissue context, references, license and raw source row; UniProt↔gene bridges are explicit mapping evidence, never causal edges. Original assertion JSON is retained in `source_evidence`. Reactome membership and hierarchy edges have `direction=unknown` for regulatory interpretation. Evidence rows from separate databases are not counted as independent experiments solely because they are separate rows.

## Neo4j constraints and import gate

No live Neo4j labels, counts, constraints or uniqueness collisions could be inspected because Docker Desktop access to its engine pipe was denied. Consequently no constraint-creation Cypher or apply import was run. Before adding constraints in an isolated DB, inspect duplicate IDs using the exact ID property used in `kg/config/biocypher_schema.yaml`; then create uniqueness constraints only for validated stable IDs. The project import implementation under `kg/scripts/import_phase_b_to_neo4j.py` and the version-scoped rollback helper must be checked against the selected database version before reuse.

## Import readiness

An offline BioCypher extension is available at `artifacts/kg_enrichment/regulatory_extension/`: 133 Protein nodes, 164 Gene nodes, 133 exact protein→gene mapping edges and 328 signed source assertions. BioCypher schema translation and the importer's row preparation both pass without connecting to a database. Signed assertions receive assertion-specific relationship IDs, so opposite/context-specific evidence can coexist. Before database writes, perform a live schema/count/duplicate audit, isolated-database dry run, compatible backup and rollback rehearsal; these remain unverified because the Neo4j runtime was unreachable.
