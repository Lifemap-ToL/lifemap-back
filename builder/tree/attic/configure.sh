#! /bin/sh

usage="$(basename "$0") [-h] -- this code entirely configures a new ubuntu 18.04 server to be ready to display Lifemap. It needs to be run as root (sudo ./configure.sh)
where : 
    -h  display this help message

    there are no other configuration options."

while getopts ':h' option; do
  case "$option" in
    h) echo "$usage"
       exit
       ;;
  esac
done
shift $((OPTIND - 1))


##UPDATE AND INSTALL REQUIRED PACKAGES
sudo apt-get --yes update
sudo apt-get --yes upgrade
sudo apt-get --yes install libboost-all-dev git-core tar unzip wget bzip2 build-essential autoconf libtool 
sudo apt-get --yes install libxml2-dev libgeos-dev libgeos++-dev libpq-dev libbz2-dev libproj-dev munin-node munin 
sudo apt-get --yes install libprotobuf-c0-dev protobuf-c-compiler libfreetype6-dev libpng-dev libtiff5-dev libicu-dev libgdal-dev libcairo-dev 
sudo apt-get --yes install libcairomm-1.0-dev apache2 apache2-dev libagg-dev liblua5.2-dev ttf-unifont lua5.1 liblua5.1-dev libgeotiff-epsg node-carto
sudo apt-get --yes install postgresql postgresql-contrib postgis postgresql-10-postgis-2.4
sudo apt-get --yes install gdal-bin libgdal-dev libmapnik-dev mapnik-utils python-mapnik
sudo apt-get --yes install python-numpy python-qt4 python-lxml python-six python-pip
sudo apt-get --yes install r-base-core

##INSTALL R PACKAGE JSONLITE
wget -P /tmp/ https://cran.r-project.org/src/contrib/Archive/jsonlite/jsonlite_1.8.5.tar.gz
Rscript -e "install.packages('/tmp/jsonlite_1.8.5.tar.gz', lib='/tmp/')"


##CONFIGURE POSTGRESQL/POSTGIS USER AND DATABASE
sudo -u postgres psql -c "DROP DATABASE IF EXISTS tree;"
sudo -u postgres psql -c "DROP USER IF EXISTS lm;"
sudo -u postgres psql -c "CREATE USER lm WITH PASSWORD 'gvC5b78Ch9nDePjF';"
sudo -u postgres psql -c "CREATE DATABASE tree OWNER lm ENCODING UTF8;"
sudo -u postgres psql -d tree -c "CREATE EXTENSION postgis;"
sudo -u postgres psql -d tree -c "ALTER TABLE geometry_columns OWNER TO lm;"
sudo -u postgres psql -d tree -c "ALTER TABLE spatial_ref_sys OWNER TO lm;" 
##copy pgpass locally 
cp conf/.pgpass /root/.pgpass ##so that it is visible when executing script as root.
sudo chmod 0600 /root/.pgpass 

##CREATE LIFEMAP FOLDERS AND COPY CONF FILES
sudo mkdir /usr/share/fonts/lifemap
sudo mkdir /usr/lifemap/
sudo mkdir /usr/local/lifemap #to store tree data
sudo cp -r fonts/ /usr/lifemap/
sudo cp -r style/ /usr/lifemap/


##INSTALL MOD TILE and RENDERD
sudo git clone git://github.com/damiendevienne/mod_tile_deepzoom.git /opt/mod_tile
(cd /opt/mod_tile/ ; sudo ./autogen.sh)
(cd /opt/mod_tile/ ; sudo ./configure)
(cd /opt/mod_tile/ ; sudo make)
(cd /opt/mod_tile/ ; sudo make install)
(cd /opt/mod_tile/ ; sudo make install-mod_tile)
sudo ldconfig
sudo mkdir /var/lib/mod_tile
sudo chown www-data:www-data /var/lib/mod_tile
sudo mkdir /var/run/renderd
sudo cp conf/mod_tile.conf /etc/apache2/conf-available/mod_tile.conf
sudo a2enconf mod_tile
sudo cp conf/renderd.conf /etc/ ## a faire avant de relancer apache2
#create a service for renderd
sudo cp conf/renderd.init /etc/init.d/renderd
sudo chmod a+x /etc/init.d/renderd
#create a service for renderdlist that allows rendering list of tiles from list of coordinates
sudo cp conf/renderdlist.service /etc/systemd/system/
sudo systemctl enable renderdlist
#start renderd service
sudo systemctl daemon-reload
sudo systemctl start renderd
sudo systemctl enable renderd

##CONFIGURE APACHE
sudo service apache2 reload
sudo cp conf/000-default.conf /etc/apache2/sites-available/ #replace apache config file 
sudo a2enmod proxy proxy_http
sudo echo -e "#Get server adress as a variable for Lifemap apache config\n. /etc/lifemap_envir\n" >> /etc/apache2/envvars
sudo service apache2 restart

##INSTALL ETE (TREE MANIPULATION) AND DEPENDENCIES 
#python2.7 -m pip install --upgrade ete3

##INSTALL AND CONFIGURE SOLR
# sudo apt-get --yes install default-jre default-jdk
# (cd /tmp/ ; wget https://archive.apache.org/dist/lucene/solr/8.3.1/solr-8.3.1.tgz)
# (cd /tmp/ ; tar xzf solr-8.3.1.tgz solr-8.3.1/bin/install_solr_service.sh --strip-components=2)
# (cd /tmp/ ; sudo bash ./install_solr_service.sh solr-8.3.1.tgz -n)

# sudo service solr start

# sudo su - solr -c "/opt/solr/bin/solr create -c addi -n data_driven_schema_configs"
# sudo su - solr -c "/opt/solr/bin/solr create -c taxo -n data_driven_schema_configs"
# sudo cp conf/solrconfig.xml /var/solr/data/taxo/conf/
# sudo cp conf/schema.xml /var/solr/data/taxo/conf/
# sudo rm /var/solr/data/taxo/conf/managed-schema

# sudo service solr restart


##CONFIGURE SERVER
#edit /etc/apache2/envvars to read server_adress from external file as an environment variable
sudo echo -e ". /etc/lifemap_envir\n" >> /etc/apache2/envvars
sudo ./update_server.sh

##COPY LIFEMAP CODE TO DEDICATED FOLDER
#sudo cp -r tree/* /usr/local/lifemap/
