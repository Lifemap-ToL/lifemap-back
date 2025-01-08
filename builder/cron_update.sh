#!/bin/bash

# Get DISCORD_WEBHOOK_URL environment variable
source .env

OUTPUT_FILE=/tmp/lifemap_update.log

# Lifemap update

./update_lifemap.sh > "$OUTPUT_FILE" 2>&1
EXIT_STATUS=$?

MESSAGE="Lifemap update has run.\nExit status: $EXIT_STATUS."

curl -F "file=@$OUTPUT_FILE" \
     -F "payload_json={\"content\":\"$MESSAGE\"}" \
     "$DISCORD_WEBHOOK_URL"


# Bbox prerender

OUTPUT_FILE=/tmp/bbox_prerender.log
./prerender_bbox.sh > "$OUTPUT_FILE" 2>&1
EXIT_STATUS=$?

MESSAGE="Bbox tiles prerendering has run.\nExit status: $EXIT_STATUS."

curl -F "file=@$OUTPUT_FILE" \
     -F "payload_json={\"content\":\"$MESSAGE\"}" \
     "$DISCORD_WEBHOOK_URL"


# mod_tile prerender

OUTPUT_FILE=/tmp/mod_tiles_prerender.log
./prerender_mod_tiles.sh > "$OUTPUT_FILE" 2>&1
EXIT_STATUS=$?

MESSAGE="mod_tile tiles prerendering has run.\nExit status: $EXIT_STATUS."

curl -F "file=@$OUTPUT_FILE" \
     -F "payload_json={\"content\":\"$MESSAGE\"}" \
     "$DISCORD_WEBHOOK_URL"


exit 0
