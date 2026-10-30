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


exit 0
