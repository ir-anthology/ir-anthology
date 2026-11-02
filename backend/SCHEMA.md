# SPARQL / RDF schema reference

This file exists to let an LLM coding agent write correct SPARQL against this
project's QLever store on the first try — reproducing this app's established query
idioms, not just producing syntactically valid SPARQL. It is generated/maintained
alongside `sparqlTemplates.py`, which is the actual source of truth: when in doubt,
that file (and `main.py`, which substitutes the `$PLACEHOLDER`s below at request
time) wins over this document.

Human-readable documentation of the same data is a separate, lower-priority concern
— `../database/README.md` and `./README.md` cover deployment/operations; this file
is scoped to "what do I need to know to write one more correct query."

## Mental model

This store holds a filtered slice of [DBLP](https://dblp.org)'s RDF graph (the
`dblp:` schema) — Information Retrieval journals, conferences, and workshops only,
see `../database/README.md`'s "Covered streams" — plus a two-term extension this
project adds itself (`ex:`). Core entities:

- **Publication** (`dblp:Publication`, typed more specifically via `dblp:bibtexType`
  as `bibtex:Article` / `bibtex:Inproceedings` / `bibtex:Proceedings`) — a paper, an
  article, or a proceedings volume ("book").
- **Creator** (`dblp:Creator`) — a person, as author or editor.
- **Stream** — a venue: a conference, journal, or (see below) workshop.
- **Signature** (`dblp:AuthorSignature`) — an ordered link between one Creator and
  one Publication, carrying that Creator's position in the author/editor list.

**Workshops are not a separate entity type at the data level.** They're ordinary
`dblp:Stream` nodes additionally typed `ex:Workshop` at import time (see
`../database/add_workshop_stream.rq`). The application layer — both this backend's
query templates and the frontend — collapses every `ex:Workshop`-typed stream into
one synthetic pseudo-venue, `<https://dblp.org/workshops>`, labeled "Workshops". A
query iterating "venues" that doesn't know this idiom will see 44 separate workshop
streams instead of the one aggregate row the UI actually shows — see the
workshop-collapse gotcha below.

## Prefixes

| Prefix | IRI | Canonical docs | Notes |
|---|---|---|---|
| `dblp:` | `https://dblp.org/rdf/schema#` | [schema.rdf](https://dblp.org/rdf/schema.rdf), [docu](https://dblp.org/rdf/docu/) | DBLP's own vocabulary. This project uses a subset — see below. |
| `bibtex:` | `http://purl.org/net/nknouf/ns/bibtex#` | [ontology source](http://purl.org/net/nknouf/ns/bibtex) | Community BibTeX-entry-type vocabulary. Used only for the three entry-type classes below. |
| `ex:` | `https://ir.webis.de/kg#` | — (this file) | This project's own extension. No upstream docs exist; fully defined below. |
| `rdf:` | `http://www.w3.org/1999/02/22-rdf-syntax-ns#` | — | Standard; used only for `?x a ?type` / `rdf:type` triples. |
| `xsd:` | `http://www.w3.org/2001/XMLSchema#` | — | **Declared in most templates but never actually used** — safe to omit in new queries. |

## Gotchas — read before writing a query

### 1. `ex:yearOfConference` vs. `dblp:yearOfEvent` — different properties, not interchangeable

Both exist to capture the true event year where it can differ from
`dblp:yearOfPublication` (DBLP's publication-year metadata). **They are not synonyms
and are not meant to be used interchangeably** — this is an intentional design split,
not an inconsistency to "fix":

- **`ex:yearOfConference`** — this project's own property, injected at import time
  (`../database/get_data.sh` step 3 / `dblp_fetch.py`'s `_extract_year_of_conference()`,
  which regex-extracts a year from a proceedings title) specifically onto conference
  proceedings. This is the one used by the entity-table templates
  (`_ENTITY_TABLE_BODY`, shared by `AUTHOR_TABLE_TEMPLATE` / `VENUE_TABLE_TEMPLATE` /
  `YEARS_TABLE_TEMPLATE` / `PUBLICATION_TABLE_TEMPLATE`) and the venue/workshop
  overview templates (`VENUE_PROCEEDINGS_TEMPLATE`, `WORKSHOPS_PROCEEDINGS_TEMPLATE`,
  `VENUE_YEAR_PROCEEDINGS_QUERY_TEMPLATE`, `WORKSHOPS_YEAR_PROCEEDINGS_QUERY_TEMPLATE`,
  `INPROCEEDINGS_FROM_PROCEEDINGS_TEMPLATE`,
  `WORKSHOPS_INPROCEEDINGS_FROM_PROCEEDINGS_TEMPLATE`) — the conference-scoped signal.
- **`dblp:yearOfEvent`** — an upstream DBLP property, used in the three detail-page
  templates (`BIB_PUBLICATION_TEMPLATE`, `JOURNAL_YEAR_TEMPLATE`, `PERSON_TEMPLATE`)
  as a forward-looking `OPTIONAL`, kept for broader upstream DBLP coverage over time.

Both are always wrapped in `OPTIONAL { ... }` followed by
`BIND(COALESCE(?eventYear, ?pubYear) AS ?year)`, falling back to
`dblp:yearOfPublication` when unset — so using the "wrong" one of the two doesn't
break a query, it just silently loses the preferred-year signal for that query.
**Rule of thumb:** writing something in the style of the entity-table/overview
templates → use `ex:yearOfConference`; writing something in the style of the
detail-page templates → use `dblp:yearOfEvent`. Don't consolidate the two without
checking with a maintainer first. Current live coverage of each can be checked with
the verification recipe at the end of this file.

### 2. Workshop-stream collapse

Every template that lists venues implements the same idiom to fold all
`ex:Workshop`-typed streams into one synthetic row:

```sparql
OPTIONAL { ?stream_URI a ex:Workshop . BIND(true AS ?isWorkshop) }
?stream_URI dblp:primaryStreamTitle ?stream_label .
BIND(IF(BOUND(?isWorkshop), <https://dblp.org/workshops>, ?stream_URI) AS ?venue_URI)
BIND(IF(BOUND(?isWorkshop), "Workshops", ?stream_label) AS ?venue_label)
```

A publication can be reachable through more than one `dblp:publishedInStream` value
(e.g. a paper co-listed under both a workshop stream and its parent conference
stream). Templates that attribute one publication to exactly one venue
(`PUBLICATION_TABLE_TEMPLATE`, `PERSON_TEMPLATE`) additionally apply an
attribution-priority filter: prefer a non-workshop stream if the publication has one,
only fall back to the workshop stream if it doesn't —

```sparql
FILTER(
  NOT EXISTS { ?stream_URI a ex:Workshop }
  ||
  NOT EXISTS {
    ?publication_URI dblp:publishedInStream ?s2 .
    FILTER NOT EXISTS { ?s2 a ex:Workshop }
  }
)
```

### 3. Ordinal-encoded author/editor lists

`dblp:hasSignature` links a publication to `dblp:AuthorSignature` nodes carrying
`dblp:signatureOrdinal` (position), `dblp:signatureCreator` (the Creator IRI), and
`dblp:signatureDblpName` (display name at time of publication — may differ from the
Creator's current `dblp:primaryCreatorName`, e.g. after a name change/merge). Since
SPARQL's `GROUP_CONCAT` can't preserve per-value ordinal ordering natively, every
template needing an ordered author or editor list packs both into one string:

```sparql
(GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", ?authorName); separator=", ") AS ?authors)
(GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", STR(?authorUri)); separator=", ") AS ?authorIds)
```

producing values like `"0@@Jane Doe, 1@@John Smith"`. This is a convention invented
by this codebase, not discoverable from any RDF-level schema — it's decoded by
`decode_ordered()` in `bibtex.py`, which splits on `", "`, then on the first `"@@"`,
sorts by the leading integer, and (with `strip_disambig=True`) strips a DBLP
disambiguation suffix like `" 0001"` from the name. Any new template producing an
author/editor list should reuse this exact `"ordinal@@value"` encoding rather than
inventing a different one.

### 4. `dblp:createdBy` vs. `dblp:authoredBy` — flagged, not yet resolved

Every template uses `dblp:authoredBy` to link a publication to its authors, **except**
`PERSON_TEMPLATE` (backing `GET /api/people/{id}`), which uses `dblp:createdBy`
instead. DBLP's own schema has both `dblp:authoredBy` and `dblp:editedBy` as more
specific properties, with `dblp:createdBy` appearing to be an umbrella covering both —
consistent with `dblp_fetch.py`'s person-import query, which does
`{?pub dblp:authoredBy <person>} UNION {?pub dblp:editedBy <person>}` when *fetching*
a person's data. Whether `PERSON_TEMPLATE` uses `dblp:createdBy` deliberately (so a
person's detail page also picks up publications they edited, not just authored) or
should be aligned with the rest of the codebase has not been confirmed with a
maintainer. Don't assume one is a typo for the other; check before changing either.

### 5. "Loose papers" pattern

`CONFERENCE_LOOSE_PAPERS_TEMPLATE` / `WORKSHOPS_LOOSE_PAPERS_TEMPLATE` find papers
published directly in a stream without going through a proceedings volume — needed
because most papers instead reach a stream indirectly (`pub -[publishedAsPartOf]->
proceedings -[publishedInStream]-> stream`), and the "loose" ones would otherwise be
invisible to per-year proceedings-first browsing:

```sparql
FILTER NOT EXISTS { ?pub dblp:bibtexType bibtex:Proceedings }
FILTER NOT EXISTS {
  ?pub dblp:publishedAsPartOf ?proc .
  ?proc dblp:publishedInStream ?stream .
}
```

## Classes and properties

### `ex:` — this project's own extension (fully defined here; no upstream docs)

| Term | Kind | Meaning |
|---|---|---|
| `ex:Workshop` | Class | Marks a `dblp:Stream` as a workshop (in addition to whatever native DBLP type it may also carry). Injected at import time by `../database/add_workshop_stream.rq`. See gotcha 2 for the venue-collapse idiom this enables. |
| `ex:yearOfConference` | Property (domain: conference-proceedings `bibtex:Proceedings` entities; range: `xsd:string`, a bare year like `"2023"`) | The true conference-event year, regex-extracted from a proceedings title at import time. See gotcha 1. |

### `dblp:` — used subset (canonical definitions: [schema.rdf](https://dblp.org/rdf/schema.rdf) / [docu](https://dblp.org/rdf/docu/))

**Classes**

| Term | Meaning |
|---|---|
| `dblp:Publication` | A publication (paper, article, or proceedings volume). |
| `dblp:Creator` | A person (author or editor). |
| `dblp:Conference` | A conference-series stream. |
| `dblp:Journal` | A journal stream. |
| `dblp:AuthorSignature` | An ordered Creator↔Publication link — see gotcha 3. |

**Properties**

| Term | Meaning |
|---|---|
| `dblp:title` | Title of a publication. |
| `dblp:yearOfPublication` | DBLP's publication-year metadata — the fallback year; see gotcha 1 for the preferred-year overrides. |
| `dblp:yearOfEvent` | Upstream true-event-year property; see gotcha 1. |
| `dblp:authoredBy` | Publication → author Creator. |
| `dblp:createdBy` | Publication → author-or-editor Creator (umbrella); see gotcha 4. |
| `dblp:editedBy` | Publication → editor Creator. |
| `dblp:publishedInStream` | Publication → venue Stream. |
| `dblp:publishedAsPartOf` | Publication → the Proceedings volume it's part of. |
| `dblp:primaryStreamTitle` | Display title of a Stream. |
| `dblp:primaryCreatorName` | A Creator's current display name. |
| `dblp:bibtexType` | Entry type: `bibtex:Article` / `bibtex:Inproceedings` / `bibtex:Proceedings`. |
| `dblp:hasSignature` | Publication → `dblp:AuthorSignature` node; see gotcha 3. |
| `dblp:signatureOrdinal` | Author/editor position within a publication. |
| `dblp:signatureCreator` | Signature → the Creator IRI. |
| `dblp:signatureDblpName` | Author/editor display name at time of publication (may differ from `primaryCreatorName`). |
| `dblp:doi`, `dblp:isbn`, `dblp:pagination`, `dblp:primaryDocumentPage` | Standard bibliographic metadata, all `OPTIONAL` in every template that uses them. |
| `dblp:publishedBy` | Publisher (of a publication or its parent Proceedings). |
| `dblp:publishedInSeries`, `dblp:publishedInSeriesVolume` | Book series metadata (Proceedings). |
| `dblp:publishedInJournalVolume`, `dblp:publishedInJournalVolumeIssue` | Journal volume/issue (Articles). |
| `dblp:monthOfPublication` | Publication month, where DBLP has it. |

### `bibtex:` — used subset

| Term | Meaning |
|---|---|
| `bibtex:Article` | Journal article entry type. |
| `bibtex:Inproceedings` | Conference/workshop paper entry type. |
| `bibtex:Proceedings` | Proceedings-volume ("book") entry type. |

## Worked examples

Real, currently-executing query templates from `sparqlTemplates.py`, regenerated by
`scripts/gen_schema_doc.py` whenever that file changes — **do not hand-edit below
this point**; run the generator instead. `$PLACEHOLDER` tokens (`$FILTERS`, `$ORDER`,
`$LIMIT`, `$OFFSET`, `$SEED`, `$VENUE_URI`, `$YEAR`, …) are substituted by `main.py`
at request time via plain string `.replace()` calls — they are not valid SPARQL on
their own; see `main.py`'s route handlers (e.g. `_run_table_page`, `build_filters`,
`build_year_seed`, `parse_order`) for exactly how each is built.

<!-- GENERATED:EXAMPLES START -->

#### `AUTHOR_TABLE_TEMPLATE`

Used by: `GET /api/table/authors`

```sparql
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT (?author_label AS ?Entity)
  (?author_URI AS ?URI)
  (COUNT(DISTINCT ?publication_label) AS ?Publications)
  (COUNT(DISTINCT ?venue_label)       AS ?Venues)
WHERE {

  ?publication_URI dblp:title ?publication_label ;
                   dblp:yearOfPublication ?pubYear ;
                   dblp:authoredBy ?author_URI ;
                   dblp:publishedInStream ?stream_URI .

  OPTIONAL { ?publication_URI ex:yearOfConference ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)
  BIND(STR(?year) AS ?year_label)

  OPTIONAL { ?stream_URI a ex:Workshop . BIND(true AS ?isWorkshop) }
  ?stream_URI dblp:primaryStreamTitle ?stream_label .
  BIND(IF(BOUND(?isWorkshop), <https://dblp.org/workshops>, ?stream_URI) AS ?venue_URI)
  BIND(IF(BOUND(?isWorkshop), "Workshops", ?stream_label) AS ?venue_label)
  OPTIONAL { ?author_URI dblp:primaryCreatorName ?author_label . }

  $FILTERS

}
GROUP BY ?author_label ?author_URI
HAVING (BOUND(?author_label))
$ORDER
LIMIT $LIMIT
OFFSET $OFFSET
```

#### `VENUE_TABLE_TEMPLATE`

Used by: `GET /api/table/venues`

```sparql
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT (?venue_label AS ?Entity)
  (?venue_URI AS ?URI)
  (COUNT(DISTINCT ?author_label)      AS ?Authors)
  (COUNT(DISTINCT ?publication_label) AS ?Publications)
  (STRAFTER(STR(?venue_rdf_type), "#") AS ?VenueType)
WHERE {

  ?publication_URI dblp:title ?publication_label ;
                   dblp:yearOfPublication ?pubYear ;
                   dblp:authoredBy ?author_URI ;
                   dblp:publishedInStream ?stream_URI .

  OPTIONAL { ?publication_URI ex:yearOfConference ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)
  BIND(STR(?year) AS ?year_label)

  OPTIONAL { ?stream_URI a ex:Workshop . BIND(true AS ?isWorkshop) }
  ?stream_URI dblp:primaryStreamTitle ?stream_label .
  BIND(IF(BOUND(?isWorkshop), <https://dblp.org/workshops>, ?stream_URI) AS ?venue_URI)
  BIND(IF(BOUND(?isWorkshop), "Workshops", ?stream_label) AS ?venue_label)
  OPTIONAL { ?author_URI dblp:primaryCreatorName ?author_label . }

  $FILTERS

  # sort key mirroring the frontend's venueDisplayLabel: the venue's abbreviation
  # (last parenthesized group of the title, else the uppercased URI tail) — the
  # Entity column displays abbreviations, so Entity sorting must order by them
  BIND(UCASE(IF(REGEX(?venue_label, "\\(([^)]+)\\)"),
                REPLACE(?venue_label, "^.*\\(([^)]+)\\).*$", "$1"),
                REPLACE(STR(?venue_URI), "^.*/", ""))) AS ?venue_sort)
  OPTIONAL {
    ?venue_URI a ?venue_rdf_type .
    VALUES ?venue_rdf_type { dblp:Conference dblp:Journal }
  }
}
GROUP BY ?venue_label ?venue_URI ?venue_sort ?venue_rdf_type
HAVING (BOUND(?venue_label))
$ORDER
LIMIT $LIMIT
OFFSET $OFFSET
```

#### `YEARS_TABLE_TEMPLATE`

Used by: `GET /api/table/years`

```sparql
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT (?year AS ?Entity)
  (?year AS ?URI)
  (COUNT(DISTINCT ?publication_label) AS ?Publications)
  (COUNT(DISTINCT ?venue_label)       AS ?Venues)
  (COUNT(DISTINCT ?author_label)      AS ?Authors)
WHERE {

  ?publication_URI dblp:title ?publication_label ;
                   dblp:yearOfPublication ?pubYear ;
                   dblp:authoredBy ?author_URI ;
                   dblp:publishedInStream ?stream_URI .

  OPTIONAL { ?publication_URI ex:yearOfConference ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)
  BIND(STR(?year) AS ?year_label)

  OPTIONAL { ?stream_URI a ex:Workshop . BIND(true AS ?isWorkshop) }
  ?stream_URI dblp:primaryStreamTitle ?stream_label .
  BIND(IF(BOUND(?isWorkshop), <https://dblp.org/workshops>, ?stream_URI) AS ?venue_URI)
  BIND(IF(BOUND(?isWorkshop), "Workshops", ?stream_label) AS ?venue_label)
  OPTIONAL { ?author_URI dblp:primaryCreatorName ?author_label . }

  $FILTERS

}
GROUP BY ?year
$ORDER
LIMIT $LIMIT
OFFSET $OFFSET
```

#### `AUTHOR_YEAR_COUNTS_TEMPLATE`

Used by: `GET /api/table/authors`

```sparql
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT (?author_URI AS ?URI) (GROUP_CONCAT(CONCAT(STR(?year), "@@", STR(?cnt)); separator=", ") AS ?Years)
WHERE {
  SELECT ?author_URI ?year (COUNT(DISTINCT ?publication_URI) AS ?cnt)
  WHERE {
    $SEED

  ?publication_URI dblp:title ?publication_label ;
                   dblp:yearOfPublication ?pubYear ;
                   dblp:authoredBy ?author_URI ;
                   dblp:publishedInStream ?stream_URI .

  OPTIONAL { ?publication_URI ex:yearOfConference ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)
  BIND(STR(?year) AS ?year_label)

  OPTIONAL { ?stream_URI a ex:Workshop . BIND(true AS ?isWorkshop) }
  ?stream_URI dblp:primaryStreamTitle ?stream_label .
  BIND(IF(BOUND(?isWorkshop), <https://dblp.org/workshops>, ?stream_URI) AS ?venue_URI)
  BIND(IF(BOUND(?isWorkshop), "Workshops", ?stream_label) AS ?venue_label)
  OPTIONAL { ?author_URI dblp:primaryCreatorName ?author_label . }

  $FILTERS

  }
  GROUP BY ?author_URI ?year
}
GROUP BY ?author_URI
```

#### `PUBLICATION_TABLE_TEMPLATE`

Used by: `GET /api/table/publications`

```sparql
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?Entity ?URI ?Authors ?authors ?authorIds ?Year
  (STRBEFORE(STRAFTER(?venuePair, "@@"), "@@") AS ?Venue)
  (STRAFTER(STRAFTER(?venuePair, "@@"), "@@") AS ?VenueURI)
WHERE {
  SELECT (?publication_label AS ?Entity)
    (?publication_URI AS ?URI)
    (COUNT(DISTINCT ?author_label) AS ?Authors)
    (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", ?authorName); separator=", ") AS ?authors)
    (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", STR(?authorUri)); separator=", ") AS ?authorIds)
    (MIN(STR(?year)) AS ?Year)
    (MIN(CONCAT(?venue_sort, "@@", ?venue_label, "@@", STR(?venue_URI))) AS ?venuePair)
  WHERE {

  ?publication_URI dblp:title ?publication_label ;
                   dblp:yearOfPublication ?pubYear ;
                   dblp:authoredBy ?author_URI ;
                   dblp:publishedInStream ?stream_URI .

  OPTIONAL { ?publication_URI ex:yearOfConference ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)
  BIND(STR(?year) AS ?year_label)

  OPTIONAL { ?stream_URI a ex:Workshop . BIND(true AS ?isWorkshop) }
  ?stream_URI dblp:primaryStreamTitle ?stream_label .
  BIND(IF(BOUND(?isWorkshop), <https://dblp.org/workshops>, ?stream_URI) AS ?venue_URI)
  BIND(IF(BOUND(?isWorkshop), "Workshops", ?stream_label) AS ?venue_label)
  OPTIONAL { ?author_URI dblp:primaryCreatorName ?author_label . }

  $FILTERS

    # abbreviation-first pair: MIN picks (and sort_by=Venue orders by) the venue
    # abbreviation, matching what the Venue column displays
    BIND(UCASE(IF(REGEX(?venue_label, "\\(([^)]+)\\)"),
                  REPLACE(?venue_label, "^.*\\(([^)]+)\\).*$", "$1"),
                  REPLACE(STR(?venue_URI), "^.*/", ""))) AS ?venue_sort)
    # venue attribution (as in PERSON_TEMPLATE): keep non-workshop stream rows;
    # workshop rows only survive when the publication has no non-workshop stream
    FILTER(
      NOT EXISTS { ?stream_URI a ex:Workshop }
      ||
      NOT EXISTS {
        ?publication_URI dblp:publishedInStream ?s2 .
        FILTER NOT EXISTS { ?s2 a ex:Workshop }
      }
    )
    OPTIONAL {
      ?publication_URI dblp:hasSignature ?sig .
      ?sig a dblp:AuthorSignature ;
           dblp:signatureOrdinal ?ord ;
           dblp:signatureCreator ?authorUri ;
           dblp:signatureDblpName ?authorName .
    }
  }
  GROUP BY ?publication_label ?publication_URI
  $ORDER
  LIMIT $LIMIT
  OFFSET $OFFSET
}
$ORDER
```

#### `VENUE_YEAR_COUNTS_TEMPLATE`

Used by: `GET /api/table/venues`

```sparql
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT (?venue_URI AS ?URI) (GROUP_CONCAT(CONCAT(STR(?year), "@@", STR(?cnt)); separator=", ") AS ?Years)
WHERE {
  SELECT ?venue_URI ?year (COUNT(DISTINCT ?publication_URI) AS ?cnt)
  WHERE {
    $SEED

  ?publication_URI dblp:title ?publication_label ;
                   dblp:yearOfPublication ?pubYear ;
                   dblp:authoredBy ?author_URI ;
                   dblp:publishedInStream ?stream_URI .

  OPTIONAL { ?publication_URI ex:yearOfConference ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)
  BIND(STR(?year) AS ?year_label)

  OPTIONAL { ?stream_URI a ex:Workshop . BIND(true AS ?isWorkshop) }
  ?stream_URI dblp:primaryStreamTitle ?stream_label .
  BIND(IF(BOUND(?isWorkshop), <https://dblp.org/workshops>, ?stream_URI) AS ?venue_URI)
  BIND(IF(BOUND(?isWorkshop), "Workshops", ?stream_label) AS ?venue_label)
  OPTIONAL { ?author_URI dblp:primaryCreatorName ?author_label . }

  $FILTERS

  }
  GROUP BY ?venue_URI ?year
}
GROUP BY ?venue_URI
```

#### `ANTHOLOGY_CONFERENCES_QUERY_TEMPLATE`

Used by: `GET /api/conferences`

```sparql
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT DISTINCT ?stream ?venue_label ?year ?type
WHERE {
  VALUES ?type {dblp:Conference}
  ?stream a ?type ;
          dblp:primaryStreamTitle ?venue_label .

  FILTER NOT EXISTS { ?stream a ex:Workshop }

  ?pub ex:yearOfConference ?year ;
       dblp:publishedInStream ?stream .
}
ORDER BY ?type ?venue_label ?year
```

#### `ANTHOLOGY_WORKSHOPS_QUERY_TEMPLATE`

Used by: `GET /api/workshops`

```sparql
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT DISTINCT ?stream ?venue_label ?year ?type
WHERE {
  VALUES ?type {ex:Workshop}
  ?stream a ?type ;
          dblp:primaryStreamTitle ?venue_label .

  ?pub ex:yearOfConference ?year ;
       dblp:publishedInStream ?stream .
}
ORDER BY ?type ?venue_label ?year
```

#### `ANTHOLOGY_JOURNALS_QUERY_TEMPLATE`

Used by: `GET /api/journals`

```sparql
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT DISTINCT ?stream ?venue_label ?year ?type
WHERE {
  VALUES ?type { dblp:Journal }
  ?pub dblp:yearOfPublication ?year ;
                   dblp:publishedInStream ?stream .

  ?stream a ?type ;
          dblp:primaryStreamTitle ?venue_label .
}
ORDER BY ?type ?venue_label ?year
```

#### `YEARS_QUERY_TEMPLATE`

**Not referenced by any route in `main.py` at generation time** — appears unused; verify before treating this as a live query pattern.

```sparql
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT DISTINCT ?year ?title ?streamTitle ?pub WHERE{
  VALUES ?stream {
  <$VENUE_URI>
  }
  ?pub dblp:yearOfPublication ?pubYear ;
      dblp:publishedInStream ?stream ;
      dblp:title ?title ;
      dblp:bibtexType bibtex:Proceedings .

  OPTIONAL { ?pub ex:yearOfConference ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)

  ?stream dblp:primaryStreamTitle ?streamTitle .
}
```

#### `VENUE_PROCEEDINGS_TEMPLATE`

Used by: `GET /api/conferences/{id}`

```sparql
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?year ?title ?streamTitle ?pub ?type ?proc WHERE {
  VALUES ?stream {
    <$VENUE_URI>
  }
  ?pub dblp:yearOfPublication ?pubYear ;
       dblp:publishedInStream ?stream ;
       dblp:title ?title ;
       dblp:bibtexType ?type .

  OPTIONAL { ?pub ex:yearOfConference ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)

  ?stream dblp:primaryStreamTitle ?streamTitle .
  OPTIONAL {
    ?pub dblp:publishedAsPartOf ?proc .
    ?proc dblp:bibtexType bibtex:Proceedings .
  }
}
GROUP BY ?year ?title ?streamTitle ?pub ?type ?proc
ORDER BY ?type DESC(?year) ?title
```

#### `WORKSHOPS_PROCEEDINGS_TEMPLATE`

Used by: `GET /api/workshops/proceedings`

```sparql
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?year ?title ?streamTitle ?pub ?type ?proc WHERE {
  VALUES ?streamTitle {'Workshops'}
  ?stream a ex:Workshop .
  ?pub dblp:yearOfPublication ?pubYear ;
       dblp:publishedInStream ?stream ;
       dblp:title ?title ;
       dblp:bibtexType ?type .

  OPTIONAL { ?pub ex:yearOfConference ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)

  OPTIONAL {
    ?pub dblp:publishedAsPartOf ?proc .
    ?proc dblp:bibtexType bibtex:Proceedings .
  }
}
GROUP BY ?year ?title ?streamTitle ?pub ?type ?proc
ORDER BY ?type DESC(?year) ?title
```

#### `WORKSHOPS_YEAR_PROCEEDINGS_QUERY_TEMPLATE`

Used by: `GET /api/workshops/{year}/proceedings`

```sparql
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?title (MIN(STR(?doi_raw)) AS ?doi) ?pub ?streamTitle WHERE{
  ?stream a ex:Workshop .
  VALUES ?streamTitle {'Workshops'}
  ?pub dblp:title ?title ;
       dblp:publishedInStream ?stream ;
	   dblp:bibtexType bibtex:Proceedings ;
	   dblp:yearOfPublication ?pubYear .
       
  OPTIONAL { ?pub ex:yearOfConference ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)

  FILTER(STR(?year) = "$YEAR")

  OPTIONAL{?pub dblp:doi ?doi_raw}
}
GROUP BY ?title ?pub ?streamTitle
```

#### `VENUE_YEAR_PROCEEDINGS_QUERY_TEMPLATE`

Used by: `GET /api/conferences/{id}/{year}/proceedings`

```sparql
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?title (MIN(STR(?doi_raw)) AS ?doi) ?pub ?streamTitle WHERE{
  VALUES ?stream {
    <$VENUE_ID>
  }
  ?pub dblp:title ?title ;
       dblp:publishedInStream ?stream ;
	   dblp:bibtexType bibtex:Proceedings ;
	   dblp:yearOfPublication ?pubYear .
       
  OPTIONAL { ?pub ex:yearOfConference ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)

  ?stream dblp:primaryStreamTitle ?streamTitle .
  FILTER(STR(?year) = "$YEAR")

  OPTIONAL{?pub dblp:doi ?doi_raw}
}
GROUP BY ?title ?pub ?streamTitle
```

#### `INPROCEEDINGS_FROM_PROCEEDINGS_TEMPLATE`

Used by: `GET /api/conferences/{id}/{year}/inproceedings`

```sparql
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?title (MIN(STR(?doi_raw)) AS ?doi) ?book ?pub
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", ?authorName); separator=", ") AS ?authors)
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", STR(?authorUri)); separator=", ") AS ?authorIds)
WHERE{
  VALUES ?stream {
    <$VENUE_ID>
  }
  ?book dblp:publishedInStream ?stream ;
        dblp:bibtexType bibtex:Proceedings ;
        dblp:yearOfPublication ?pubYear .

  OPTIONAL { ?book ex:yearOfConference ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)

  FILTER(STR(?year) = "$YEAR")

  ?pub dblp:publishedAsPartOf ?book ;
       dblp:title ?title ;
	   dblp:bibtexType bibtex:Inproceedings .

  OPTIONAL{?pub dblp:doi ?doi_raw}
  OPTIONAL {
    ?pub dblp:hasSignature ?sig .
    ?sig a dblp:AuthorSignature ;
         dblp:signatureOrdinal ?ord ;
         dblp:signatureCreator ?authorUri ;
         dblp:signatureDblpName ?authorName .
  }
}
GROUP BY ?title ?book ?pub
```

#### `WORKSHOPS_INPROCEEDINGS_FROM_PROCEEDINGS_TEMPLATE`

Used by: `GET /api/workshops/{year}/inproceedings`

```sparql
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?title (MIN(STR(?doi_raw)) AS ?doi) ?book ?pub
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", ?authorName); separator=", ") AS ?authors)
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", STR(?authorUri)); separator=", ") AS ?authorIds)
WHERE{
  ?stream a ex:Workshop .
  ?book dblp:publishedInStream ?stream ;
        dblp:bibtexType bibtex:Proceedings ;
        dblp:yearOfPublication ?pubYear .

  OPTIONAL { ?book ex:yearOfConference ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)

  FILTER(STR(?year) = "$YEAR")

  ?pub dblp:publishedAsPartOf ?book ;
       dblp:title ?title ;
	   dblp:bibtexType bibtex:Inproceedings .

  OPTIONAL{?pub dblp:doi ?doi_raw}
  OPTIONAL {
    ?pub dblp:hasSignature ?sig .
    ?sig a dblp:AuthorSignature ;
         dblp:signatureOrdinal ?ord ;
         dblp:signatureCreator ?authorUri ;
         dblp:signatureDblpName ?authorName .
  }
}
GROUP BY ?title ?book ?pub
```

#### `CONFERENCE_LOOSE_PAPERS_TEMPLATE`

Used by: `GET /api/conferences/{id}/{year}/loose`

```sparql
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?title (MIN(STR(?doi_raw)) AS ?doi) ?pub ?streamTitle
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", ?authorName); separator=", ") AS ?authors)
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", STR(?authorUri)); separator=", ") AS ?authorIds)
WHERE {
  VALUES ?stream { <$VENUE_ID> }
  ?stream dblp:primaryStreamTitle ?streamTitle .
  ?pub dblp:publishedInStream ?stream ;
       dblp:yearOfPublication ?year ;
       dblp:title ?title .

  FILTER(STR(?year) = "$YEAR")
  FILTER NOT EXISTS { ?pub dblp:bibtexType bibtex:Proceedings }
  FILTER NOT EXISTS {
    ?pub dblp:publishedAsPartOf ?proc .
    ?proc dblp:publishedInStream ?stream .
  }

  OPTIONAL { ?pub dblp:doi ?doi_raw }
  OPTIONAL {
    ?pub dblp:hasSignature ?sig .
    ?sig a dblp:AuthorSignature ;
         dblp:signatureOrdinal ?ord ;
         dblp:signatureCreator ?authorUri ;
         dblp:signatureDblpName ?authorName .
  }
}
GROUP BY ?title ?pub ?streamTitle
ORDER BY ?title
```

#### `WORKSHOPS_LOOSE_PAPERS_TEMPLATE`

Used by: `GET /api/workshops/{year}/loose`

```sparql
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?title (MIN(STR(?doi_raw)) AS ?doi) ?pub
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", ?authorName); separator=", ") AS ?authors)
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", STR(?authorUri)); separator=", ") AS ?authorIds)
WHERE {
  ?stream a ex:Workshop .
  ?pub dblp:publishedInStream ?stream ;
       dblp:yearOfPublication ?year ;
       dblp:title ?title .

  FILTER(STR(?year) = "$YEAR")
  FILTER NOT EXISTS { ?pub dblp:bibtexType bibtex:Proceedings }
  FILTER NOT EXISTS {
    ?pub dblp:publishedAsPartOf ?proc .
    ?proc dblp:publishedInStream ?stream .
  }

  OPTIONAL { ?pub dblp:doi ?doi_raw }
  OPTIONAL {
    ?pub dblp:hasSignature ?sig .
    ?sig a dblp:AuthorSignature ;
         dblp:signatureOrdinal ?ord ;
         dblp:signatureCreator ?authorUri ;
         dblp:signatureDblpName ?authorName .
  }
}
GROUP BY ?title ?pub
ORDER BY ?title
```

#### `PUBLICATIONS_TEMPLATE`

Used by: `GET /api/publications`

```sparql
PREFIX dblp: <https://dblp.org/rdf/schema#>
SELECT ?pub ?title WHERE {
  ?pub a dblp:Publication .
  ?pub dblp:title ?title .
}
```

#### `BIB_PUBLICATION_TEMPLATE`

Used by: `GET /api/publications/{id}`

```sparql
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>

SELECT ?title ?booktitle ?series ?pages ?publisher (MIN(STR(?doi_raw)) AS ?doi) ?url ?year ?book ?pub ?stream ?streamTitle ?month ?volume ?number ?isbn ?bibtexType
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", ?authorName); separator=", ") AS ?authors)
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", STR(?authorUri)); separator=", ") AS ?authorIds)
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?edOrd), "@@", ?editorName); separator=", ") AS ?editors)
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?edOrd), "@@", STR(?editor)); separator=", ") AS ?editorIds)
WHERE{
  VALUES ?pub {
    <$PUBLICATION>
  }
  ?pub dblp:title ?title ;
       dblp:publishedInStream ?stream ;
	   dblp:bibtexType ?bibtexType ;
	   dblp:yearOfPublication ?pubYear .

  OPTIONAL { ?pub dblp:yearOfEvent ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)

  ?stream dblp:primaryStreamTitle ?streamTitle .

  OPTIONAL{?pub dblp:pagination ?pages}
  OPTIONAL{?pub dblp:doi ?doi_raw}
  OPTIONAL{?pub dblp:publishedBy ?pubPublisher}
  OPTIONAL{?pub dblp:primaryDocumentPage ?url}
  OPTIONAL{?pub dblp:monthOfPublication ?month}
  OPTIONAL{?pub dblp:publishedInJournalVolume ?journalVolume}
  OPTIONAL{?pub dblp:publishedInSeriesVolume ?seriesVolume}
  BIND(COALESCE(?journalVolume, ?seriesVolume) AS ?pubVolume)
  OPTIONAL{?pub dblp:publishedInJournalVolumeIssue ?number}
  OPTIONAL{?pub dblp:publishedInSeries ?pubSeries }
  OPTIONAL{?pub dblp:isbn ?isbn}
  OPTIONAL{?pub dblp:hasSignature ?sig .
            ?sig a dblp:AuthorSignature ;
                 dblp:signatureOrdinal ?ord ;
                 dblp:signatureCreator ?authorUri ;
                 dblp:signatureDblpName ?authorName}
  OPTIONAL {
                ?pub dblp:editedBy ?pubEditor .
                ?pubEditor dblp:primaryCreatorName ?pubEditorName .
                OPTIONAL {
                    ?pub dblp:hasSignature ?pubEdSig .
                    ?pubEdSig dblp:signatureCreator ?pubEditor ;
                              dblp:signatureOrdinal ?pubEdOrd .
                }
            }
  OPTIONAL {?pub dblp:publishedAsPartOf ?book .
            ?book dblp:title ?booktitle .
            OPTIONAL {
                ?book dblp:editedBy ?bookEditor .
                ?bookEditor dblp:primaryCreatorName ?bookEditorName .
                OPTIONAL {
                    ?book dblp:hasSignature ?bookEdSig .
                    ?bookEdSig dblp:signatureCreator ?bookEditor ;
                               dblp:signatureOrdinal ?bookEdOrd .
                }
            }
            OPTIONAL { ?book dblp:publishedBy ?bookPublisher }
            OPTIONAL { ?book dblp:publishedInSeries ?bookSeries }
            OPTIONAL{?book dblp:publishedInSeriesVolume ?bookSeriesVolume}
  }
  BIND(COALESCE(?pubPublisher, ?bookPublisher) AS ?publisher)  
  BIND(COALESCE(?pubSeries, ?bookSeries) AS ?series)  
  BIND(COALESCE(?pubEditor, ?bookEditor) AS ?editor)
  BIND(COALESCE(?pubEditorName, ?bookEditorName) AS ?editorName)
  BIND(COALESCE(?pubEdOrd, ?bookEdOrd) AS ?edOrd)  
  BIND(COALESCE(?pubVolume, ?bookSeriesVolume) AS ?volume)

}
GROUP BY ?title ?booktitle ?series ?pages ?publisher ?url ?year ?book ?pub ?stream ?streamTitle ?month ?volume ?number ?isbn ?bibtexType
```

#### `JOURNAL_YEAR_TEMPLATE`

Used by: `GET /api/journals/{id}/{year}`

```sparql
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>

SELECT ?title ?journalTitle ?volume ?number (MIN(STR(?doi_raw)) AS ?doi) ?pub
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", ?authorName); separator=", ") AS ?authors)
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", STR(?authorUri)); separator=", ") AS ?authorIds)
WHERE{
  VALUES ?journal {
    <$JOURNAL>
  }
  ?journal dblp:primaryStreamTitle ?journalTitle .
  ?pub dblp:publishedInStream ?journal ;
       dblp:title ?title ;
	   dblp:bibtexType bibtex:Article ;
	   dblp:yearOfPublication ?pubYear .
       
  OPTIONAL { ?pub dblp:yearOfEvent ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)

  FILTER(STR(?year) = "$YEAR")
  OPTIONAL{?pub dblp:publishedInJournalVolume ?volume}
  OPTIONAL{?pub dblp:publishedInJournalVolumeIssue ?number}
  OPTIONAL{?pub dblp:doi ?doi_raw}
  OPTIONAL {
    ?pub dblp:hasSignature ?sig .
    ?sig a dblp:AuthorSignature ;
         dblp:signatureOrdinal ?ord ;
         dblp:signatureCreator ?authorUri ;
         dblp:signatureDblpName ?authorName .
  }
}
GROUP BY ?title ?journalTitle ?volume ?number ?pub
```

#### `JOURNAL_OVERVIEW_TEMPLATE`

Used by: `GET /api/journals/{id}`

```sparql
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>

SELECT ?year ?volume ?number ?journalTitle (COUNT(DISTINCT ?pub) AS ?count) WHERE {
  VALUES ?journal {
    <$JOURNAL>
  }
  ?journal dblp:primaryStreamTitle ?journalTitle .
  ?pub dblp:publishedInStream ?journal ;
       dblp:bibtexType bibtex:Article ;
       dblp:yearOfPublication ?year .

  OPTIONAL { ?pub dblp:publishedInJournalVolume ?volume }
  OPTIONAL { ?pub dblp:publishedInJournalVolumeIssue ?number }
}
GROUP BY ?year ?volume ?number ?journalTitle
ORDER BY DESC(?year) ?volume ?number
```

#### `PEOPLE_TEMPLATE`

Used by: `GET /api/people`

```sparql
PREFIX dblp: <https://dblp.org/rdf/schema#>
SELECT ?person ?name WHERE {
  ?person a dblp:Creator .
  ?person dblp:primaryCreatorName ?name .
}
```

#### `PERSON_TEMPLATE`

Used by: `GET /api/people/{id}`

```sparql
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?title ?year (MIN(STR(?doi_raw)) AS ?doi) ?pub ?name ?book ?booktitle ?streamTitle ?journalVolume ?journalNumber ?stream
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", ?authorName); separator=", ") AS ?authors)
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", STR(?authorUri)); separator=", ") AS ?authorIds)
WHERE {
  VALUES ?author {
    <$AUTHOR>
  }
  ?pub dblp:createdBy ?author ;
       dblp:bibtexType ?bibtexType ;
       dblp:yearOfPublication ?pubYear ;
       dblp:publishedInStream ?stream ;
       dblp:title ?title .

  ?stream dblp:primaryStreamTitle ?streamTitle .
  FILTER(
    NOT EXISTS { ?stream a ex:Workshop }
    ||
    NOT EXISTS {
      ?pub dblp:publishedInStream ?s2 .
      FILTER NOT EXISTS { ?s2 a ex:Workshop }
    }
  )

  OPTIONAL { ?pub dblp:yearOfEvent ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)

  OPTIONAL { ?pub dblp:doi ?doi_raw }
  OPTIONAL { ?author dblp:primaryCreatorName ?name }
  OPTIONAL { ?pub dblp:publishedAsPartOf ?book .
             ?book dblp:title ?booktitle }
  OPTIONAL { ?pub dblp:publishedInJournalVolume ?journalVolume }
  OPTIONAL { ?pub dblp:publishedInJournalVolumeIssue ?journalNumber }
  OPTIONAL {
    ?pub dblp:hasSignature ?sig .
    ?sig a dblp:AuthorSignature ;
         dblp:signatureOrdinal ?ord ;
         dblp:signatureCreator ?authorUri ;
         dblp:signatureDblpName ?authorName .
  }
}
GROUP BY ?title ?year ?pub ?name ?booktitle ?streamTitle ?journalVolume ?journalNumber ?stream ?book
```

<!-- GENERATED:EXAMPLES END -->

## Live verification recipe

The store is rebuilt periodically from DBLP's own live endpoint (`qlever get-data &&
qlever index` — see `../database/README.md`), so class/property *coverage* can shift
over time even though the vocabulary and query idioms above are stable. If a query
using something above returns fewer/more rows than expected, verify against the live
endpoint before assuming the doc is wrong (or right):

```sparql
# Every class in use, with instance counts
PREFIX dblp: <https://dblp.org/rdf/schema#>
SELECT ?class (COUNT(DISTINCT ?s) AS ?count) WHERE { ?s a ?class }
GROUP BY ?class ORDER BY DESC(?count)
```

```sparql
# Every property in use, with usage/subject/object counts
SELECT ?p (COUNT(*) AS ?count) (COUNT(DISTINCT ?s) AS ?subjects) (COUNT(DISTINCT ?o) AS ?objects)
WHERE { ?s ?p ?o } GROUP BY ?p ORDER BY DESC(?count)
```

```sparql
# Properties actually used on instances of one class, with one sample value each
PREFIX dblp: <https://dblp.org/rdf/schema#>
SELECT ?p (SAMPLE(?o) AS ?example) (COUNT(*) AS ?count)
WHERE { ?s a dblp:Publication ; ?p ?o } GROUP BY ?p ORDER BY DESC(?count)
```

```sparql
# The two "true event year" properties (gotcha 1) — coverage and overlap
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX ex: <https://ir.webis.de/kg#>
SELECT (COUNT(*) AS ?n) WHERE { ?pub dblp:yearOfEvent ?y }
# run again with ex:yearOfConference in place of dblp:yearOfEvent
```

```sparql
# All triples for one specific IRI — the fastest way to sanity-check a single
# publication/stream/person against everything above
SELECT ?p ?o WHERE { <REPLACE_WITH_IRI> ?p ?o }
```
