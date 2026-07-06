# IR Anthology — Backend

FastAPI REST API that translates HTTP requests into SPARQL queries against a QLever triplestore, with DBLP import tooling and a GitLab-authenticated admin panel.

## Tech stack

| Concern | Tool |
|---|---|
| Framework | FastAPI (`fastapi[standard]`) |
| Language | Python 3.14 |
| Server | Uvicorn (bundled with `fastapi[standard]`) |
| HTTP client | `httpx` — async, shared `AsyncClient` on `app.state` |
| Data validation | Pydantic v2 |
| Data access | Raw SPARQL — no ORM |
| Auth | GitLab OAuth2 token introspection (`/oauth/userinfo`) |
| Dependencies | `pip install "fastapi[standard]"` — no `requirements.txt` |

## Project structure

```
backend/
├── Dockerfile           python:3.14.5-trixie; entrypoint: fastapi run main.py; port 8000
├── main.py              all route handlers, shared httpx client, SPARQL helpers, Pydantic models
├── auth_utils.py        require_admin dependency — GitLab userinfo check per request
├── sparqlTemplates.py   all SPARQL SELECT/CONSTRUCT/INSERT string templates
├── bibtex.py            BibTeX key derivation, Unicode escaping, entry formatting
├── dblp_fetch.py        paginated CONSTRUCT queries against sparql.dblp.org, dedup, year extraction
└── patches.py           patch file persistence (.nt + .meta.json sidecars) and INSERT DATA helpers
```

## Configuration

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `SPARQL_ACCESS_TOKEN` | `""` | Appended as `?access-token=<token>` to SPARQL write requests when non-empty |
| `DATA_PATH` | `./data` | Root directory for the `patches/` subdirectory. The Docker image sets this to `/app/data`. |

### Hardcoded constants

These must be changed in source:

| Constant | File | Value |
|---|---|---|
| `SPARQL_ENDPOINT` | `main.py` | `https://database-ir-anthology.srv.webis.de/` |
| `DBLP_ENDPOINT` | `dblp_fetch.py` | `https://sparql.dblp.org/sparql` |
| `GITLAB_URL` | `auth_utils.py` | `https://git.webis.de` |
| `ADMIN_GROUP` | `auth_utils.py` | `auth/auth-webis-admin` |

### CORS

Allowed origins (regex): `https://.*\.webis\.de` and `http://localhost(:\d+)?`. Methods: GET, POST.

## Commands

```sh
pip install "fastapi[standard]"

fastapi dev main.py     # development — auto-reload, port 8000
fastapi run main.py     # production
```

```sh
# Docker
docker build -t ir-anthology-backend .
docker run -p 8000:8000 \
  -e SPARQL_ACCESS_TOKEN=your_token \
  -v /host/data:/app/data \
  ir-anthology-backend
```

Interactive API docs are available at `http://localhost:8000/docs` when running.

## API endpoints

### ID encoding

Path segments labelled `{id}` are DBLP URIs with `/` replaced by `+`. `main.py` reverses this with:

```python
def get_uri_from_id(ir_id: str):
    return "https://dblp.org/" + ir_id.replace("+", "/")
```

So `/api/conferences/journals+tois` maps to `https://dblp.org/journals/tois`.

### Public endpoints

| Method | Path | SPARQL template | Key response vars |
|---|---|---|---|
| GET | `/api/table` | `TABLE_QUERY_TEMPLATE` | `Entity`, `URI`, `Publication`, `Venue`, `Author`, `Year` |
| GET | `/api/conferences` | `ANTHOLOGY_CONFERENCES_QUERY_TEMPLATE` | `stream`, `venue_label`, `year`, `type` |
| GET | `/api/conferences/{id}` | `VENUE_PROCEEDINGS_TEMPLATE` | `year`, `title`, `streamTitle`, `pub`, `count` |
| GET | `/api/conferences/{id}/{year}/proceedings` | `PROCEEDINGS_QUERY_TEMPLATE` | `title`, `doi`, `pub`, `streamTitle` |
| GET | `/api/conferences/{id}/{year}/inproceedings` | `INPROCEEDINGS_FROM_PROCEEDINGS_TEMPLATE` | `title`, `doi`, `book`, `pub`, `authors`, `authorIds` |
| GET | `/api/workshops` | `ANTHOLOGY_WORKSHOPS_QUERY_TEMPLATE` | `stream`, `venue_label`, `year`, `type` |
| GET | `/api/workshops/{year}/proceedings` | `WORKSHOPS_YEAR_PROCEEDINGS_QUERY_TEMPLATE` | `title`, `doi`, `pub`, `streamTitle` |
| GET | `/api/workshops/{year}/inproceedings` | `WORKSHOPS_INPROCEEDINGS_FROM_PROCEEDINGS_TEMPLATE` | `title`, `doi`, `book`, `pub`, `authors`, `authorIds` |
| GET | `/api/journals` | `ANTHOLOGY_JOURNALS_QUERY_TEMPLATE` | `stream`, `venue_label`, `year`, `type` |
| GET | `/api/journals/{id}` | `JOURNAL_OVERVIEW_TEMPLATE` | `year`, `volume`, `number`, `journalTitle`, `count` |
| GET | `/api/journals/{id}/{year}` | `ARTICLES_FROM_JOURNAL_TEMPLATE` | `title`, `journalTitle`, `volume`, `number`, `doi`, `pub`, `authors`, `authorIds` |
| GET | `/api/people` | `PERSONS_TEMPLATE` | `person`, `name` |
| GET | `/api/people/{id}` | `PERSON_TEMPLATE` | `title`, `year`, `doi`, `pub`, `booktitle`, `stream`, `authors`, `authorIds`, … |
| GET | `/api/publications` | `PUBLICATIONS_TEMPLATE` | `pub`, `title` |
| GET | `/api/publications/{id}` | `BIB_PUBLICATION_TEMPLATE` | all publication fields + `"bibtex"` string |

`/api/publications/{id}` is the only endpoint that adds a non-SPARQL field: the response includes a `"bibtex"` key containing the generated BibTeX entry string (see [BibTeX generation](#bibtex-generation)).

**`/api/table` query parameters:**

| Param | Default | Description |
|---|---|---|
| `entity` | `Author` | One of: `Author`, `Venue`, `Publication`, `Year`, `2020s`, `2010s`, `2000s`, `Pre2000s` |
| `sort_by` | `Publication` | SPARQL variable name to sort by |
| `order` | `DESC` | `ASC` or `DESC` |
| `page` | `1` | 1-based page number |
| `limit` | `50` | Results per page |
| `filter_<key>` | — | Any param prefixed `filter_` becomes a SPARQL `FILTER(CONTAINS(...))` clause |

### Admin endpoints

All admin endpoints require `Authorization: Bearer <token>` where the token is a valid GitLab OAuth2 access token for a member of the admin group.

#### GET /api/admin/patches

Returns all saved patch files with audit metadata.

```json
{
  "patches": [
    {
      "filename": "2024-01-15T10-30-00Z_sigir-2023.nt",
      "timestamp": "2024-01-15T10:30:00+00:00",
      "user_name": "Jane Doe",
      "user_email": "jane@example.com",
      "action": "import",
      "details": { "type": "conference", "iri": "https://dblp.org/...", "year": 2023 },
      "triples": 4521,
      "live_applied": true
    }
  ]
}
```

#### POST /api/admin/import

Fetches data from DBLP and applies it to the live triplestore.

```json
{ "iri": "https://dblp.org/db/conf/sigir", "type": "conference", "year": 2023 }
```

`type` must be one of: `journal`, `conference`, `workshop`, `person`, `publication`. `year` is optional (ignored for `person` and `publication`).

Response: `{ "filename": "...", "triples": 4521, "live_applied": true }`

`live_applied` is `false` if the SPARQL INSERT failed (the patch file is still saved). Returns 404 if DBLP returns no triples.

#### POST /api/admin/workshop/custom/preview

Searches DBLP for proceedings matching the given title/abbreviation and returns candidates without writing anything.

```json
{ "abbreviation": "DESIRES", "title": "Designing Information Retrieval Evaluation Studies", "year": 2021 }
```

Response: `{ "proceedings": [{ "proc": "https://dblp.org/...", "title": "...", "year": "2021" }] }`

#### POST /api/admin/workshop/custom

Creates a custom workshop stream from a specific set of proceedings IRIs (obtained from the preview endpoint).

```json
{
  "abbreviation": "DESIRES",
  "title": "Designing Information Retrieval Evaluation Studies",
  "year": 2021,
  "proc_iris": ["https://dblp.org/rec/conf/desires/2021"]
}
```

Response: `{ "filename": "...", "triples": 312, "live_applied": true }`

Creates a synthetic stream at `https://ir.webis.de/anthology/venues/workshops+<abbreviation_lower>`, links the provided proceedings to it, and fetches all papers, authors, and signatures from DBLP.

## SPARQL query patterns

### Read queries

All reads use `main.py`'s `sparql_post` helper:

```python
await client.post(
    SPARQL_ENDPOINT,
    headers={"Content-Type": "application/sparql-query", "Accept": "application/sparql-results+json"},
    content=query,
)
```

**Key vocabulary:**
- `dblp:publishedInStream` — links a publication to its venue stream
- `dblp:bibtexType` — `bibtex:Proceedings`, `bibtex:Inproceedings`, `bibtex:Article`
- `ex:yearOfConference` — custom triple injected at import time (conference year can differ from publication year); queries use `COALESCE(?eventYear, ?pubYear)` to prefer it over `dblp:yearOfPublication`
- `dblp:hasSignature` → `dblp:signatureOrdinal` + `dblp:signatureDblpName` — used for ordered author lists

**Author ordering:** a `GROUP_CONCAT` packs all authors into a single string with `"<ordinal>@@<name>"` entries (comma-separated). `bibtex.py`'s `decode_ordered()` unpacks and re-sorts by ordinal. The same encoding is used for `authorIds`.

**`/api/table` filter injection:** `filter_<key>=value` query params become `FILTER(CONTAINS(LCASE(?label), LCASE("value")))` SPARQL clauses. Multiple values for the same key are OR-ed; multiple keys are AND-ed. The combined string is interpolated into `$FILTERS` in `TABLE_QUERY_TEMPLATE`.

### Write queries

`sparql_update` POSTs with `Content-Type: application/sparql-update`. `patches.nt_to_sparql_insert()` wraps raw N-Triples lines in `INSERT DATA { ... }`. If `SPARQL_ACCESS_TOKEN` is set, it is appended as `?access-token=<token>` to the endpoint URL.

## Authentication

No session, no JWT. Every request to an admin endpoint makes a live call to GitLab:

1. Bearer token extracted from `Authorization` header
2. `GET https://git.webis.de/oauth/userinfo` called with that token
3. Non-200 response → HTTP 401 "Invalid or expired token"
4. `groups` array in the response does not contain `auth/auth-webis-admin` → HTTP 403
5. Full userinfo dict (with `name`, `email`) returned to the handler for audit logging

## Patch files

Each import writes two files to `DATA_PATH/patches/`:

- `<timestamp>_<label>.nt` — raw N-Triples, applied to the live triplestore via `INSERT DATA`
- `<timestamp>_<label>.meta.json` — audit sidecar: timestamp, user name/email, action type, input parameters, triple count, and whether the live apply succeeded

`patches.list_patches()` drives the list from `.nt` files and merges in the sidecar when present. Patches created before the audit sidecar feature was added appear without metadata fields (all are optional).

## DBLP import

`dblp_fetch.py` runs paginated SPARQL CONSTRUCT queries against `sparql.dblp.org` in pages of 100,000 triples until an empty page is returned. After each fetch:

- `_dedup()` removes duplicate N-Triples lines
- `_extract_year_of_conference()` scans proceedings title triples with a regex and injects `ex:yearOfConference` triples (e.g. a title containing "2023" produces `<proc_iri> ex:yearOfConference "2023" .`)

For `person` imports, the backend first queries its own triplestore for all known stream IRIs and uses them to filter the DBLP import to IR-relevant publications only.

## BibTeX generation

`bibtex.py` generates a BibTeX entry string for each publication requested via `/api/publications/{id}`. The entry type (`@inproceedings`, `@proceedings`, `@article`) is determined by `dblp:bibtexType`. The citation key is derived from first-author last name + year + first non-stopword title word. Unicode characters are escaped to LaTeX sequences using `BIBTEX_CHAR_MAP`. Trailing dots are stripped from `title` and `booktitle` fields.
