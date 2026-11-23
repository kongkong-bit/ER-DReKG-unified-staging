args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 7) stop("usage: limma_microarray.R matrix.csv samples.csv output.csv positive_group negative_group identifier_type fdr_threshold")

matrix_path <- args[[1]]
samples_path <- args[[2]]
output_path <- args[[3]]
positive_group <- args[[4]]
negative_group <- args[[5]]
identifier_type <- args[[6]]
fdr <- as.numeric(args[[7]])
if (length(fdr) != 1 || is.na(fdr) || fdr <= 0 || fdr > 1) stop("FDR 阈值必须位于 (0, 1]")

suppressPackageStartupMessages(library(limma))

read_table <- function(path) {
  delimiter <- if (grepl("\\.tsv$|\\.txt$", path, ignore.case = TRUE)) "\t" else ","
  read.table(path, header = TRUE, sep = delimiter, quote = "\"", comment.char = "", check.names = FALSE,
             stringsAsFactors = FALSE, na.strings = c("", "NA", "NaN"), fileEncoding = "UTF-8-BOM")
}

expression <- read_table(matrix_path)
if (ncol(expression) < 3) stop("表达矩阵至少需要一列 feature ID 和两个样本列")
feature_ids <- trimws(as.character(expression[[1]]))
if (anyNA(feature_ids) || any(feature_ids == "")) stop("表达矩阵 feature ID 存在空值")
if (anyDuplicated(feature_ids)) stop("表达矩阵 feature ID 必须唯一；请先提供明确的 probe-to-gene 处理表")
sample_names <- names(expression)[-1]
if (anyDuplicated(tolower(sample_names))) stop("表达矩阵存在重复样本列名")

values <- as.matrix(expression[-1])
suppressWarnings(storage.mode(values) <- "numeric")
if (any(is.infinite(values), na.rm = TRUE)) stop("表达矩阵包含 Inf")
rownames(values) <- feature_ids
if (any(rowSums(is.finite(values)) == 0)) stop("表达矩阵含有完全缺失的 feature；请先清理缺失行")

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
  stop(sprintf("样本注释和表达矩阵样本不一致；缺少=%s；多余=%s", paste(missing, collapse = ","), paste(extra, collapse = ",")))
}
samples <- samples[match(sample_names, sample_ids), , drop = FALSE]
groups <- trimws(as.character(samples[[group_col]]))
if (!setequal(unique(groups), c(positive_group, negative_group))) stop("本插件要求样本注释恰好包含指定的正、负两组")
counts <- table(groups)
if (any(counts[c(positive_group, negative_group)] < 2)) stop("每组至少需要两个独立样本")

safe_names <- make.names(c(negative_group, positive_group), unique = FALSE)
if (anyDuplicated(safe_names)) stop("组名转换后出现重名；请更换组名")
group_factor <- factor(groups, levels = c(negative_group, positive_group))
design <- model.matrix(~ 0 + group_factor)
colnames(design) <- safe_names
contrast_text <- paste0(make.names(positive_group), "-", make.names(negative_group))
contrasts <- makeContrasts(contrasts = contrast_text, levels = design)
fit <- lmFit(values, design)
fit <- eBayes(contrasts.fit(fit, contrasts), robust = TRUE)
table <- topTable(fit, number = Inf, sort.by = "none", adjust.method = "BH")
table$gene_id <- feature_ids
table$gene_symbol <- if (identifier_type == "symbol") feature_ids else ""
table$direction <- ifelse(table$logFC > 0, "up", ifelse(table$logFC < 0, "down", "unchanged"))
table <- table[, c("gene_id", "gene_symbol", "logFC", "AveExpr", "t", "P.Value", "adj.P.Val", "B", "direction")]
write.csv(table, output_path, row.names = FALSE, na = "", fileEncoding = "UTF-8")

summary_path <- paste0(output_path, ".summary.json")
summary <- list(
  tested_features = nrow(table),
  significant_features = sum(table$adj.P.Val < fdr, na.rm = TRUE),
  up = sum(table$adj.P.Val < fdr & table$logFC > 0, na.rm = TRUE),
  down = sum(table$adj.P.Val < fdr & table$logFC < 0, na.rm = TRUE),
  contrast = paste(positive_group, "-", negative_group),
  positive_group = positive_group,
  negative_group = negative_group,
  sample_count = length(sample_names),
  group_counts = as.list(counts[c(negative_group, positive_group)]),
  identifier_type = identifier_type,
  method = "limma lmFit + contrasts.fit + eBayes(robust=TRUE), BH adjustment",
  R = R.version.string,
  limma = as.character(packageVersion("limma"))
)
if (!requireNamespace("jsonlite", quietly = TRUE)) stop("jsonlite package is required for the run summary")
jsonlite::write_json(summary, summary_path, auto_unbox = TRUE, pretty = TRUE)
cat(jsonlite::toJSON(summary, auto_unbox = TRUE, pretty = TRUE), "\n")
