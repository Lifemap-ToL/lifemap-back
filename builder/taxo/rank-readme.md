# Taxonomic rank translations

`ranks.csv` maps the rank names used by the NCBI taxonomy dump (English column) to display labels in other languages. Add one column per language, using the two-letter language code as the column name. Keep the English rank keys unchanged so the builder can look up each rank consistently.

## English (`en`)

Rank names are taken from NCBI Taxonomy. The values in this column are the English rank keys supplied by NCBI, including labels such as `no rank`, `no_rank`, and specialized ranks. NCBI describes its Taxonomy Database as a curated classification and nomenclature resource: <https://www.ncbi.nlm.nih.gov/taxonomy>.

## French (`fr`)

French labels are ad-hoc translations prepared for Lifemap. They are not presented as a standardized or authoritative French taxonomy vocabulary.

## Spanish (`es`)

Spanish labels were selected using Spanish-language taxonomic and nomenclatural references:

- The Spanish translation of the International Code of Nomenclature for algae, fungi, and plants provides established rank terms and subrank forms, including *reino*, *filo*, *subfilo*, *subgénero*, *subespecie*, *variedad*, and *subvariedad*: <https://www.iapt-taxon.org/nomen/Shenzhen/Spanish/Spanish.pdf>.
- UNAM's biology material lists the principal categories *dominio, reino, filo o división, clase, orden, familia, género,* and *especie*: <https://portalacademico.cch.unam.mx/biologia2/caracteristicas-generales-dominios-y-reinos/categorias-taxonomicas>.
- For the NCBI rank `realm`, a Spanish specialist terminology source uses *dominio* and explains that Spanish uses that same term for both viral `realm` and cellular `domain`: <https://repositori.uji.es/bitstreams/72ae86c8-39d3-4eae-9780-0a9c3d984ac5/download>.
- The IAPT Spanish Code glossary renders `forma specialis` as *forma especial* while retaining the Latin term: <https://www.iapt-taxon.org/nomen/Shenzhen/Spanish/Spanish.pdf>.

Some NCBI ranks are specialized or informal rather than standard ranks covered by general references. Their Spanish values are practical translations for Lifemap; in particular, `morph` is rendered literally as *morfo*, and the compound labels such as `species subgroup`, `pathogroup`, `acellular root`, and `cellular root` do not have a single authoritative Spanish form established here. Review these if a domain-specific Spanish vocabulary becomes available.

## Greek (`el`)

The principal labels follow Greek university material on [taxonomic and animal phylogeny](https://opencourses.uoa.gr/modules/units/?course=BIOL3&id=636): *βασίλειο*, *φύλο*, *ομοταξία*, *τάξη*, *οικογένεια*, *γένος*, and *είδος*. Subrank and superrank labels use the corresponding Greek forms. NCBI describes `realm` as the viral equivalent of `domain`, so both use *επικράτεια* here; see [NCBI's rank update](https://ncbiinsights.ncbi.nlm.nih.gov/2025/02/27/new-ranks-ncbi-taxonomy/).

Specialized or informal ranks, including `species subgroup`, `pathogroup`, `morph`, and the cellular root labels, are practical Greek renderings for Lifemap rather than standardized nomenclature. The two source spellings `no rank` and `no_rank` deliberately share *χωρίς βαθμίδα*.

## Future languages

For each new language, add a column named with its language code. Record the source and translation policy here, including authoritative references where available. Keep uncertain or ad-hoc rank translations identified as such rather than treating them as formally standardized terms.
