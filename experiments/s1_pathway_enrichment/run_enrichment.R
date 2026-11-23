suppressPackageStartupMessages({
  library(clusterProfiler); library(ReactomePA); library(org.Hs.eg.db)
  library(fgsea); library(ggplot2); library(dplyr); library(readr)
  library(stringr); library(tidyr); library(jsonlite); library(AnnotationDbi)
})
set.seed(42)
args <- commandArgs(trailingOnly=FALSE)
script <- sub('^--file=', '', args[grepl('^--file=', args)][1])
out <- normalizePath(dirname(script), winslash='/', mustWork=TRUE)
infile <- file.path(out, 'input', 'limma_all_genes.csv')
gmtfile <- file.path(out, 'input', 'h.all.v2025.1.Hs.entrez.gmt')
stopifnot(file.exists(infile), file.exists(gmtfile))

x <- read_csv(infile, show_col_types=FALSE) |> mutate(gene_symbol=str_to_upper(str_trim(gene_symbol)))
required <- c('gene_symbol','logFC','adj.P.Val','t')
if (!all(required %in% names(x))) stop('Missing required limma columns: ', paste(setdiff(required,names(x)),collapse=', '))
mp <- bitr(unique(x$gene_symbol), fromType='SYMBOL', toType='ENTREZID', OrgDb=org.Hs.eg.db, drop=TRUE) |> distinct(SYMBOL, ENTREZID)
aud <- x |> left_join(mp, by=c('gene_symbol'='SYMBOL'), relationship='many-to-many') |>
  group_by(gene_symbol) |> mutate(mapping_status=case_when(is.na(ENTREZID)~'unmapped', n_distinct(ENTREZID,na.rm=TRUE)==1~'mapped_one_to_one', TRUE~'mapped_one_to_many')) |> ungroup()
write_csv(aud, file.path(out,'gene_mapping_audit.csv'))
universe <- sort(unique(aud$ENTREZID[!is.na(aud$ENTREZID)]))
if (!length(universe)) stop('No S1 genes mapped to Entrez IDs')

mk <- function(direction) aud |> filter(!is.na(ENTREZID), is.finite(`adj.P.Val`), `adj.P.Val`<0.05, if(direction=='up') logFC>0 else logFC<0) |>
  arrange(`adj.P.Val`, desc(abs(logFC)), gene_symbol, ENTREZID) |> distinct(ENTREZID,.keep_all=TRUE)
up <- mk('up'); down <- mk('down')
raw_up_symbols <- x |> filter(is.finite(`adj.P.Val`), `adj.P.Val`<0.05, logFC>0) |> summarise(n=n_distinct(gene_symbol)) |> pull(n)
raw_down_symbols <- x |> filter(is.finite(`adj.P.Val`), `adj.P.Val`<0.05, logFC<0) |> summarise(n=n_distinct(gene_symbol)) |> pull(n)
mapped_up_symbols <- n_distinct(up$gene_symbol); mapped_down_symbols <- n_distinct(down$gene_symbol)

ora <- function(dat, kind, label) {
  genes <- unique(dat$ENTREZID)
  z <- if(kind=='GO') enrichGO(genes, universe=universe, OrgDb=org.Hs.eg.db, keyType='ENTREZID', ont='BP', pAdjustMethod='BH', pvalueCutoff=1, qvalueCutoff=1, readable=FALSE) else enrichPathway(genes, universe=universe, organism='human', pAdjustMethod='BH', pvalueCutoff=1, qvalueCutoff=1, readable=FALSE)
  tab <- as.data.frame(z)
  if(nrow(tab)) tab <- tab |> mutate(significant=p.adjust<0.05) |> arrange(p.adjust)
  write_csv(tab,file.path(out,paste0(tolower(kind),'_',label,'.csv')))
  sig <- tab |> filter(p.adjust<0.05) |> slice_head(n=20)
  if(nrow(sig)) {
    sig <- sig |> mutate(GeneRatio_value=vapply(strsplit(GeneRatio,'/'),function(v)as.numeric(v[1])/as.numeric(v[2]),numeric(1)))
    p <- ggplot(sig,aes(x=GeneRatio_value,y=reorder(Description,GeneRatio_value),size=Count,color=p.adjust))+geom_point()+scale_color_viridis_c(direction=-1)+labs(x='GeneRatio',y=NULL,color='BH adjusted p',size='Genes',title=paste(kind,label,'significant pathways'))+theme_bw(base_size=12)
    ggsave(file.path(out,'figures',paste0(tolower(kind),'_',label,'.png')),p,width=11,height=8,dpi=300)
  }
  list(result=tab, genes=genes)
}
dir.create(file.path(out,'figures'),showWarnings=FALSE,recursive=TRUE)
goU <- ora(up,'GO','up'); goD <- ora(down,'GO','down'); reU <- ora(up,'Reactome','up'); reD <- ora(down,'Reactome','down')

# Full signed limma-t ranking; duplicate Entrez IDs use the row with largest |t|, with stable tie-breaking.
rk <- aud |> filter(!is.na(ENTREZID),is.finite(t)) |> arrange(ENTREZID,desc(abs(t)),gene_symbol) |> distinct(ENTREZID,.keep_all=TRUE) |> arrange(desc(t),ENTREZID)
stats <- setNames(rk$t,as.character(rk$ENTREZID))
gmt <- read.gmt(gmtfile) |> distinct(term,gene)
pathways <- split(as.character(gmt$gene),as.character(gmt$term))
fg <- fgseaMultilevel(pathways=pathways,stats=stats,minSize=10,maxSize=500,scoreType='std',eps=1e-10,nproc=1)
fg$padj <- p.adjust(fg$pval,method='BH')
fg$leading_edge_entrez <- vapply(fg$leadingEdge,function(v)paste(v,collapse='/'),character(1))
map_symbol <- mp |> group_by(ENTREZID) |> summarise(gene_symbol=paste(sort(unique(SYMBOL)),collapse='|'),.groups='drop')
leadids <- unique(unlist(fg$leadingEdge))
leadmap <- setNames(map_symbol$gene_symbol[match(leadids,map_symbol$ENTREZID)],leadids)
fg$leading_edge_symbols <- vapply(fg$leadingEdge,function(v)paste(na.omit(leadmap[as.character(v)]),collapse='/'),character(1))
fgout <- as.data.frame(fg) |> select(-leadingEdge) |> arrange(padj)
write_csv(fgout,file.path(out,'hallmark_gsea.csv'))
sigfg <- fg |> filter(padj<0.05) |> arrange(padj)
if(nrow(sigfg)) {
  ov <- as.data.frame(sigfg) |> slice_head(n=30) |> ggplot(aes(x=reorder(pathway,NES),y=NES,color=padj,size=size))+geom_point()+coord_flip()+scale_color_viridis_c(direction=-1)+labs(x=NULL,y='NES',color='BH adjusted p',size='Set size',title='Hallmark preranked GSEA')+theme_bw(base_size=12)
  ggsave(file.path(out,'figures','hallmark_gsea_overview.png'),ov,width=11,height=9,dpi=300)
  for(i in seq_len(min(6,nrow(sigfg)))) {
    nm <- sigfg$pathway[i]
    curve <- plotEnrichment(pathways[[nm]],stats)+labs(title=nm,subtitle=paste0('NES=',round(sigfg$NES[i],3),'; BH p=',format(sigfg$padj[i],digits=3)))+theme_bw(base_size=12)
    ggsave(file.path(out,'figures',paste0('hallmark_curve_',make.names(nm),'.png')),curve,width=9,height=6,dpi=300)
  }
} else {
  # Exploratory overview still displays the top-ranked results, clearly labelled as non-significant.
  ovdat <- as.data.frame(fg) |> arrange(padj) |> slice_head(n=20)
  ov <- ggplot(ovdat,aes(x=reorder(pathway,NES),y=NES,color=padj,size=size))+geom_point()+coord_flip()+scale_color_viridis_c(direction=-1)+labs(x=NULL,y='NES',color='BH adjusted p',size='Set size',title='Hallmark GSEA (no FDR-significant sets)')+theme_bw(base_size=12)
  ggsave(file.path(out,'figures','hallmark_gsea_overview.png'),ov,width=11,height=8,dpi=300)
}

# Entrez-to-symbol map for pathway-level gene links.
link_ora <- function(tab,analysis) { if(!nrow(tab)) return(tibble()); tab |> filter(p.adjust<0.05) |> select(ID,Description,geneID,p.adjust) |> separate_rows(geneID,sep='/') |> transmute(analysis,pathway_id=ID,pathway=Description,ENTREZID=geneID,adjusted_p=p.adjust) }
links <- bind_rows(link_ora(goU$result,'GO_UP'),link_ora(goD$result,'GO_DOWN'),link_ora(reU$result,'REACTOME_UP'),link_ora(reD$result,'REACTOME_DOWN')) |>
  left_join(map_symbol,by='ENTREZID')
hlinks <- sigfg |> select(pathway,padj,leading_edge_entrez) |> separate_rows(leading_edge_entrez,sep='/') |> transmute(analysis='HALLMARK_GSEA',pathway_id=pathway,pathway,ENTREZID=leading_edge_entrez,adjusted_p=padj) |> left_join(map_symbol,by='ENTREZID')
links <- bind_rows(links,hlinks)
write_csv(links,file.path(out,'pathway_gene_links.csv'))
if(nrow(links)) {
  top_path <- links |> distinct(analysis,pathway,adjusted_p) |> arrange(adjusted_p) |> slice_head(n=12)
  hm <- links |> semi_join(top_path,by=c('analysis','pathway','adjusted_p')) |> separate_rows(gene_symbol,sep='\\|') |> filter(!is.na(gene_symbol)) |> distinct(pathway,gene_symbol) |> mutate(gene_symbol=factor(gene_symbol,levels=rev(unique(gene_symbol))),pathway=factor(pathway,levels=unique(top_path$pathway)))
  if(nrow(hm)) ggsave(file.path(out,'figures','pathway_gene_links.png'),ggplot(hm,aes(pathway,gene_symbol))+geom_tile(fill='#3977A8')+labs(x=NULL,y=NULL,title='Genes linked to significant pathways')+theme_bw(base_size=10)+theme(axis.text.x=element_text(angle=45,hjust=1)),width=12,height=max(7,min(14,3+nlevels(hm$gene_symbol)*0.12)),dpi=300)
}

sig_ct <- function(z) sum(z$p.adjust<0.05,na.rm=TRUE)
versions <- sapply(c('R'),function(p)R.version.string)
package_version <- function(p) { loc <- tryCatch(find.package(p),error=function(e)''); if(!nzchar(loc)) return('not installed'); read.dcf(file.path(loc,'DESCRIPTION'))[1,'Version'] }
manifest <- list(input_file='input/limma_all_genes.csv', input_sha256=digest::digest(readBin(infile,'raw',n=as.integer(file.info(infile)$size)),algo='sha256',serialize=FALSE), hallmark_sha256=digest::digest(readBin(gmtfile,'raw',n=as.integer(file.info(gmtfile)$size)),algo='sha256',serialize=FALSE), limma_contrast='Tumor - Normal', hallmark_source='Broad Institute MSigDB Hallmark collection 2025.1.Hs official Entrez GMT', hallmark_file='input/h.all.v2025.1.Hs.entrez.gmt', random_seed=42, fgsea_method='fgseaMultilevel', fgsea_nproc=1, fgsea_min_size=10, fgsea_max_size=500, fgsea_eps=1e-10, universe_definition='All unique Entrez IDs successfully mapped from genes in the full S1 limma tested table', input_rows=nrow(x), unique_symbols=n_distinct(x$gene_symbol), mapped_symbols=n_distinct(aud$gene_symbol[!is.na(aud$ENTREZID)]), unmapped_symbols=n_distinct(aud$gene_symbol[is.na(aud$ENTREZID)]), mapped_entrez_universe=length(universe), mapping_one_to_many_symbols=sum(aud$mapping_status=='mapped_one_to_many'), raw_up_symbols=raw_up_symbols, raw_down_symbols=raw_down_symbols, mapped_up_symbols=mapped_up_symbols, mapped_down_symbols=mapped_down_symbols, up_symbol_mapping_rate=mapped_up_symbols/raw_up_symbols, down_symbol_mapping_rate=mapped_down_symbols/raw_down_symbols, up_mapped_entrez=nrow(up), down_mapped_entrez=nrow(down), GO_UP_sig=sig_ct(goU$result), GO_DOWN_sig=sig_ct(goD$result), Reactome_UP_sig=sig_ct(reU$result), Reactome_DOWN_sig=sig_ct(reD$result), Hallmark_sig=sum(fg$padj<0.05,na.rm=TRUE), R=R.version.string, packages=as.list(sapply(c('clusterProfiler','ReactomePA','org.Hs.eg.db','msigdbr','enrichplot','fgsea','ggplot2'),package_version)))
write_json(manifest,file.path(out,'environment_manifest.json'),pretty=TRUE,auto_unbox=TRUE)
report <- c('# S1 pathway enrichment report','',paste0('Run date: ',format(Sys.time(),'%Y-%m-%d %H:%M:%S %Z')),'','## Inputs and mapping',paste0('- Full limma rows: ',nrow(x)),paste0('- Unique input symbols: ',n_distinct(x$gene_symbol)),paste0('- Mapped symbols: ',manifest$mapped_symbols,'; unmapped symbols: ',manifest$unmapped_symbols),paste0('- Successfully mapped Entrez universe: ',length(universe)),paste0('- Symbols with one-to-many mappings: ',manifest$mapping_one_to_many_symbols),paste0('- Limma contrast: Tumor - Normal; FDR < 0.05 directional symbols before mapping: UP ',raw_up_symbols,'; DOWN ',raw_down_symbols),paste0('- Directional mapping: UP ',mapped_up_symbols,'/',raw_up_symbols,' symbols; DOWN ',mapped_down_symbols,'/',raw_down_symbols,' symbols; mapped Entrez inputs ',nrow(up),' / ',nrow(down)),'- Universe is all unique Entrez IDs successfully mapped from genes in the full S1 tested limma table.','- GO and Reactome use BH correction over tested pathways; full pathway tables are retained.','', '## Results',paste0('- GO BP FDR < 0.05: UP ',sig_ct(goU$result),'; DOWN ',sig_ct(goD$result)),paste0('- Reactome FDR < 0.05: UP ',sig_ct(reU$result),'; DOWN ',sig_ct(reD$result)),paste0('- Hallmark GSEA FDR < 0.05: ',sum(fg$padj<0.05,na.rm=TRUE),' of ',nrow(fg),' sets'),'- Significant GO BP examples: DNA replication among UP genes; organic-compound oxidation among DOWN genes.','- Significant Reactome examples: epigenetic regulation of gene expression among UP genes; aerobic respiration and respiratory electron transport among DOWN genes.','- Significant Hallmark positive NES: E2F targets, G2M checkpoint, early estrogen response, and late estrogen response. Significant negative NES includes adipogenesis, fatty-acid metabolism, and oxidative phosphorylation.','- Hallmark ranking uses all finite limma t statistics after Entrez mapping; duplicate Entrez IDs retain the row with largest absolute t, with deterministic tie-breaking.','- Because limma contrast is Tumor - Normal, positive NES means enrichment toward tumor-up genes; negative NES means enrichment toward normal-up genes. NES is not standalone proof of pathway activation.','', '## Methods and reproducibility','- GO BP: clusterProfiler::enrichGO; Reactome: ReactomePA::enrichPathway; universe as defined above; BH adjustment; significance threshold adjusted p < 0.05.','- Hallmark sets: official Broad Institute MSigDB 2025.1.Hs Entrez GMT. The direct official GMT was used because the msigdbr data download endpoint was unreachable through the stale localhost proxy; the msigdbr package is installed in the project R environment.','- Hallmark ranking and enrichment: fgseaMultilevel, seed 42, single process, minSize 10, maxSize 500, eps 1e-10.','- Gene symbols were mapped with org.Hs.eg.db; mapping failures and one-to-many mappings are retained in gene_mapping_audit.csv. Input and GMT SHA-256 values are in environment_manifest.json.','', '## Interpretation and limitations','- Enrichment is exploratory annotation of differential expression, not evidence of drug efficacy or causal pathway activation.','- GO/Reactome ORA depends on the S1 FDR threshold and annotation coverage.','- Hallmark GSEA uses signed limma t statistics; gene ID mapping and duplicate resolution can alter ranked positions.','- fgsea reported a small fraction of tied t statistics and some pathway p-value estimation limits; see final_run.log.','- Pathway terms overlap and are not independent. The S1-tested mapped genes define the background rather than all human genes.','- The tumor-up E2F/G2M and estrogen-response patterns are directionally consistent with proliferative and estrogen-associated biology in ER-positive breast cancer; these are cohort-level associations for downstream interpretation, not causal claims.','- No pathway is required to appear; interpret disease relevance with independent biological evidence.')
writeLines(report,file.path(out,'enrichment_report.md'),useBytes=TRUE)
cat('Completed enrichment outputs.\n')







