#!/bin/bash


OUTPUT_FILE=/tmp/lifemap_update.log
WEBHOOK_URL=https://discord.com/api/webhooks/1294229537584054354/U0rcCqt1P8M2hz4tDa0Nm_xwjGQDa68lEw8OSARKQkdT7PtlTEnIlnCQ1HjNfiStd5I6

# Lifemap update

./update_lifemap.sh > "$OUTPUT_FILE" 2>&1
EXIT_STATUS=$?

MESSAGE="Lifemap update has run.\nExit status: $EXIT_STATUS."

curl -F "file=@$OUTPUT_FILE" \
     -F "payload_json={\"content\":\"$MESSAGE\"}" \
     "$WEBHOOK_URL"


# Bbox prerender

OUTPUT_FILE=/tmp/bbox_prerender.log
./prerender_bbox.sh > "$OUTPUT_FILE" 2>&1
EXIT_STATUS=$?

MESSAGE="Bbox tiles prerendering has run.\nExit status: $EXIT_STATUS."

curl -F "file=@$OUTPUT_FILE" \
     -F "payload_json={\"content\":\"$MESSAGE\"}" \
     "$WEBHOOK_URL"


# mod_tile prerender

OUTPUT_FILE=/tmp/mod_tiles_prerender.log
./prerender_mod_tiles.sh > "$OUTPUT_FILE" 2>&1
EXIT_STATUS=$?

MESSAGE="mod_tile tiles prerendering has run.\nExit status: $EXIT_STATUS."

curl -F "file=@$OUTPUT_FILE" \
     -F "payload_json={\"content\":\"$MESSAGE\"}" \
     "$WEBHOOK_URL"


exit 0
