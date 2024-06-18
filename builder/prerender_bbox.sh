#!/bin/sh

BBOX_CONTAINER=lifemap-bbox
PRERENDER_THREADS=30
MAX_ZOOM=10

# Remove cached tiles
echo "- REMOVE OLD TILES"
docker exec -t $BBOX_CONTAINER rm -rf /opt/data/*

# Compute tiles for the 5 first zoom levels on 7 threads
echo "- SEEDING TILES"
docker exec -t $BBOX_CONTAINER sh -c "bbox-server seed --tileset lifemap --minzoom 4 --maxzoom $MAX_ZOOM --threads $PRERENDER_THREADS"
