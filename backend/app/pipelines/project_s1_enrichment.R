suppressPackageStartupMessages({
  library(clusterProfiler); library(ReactomePA); library(org.Hs.eg.db)
  library(fgsea); library(ggplot2); library(dplyr); library(readr)
  library(tidyr); library(jsonlite); library(AnnotationDbi)
})

args <- commandArgs(trailingOnly=TRUE)
if (length(args) != 5) stop("usage: input.csv output_dir identifier_type contrast fdr")
input_file <- args[[1]]
out <- args[[2]]
identifier_type <- args[[3]]
contrast <- args[[4]]
fdr <- as.numeric(args[[5]])
if (!identifier_type %in% c("symbol", "entrez", "ensembl")) stop("unsupported identifier type")
if (!is.finite(fdr) || fdr <= 0 || fdr > 1) stop("invalid FDR threshold")
dir.create(out, recursive=TRUE, showWarnings=FALSE)
dir.create(file.path(out,"figures"), recursive=TRUE, showWarnings=FALSE)

x <- read_csv(input_file, show_col_types=FALSE, name_repair="minimal")
required <- c("gene_id", "logFC", "t", "adj.P.Val")
missing <- setdiff(required, names(x))
if (length(missing)) stop(paste("S1 result is missing required columns:", paste(missing,collapse=", ")))
x <- x |> mutate(gene_id=trimws(as.character(gene_id)), logFC=as.numeric(logFC), t=as.numeric(t), `adj.P.Val`=as.numeric(`adj.P.Val`)) |> filter(!is.na(gene_id), nzchar(gene_id))
if (!"gene_symbol" %in% names(x)) x$gene_symbol <- x$gene_id
x$gene_symbol <- trimws(as.character(x$gene_symbol))
if (!nrow(x)) stop("S1 result contains no gene identifiers")

if (identifier_type == "entrez") {
  mp <- tibble(gene_id=unique(x$gene_id), ENTREZID=as.character(x$gene_id))
} else {
  keytype <- if (identifier_type == "symbol") "SYMBOL" else "ENSEMBL"
  query_ids <- unique(if (identifier_type == "ensembl") sub("\\.[0-9]+$","",x$gene_id) else if (identifier_type == "symbol") toupper(x$gene_id) else x$gene_id)
  mapped <- suppressMessages(bitr(query_ids, fromType=keytype, toType="ENTREZID", OrgDb=org.Hs.eg.db, drop=TRUE))
  mp <- tibble(gene_id=query_ids, source_id=mapped[[keytype]][match(query_ids,mapped[[keytype]])])
  mp <- mapped |> transmute(source_id=.data[[keytype]], ENTREZID=as.character(ENTREZID)) |> distinct()
  if (identifier_type == "ensembl") x <- x |> mutate(mapping_source=sub("\\.[0-9]+$","",gene_id)) else if (identifier_type == "symbol") x <- x |> mutate(mapping_source=toupper(gene_id)) else x <- x |> mutate(mapping_source=gene_id)
  mp <- mp |> rename(mapping_source=source_id)
}
if (identifier_type == "entrez") x <- x |> mutate(mapping_source=gene_id)
if (!"mapping_source" %in% names(x)) x <- x |> mutate(mapping_source=gene_id)
mp <- mp |> distinct(mapping_source, ENTREZID)
aud <- x |> left_join(mp,by="mapping_source") |> group_by(gene_id) |> mutate(mapping_status=case_when(is.na(ENTREZID)~"unmapped", n_distinct(ENTREZID,na.rm=TRUE)==1~"mapped_one_to_one", TRUE~"mapped_one_to_many")) |> ungroup()
universe <- sort(unique(aud$ENTREZID[!is.na(aud$ENTREZID)]))
if (length(universe)<10) stop("fewer than 10 tested genes map to Entrez IDs; enrichment is not supported")
ensembl_map <- suppressMessages(bitr(universe,fromType="ENTREZID",toType="ENSEMBL",OrgDb=org.Hs.eg.db,drop=TRUE)) |> transmute(ENTREZID=as.character(ENTREZID),ENSEMBL=as.character(ENSEMBL)) |> distinct() |> group_by(ENTREZID) |> summarise(ensembl_gene_ids=paste(sort(unique(ENSEMBL)),collapse="|"),ensembl_mapping_count=n_distinct(ENSEMBL),.groups="drop")
aud <- aud |> left_join(ensembl_map,by="ENTREZID") |> mutate(ensembl_mapping_status=case_when(is.na(ensembl_gene_ids)~"unmapped",ensembl_mapping_count==1~"mapped_unique_ensembl",TRUE~"ambiguous_ensembl"))
write_csv(aud,file.path(out,"gene_mapping_audit.csv"))

# Resolve duplicate Entrez IDs independently for ORA and GSEA: ORA keeps the most significant row;
# the signed GSEA ranking keeps the row with the largest absolute t statistic.
de_ranked <- aud |> filter(!is.na(ENTREZID)) |> arrange(ENTREZID, `adj.P.Val`, desc(abs(logFC)), gene_id) |> distinct(ENTREZID,.keep_all=TRUE)
ranked_t <- aud |> filter(!is.na(ENTREZID),is.finite(t)) |> arrange(ENTREZID,desc(abs(t)),gene_id) |> distinct(ENTREZID,.keep_all=TRUE) |> arrange(desc(t),ENTREZID)
sig <- de_ranked |> filter(is.finite(`adj.P.Val`), `adj.P.Val` < fdr, is.finite(logFC))
up <- sig |> filter(logFC>0)
down <- sig |> filter(logFC<0)
write_csv(up,file.path(out,"s1_up_genes.csv")); write_csv(down,file.path(out,"s1_down_genes.csv"))

ora <- function(ids, kind, direction) {
  result <- if (!length(ids)) NULL else if(kind=="go") enrichGO(ids,universe=universe,OrgDb=org.Hs.eg.db,keyType="ENTREZID",ont="BP",pAdjustMethod="BH",pvalueCutoff=1,qvalueCutoff=1,readable=FALSE) else enrichPathway(ids,universe=universe,organism="human",pAdjustMethod="BH",pvalueCutoff=1,qvalueCutoff=1,readable=FALSE)
  tab <- if(is.null(result)) tibble() else as.data.frame(result)
  if(nrow(tab)) {
    tab <- tab |> mutate(significant=p.adjust<0.05)
    display <- tab |> filter(p.adjust<0.05) |> arrange(p.adjust) |> slice_head(n=20)
    if(nrow(display)) {
      display <- display |> mutate(GeneRatio_value=vapply(strsplit(GeneRatio,"/"),function(v)as.numeric(v[1])/as.numeric(v[2]),numeric(1)))
      plot <- ggplot(display,aes(GeneRatio_value,reorder(Description,GeneRatio_value),size=Count,color=p.adjust))+geom_point()+scale_color_viridis_c(direction=-1)+labs(x="GeneRatio",y=NULL,color="BH adjusted p",size="Genes",title=paste(toupper(kind),direction,"enrichment"))+theme_bw(base_size=12)
      ggsave(file.path(out,"figures",paste0(kind,"_",direction,".png")),plot,width=10,height=7,dpi=220)
    }
  }
  write_csv(tab,file.path(out,paste0(kind,"_",direction,".csv")))
  tab
}
go_up <- ora(as.character(up$ENTREZID),"go","up"); go_down <- ora(as.character(down$ENTREZID),"go","down")
reactome_up <- ora(as.character(up$ENTREZID),"reactome","up"); reactome_down <- ora(as.character(down$ENTREZID),"reactome","down")

# Hallmark ranked GSEA uses all finite signed limma t statistics after Entrez mapping.
gsea_table <- tibble()
if (nrow(ranked_t)>=10) {
  repo_root <- Sys.getenv("DISEASEGRAPH_REPO_ROOT")
  if (!nzchar(repo_root)) stop("DISEASEGRAPH_REPO_ROOT is not configured")
  gmt_file <- file.path(repo_root,"experiments","s1_pathway_enrichment","input","h.all.v2025.1.Hs.entrez.gmt")
  if (!file.exists(gmt_file)) stop("project R environment Hallmark GMT resource is missing")
  lines <- readLines(gmt_file,warn=FALSE)
  terms <- strsplit(lines,"\\t",fixed=FALSE)
  sets <- setNames(lapply(terms,function(z)z[-c(1,2)]),vapply(terms,`[[`,character(1),1))
  stats <- setNames(ranked_t$t,as.character(ranked_t$ENTREZID))
  set.seed(42)
  fg <- fgseaMultilevel(pathways=sets,stats=stats,minSize=10,maxSize=500,scoreType="std",eps=1e-10,nproc=1)
  fg$padj <- p.adjust(fg$pval,"BH")
  fg$leading_edge_entrez <- vapply(fg$leadingEdge,function(v)paste(v,collapse="/"),character(1))
  gsea_table <- as.data.frame(fg) |> select(-leadingEdge) |> arrange(padj)
}
write_csv(gsea_table,file.path(out,"hallmark_gsea.csv"))
if(nrow(gsea_table)) {
  shown <- gsea_table |> slice_head(n=30)
  p <- ggplot(shown,aes(reorder(pathway,NES),NES,color=padj,size=size))+geom_point()+coord_flip()+scale_color_viridis_c(direction=-1)+labs(x=NULL,y="NES",color="BH adjusted p",size="Set size",title="Hallmark preranked GSEA")+theme_bw(base_size=11)
  ggsave(file.path(out,"figures","hallmark_gsea_overview.png"),p,width=10,height=8,dpi=220)
  significant_gsea <- gsea_table |> filter(padj<0.05) |> slice_head(n=6)
  for (i in seq_len(nrow(significant_gsea))) {
    term <- significant_gsea$pathway[i]
    curve <- plotEnrichment(sets[[term]],stats)+labs(title=term,subtitle=paste0("NES=",round(significant_gsea$NES[i],3),"；BH 调整后 P=",format(significant_gsea$padj[i],digits=3)))+theme_bw(base_size=11)
    ggsave(file.path(out,"figures",paste0("hallmark_curve_",make.names(term),".png")),curve,width=9,height=6,dpi=220)
  }
}
links <- bind_rows(
  bind_rows(lapply(list(GO_UP=go_up,GO_DOWN=go_down,REACTOME_UP=reactome_up,REACTOME_DOWN=reactome_down),function(tab) if(!nrow(tab)) tibble() else tab |> filter(p.adjust<0.05) |> select(analysis=ID,pathway=Description,adjusted_p=p.adjust,geneID) |> separate_rows(geneID,sep="/") |> rename(ENTREZID=geneID))),
  if(nrow(gsea_table)) gsea_table |> filter(padj<0.05) |> transmute(analysis="HALLMARK_GSEA",pathway=pathway,adjusted_p=padj,ENTREZID=leading_edge_entrez) |> separate_rows(ENTREZID,sep="/") else tibble()
)
symbol_map <- aud |> filter(!is.na(ENTREZID),!is.na(gene_symbol),nzchar(gene_symbol)) |> group_by(ENTREZID) |> summarise(gene_symbol=paste(sort(unique(gene_symbol)),collapse="|"),.groups="drop")
links <- links |> left_join(symbol_map,by="ENTREZID") |> left_join(ensembl_map,by="ENTREZID")
write_csv(links,file.path(out,"pathway_gene_links.csv"))
if(nrow(links)) {
  top_links <- links |> distinct(analysis,pathway,adjusted_p) |> arrange(adjusted_p) |> slice_head(n=12)
  heat <- links |> semi_join(top_links,by=c("analysis","pathway","adjusted_p")) |> separate_rows(gene_symbol,sep="\\|") |> filter(!is.na(gene_symbol),nzchar(gene_symbol)) |> distinct(pathway,gene_symbol) |> slice_head(n=240) |> mutate(pathway=factor(pathway,levels=rev(unique(top_links$pathway))))
  if(nrow(heat)) ggsave(file.path(out,"figures","pathway_gene_links.png"),ggplot(heat,aes(pathway,gene_symbol))+geom_tile(fill="#3977A8")+labs(x=NULL,y=NULL,title="显著通路与命中基因关系")+theme_bw(base_size=10)+theme(axis.text.x=element_text(angle=45,hjust=1)),width=12,height=8,dpi=220)
}
summary <- list(contrast=contrast,identifier_type=identifier_type,fdr_threshold=fdr,input_genes=nrow(x),mapped_rows=sum(!is.na(aud$ENTREZID)),mapped_universe=length(universe),unmapped_genes=sum(is.na(aud$ENTREZID)),one_to_many_genes=sum(aud$mapping_status=="mapped_one_to_many"),unique_ensembl_genes=sum(aud$ensembl_mapping_status=="mapped_unique_ensembl",na.rm=TRUE),ambiguous_ensembl_genes=sum(aud$ensembl_mapping_status=="ambiguous_ensembl",na.rm=TRUE),unmapped_ensembl_genes=sum(aud$ensembl_mapping_status=="unmapped",na.rm=TRUE),up_genes=nrow(up),down_genes=nrow(down),go_up_significant=sum(go_up$p.adjust<0.05,na.rm=TRUE),go_down_significant=sum(go_down$p.adjust<0.05,na.rm=TRUE),reactome_up_significant=sum(reactome_up$p.adjust<0.05,na.rm=TRUE),reactome_down_significant=sum(reactome_down$p.adjust<0.05,na.rm=TRUE),hallmark_significant=sum(gsea_table$padj<0.05,na.rm=TRUE),r_version=R.version.string,packages=list(clusterProfiler=as.character(packageVersion("clusterProfiler")),ReactomePA=as.character(packageVersion("ReactomePA")),org.Hs.eg.db=as.character(packageVersion("org.Hs.eg.db")),fgsea=as.character(packageVersion("fgsea")),ggplot2=as.character(packageVersion("ggplot2"))))
write_json(summary,file.path(out,"summary.json"),auto_unbox=TRUE,pretty=TRUE)
writeLines(c("# 项目级 S1 通路富集分析报告","",paste0("- 比较方向：",contrast),paste0("- 基因 ID 类型：",identifier_type),paste0("- 输入基因：",nrow(x),"；成功映射背景基因（Entrez）：",length(universe)),paste0("- FDR 阈值：",fdr,"；上调基因：",nrow(up),"；下调基因：",nrow(down)),paste0("- GO BP 显著通路：上调 ",summary$go_up_significant,"；下调 ",summary$go_down_significant),paste0("- Reactome 显著通路：上调 ",summary$reactome_up_significant,"；下调 ",summary$reactome_down_significant),paste0("- Hallmark GSEA 显著集合：",summary$hallmark_significant),"- ORA 背景为本次 S1 中映射成功的实际检验基因；Hallmark 使用所有可映射且具有限 limma t 值的排序基因。","- 结果是基因集统计关联，不证明因果、疾病特异机制或药物疗效。"),file.path(out,"enrichment_report.md"),useBytes=TRUE)
cat("Project S1 enrichment complete.\n")
