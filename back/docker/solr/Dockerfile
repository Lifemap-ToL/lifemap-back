FROM solr:9

RUN mkdir /var/solr/data; \
    start-local-solr; \
    solr create -c addi -n data_driven_schema_configs; \
    solr create -c taxo -n data_driven_schema_configs; \
    stop-local-solr
COPY schema.xml /var/solr/data/taxo/conf/
COPY solrconfig.xml /var/solr/data/taxo/conf/
#RUN rm /var/solr/data/taxo/conf/managed-schema


CMD [ "solr-foreground" ]