#!/bin/sh

BBOX_CONTAINER=lifemap-bbox
PRERENDER_THREADS=7
MAX_ZOOM=10

# Remove cached tiles
echo "- REMOVE OLD TILES"
docker exec -t $BBOX_CONTAINER rm -rf /var/www/bbox-map-server/tilecache/*

# Compute tiles for the 5 first zoom levels on 7 threads
echo "- SEEDING TILES"
docker exec -t $BBOX_CONTAINER sh -c "bbox-server seed --tileset branches --minzoom 4 --maxzoom $MAX_ZOOM --threads $PRERENDER_THREADS"
docker exec -t $BBOX_CONTAINER sh -c "bbox-server seed --tileset polygons --minzoom 4 --maxzoom $MAX_ZOOM --threads $PRERENDER_THREADS"
docker exec -t $BBOX_CONTAINER sh -c "bbox-server seed --tileset ranks --minzoom 4 --maxzoom $MAX_ZOOM --threads $PRERENDER_THREADS"

