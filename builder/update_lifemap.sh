#!/bin/bash

set -e

source ~/.env

echo $SOLR_PASSWORD

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
echo "Deleting taxo..."
curl --user solr:$SOLR_PASSWD http://localhost:8983/solr/taxo/update -H 'Content-type:application/xml' -d '<delete><query>*:*</query></delete>' -o /dev/null 
echo "Deleting addi..."
curl --user solr:$SOLR_PASSWD http://localhost:8983/solr/addi/update -H 'Content-type:application/xml' -d '<delete><query>*:*</query></delete>' -o /dev/null 
echo "-- Uploading tree features"
for num in $(seq 1 3); do
    echo "Uploading TreeFeatures${num}..."
    curl --progress-bar --user solr:CHANGE_ME http://localhost:8983/solr/taxo/update -H 'Content-type:application/json' -T $BUILD_DIRECTORY/TreeFeatures${num}.json -X POST -o /dev/null | cat
done
echo "-- Uploading additional informations"
for num in $(seq 1 3); do
    echo "Uploading ADDITIONAL.${num}..."
    curl --progress-bar --user solr:CHANGE_ME http://localhost:8983/solr/addi/update -H 'Content-type:application/json' -T $BUILD_DIRECTORY/ADDITIONAL.${num}.json -X POST -o /dev/null | cat
done
echo "-- Committing changes"
curl --user solr:$SOLR_PASSWD http://localhost:8983/solr/taxo/update?commit=true -o /dev/null 
curl --user solr:$SOLR_PASSWD http://localhost:8983/solr/addi/update?commit=true -o /dev/null 
echo "Builder ended at `date`"

