# R script to convert lmdata.parquet to lmdata.Rdata
# The script is called by export_data.py
#
# It takes one argument: the path to the lmdata directory which contains
# the parquet file to be converted.

library(arrow, warn.conflicts = FALSE)

args <- commandArgs(trailingOnly = TRUE)
lmdata_dir <- args[1]

cat("    Reading lmdata.parquet...\n")
DF <- read_parquet(file.path(lmdata_dir, "lmdata.parquet"))

cat("    Saving dataframe to binary file lmdata.Rdata...\n")
save(DF, file = file.path(lmdata_dir, "lmdata.Rdata"))
