
# ============================================================
# GSE42568: ER-positive breast cancer vs normal breast tissue
# Differential expression analysis using limma
# ============================================================

# 1. Load package
suppressPackageStartupMessages(library(limma))

# 2. Set working directory
work_dir <- "E:/生物医学信息/gse42568_limma"
setwd(work_dir)

# 3. Read expression matrix
expr_df <- read.csv(
  "expression_matrix.csv",
  check.names = FALSE,
  stringsAsFactors = FALSE
)

# First column contains gene symbols
gene_symbols <- expr_df[[1]]
expr <- as.matrix(expr_df[, -1, drop = FALSE])
rownames(expr) <- gene_symbols
storage.mode(expr) <- "numeric"

# 4. Read sample groups
groups <- read.csv(
  "sample_groups.csv",
  stringsAsFactors = FALSE
)

# 5. Verify sample IDs and order
if (!setequal(colnames(expr), groups$sample_id)) {
  stop("Sample IDs in expression matrix and group file do not match.")
}

groups <- groups[match(colnames(expr), groups$sample_id), ]

if (!identical(colnames(expr), groups$sample_id)) {
  stop("Sample order alignment failed.")
}

group <- factor(groups$group, levels = c("Normal", "Tumor"))

if (anyNA(group)) {
  stop("Unexpected group label found.")
}

if (sum(group == "Tumor") != 67 || sum(group == "Normal") != 17) {
  stop("Unexpected group counts.")
}

# 6. Build design matrix
design <- model.matrix(~ 0 + group)
colnames(design) <- levels(group)

# 7. Compare Tumor against Normal
contrast_matrix <- makeContrasts(
  Tumor - Normal,
  levels = design
)

# 8. Fit linear model and apply empirical Bayes moderation
fit <- lmFit(expr, design)
fit_contrast <- contrasts.fit(fit, contrast_matrix)
fit_ebayes <- eBayes(fit_contrast)

# 9. Export all genes, sorted by statistical significance
result <- topTable(
  fit_ebayes,
  coef = 1,
  number = Inf,
  adjust.method = "BH",
  sort.by = "P"
)

result$gene_symbol <- rownames(result)
result <- result[, c(
  "gene_symbol", "logFC", "AveExpr",
  "t", "P.Value", "adj.P.Val", "B"
)]

write.csv(
  result,
  "limma_all_genes.csv",
  row.names = FALSE
)

# 10. Export significant genes
sig_result <- result[result$adj.P.Val < 0.05, ]
write.csv(
  sig_result,
  "limma_significant_genes_FDR05.csv",
  row.names = FALSE
)

# 11. Print summary
cat("Analysis completed successfully!\n")
cat("Expression matrix:", nrow(expr), "genes x", ncol(expr), "samples\n")
cat("Tumor samples:", sum(group == "Tumor"), "\n")
cat("Normal samples:", sum(group == "Normal"), "\n")
cat("Genes with FDR < 0.05:", nrow(sig_result), "\n")
cat("Upregulated genes:", sum(sig_result$logFC > 0), "\n")
cat("Downregulated genes:", sum(sig_result$logFC < 0), "\n")
cat("Full results: limma_all_genes.csv\n")
cat("Significant results: limma_significant_genes_FDR05.csv\n")
