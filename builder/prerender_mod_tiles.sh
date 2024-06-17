#!/bin/sh

MOD_TILE_CONTAINER=lifemap-mod_tile
PRERENDER_THREADS=7

# Kill render_list-
echo "- KILL RENDER LIST"
docker exec -t $MOD_TILE_CONTAINER killall render_list

# Remove ALL old tiles
echo "- REMOVE OLD TILES"
docker exec -t $MOD_TILE_CONTAINER rm -r /var/lib/mod_tile/*

# Restart services
#echo "- RESTART SERVICES"
#docker restart $MOD_TILE_CONTAINER

# Compute tiles for the 5 first zoom levels on 7 threads
echo "- PRERENDER TILES"
docker exec -t $MOD_TILE_CONTAINER sh -c "/opt/mod_tile/render_list -n $PRERENDER_THREADS < /opt/build_results/XYZcoordinates >> /opt/build_results/tilerenderer.log"
docker exec -t $MOD_TILE_CONTAINER sh -c "/opt/mod_tile/render_list -m onlylabels -n $PRERENDER_THREADS < /opt/build_results/XYZcoordinates >> /opt/build_results/tilerenderer.log"
docker exec -t $MOD_TILE_CONTAINER sh -c "/opt/mod_tile/render_list -m nolabels -n $PRERENDER_THREADS < /opt/build_results/XYZcoordinates >> /opt/build_results/tilerenderer.log"
