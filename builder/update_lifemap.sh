#!/bin/bash

set -e

# WWW_STATIC_DIR and BUILD_RESULTS_DIR environment variables
source ~/.env

SOLR_CONTAINER=lifemap-solr

# Update tree
echo "Builder started at `date`"
echo "- BUILD TREE"
uv run python tree/Main.py

# Copy lmdata and metadata files
echo "- COPYING lmdata AND metadata.json FILES TO WEB ROOT"
mkdir -p $WWW_STATIC_DIR/data
cp $BUILD_RESULTS_DIR/lmdata/* $WWW_STATIC_DIR/data
cp $BUILD_RESULTS_DIR/metadata.json $WWW_STATIC_DIR/

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
    curl --progress-bar --user solr:$SOLR_PASSWD http://localhost:8983/solr/taxo/update -H 'Content-type:application/json' -T $BUILD_RESULTS_DIR/TreeFeatures${num}.json -X POST -o /dev/null | cat
done
echo "-- Uploading additional informations"
for num in $(seq 1 3); do
    echo "Uploading ADDITIONAL.${num}..."
    curl --progress-bar --user solr:$SOLR_PASSWD http://localhost:8983/solr/addi/update -H 'Content-type:application/json' -T $BUILD_RESULTS_DIR/ADDITIONAL.${num}.json -X POST -o /dev/null | cat
done
echo "-- Committing changes"
curl --user solr:$SOLR_PASSWD http://localhost:8983/solr/taxo/update?commit=true -o /dev/null
curl --user solr:$SOLR_PASSWD http://localhost:8983/solr/addi/update?commit=true -o /dev/null
echo "Builder ended at `date`"

