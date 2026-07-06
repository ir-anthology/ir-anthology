# IR Anthology — Database

QLever SPARQL triplestore seeded with a curated subset of the DBLP knowledge graph, covering Information Retrieval journals, conferences, and workshops. Data is fetched from the public DBLP SPARQL endpoint at build time and indexed locally.

## Tech stack

| Concern | Tool |
|---|---|
| SPARQL engine | QLever (`adfreiburg/qlever`) |
| Port | 7016 |
| Index format | N-Triples (`.nt`) |
| Data source | `sparql.dblp.org` — paginated CONSTRUCT queries |
| Index name prefix | `data/test` |
| CLI tooling | `qlever` (from `packages.qlever.dev`) |

## Project structure

```
database/
├── Dockerfile                          adfreiburg/qlever base; entrypoint: run_qlever.sh; port 7016
├── Qleverfile                          qlever CLI configuration (port, memory, access token, …)
├── run_qlever.sh                       Docker entrypoint: index + start, or re-fetch data
├── get_data.sh                         data fetch script: paginates DBLP, writes chunks to DATA_PATH
├── streams.txt                         37 DBLP stream URIs (journals + conferences)
├── workshop_streams.txt                44 DBLP workshop stream URIs
├── add_publications_from_stream.rq     CONSTRUCT: all publications in a stream
├── add_authors_from_stream.rq          CONSTRUCT: all creator nodes referenced by a stream
├── add_editors_from_stream.rq          CONSTRUCT: all editor nodes referenced by a stream
├── add_signatures_from_stream.rq       CONSTRUCT: all signature nodes (ordered author links)
├── add_stream.rq                       CONSTRUCT: stream node triples (label, type, …)
├── add_workshop_stream.rq              CONSTRUCT: stream node triples + injects rdf:type ex:Workshop
├── get_proceedings_titles_from_stream.rq  CONSTRUCT: proceedings titles (used to extract conference year)
└── data/                               index files and fetched chunks (not committed)
    ├── chunks/                         raw .nt files produced by get_data.sh
    └── patches/                        .nt patch files applied by the backend admin panel
```

## Configuration

### Qleverfile (local dev)

The `Qleverfile` in this directory drives the `qlever` CLI:

| Section | Key | Value |
|---|---|---|
| `[data]` | `NAME` | `data/test` (index file prefix) |
| `[data]` | `GET_DATA_CMD` | `./get_data.sh` |
| `[server]` | `PORT` | `7016` |
| `[server]` | `ACCESS_TOKEN` | `1234` (dev default — set `SPARQL_ACCESS_TOKEN=1234` in env) |
| `[server]` | `MEMORY_FOR_QUERIES` | `10G` |
| `[server]` | `CACHE_MAX_SIZE` | `5G` |
| `[server]` | `TIMEOUT` | `30s` |
| `[runtime]` | `SYSTEM` | `native` (uses the locally installed `qlever-server` binary) |

### Environment variables

| Variable | Purpose |
|---|---|
| `SPARQL_ACCESS_TOKEN` | Required by the server for write operations. Set to `1234` locally (matches `ACCESS_TOKEN` in Qleverfile). Set to a secret value in production. |
| `DATA_PATH` | Directory for chunks and patches. Defaults to `./data` locally; Docker bakes in `/app/data`. |

## Commands

All commands must be run from the `database/` directory so the `Qleverfile` is discovered automatically.

```sh
# Install the qlever CLI (done automatically in the devcontainer via PostCreate.sh)
pip install qlever   # or: apt install qlever (packages.qlever.dev)

# First time — fetch data from sparql.dblp.org and build the index:
qlever get-data     # runs get_data.sh; writes chunks to data/chunks/ (~15 min)
qlever index        # builds the QLever index from data/**/*.nt

# Every time — start the server on localhost:7016:
qlever start        # uses Qleverfile settings

# Other useful commands:
qlever stop         # stop the running server
qlever status       # check if the server is running
qlever log          # tail the server log
```

```sh
# Docker
docker build -t ir-anthology-database .
docker run -p 7016:7016 \
  -e SPARQL_ACCESS_TOKEN=your_secret \
  ir-anthology-database
```

The Docker entrypoint (`run_qlever.sh`) re-indexes from the baked-in data on every start. Pass `true` as the first argument to re-fetch from DBLP instead:

```sh
docker run -p 7016:7016 ir-anthology-database true   # re-fetches from DBLP
```

## Data fetch pipeline

`get_data.sh` runs when `qlever get-data` is called. It:

1. Reads every stream URI from `streams.txt` (37 streams) and `workshop_streams.txt` (44 streams)
2. For each stream, runs six SPARQL CONSTRUCT queries against `https://sparql.dblp.org/sparql`:

| Query template | What it fetches |
|---|---|
| `add_publications_from_stream.rq` | All publication nodes (`?pub dblp:publishedInStream <stream>`) |
| `add_authors_from_stream.rq` | All `dblp:Creator` nodes referenced as authors |
| `add_editors_from_stream.rq` | All `dblp:Creator` nodes referenced as editors |
| `add_signatures_from_stream.rq` | All `dblp:Signature` nodes (ordered author↔publication links) |
| `add_stream.rq` | The stream node itself (label, type, homepage, …) |
| `add_workshop_stream.rq` | Same as above, plus injects `rdf:type ex:Workshop` |

3. For each stream, also fetches proceedings titles and extracts a `ex:yearOfConference` triple from the title string using a regex (e.g. a title containing "2023" → `<proc> ex:yearOfConference "2023" .`). This is needed because the DBLP `yearOfPublication` for proceedings can differ from the actual conference year.

4. Each query is paginated: pages of 100,000 triples are fetched until an empty page is returned. Output files land in `DATA_PATH/chunks/`.

5. Outputs a final triple count.

## SPARQL query templates

Each `.rq` file uses two placeholders substituted by `get_data.sh` with `sed`:

| Placeholder | Substituted with |
|---|---|
| `__STREAM__` | The full DBLP stream URI (e.g. `https://dblp.org/streams/conf/sigir`) |
| `__LIMIT__` | `100000` |
| `__OFFSET__` | Current pagination offset (0, 100000, 200000, …) |

**Workshop streams** use `add_workshop_stream.rq` instead of `add_stream.rq`. The only difference is that `add_workshop_stream.rq` also injects `<stream> rdf:type ex:Workshop .` so the backend can distinguish workshops from conferences and journals.

## RDF vocabulary

The triplestore uses the DBLP vocabulary plus a small IR Anthology extension:

| Prefix | IRI | Used for |
|---|---|---|
| `dblp:` | `https://dblp.org/rdf/schema#` | Publication, creator, stream, signature properties |
| `bibtex:` | `http://purl.org/net/nknouf/ns/bibtex#` | `bibtex:Article`, `bibtex:Inproceedings`, `bibtex:Proceedings` entry types |
| `ex:` | `https://ir.webis.de/kg#` | `ex:Workshop` type, `ex:yearOfConference` |

Key properties used by the backend:

| Property | Meaning |
|---|---|
| `dblp:publishedInStream` | Links a publication to its venue stream |
| `dblp:bibtexType` | Entry type (`bibtex:Article`, etc.) |
| `dblp:yearOfPublication` | Publication year (from DBLP) |
| `ex:yearOfConference` | Actual conference year (injected at import; preferred over `yearOfPublication`) |
| `dblp:hasSignature` | Links a publication to a `dblp:Signature` node |
| `dblp:signatureOrdinal` | Author order within a publication |
| `dblp:signatureDblpName` | Author display name at time of publication |
| `ex:Workshop` | Stream type for workshop venues |

## Covered streams

### Journals (12)

FTIR, IJIRR, IJMIR, IPM, IR Journal, JASIST, SIGIR Forum, TISMIR, TIST, TOIS, TWEB, WWW Journal

### Conferences (25)

ADCS, AIRS, CCIR, CERI/CORIA, CHIIR, CIKM, CIVR, CLEF, DESIRES, ECIR, FDIA, FIRE, HCIR, ICTIR, IRFC, ISMIR, IIIX, MIR, NTCIR, RIAO, SIGIR, SPIRE, TREC, WSDM, WWW

### Workshops (44)

IR-adjacent workshops co-located with the conferences above. The full list is in `workshop_streams.txt`. New workshops can be added either by appending a DBLP stream URI to that file (for recurring workshops) or via the backend admin panel's custom workshop import (for one-off proceedings).

## Adding or updating streams

**To add a recurring venue:** append its DBLP stream URI to `streams.txt` (conference/journal) or `workshop_streams.txt` (workshop), then re-run `qlever get-data && qlever index`.

**To add a one-off workshop or individual proceedings:** use the backend admin panel (`POST /api/admin/workshop/custom`). This creates a patch file in `data/patches/` and applies it to the live database without a full re-index. The patch is automatically included in the next full re-index.

**To update an existing stream** (e.g. after new papers appear in DBLP): re-run `qlever get-data && qlever index`. The full dataset is re-fetched and re-indexed from scratch.
