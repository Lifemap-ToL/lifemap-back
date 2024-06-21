FROM solr:9

RUN mkdir /var/solr/data; \
    start-local-solr; \
    solr create -c addi -n data_driven_schema_configs; \
    solr create -c taxo -n data_driven_schema_configs; \
    stop-local-solr

COPY --chown=solr:solr schema.xml /var/solr/data/taxo/conf/
COPY --chown=solr:solr solrconfig.xml /var/solr/data/taxo/conf/
COPY --chown=solr:solr security.json /var/solr/data/


#RUN rm /var/solr/data/taxo/conf/managed-schema


CMD [ "solr-foreground" ]