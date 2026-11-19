#!/bin/bash

set -e

if [ $# -lt 1 ]; then
    echo "Usage: $0 <source> <root_id> [root_id ...]"
    exit 1
fi

source_name=$1
shift

if [ $# -eq 0 ]; then
    echo "Usage: $0 <source> <root_id> [root_id ...]"
    exit 1
fi

# Load environment variables
source ~/.env

echo "Builder started at `date`"

echo "- UPDATE TAXONOMY DATA"
uv run python taxonomy_sources/update_taxonomy_generic.py "$source_name"

echo "- RESTARTING CONTAINERS"
docker compose -f ~/back/docker-compose.yml restart postgis
docker compose -f ~/back/docker-compose.yml restart bbox
docker compose -f ~/back/docker-compose.yml restart caddy

echo "- BUILD TREE"
uv run python tree/Main_generic.py \
    --source "$source_name" \
    --roots "$@"

echo "- COPYING lmdata AND metadata.json FILES TO WEB ROOT"
mkdir -p "$WWW_STATIC_DIR/data"
cp "$BUILD_RESULTS_DIR/$source_name/lmdata.parquet" "$WWW_STATIC_DIR/data"
cp "$BUILD_RESULTS_DIR/$source_name/lmdata_R.parquet" "$WWW_STATIC_DIR/data"
cp "$BUILD_RESULTS_DIR/$source_name/metadata.json" "$WWW_STATIC_DIR/"

echo "-- Restart containers"
docker compose -f ~/back/docker-compose.yml restart postgis
docker compose -f ~/back/docker-compose.yml restart bbox
docker compose -f ~/back/docker-compose.yml restart caddy

sleep 5

echo "-- Update Solr"
./update_solr_generic.sh "$source_name"

echo "Builder ended at `date`"
