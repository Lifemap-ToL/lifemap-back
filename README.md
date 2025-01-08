# Lifemap infrastructure

This repository allows to deploy a lifemap backend.

## Deployment with ansible

You must first [install Ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html), for example with [pipx](https://pipx.pypa.io/latest/installation/):

```sh
pipx install --include-deps ansible
```

Or with `uv`:

```sh
uv tool install ansible-core
uv tool install ansible
```

The backend is composed of several elements:

-   A postgis server, deployed with docker. The database contains "build" tables (`points`, `lines` and `polygons` tables), as well as "production" tables (`points_prod`, `lines_prod` and `polygons_prod` tables). When the tree is updated, build tables are emptied and recreated, and production tables are copied from build tables only if the update process is successful.
-   A solr server, deployed with docker. The server contains two cores, `taxo` for tree data and `addi` for additional data.
-   A modified mod_tile server for bitmap tiles generation, build and deployed with docker.
-   A [bbox](https://www.bbox.earth/index.html) vector tiles server, deployed with docker.

These elements are build and deployed with docker compose, from `back/docker-compose.yml`.

Another element deployed to the backend is the `builder`, a set of Python and shell scripts that download and process data to build both the tree data in postgis and additional informations stored in solr.

The backend should be deployable on any recent debian-based distribution by following these steps:

1. Copy the file `ansible/inventory_example.yml` to `ansible/inventory.yml`.

2. Edit `ansible/inventory.yml` and change the values of `backend_hostname`, `ansible-user`, `postgresql_password` and `solr_password`.

3. Install the base system by running:

```sh
ansible-playbook -i ansible/inventory.yml ansible/install_system.yml
```

4. Install the backend elements with:

```sh
ansible-playbook -i ansible/inventory.yml ansible/install_back.yml
```

5. Install the builder with:

```sh
ansible-playbook -i ansible/inventory.yml ansible/install_builder.yml
```

### Optional test frontends deployment

This repository also contains two test frontends which are deployable on the backend server (it should also be possible to deploy them on another machine). These are development frontends, the real one is in the [lifemap-front](https://github.com/Lifemap-ToL/lifemap-front) repository.

To deploy these frontends:

```sh
ansible-playbook -i ansible/inventory.yml ansible/install_front.yml
```

They will be accessible at the `/ncbi/` (for the mod_tile bitmap frontend) and `/bbox/` (for the bbox vector frontend) urls.

## Creating / updating lifemap data

To create or update the data needed to run Lifemap, ssh to the backend and run:

```sh
cd ~/builder/
./update_lifemap.sh
# Optional: prerender mod_tile tiles
./prerender_mod_tiles.sh
# Optional: seed bbox vector tiles
./prerender_bbox.sh
```

The `~/builder/cron_update.sh` can be used to automate updates. To have an automated weekly update each sunday at 2am, you can create a cronjob such as:

```
0 2 * * 1 user . /home/user/.profile && cd /home/user/builder && ./cron_update.sh
```

## Endpoints

-   Solr API is at `/solr/`
    -   Solr english taxonomy autocompletion is at `/solr/taxo/suggesthandler`
    -   Solr french taxonomy autocompletion is at `/solr/taxo/suggesthandlerfr`
-   JSON metadata file is at `/static/metadata.json`
-   Vector tiles are at `/vector_tiles/`
-   Bitmap mod_tile tiles are at `/osm_tiles/`, `/nolabels/` and `/only_labels/`
-   Optional test vector frontend is at `/bbox/`
-   Optional bitmap mod_tile frontend is at `/ncbi/`
-   Data files for `pylifemap` and `lifemapR` are at `/static/data/` or `/data/`

### Health endpoints

-   Global backend health endpoint is at `/health`
-   Solr health endpointsare at `/solr/taxo/admin/ping` and `/solr/addi/admin/ping`
-   Bbox health endpoint is at `/vector_tiles/health`

## Notes

-   If not deploying on Ubuntu 24.04, the binary R arrow package installation and docker apt repository must be modified in Ansible scripts.
-   If the file TAXONOMIC-VERNACULAR-FR.txt has changed, remove the cache pkl file
