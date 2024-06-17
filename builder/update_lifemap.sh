#!/bin/sh

set -e

BUILD_DIRECTORY=~/builder_results
SOLR_CONTAINER=lifemap-solr
WWW_DIRECTORY=/var/www/lifemap_back

# Update tree
echo "Builder started at `date`"
echo "- BUILD TREE"
python3 tree/Main.py
#python3 tree/Main.py --skip-traversal --skip-add-info --skip-merge-jsons --skip-rdata --skip-index

# Copy lmdata and metadata files
echo "- COPYING lmdata AND metadata.json FILES TO WEB ROOT"
mkdir -p $WWW_DIRECTORY/data
cp $BUILD_DIRECTORY/lmdata/* $WWW_DIRECTORY/data
cp $BUILD_DIRECTORY/metadata.json $WWW_DIRECTORY/

# Update Solr
echo "- UPDATING SOLR"
echo "-- deleting taxo collection content"
docker exec -t $SOLR_CONTAINER /opt/solr/bin/solr post -c taxo -mode args -type application/xml '<delete><query>*:*</query></delete>'
docker exec -t $SOLR_CONTAINER /opt/solr/bin/solr post -c addi -mode args -type application/xml '<delete><query>*:*</query></delete>'
echo "-- Uploading tree features"
for num in $(seq 1 3); do
    docker cp $BUILD_DIRECTORY/TreeFeatures${num}.json $SOLR_CONTAINER:/opt/
    docker exec -t $SOLR_CONTAINER /opt/solr/bin/solr post -c taxo /opt/TreeFeatures${num}.json
    echo "== TreeFeatures${num} uploaded =="
done
echo "-- Uploading additional informations"
for num in $(seq 1 3); do
    docker cp $BUILD_DIRECTORY/ADDITIONAL.${num}.json $SOLR_CONTAINER:/opt/
    docker exec -t $SOLR_CONTAINER /opt/solr/bin/solr post -c addi /opt/ADDITIONAL.${num}.json
    echo "== ADDITIONAL.${num} uploaded =="
done

echo "Builder ended at `date`"

