# S1 BING compatibility and WTCS comparison

## Method provenance
CMap WTCS follows Subramanian et al. 2017: weighted KS enrichment of UP and DOWN lists, combined as (ES_UP - ES_DOWN)/2 when signs differ and zero otherwise. Lim & Pavlidis 2021 describe BING-only queries and 10–150 genes per direction. Both here are literature methods. Project-specific settings are A=original Top 100 clipped to BING and B=FDR<0.05 full limma list restricted to BING then separately ranked by adjusted P ascending and absolute logFC descending.

## Mapping
Exact official symbol matches 130/200. Supplied gene_info contains Entrez, symbol, title, LM, BING but no alias/synonym field, so unmatched symbols cannot be alias-resolved from supplied annotations. LINCS counts: LM 978, BING 10174, AIG/non-BING 2154.

A sizes UP/DOWN 70/55. B sizes 100/100.

## Comparison
Same 30 signatures, same BING ranked background (10174 unique genes), same score vectors and WTCS implementation. Spearman rank correlation 0.9656; Top-10 overlap 10/10; mean absolute WTCS difference 0.0406; maximum 0.3212. Changes come from query membership and list sizes. This 30-signature smoke test does not show B is superior. More negative WTCS is inverse connectivity, not evidence of efficacy.
