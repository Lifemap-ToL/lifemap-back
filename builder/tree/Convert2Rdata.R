# R script to convert lmdata.parquet to lmdata.Rdata
# The script is called by export_data.py
#
# It takes one argument: the path to the lmdata directory which contains
# the parquet file to be converted.

library(arrow, warn.conflicts = FALSE)

args <- commandArgs(trailingOnly = TRUE)
build_dir <- args[1]

cat("    Reading TreeFeaturesComplete.parquet...\n")
# Warning: keep the DF name as is as it is used with this name by LifemapR
DF <- read_parquet(file.path(build_dir, "TreeFeaturesComplete.parquet"))

cat("    Saving dataframe to binary file lmdata.Rdata...\n")
save(DF, file = file.path(build_dir, "lmdata.Rdata"))
