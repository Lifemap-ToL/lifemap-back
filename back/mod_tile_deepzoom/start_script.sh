#!/bin/bash

mkdir /var/run/apache2
source /etc/apache2/envvars
apache2 -D FOREGROUND &
/opt/mod_tile/renderd -f &

wait -n

exit $?
