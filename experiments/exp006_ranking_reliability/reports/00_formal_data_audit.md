# Formal S2 data audit

- Signature-score rows: 9522; unique signatures: 4761; per scheme: {'A': 4761, 'B': 4761}.
- Condition rows: 7430; by scheme: {'A': 3715, 'B': 3715}; unique condition key `(scheme, pert_id, cell_id, dose, time)`: True.
- All perturbagen IDs/names non-empty: True. IDs with multiple names: 0.
- Independent recomputation of condition WTCS median: PASS.
- Time records are 24 h. Dose strings retained as exact strata. Source uses one consistent `um` dose unit.
- WTCS ascending order is inverse-connectivity-first. Source rank_signature is ascending WTCS.
- Signature rows are already Level 5 replicate-aggregated signatures; their internal replicates are not counted as independent Level 5 records.
