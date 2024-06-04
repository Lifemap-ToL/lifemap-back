FROM ubuntu:20.04 as base

RUN apt-get update; \
    apt-get -y full-upgrade; \
    DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y git build-essential apache2 apache2-dev libmapnik-dev mapnik-utils psmisc;


FROM base as compile

WORKDIR /opt
RUN git clone https://github.com/damiendevienne/mod_tile_deepzoom.git mod_tile
WORKDIR /opt/mod_tile
RUN ./autogen.sh; \
    ./configure; \
    make; \
    make install; \
    make install-mod_tile; \
    mkdir /var/lib/mod_tile; \
    mkdir /usr/lifemap/; \
    chown www-data:www-data /var/lib/mod_tile; \
    mkdir /var/run/renderd;

COPY fonts /usr/lifemap/fonts
COPY style /usr/lifemap/style

COPY renderd.conf /etc/
COPY mod_tile.conf /etc/apache2/conf-available/
COPY 000-default.conf /etc/apache2/sites-available/

RUN a2enconf mod_tile; \
    a2enmod proxy proxy_http;
#   service apache2 restart


#COPY renderd.init /etc/init.d/renderd
#RUN chmod a+x /etc/init.d/renderd; \
#    service renderd start
#COPY renderdlist.service /etc/system/system/
#RUN systemctl daemon-reload; \
#    systemctl enable renderdlist; \
#    systemctl enable renderd; \
#    systemctl start renderd

COPY start_script.sh /opt/
RUN chmod +x /opt/start_script.sh

CMD ["/opt/start_script.sh"]