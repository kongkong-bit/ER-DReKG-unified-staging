options(stringsAsFactors=FALSE, repos=c(CRAN='https://cloud.r-project.org'))
suppressPackageStartupMessages({
  library(limma); library(AnnotationDbi); library(org.Hs.eg.db)
  library(clusterProfiler); library(ReactomePA)
})
args <- commandArgs(trailingOnly=TRUE)
root <- if(length(args)) normalizePath(args[[1]], winslash='/', mustWork=TRUE) else normalizePath(getwd(),winslash='/',mustWork=TRUE)
exp <- file.path(root,'experiments','exp010_external_s1'); data_dir <- file.path(exp,'data'); out <- file.path(exp,'results')
dir.create(out,recursive=TRUE,showWarnings=FALSE); dir.create(file.path(exp,'figures'),recursive=TRUE,showWarnings=FALSE); dir.create(file.path(exp,'reports'),recursive=TRUE,showWarnings=FALSE)
gse <- file.path(data_dir,'GSE139038_series_matrix.txt.gz'); gpl <- file.path(data_dir,'GPL27630_family.soft.gz')
stopifnot(file.exists(gse),file.exists(gpl))
read_geo_series <- function(path) {
  lines <- readLines(gzfile(path),warn=FALSE,encoding='UTF-8')
  begin <- which(grepl('^!series_matrix_table_begin',lines))[1]
  # Parse per-sample annotation lines without depending on GEOquery.
  sample_rows <- lines[grepl('^!Sample_',lines)]
  sample_fields <- strsplit(sample_rows,'\t',fixed=FALSE)
  clean <- function(z) sub('"$','',sub('^"','',z))
  getrow <- function(key) {
    x <- sample_fields[vapply(sample_fields,function(z) length(z)>0 && z[1]==key,logical(1))]
    if(!length(x)) return(NULL)
    clean(unlist(x[[1]][-1]))
  }
  acc <- getrow('!Sample_geo_accession'); title <- getrow('!Sample_title'); source <- getrow('!Sample_source_name_ch1')
  desc <- getrow('!Sample_description')
  if(is.null(source)) source <- rep('',length(acc)); if(is.null(desc)) desc <- rep('',length(acc))
  ch_idx <- which(vapply(sample_fields,function(z) length(z)>0 && z[1]=='!Sample_characteristics_ch1',logical(1)))
  chars <- vector('list',length(acc)); names(chars)<-acc
  for(i in ch_idx) {
    z <- clean(sample_fields[[i]][-1])
    for(j in seq_along(z)) if(grepl(':',z[j],fixed=TRUE)) {
      kv <- strsplit(z[j],':',fixed=TRUE)[[1]]
      key <- tolower(trimws(kv[1])); val <- trimws(paste(kv[-1],collapse=':'))
      chars[[j]][key] <- val
    }
  }
  tab <- read.delim(gzfile(path),skip=begin,nrows=44544,check.names=FALSE,quote='"',comment.char='',stringsAsFactors=FALSE)
  rownames(tab) <- tab[[1]]; tab[[1]] <- NULL; expr <- as.matrix(tab); storage.mode(expr)<-'numeric'
  stopifnot(identical(colnames(expr),acc),nrow(expr)==44544L,ncol(expr)==65L)
  list(expr=expr,meta=data.frame(gsm=acc,title=title,source=source,description=desc,stringsAsFactors=FALSE),chars=chars,lines=lines)
}
read_geo_platform <- function(path) {
  lines <- readLines(gzfile(path),warn=FALSE,encoding='UTF-8'); begin <- which(grepl('^!platform_table_begin',lines))[1]
  tab <- read.delim(gzfile(path),skip=begin,nrows=44544,check.names=FALSE,quote='"',comment.char='',stringsAsFactors=FALSE)
  tab
}
geo <- read_geo_series(gse); ann <- read_geo_platform(gpl)
stopifnot(all(rownames(geo$expr) %in% ann$ID),!anyDuplicated(ann$ID))
meta <- geo$meta
getchar <- function(gsm,key) { z<-geo$chars[[gsm]]; if(is.null(z)||!key %in% names(z)) '' else unname(z[[key]]) }
meta$er_status <- vapply(meta$gsm,getchar,character(1),'er status')
meta$cancer_stage <- vapply(meta$gsm,getchar,character(1),'cancer stage')
meta$histology <- vapply(meta$gsm,getchar,character(1),'histopathological examination (hpe); inflitrating lobular carcinoma (ilc); infiltrating ductal carcinoma (idc)')
meta$sample_type <- vapply(meta$gsm,getchar,character(1),'sample type')
meta$patient <- sub('.*(?:breast cancer|cancer)_([0-9]+).*','\\1',meta$title,ignore.case=TRUE,perl=TRUE)
meta$patient[meta$patient==meta$title] <- ''
is_tumor <- grepl('^breast cancer_',meta$title,ignore.case=TRUE)
is_paired_normal <- grepl('^paired normal',meta$title,ignore.case=TRUE)
meta$group <- ifelse(is_tumor & tolower(meta$er_status)=='positive','ER+_Tumor',ifelse(is_paired_normal,'Paired_Normal',ifelse(grepl('^apparent normal',meta$title,ignore.case=TRUE),'Apparent_Normal',ifelse(is_tumor & tolower(meta$er_status)=='negative','ER-_Tumor','Other'))))
er_tumor <- which(meta$group=='ER+_Tumor'); normal <- which(meta$group=='Paired_Normal')
pair_t <- er_tumor[meta$patient[er_tumor] %in% meta$patient[normal]]
pair_patients <- unique(meta$patient[pair_t]); pair_n <- normal[meta$patient[normal] %in% pair_patients]
stopifnot(length(pair_patients)>=10L,length(pair_t)==length(pair_n))
selected <- c(pair_n,pair_t); selected_meta <- meta[selected,]
selected_meta$group <- factor(ifelse(selected_meta$group=='ER+_Tumor','Tumor','Normal'),levels=c('Normal','Tumor'))
selected_meta$patient_factor <- factor(selected_meta$patient)
if(any(table(selected_meta$patient_factor,selected_meta$group)!=1L)) stop('Expected exactly one ER+ tumor and paired normal per selected patient')
write.csv(meta,file.path(out,'external_sample_metadata.csv'),row.names=FALSE,na='')
write.csv(selected_meta,file.path(out,'paired_ERpositive_samples.csv'),row.names=FALSE,na='')
# Probe mapping is from the NCBI GEO GPL27630 platform table. Symbols are normalized to uppercase.
ann$gene_symbol <- toupper(trimws(as.character(ann$Gene_Symbol)))
ann$gene_symbol <- sub('\\s*///.*$','',ann$gene_symbol)
ann$gene_symbol[ann$gene_symbol %in% c('','---','NA')] <- NA
map_entrez <- AnnotationDbi::mapIds(org.Hs.eg.db,keys=unique(na.omit(ann$gene_symbol)),keytype='SYMBOL',column='ENTREZID',multiVals='first')
ann$entrez_id <- unname(map_entrez[ann$gene_symbol])
ann$mapped_gene <- !is.na(ann$gene_symbol)
write.csv(ann[,intersect(c('ID','Gene_Symbol','SPOT_ID','gene_symbol','entrez_id','mapped_gene'),names(ann))],file.path(out,'probe_gene_mapping_audit.csv'),row.names=FALSE,na='')
ix <- match(rownames(geo$expr),ann$ID); sym <- ann$gene_symbol[ix]
keep <- !is.na(sym) & nzchar(sym)
expr <- geo$expr[keep,selected,drop=FALSE]; sym <- sym[keep]
# Collapse replicated spots by mean log-ratio per symbol before gene-level limma.
expr_gene <- limma::avereps(expr,ID=sym)
patient <- factor(selected_meta$patient[match(colnames(expr_gene),selected_meta$gsm)])
group <- factor(selected_meta$group[match(colnames(expr_gene),selected_meta$gsm)],levels=c('Normal','Tumor'))
design <- model.matrix(~ patient + group)
if(qr(design)$rank!=ncol(design)) stop('Paired limma design is rank deficient')
fit <- eBayes(lmFit(expr_gene,design),trend=TRUE,robust=TRUE)
coef <- which(colnames(design)=='groupTumor'); if(length(coef)!=1) stop('Tumor-minus-normal coefficient not found')
tab <- topTable(fit,coef=coef,number=Inf,sort.by='none')
tab$gene_symbol <- rownames(tab); tab$entrez_id <- unname(AnnotationDbi::mapIds(org.Hs.eg.db,keys=tab$gene_symbol,keytype='SYMBOL',column='ENTREZID',multiVals='first'))
out_limma <- data.frame(gene_symbol=tab$gene_symbol,entrez_id=tab$entrez_id,logFC=tab$logFC,t=tab$t,P.Value=tab$P.Value,adj.P.Val=tab$adj.P.Val,B=tab$B,stringsAsFactors=FALSE)
out_limma <- out_limma[order(out_limma$adj.P.Val,-abs(out_limma$logFC),out_limma$gene_symbol),]
write.csv(out_limma,file.path(out,'external_limma_results.csv'),row.names=FALSE,na='')
cat('SAMPLE_COUNTS',length(er_tumor),length(normal),length(pair_patients),'\n')
cat('MAPPING_COUNTS',nrow(ann),sum(ann$mapped_gene),length(unique(ann$gene_symbol[ann$mapped_gene])),sum(!is.na(ann$entrez_id)),'\n')
cat('LIMMA_COUNTS',nrow(out_limma),sum(out_limma$adj.P.Val<.05,na.rm=TRUE),sum(out_limma$adj.P.Val<.05 & out_limma$logFC>0,na.rm=TRUE),sum(out_limma$adj.P.Val<.05 & out_limma$logFC<0,na.rm=TRUE),'\n')
# Directional gene-level comparison with S1. No expression matrices are merged across platforms.
s1_file <- file.path(root,'experiments','s1_pathway_enrichment','input','limma_all_genes.csv')
if(!file.exists(s1_file)) stop('Verified read-only copy of original S1 limma file is missing')
s1 <- read.csv(s1_file,check.names=FALSE)
s1$gene_symbol <- toupper(trimws(as.character(s1$gene_symbol)))
names(s1)[names(s1)=='logFC'] <- 'logFC_S1'; names(s1)[names(s1)=='adj.P.Val'] <- 'FDR_S1'
names(out_limma)[names(out_limma)=='logFC'] <- 'logFC_external'; names(out_limma)[names(out_limma)=='adj.P.Val'] <- 'FDR_external'
common <- merge(s1[,c('gene_symbol','logFC_S1','FDR_S1','t')],out_limma[,c('gene_symbol','logFC_external','FDR_external','t')],by='gene_symbol',suffixes=c('_S1','_external'))
common$direction_concordant <- sign(common$logFC_S1)==sign(common$logFC_external)
common$both_FDR05 <- common$FDR_S1<.05 & common$FDR_external<.05
write.csv(common,file.path(out,'cross_cohort_gene_concordance.csv'),row.names=FALSE)
source_samples <- read.csv(file.path(data_dir,'GSE42568_sample_groups.csv'),check.names=FALSE)
overlap <- intersect(source_samples$sample_id,meta$gsm)
if(length(overlap)>0L) stop('External cohort shares sample accession(s) with GSE42568')
write.csv(data.frame(GSE42568_sample_n=nrow(source_samples),external_sample_n=nrow(meta),shared_GSM_n=length(overlap),independent_accessions=length(overlap)==0L),file.path(out,'sample_independence_check.csv'),row.names=FALSE)
# Generate external enrichment with the correct detected/mapped universe.
univ <- unique(na.omit(out_limma$entrez_id)); sig_up <- unique(na.omit(out_limma$entrez_id[out_limma$FDR_external<.05 & out_limma$logFC_external>0])); sig_dn <- unique(na.omit(out_limma$entrez_id[out_limma$FDR_external<.05 & out_limma$logFC_external<0]))
safe_enrich <- function(ids,fun,args,outfile) {
  if(length(ids)<3) { write.csv(data.frame(),outfile,row.names=FALSE); return(data.frame()) }
  obj <- tryCatch(do.call(fun,c(list(gene=ids),args)),error=function(e){message(conditionMessage(e));NULL})
  if(is.null(obj)||!nrow(as.data.frame(obj))) {write.csv(data.frame(),outfile,row.names=FALSE);return(data.frame())}
  d<-as.data.frame(obj);write.csv(d,outfile,row.names=FALSE);d
}
ego_up <- safe_enrich(sig_up,enrichGO,list(OrgDb=org.Hs.eg.db,keyType='ENTREZID',ont='BP',universe=univ,pAdjustMethod='BH',pvalueCutoff=1,qvalueCutoff=1,readable=TRUE),file.path(out,'external_go_up.csv'))
ego_dn <- safe_enrich(sig_dn,enrichGO,list(OrgDb=org.Hs.eg.db,keyType='ENTREZID',ont='BP',universe=univ,pAdjustMethod='BH',pvalueCutoff=1,qvalueCutoff=1,readable=TRUE),file.path(out,'external_go_down.csv'))
rea_up <- safe_enrich(sig_up,enrichPathway,list(organism='human',universe=univ,pAdjustMethod='BH',pvalueCutoff=1,qvalueCutoff=1,readable=TRUE),file.path(out,'external_reactome_up.csv'))
rea_dn <- safe_enrich(sig_dn,enrichPathway,list(organism='human',universe=univ,pAdjustMethod='BH',pvalueCutoff=1,qvalueCutoff=1,readable=TRUE),file.path(out,'external_reactome_down.csv'))
# Fixed rule for the external S1 query: BING-restricted, FDR<0.05, top 100 per direction;
# if fewer than 100 are significant, retain the available genes and do not top up.
geneinfo <- read.delim(list.files(file.path(root,'s2_lincs','data'),pattern='gene_info.*gz$',full.names=TRUE)[1],check.names=FALSE)
bing <- toupper(trimws(geneinfo$pr_gene_symbol[geneinfo$pr_is_bing==1])); bing <- unique(bing[nzchar(bing)])
query <- out_limma[out_limma$FDR_external<.05 & out_limma$gene_symbol %in% bing,]
query$abs_logFC <- abs(query$logFC_external)
query <- query[order(query$FDR_external,-query$abs_logFC,query$gene_symbol),]
query_up <- head(query[query$logFC_external>0,],100); query_dn <- head(query[query$logFC_external<0,],100)
write.csv(rbind(transform(query_up,direction='UP'),transform(query_dn,direction='DOWN')),file.path(out,'external_s1_signature.csv'),row.names=FALSE)
cat('QUERY_COUNTS',nrow(query_up),nrow(query_dn),'\n')
# Existing S1 Hallmark results are compared by stable pathway ID.
## Hallmark GSEA is performed by the companion Python module to keep the
## permutation engine deterministic and avoid lengthy multilevel optimization.
write.csv(data.frame(dataset=c('GSE139038','GSE65194','GSE42568'),role=c('primary independent paired ER+ cohort','audited candidate; subtype-derived ER proxy, not primary','discovery reference'),platform=c('GPL27630 spotted two-color array','GPL570 Affymetrix','GPL570 Affymetrix'),n_samples=c(65,178,84),ER_positive_n=c(26,59,67),normal_n=c(24,11,17),selected=c(TRUE,FALSE,FALSE),selection_reason=c('explicit per-sample ER status, paired normal tissue, independent GEO accession','luminal subtype and healthy controls exist, but ER field is not explicit','discovery cohort')),file.path(out,'external_dataset_inventory.csv'),row.names=FALSE)
cat('COMPLETE common_genes',nrow(common),'rho',cor(common$logFC_S1,common$logFC_external,method='spearman',use='complete.obs'),'direction',mean(common$direction_concordant),'\n')
