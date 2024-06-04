#!/bin/sh
sudo echo "$(echo "var DateUpdate='")" "$(date -R -r taxdump.tar.gz | cut -d' ' -f1-4)" "$(echo "';")" > /var/www/html/date-update.js
