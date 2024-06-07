#!/usr/bin/python

##FEB2016
# this code performs the following actions:
# 1. start solr (if not started)
# 2. removing all taxo and addi documents
# 3. Uploading taxo and addi data
# 4. restarting solr.

import os

# 1. start solr
print("  (1/4) Starting Solr...\n")
os.system("sudo service solr start")
print("  Solr successfully started\n")


# 2. Delete old documents
print("  (2/4) Deleting Solr docs...\n")
print("          Deleting taxo...\n")
delete1 = "curl http://localhost:8983/solr/taxo/update?commit=true -d '<delete><query>*:*</query></delete>'"
os.system(delete1)
print("          Taxo successfully deleted\n")
print("          Deleting addi...\n")
delete2 = "curl http://localhost:8983/solr/addi/update?commit=true -d '<delete><query>*:*</query></delete>'"
os.system(delete2)
print("          Addi successfully deleted\n")


# 3. Uploading files
print("  (3/4) Uploading files to Solr...\n")
for i in range(1, 4):
    uupadtesolr = (
        "sudo su - solr -c '/opt/solr/bin/post -c taxo /usr/local/lifemap/TreeFeatures%d.json'"
        % i
    )
    os.system(uupadtesolr)
    print("          -> TreeFeatures %d successfully uploaded." % i)

for i in range(1, 4):
    uupadtesolr2 = (
        "sudo su - solr -c '/opt/solr/bin/post -c addi /usr/local/lifemap/ADDITIONAL.%d.json'"
        % i
    )
    os.system(uupadtesolr2)
    print("          -> Additions %d successfully uploaded." % i)

print("        All files successfully uploaded\n")

# 4. Restarting solr
print("  (4/4) Restarting Solr...\n")
os.system("sudo service solr restart")
print("        Solr successfully restarted\n")
