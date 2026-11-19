#!/bin/bash

set -e

source ~/.env
source_name=$1

if [ -z "$source_name" ]; then
    echo "Usage: $0 SOURCE"
    exit 1
fi

source_directory=$BUILD_RESULTS_DIR/$source_name

echo "- UPDATING SOLR"
echo "-- deleting taxo collection content"
echo "Deleting taxo..."
curl --user solr:$SOLR_PASSWD http://localhost:8983/solr/taxo/update -H 'Content-type:application/xml' -d '<delete><query>*:*</query></delete>' -o /dev/null
echo "Deleting addi..."
curl --user solr:$SOLR_PASSWD http://localhost:8983/solr/addi/update -H 'Content-type:application/xml' -d '<delete><query>*:*</query></delete>' -o /dev/null

echo "-- Uploading tree features"
echo "Uploading TreeFeatures.json..."
curl --user solr:$SOLR_PASSWD http://localhost:8983/solr/taxo/update -H 'Content-type:application/json' -T $source_directory/TreeFeatures.json -X POST -o /dev/null | cat

echo "-- Uploading additional informations"
echo "Uploading ADDITIONAL.json..."
curl --user solr:$SOLR_PASSWD http://localhost:8983/solr/addi/update -H 'Content-type:application/json' -T $source_directory/ADDITIONAL.json -X POST -o /dev/null | cat

echo "-- Committing changes"
echo "Committing taxo changes..."
curl --user solr:$SOLR_PASSWD http://localhost:8983/solr/taxo/update?commit=true -o /dev/null
echo "Committing addi changes..."
curl --user solr:$SOLR_PASSWD http://localhost:8983/solr/addi/update?commit=true -o /dev/null
