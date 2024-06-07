library(arrow, warn.conflicts = FALSE)

args <- commandArgs(trailingOnly = TRUE)
data_dir <- args[1]

print("reading TreeFeaturesComplete1.parquet")
df1 <- read_parquet(file.path(data_dir, "TreeFeaturesComplete1.parquet"))
df1$ascend <- as.list(df1$ascend)
print("reading TreeFeaturesComplete2.parquet...")
df2 <- read_parquet(file.path(data_dir, "TreeFeaturesComplete2.parquet"))
df2$ascend <- as.list(df2$ascend)
print("reading TreeFeaturesComplete3.parquet...")
df3 <- read_parquet(file.path(data_dir, "TreeFeaturesComplete3.parquet"))
df3$ascend <- as.list(df3$ascend)

print("Combining dataframes...")
DF <- rbind(df1, df2, df3)
DF$taxid <- as.integer(DF$taxid)
DF$zoom <- as.integer(DF$zoom)
DF$lat <- as.numeric(DF$lat)
DF$lon <- as.numeric(DF$lon)

print("Saving dataframe to binary file lmdata.Rdata...")
save(DF, file = "lmdata.Rdata")

print("Done.")
