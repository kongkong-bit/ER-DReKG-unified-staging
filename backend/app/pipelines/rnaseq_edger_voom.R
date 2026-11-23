args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 7) stop("usage: rnaseq_edger_voom.R counts.csv samples.csv output.csv positive_group negative_group identifier_type fdr_threshold")

counts_path <- args[[1]]
samples_path <- args[[2]]
output_path <- args[[3]]
positive_group <- args[[4]]
negative_group <- args[[5]]
identifier_type <- args[[6]]
fdr <- as.numeric(args[[7]])
if (length(fdr) != 1 || is.na(fdr) || fdr <= 0 || fdr > 1) stop("FDR 阈值必须位于 (0, 1]")

suppressPackageStartupMessages({library(edgeR); library(limma)})

read_table <- function(path) {
  delimiter <- if (grepl("\\.tsv$|\\.txt$", path, ignore.case = TRUE)) "\t" else ","
  read.table(path, header = TRUE, sep = delimiter, quote = "\"", comment.char = "", check.names = FALSE,
             stringsAsFactors = FALSE, na.strings = c("", "NA", "NaN"), fileEncoding = "UTF-8-BOM")
}

count_table <- read_table(counts_path)
if (ncol(count_table) < 3) stop("RNA-seq counts 表至少需要一列 feature ID 和两个样本列")
feature_ids <- trimws(as.character(count_table[[1]]))
if (anyNA(feature_ids) || any(feature_ids == "")) stop("counts 表 feature ID 存在空值")
if (anyDuplicated(feature_ids)) stop("counts 表 feature ID 必须唯一；请先按基因汇总 transcript counts")
sample_names <- names(count_table)[-1]
if (anyDuplicated(tolower(sample_names))) stop("counts 表存在重复样本列名")
counts <- as.matrix(count_table[-1])
suppressWarnings(storage.mode(counts) <- "numeric")
if (any(!is.finite(counts))) stop("RNA-seq counts 含缺失值或非有限值")
if (any(counts < 0)) stop("RNA-seq counts 不能为负值")
if (any(abs(counts - round(counts)) > 1e-8)) stop("当前插件要求原始整数 read counts，不接受 TPM/FPKM/CPM 或估计表达量")
if (any(colSums(counts) <= 0)) stop("RNA-seq 样本至少需要一个非零 read count")
rownames(counts) <- feature_ids

samples <- read_table(samples_path)
norm_name <- function(x) tolower(gsub("[^a-z0-9]", "", x))
sample_col <- which(norm_name(names(samples)) %in% c("sampleid", "sample", "geoaccession", "gsm"))[1]
group_col <- which(norm_name(names(samples)) %in% c("group", "condition", "tissue", "phenotype"))[1]
if (is.na(sample_col) || is.na(group_col)) stop("样本注释必须包含 sample_id 和 group/condition 列")
sample_ids <- trimws(as.character(samples[[sample_col]]))
groups <- trimws(as.character(samples[[group_col]]))
if (any(sample_ids == "") || any(groups == "") || anyDuplicated(sample_ids)) stop("样本注释 ID/组别为空或 sample_id 重复")
if (!setequal(sample_names, sample_ids)) {
  missing <- setdiff(sample_names, sample_ids)
  extra <- setdiff(sample_ids, sample_names)
  stop(sprintf("样本注释和 counts 样本不一致；缺少=%s；多余=%s", paste(missing, collapse = ","), paste(extra, collapse = ",")))
}
samples <- samples[match(sample_names, sample_ids), , drop = FALSE]
groups <- trimws(as.character(samples[[group_col]]))
if (!setequal(unique(groups), c(positive_group, negative_group))) stop("本插件要求样本注释恰好包含指定的正、负两组")
group_counts <- table(groups)
if (any(group_counts[c(positive_group, negative_group)] < 2)) stop("每组至少需要两个独立样本")

safe_names <- make.names(c(negative_group, positive_group), unique = FALSE)
if (anyDuplicated(safe_names)) stop("组名转换后出现重名；请更换组名")
group_factor <- factor(groups, levels = c(negative_group, positive_group))
design <- model.matrix(~ 0 + group_factor)
colnames(design) <- safe_names
contrast_text <- paste0(make.names(positive_group), "-", make.names(negative_group))
contrast <- makeContrasts(contrasts = contrast_text, levels = design)

input_features <- nrow(counts)
dge <- DGEList(counts = counts)
keep <- filterByExpr(dge, design = design)
if (!any(keep)) stop("filterByExpr 未保留任何 feature；请检查 counts 和样本设计")
dge <- dge[keep, , keep.lib.sizes = FALSE]
dge <- calcNormFactors(dge, method = "TMM")
v <- voom(dge, design, plot = FALSE)
fit <- lmFit(v, design)
fit <- eBayes(contrasts.fit(fit, contrast), robust = TRUE)
result <- topTable(fit, number = Inf, sort.by = "none", adjust.method = "BH")
result$gene_id <- rownames(result)
result$gene_symbol <- if (identifier_type == "symbol") result$gene_id else ""
result$direction <- ifelse(result$logFC > 0, "up", ifelse(result$logFC < 0, "down", "unchanged"))
result <- result[, c("gene_id", "gene_symbol", "logFC", "AveExpr", "t", "P.Value", "adj.P.Val", "B", "direction")]
write.csv(result, output_path, row.names = FALSE, na = "", fileEncoding = "UTF-8")

summary <- list(input_features = input_features, filtered_features = input_features - sum(keep),
  tested_features = nrow(result), significant_features = sum(result$adj.P.Val < fdr, na.rm = TRUE),
  up = sum(result$adj.P.Val < fdr & result$logFC > 0, na.rm = TRUE),
  down = sum(result$adj.P.Val < fdr & result$logFC < 0, na.rm = TRUE),
  contrast = paste(positive_group, "-", negative_group), positive_group = positive_group,
  negative_group = negative_group, sample_count = length(sample_names),
  group_counts = as.list(group_counts[c(negative_group, positive_group)]), identifier_type = identifier_type,
  method = "edgeR::filterByExpr + TMM normalization + limma::voom + lmFit + eBayes(robust=TRUE), BH adjustment",
  R = R.version.string, edgeR = as.character(packageVersion("edgeR")), limma = as.character(packageVersion("limma")))
if (!requireNamespace("jsonlite", quietly = TRUE)) stop("jsonlite package is required for the run summary")
jsonlite::write_json(summary, paste0(output_path, ".summary.json"), auto_unbox = TRUE, pretty = TRUE)
cat(jsonlite::toJSON(summary, auto_unbox = TRUE, pretty = TRUE), "\n")
