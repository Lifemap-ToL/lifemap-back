require(jsonlite)

args <- commandArgs(trailingOnly = TRUE)
data_dir <- args[1]

print("reading TreeFeaturesComplete1.json...")
df1 <- fromJSON(file.path(data_dir, "TreeFeaturesComplete1.json"))

print("reading TreeFeaturesComplete2.json...")
df2 <- fromJSON(file.path(data_dir, "TreeFeaturesComplete2.json"))

print("reading TreeFeaturesComplete3.json...")
df3 <- fromJSON(file.path(data_dir, "TreeFeaturesComplete3.json"))

print("Combining dataframes...")
DF <- rbind(df1, df2, df3)
class(DF$taxid) <- "integer"
class(DF$zoom) <- "integer"
class(DF$lat) <- "numeric"
class(DF$lon) <- "numeric"

print("Saving dataframe to binary file lmdata.Rdata...")
save(DF, file = "lmdata.Rdata")

print("Done.")
