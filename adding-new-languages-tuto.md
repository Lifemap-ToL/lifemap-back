# Adding a new language

- Choose the language code, for example `it` for Italian.

- Add the vernacular names file to the `taxonomy-all` GitHub repository:
  `https://github.com/Lifemap-ToL/taxonomy-all/blob/main/<language-code>/TAXONOMIC-VERNACULAR-<CODE-IN-UPPERCASE>-LATEST.txt`
  For example:
  `https://github.com/Lifemap-ToL/taxonomy-all/blob/main/it/TAXONOMIC-VERNACULAR-IT-LATEST.txt`

- Add the language code to `LANG_LIST` in `builder/tree/config.py`.

- Add a column for the language to `builder/taxo/ranks.csv` and translate each rank.

- Add the language fields to `ansible/assets/solr/taxo/schema.xml`: `common_name_<code>`, `rank_<code>`, `all_<code>`, and their matching search fields and copy rules.

- Add a language suggester and request handler to `ansible/assets/solr/taxo/solrconfig.xml`, using the new `all-search-<code>` field. Give it a unique suggester name and index path.

- Add `rank_<code>` to both rank queries in `ansible/templates/bbox/bbox.toml.j2` so vector tiles can carry the translated rank.

- In the separate `lifemap-front` repository, add or review `src/locale/<code>.json`, register the locale in the i18n setup, and add support for the new tree locale in the taxon, search, and map code. A locale JSON file alone does not make the language selectable.

- Deploy the updated builder code and `ranks.csv` to the server. `builder/tree/config.py` runs from the installed builder directory, while `ranks.csv` is read from `builder_results/taxo/`. `ansible/install_builder.yml` copies both locations.

- Deploy the updated Solr schema, Solr config, and bbox config with `ansible/install_back.yml`. On an existing server, copying only `schema.xml` leaves the new suggester and vector tile rank unavailable. For a manual Solr update, copy both files and restart Solr:

  ```bash
  docker cp ansible/assets/solr/taxo/schema.xml lifemap-solr:/var/solr/data/taxo/conf/schema.xml
  docker cp ansible/assets/solr/taxo/solrconfig.xml lifemap-solr:/var/solr/data/taxo/conf/solrconfig.xml
  docker restart lifemap-solr
  ```

- Run `update_lifemap.sh` from the installed builder directory to rebuild the data and reload Solr after deploying the files above.
