#!/bin/sh

BUILD_DIRECTORY=~/build_results
SOLR_CONTAINER=lifemap-solr
MOD_TILE_CONTAINER=lifemap-mod_tile
PRERENDER_THREADS=7
WWW_DIRECTORY=/var/www/lifemap_back

# Update tree
echo "- BUILD TREE"
python3 tree/Main.py
#python3 tree/Main.py --skip-traversal --skip-add-info --skip-merge-jsons --skip-rdata --skip-index

# Copy lmdata and date-update files
echo "- COPYING lmdata AND date-update FILES TO WEB ROOT"
mkdir $WWW_DIRECTORY/data
cp $BUILD_DIRECTORY/lmdata/* $WWW_DIRECTORY/data
cp $BUILD_DIRECTORY/date-update.json $WWW_DIRECTORY/

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
