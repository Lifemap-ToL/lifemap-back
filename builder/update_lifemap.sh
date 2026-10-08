#!/bin/bash

set -e

# Load environment variables
source ~/.env

SOLR_CONTAINER=lifemap-solr

# Update tree
echo "Builder started at `date`"

echo "- RESTARTING CONTAINERS"
docker compose -f ~/back/docker-compose.yml restart

echo "- BUILD TREE"
uv run python tree/Main.py --disable-progress

# Copy lmdata and metadata files
echo "- COPYING lmdata AND metadata.json FILES TO WEB ROOT"
mkdir -p $WWW_STATIC_DIR/data
cp $BUILD_RESULTS_DIR/lmdata/* $WWW_STATIC_DIR/data
cp $BUILD_RESULTS_DIR/metadata.json $WWW_STATIC_DIR/

# Update Solr
source ./update_solr.sh

echo "Builder ended at `date`"
