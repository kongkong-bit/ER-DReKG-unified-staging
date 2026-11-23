# Data audit

- S1 file: `D:\CLASS\syh\s1_初步_gse42568_limma\limma_all_genes.csv`; SHA256 `b3dafdae855a0f44cbe80dbc40d17693ed01f4b31d899acbabc60e5485ed21c4`. Required columns present: ['adj.P.Val', 'gene_symbol', 'logFC', 't']. Selected genes: UP 100, DOWN 100. Contrast verified from `run_limma.R`: `Tumor - Normal`.
- LINCS GCTX gzip: `GSE70138_Broad_LINCS_Level5_COMPZ_n118050x12328_2017-03-06.gctx.gz` (5365179698 bytes). Decompressed to local work copy, HDF5 signature `\x89HDF`; matrix shape (118050, 12328), dtype float32; stored as signature-axis × gene-axis.
- GCTX signature IDs: 118050; matching sig_info: 118050. Gene IDs: 12328; matching gene_info: 12328.
- Metadata files parsed: gene_info, sig_info, sig_metrics, pert_info, inst_info. D drive free space at run start: 76.7 GiB.
- MCF7 trt_cp inventory: 12737 signatures, 1785 unique perturbagens.
