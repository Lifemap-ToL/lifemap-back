# Lifemap infrastructure

This repository allows to deploy a lifemap backend and frontend.

## Deployment with ansible

To deploy backend and frontend, first [install Ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html), for example with [pipx](https://pipx.pypa.io/latest/installation/):

```sh
pipx install --include-deps ansible
```

### Backend deployment

The backend is composed of several elements:

-   A postgis server, deployed with docker
-   A solr server, deployed with docker
-   A modified mod_tile server for tiles generation, build and deployed with docker

These elements are build and deployed with docker compose, from `back/docker/docker-compose.yml`.

Another element deployed to the backend is the `builder`, a set of Python and shell scripts that download and process data to build both the tree data in postgis and additional informations stored in solr.

The backend should be deployable on any recent debian-based distribution by following these steps:

1. Edit the file `inventory.yml`. Change the values of `backend_ip`, `frontend_ip`, `backend_hostname`, `frontend_hostname` and `postgresql_password`.

2. Install the base system by running:

```sh
ansible-playbook -i inventory.yml back/00_install_system_back.yml
```

3. Install the backend elements with:

```sh
ansible-playbook -i inventory.yml back/install_back.yml
```

4. Install the builder with:

```sh
ansible-playbook -i inventory.yml back/install_builder.yml
```

### Frontend deployment

The frontend should also be deployable on any recent debian-based distribution. It can be deployed on the same server as the backend.

Follow these steps:

1. If necessary, edit the file `inventory.yml`. Change the values of `backend_ip`, `frontend_ip`, `backend_hostname`, `frontend_hostname` and `postgresql_password`.

2. Install the base system by running:

```sh
ansible-playbook -i inventory.yml front/00_install_system_front.yml
```

3. Install the frontend code with:

```sh
ansible-playbook -i inventory.yml front/install_front.yml
```

## Creating / updating lifemap data

To create or update the data needed to run Lifemap, ssh to the builder and run:

```sh
cd ~/builder/
./update_lifemap.sh
```
