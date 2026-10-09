# Adding a new language

- Choose the language code, for example `it` for Italian.

- Add the vernacular names file to the `taxonomy-all` GitHub repository:
  `https://github.com/Lifemap-ToL/taxonomy-all/blob/main/<language-code>/TAXONOMIC-VERNACULAR-<CODE-IN-UPPERCASE>-LATEST.txt`
  For example:
  `https://github.com/Lifemap-ToL/taxonomy-all/blob/main/it/TAXONOMIC-VERNACULAR-IT-LATEST.txt`

- Add the language code to `LANG_LIST` in `builder/tree/config.py`.

- Add a column for the language to `builder/taxo/ranks.csv` and translate each rank.

- Add the language fields to `ansible/assets/solr/taxo/schema.xml`: `common_name_<code>`, `rank_<code>`, `all_<code>`, and their matching search fields and copy rules.

- `ansible/templates/bbox/bbox.toml.j2` currently selects rank columns for vector tiles. Add `rank_<code>` to both rank queries only when the frontend is configured to read that tile property; Solr rank fields are configured separately.

- After modifying `schema.xml`, copy it to Solr and restart Solr:

  ```bash
  docker cp ansible/assets/solr/taxo/schema.xml lifemap-solr:/var/solr/data/taxo/conf/schema.xml
  docker restart lifemap-solr
  ```

- Run `update_lifemap.sh` to rebuild the data and reload Solr.
