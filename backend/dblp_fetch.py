import re
import httpx
from fastapi import HTTPException

DBLP_ENDPOINT = "https://sparql.dblp.org/sparql"
_PAGE = 100_000

_YEAR_RE = re.compile(r'[12][0-9]{3}')
_YEAR_IN_TITLE = re.compile(r'^(<[^>]+>) <[^>]+> ".*?([12][0-9]{3})[^"]*"')


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

async def _construct(client: httpx.AsyncClient, query: str) -> str:
    print(query)
    resp = await client.post(
        DBLP_ENDPOINT,
        data={"query": query},
        headers={"Accept": "application/n-triples"},
    )
    if not resp.is_success:
        raise HTTPException(502, f"DBLP CONSTRUCT failed ({resp.status_code}): {resp.text[:300]}")
    print("resp_text: " + resp.text.strip()+"\n END")
    return resp.text.strip()


async def _select(client: httpx.AsyncClient, query: str) -> list[dict]:
    resp = await client.post(
        DBLP_ENDPOINT,
        data={"query": query},
        headers={"Accept": "application/sparql-results+json"},
    )
    if not resp.is_success:
        raise HTTPException(502, f"DBLP SELECT failed ({resp.status_code}): {resp.text[:300]}")
    return resp.json()["results"]["bindings"]


async def _paginate(client: httpx.AsyncClient, query_fn) -> str:
    """Run query_fn(limit, offset) until the result is empty, concatenating N-Triples."""
    chunks: list[str] = []
    offset = 0
    while True:
        chunk = await _construct(client, query_fn(_PAGE, offset))
        if not chunk:
            break
        chunks.append(chunk)
        offset += _PAGE
    return "\n".join(chunks)


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------

def _vals(iris: list[str]) -> str:
    return " ".join(f"<{iri}>\n" for iri in iris)


def _extract_year_of_conference(nt: str) -> str:
    """Derive yearOfConference triples from proceedings title N-Triples (mirrors the bash sed)."""
    lines: list[str] = []
    for line in nt.splitlines():
        m = _YEAR_IN_TITLE.match(line)
        if m:
            lines.append(
                f'{m.group(1)} <https://ir.webis.de/kg#yearOfConference> "{m.group(2)}" .'
            )
    return "\n".join(lines)


def _dedup(nt: str) -> str:
    seen: set[str] = set()
    out: list[str] = []
    for line in nt.splitlines():
        s = line.strip()
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return "\n".join(sorted(out))


# ---------------------------------------------------------------------------
# Full-stream query builders (no year filter)
# ---------------------------------------------------------------------------

def _q_stream(stream: str, is_workshop: bool, limit: int, offset: int) -> str:
    if is_workshop:
        return f"""PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX ex: <https://ir.webis.de/kg#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
CONSTRUCT {{ ?stream ?p ?o }}
WHERE {{
  {{ VALUES ?stream {{ <{stream}> }} ?stream ?p ?o . }}
  UNION
  {{ VALUES (?stream ?p ?o) {{ (<{stream}> rdf:type ex:Workshop) }} }}
}}
ORDER BY ?stream ?p ?o
LIMIT {limit} OFFSET {offset}"""
    return f"""PREFIX dblp: <https://dblp.org/rdf/schema#>
CONSTRUCT {{ ?stream ?p ?o }}
WHERE {{
  VALUES ?stream {{ <{stream}> }}
  ?stream ?p ?o .
}}
ORDER BY ?stream ?p ?o
LIMIT {limit} OFFSET {offset}"""


def _q_stream_publications(stream: str, limit: int, offset: int) -> str:
    return f"""PREFIX dblp: <https://dblp.org/rdf/schema#>
CONSTRUCT {{ ?pub ?p ?o }}
WHERE {{
  {{ SELECT DISTINCT ?pub WHERE {{ ?pub dblp:publishedInStream <{stream}> . }} }}
  ?pub ?p ?o .
}}
ORDER BY ?pub ?p ?o
LIMIT {limit} OFFSET {offset}"""


def _q_stream_authors(stream: str, limit: int, offset: int) -> str:
    return f"""PREFIX dblp: <https://dblp.org/rdf/schema#>
CONSTRUCT {{ ?author ?p ?o }}
WHERE {{
  {{ SELECT DISTINCT ?author WHERE {{
      ?pub dblp:publishedInStream <{stream}> ;
           dblp:authoredBy ?author .
  }} }}
  ?author ?p ?o .
}}
ORDER BY ?author ?p ?o
LIMIT {limit} OFFSET {offset}"""


def _q_stream_editors(stream: str, limit: int, offset: int) -> str:
    return f"""PREFIX dblp: <https://dblp.org/rdf/schema#>
CONSTRUCT {{ ?editor ?p ?o }}
WHERE {{
  {{ SELECT DISTINCT ?editor WHERE {{
      ?pub dblp:publishedInStream <{stream}> ;
           dblp:editedBy ?editor .
  }} }}
  ?editor ?p ?o .
}}
ORDER BY ?editor ?p ?o
LIMIT {limit} OFFSET {offset}"""


def _q_stream_signatures(stream: str, limit: int, offset: int) -> str:
    return f"""PREFIX dblp: <https://dblp.org/rdf/schema#>
CONSTRUCT {{ ?sig ?p ?o }}
WHERE {{
  {{ SELECT DISTINCT ?sig WHERE {{
      ?pub dblp:publishedInStream <{stream}> ;
           dblp:hasSignature ?sig .
  }} }}
  ?sig ?p ?o .
}}
ORDER BY ?sig ?p ?o
LIMIT {limit} OFFSET {offset}"""


def _q_stream_proceedings_titles(stream: str, limit: int, offset: int) -> str:
    return f"""PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
CONSTRUCT {{ ?pub dblp:title ?title }}
WHERE {{
  {{ SELECT DISTINCT ?pub WHERE {{
      ?pub dblp:publishedInStream <{stream}> ;
           dblp:bibtexType bibtex:Proceedings .
  }} }}
  ?pub dblp:title ?title .
}}
ORDER BY ?pub ?title
LIMIT {limit} OFFSET {offset}"""


# ---------------------------------------------------------------------------
# Conference/workshop year query builders
# ---------------------------------------------------------------------------

def _q_conf_proceedings(proc_iris: list[str], limit: int, offset: int) -> str:
    vals = _vals(proc_iris)
    return f"""PREFIX dblp: <https://dblp.org/rdf/schema#>
CONSTRUCT {{ ?proc ?p ?o }}
WHERE {{
  VALUES ?proc {{ {vals} }}
  ?proc ?p ?o .
}}
ORDER BY ?proc ?p ?o
LIMIT {limit} OFFSET {offset}"""


def _q_conf_papers(proc_iris: list[str], limit: int, offset: int) -> str:
    vals = _vals(proc_iris)
    return f"""PREFIX dblp: <https://dblp.org/rdf/schema#>
CONSTRUCT {{ ?pub ?p ?o }}
WHERE {{
  {{ SELECT DISTINCT ?pub WHERE {{
      VALUES ?proc {{ {vals} }}
      ?pub dblp:publishedAsPartOf ?proc .
  }} }}
  ?pub ?p ?o .
}}
ORDER BY ?pub ?p ?o
LIMIT {limit} OFFSET {offset}"""


def _q_conf_authors(proc_iris: list[str], limit: int, offset: int) -> str:
    vals = _vals(proc_iris)
    return f"""PREFIX dblp: <https://dblp.org/rdf/schema#>
CONSTRUCT {{ ?author ?p ?o }}
WHERE {{
  {{ SELECT DISTINCT ?author WHERE {{
      VALUES ?proc {{ {vals} }}
      ?pub dblp:publishedAsPartOf ?proc ;
           dblp:authoredBy ?author .
  }} }}
  ?author ?p ?o .
}}
ORDER BY ?author ?p ?o
LIMIT {limit} OFFSET {offset}"""


def _q_conf_editors(proc_iris: list[str], limit: int, offset: int) -> str:
    vals = _vals(proc_iris)
    return f"""PREFIX dblp: <https://dblp.org/rdf/schema#>
CONSTRUCT {{ ?editor ?p ?o }}
WHERE {{
  {{ SELECT DISTINCT ?editor WHERE {{
      VALUES ?proc {{ {vals} }}
      ?proc dblp:editedBy ?editor .
  }} }}
  ?editor ?p ?o .
}}
ORDER BY ?editor ?p ?o
LIMIT {limit} OFFSET {offset}"""


def _q_conf_signatures(proc_iris: list[str], limit: int, offset: int) -> str:
    vals = _vals(proc_iris)
    return f"""PREFIX dblp: <https://dblp.org/rdf/schema#>
CONSTRUCT {{ ?sig ?p ?o }}
WHERE {{
  {{ SELECT DISTINCT ?sig WHERE {{
      VALUES ?proc {{ {vals} }}
      ?pub dblp:publishedAsPartOf ?proc ;
           dblp:hasSignature ?sig .
  }} }}
  ?sig ?p ?o .
}}
ORDER BY ?sig ?p ?o
LIMIT {limit} OFFSET {offset}"""


# ---------------------------------------------------------------------------
# Journal year query builders
# ---------------------------------------------------------------------------

def _q_journal_articles(stream: str, year: int, limit: int, offset: int) -> str:
    return f"""PREFIX dblp: <https://dblp.org/rdf/schema#>
CONSTRUCT {{ ?pub ?p ?o }}
WHERE {{
  {{ SELECT DISTINCT ?pub WHERE {{
      ?pub dblp:publishedInStream <{stream}> ;
           dblp:yearOfPublication ?py .
      FILTER(STR(?py) = "{year}")
  }} }}
  ?pub ?p ?o .
}}
ORDER BY ?pub ?p ?o
LIMIT {limit} OFFSET {offset}"""


def _q_journal_authors(stream: str, year: int, limit: int, offset: int) -> str:
    return f"""PREFIX dblp: <https://dblp.org/rdf/schema#>
CONSTRUCT {{ ?author ?p ?o }}
WHERE {{
  {{ SELECT DISTINCT ?author WHERE {{
      ?pub dblp:publishedInStream <{stream}> ;
           dblp:yearOfPublication ?py ;
           dblp:authoredBy ?author .
      FILTER(STR(?py) = "{year}")
  }} }}
  ?author ?p ?o .
}}
ORDER BY ?author ?p ?o
LIMIT {limit} OFFSET {offset}"""


def _q_journal_editors(stream: str, year: int, limit: int, offset: int) -> str:
    return f"""PREFIX dblp: <https://dblp.org/rdf/schema#>
CONSTRUCT {{ ?editor ?p ?o }}
WHERE {{
  {{ SELECT DISTINCT ?editor WHERE {{
      ?pub dblp:publishedInStream <{stream}> ;
           dblp:yearOfPublication ?py ;
           dblp:editedBy ?editor .
      FILTER(STR(?py) = "{year}")
  }} }}
  ?editor ?p ?o .
}}
ORDER BY ?editor ?p ?o
LIMIT {limit} OFFSET {offset}"""


def _q_journal_signatures(stream: str, year: int, limit: int, offset: int) -> str:
    return f"""PREFIX dblp: <https://dblp.org/rdf/schema#>
CONSTRUCT {{ ?sig ?p ?o }}
WHERE {{
  {{ SELECT DISTINCT ?sig WHERE {{
      ?pub dblp:publishedInStream <{stream}> ;
           dblp:yearOfPublication ?py ;
           dblp:hasSignature ?sig .
      FILTER(STR(?py) = "{year}")
  }} }}
  ?sig ?p ?o .
}}
ORDER BY ?sig ?p ?o
LIMIT {limit} OFFSET {offset}"""


# ---------------------------------------------------------------------------
# Person query builders
# ---------------------------------------------------------------------------

def _q_person_publications(person: str, stream_vals: str, limit: int, offset: int) -> str:
    return f"""PREFIX dblp: <https://dblp.org/rdf/schema#>
CONSTRUCT {{ ?pub ?p ?o }}
WHERE {{
  {{ SELECT DISTINCT ?pub WHERE {{
      VALUES ?stream {{ {stream_vals} }}
      ?pub dblp:publishedInStream ?stream .
      {{ ?pub dblp:authoredBy <{person}> }} UNION {{ ?pub dblp:editedBy <{person}> }}
  }} }}
  ?pub ?p ?o .
}}
ORDER BY ?pub ?p ?o
LIMIT {limit} OFFSET {offset}"""


def _q_person_authors(person: str, stream_vals: str, limit: int, offset: int) -> str:
    return f"""PREFIX dblp: <https://dblp.org/rdf/schema#>
CONSTRUCT {{ ?author ?p ?o }}
WHERE {{
  {{ SELECT DISTINCT ?author WHERE {{
      VALUES ?stream {{ {stream_vals} }}
      ?pub dblp:publishedInStream ?stream ;
           dblp:authoredBy ?author .
      {{ ?pub dblp:authoredBy <{person}> }} UNION {{ ?pub dblp:editedBy <{person}> }}
  }} }}
  ?author ?p ?o .
}}
ORDER BY ?author ?p ?o
LIMIT {limit} OFFSET {offset}"""


def _q_person_editors(person: str, stream_vals: str, limit: int, offset: int) -> str:
    return f"""PREFIX dblp: <https://dblp.org/rdf/schema#>
CONSTRUCT {{ ?editor ?p ?o }}
WHERE {{
  {{ SELECT DISTINCT ?editor WHERE {{
      VALUES ?stream {{ {stream_vals} }}
      ?pub dblp:publishedInStream ?stream ;
           dblp:editedBy ?editor .
      {{ ?pub dblp:authoredBy <{person}> }} UNION {{ ?pub dblp:editedBy <{person}> }}
  }} }}
  ?editor ?p ?o .
}}
ORDER BY ?editor ?p ?o
LIMIT {limit} OFFSET {offset}"""


def _q_person_signatures(person: str, stream_vals: str, limit: int, offset: int) -> str:
    return f"""PREFIX dblp: <https://dblp.org/rdf/schema#>
CONSTRUCT {{ ?sig ?p ?o }}
WHERE {{
  {{ SELECT DISTINCT ?sig WHERE {{
      VALUES ?stream {{ {stream_vals} }}
      ?pub dblp:publishedInStream ?stream ;
           dblp:hasSignature ?sig .
      {{ ?pub dblp:authoredBy <{person}> }} UNION {{ ?pub dblp:editedBy <{person}> }}
  }} }}
  ?sig ?p ?o .
}}
ORDER BY ?sig ?p ?o
LIMIT {limit} OFFSET {offset}"""


# ---------------------------------------------------------------------------
# Publication query builders
# ---------------------------------------------------------------------------

def _q_pub_authors(pub: str, limit: int, offset: int) -> str:
    return f"""PREFIX dblp: <https://dblp.org/rdf/schema#>
CONSTRUCT {{ ?author ?p ?o }}
WHERE {{
  {{ SELECT DISTINCT ?author WHERE {{ <{pub}> dblp:authoredBy ?author . }} }}
  ?author ?p ?o .
}}
ORDER BY ?author ?p ?o
LIMIT {limit} OFFSET {offset}"""


def _q_pub_editors(pub: str, limit: int, offset: int) -> str:
    return f"""PREFIX dblp: <https://dblp.org/rdf/schema#>
CONSTRUCT {{ ?editor ?p ?o }}
WHERE {{
  {{ SELECT DISTINCT ?editor WHERE {{ <{pub}> dblp:editedBy ?editor . }} }}
  ?editor ?p ?o .
}}
ORDER BY ?editor ?p ?o
LIMIT {limit} OFFSET {offset}"""


def _q_pub_signatures(pub: str, limit: int, offset: int) -> str:
    return f"""PREFIX dblp: <https://dblp.org/rdf/schema#>
CONSTRUCT {{ ?sig ?p ?o }}
WHERE {{
  {{ SELECT DISTINCT ?sig WHERE {{ <{pub}> dblp:hasSignature ?sig . }} }}
  ?sig ?p ?o .
}}
ORDER BY ?sig ?p ?o
LIMIT {limit} OFFSET {offset}"""


def _q_entity(iri: str, limit: int, offset: int) -> str:
    return f"""PREFIX dblp: <https://dblp.org/rdf/schema#>
CONSTRUCT {{ ?s ?p ?o }}
WHERE {{
  VALUES ?s {{ <{iri}> }}
  ?s ?p ?o .
}}
ORDER BY ?s ?p ?o
LIMIT {limit} OFFSET {offset}"""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _find_year_proceedings(
    client: httpx.AsyncClient, stream_iri: str, year: int
) -> list[str]:
    """SELECT all proceedings of the stream; return those whose title contains `year`."""
    query = f"""PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
SELECT ?proc ?title WHERE {{
  ?proc dblp:publishedInStream <{stream_iri}> ;
        dblp:bibtexType bibtex:Proceedings ;
        dblp:title ?title .
}}"""
    bindings = await _select(client, query)
    result: list[str] = []
    for b in bindings:
        title = b["title"]["value"]
        m = _YEAR_RE.search(title)
        if m and m.group(0) == str(year):
            result.append(b["proc"]["value"])
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def fetch_stream(
    client: httpx.AsyncClient,
    stream_iri: str,
    year: int | None = None,
    is_workshop: bool = False,
) -> str:
    stream_nt = await _paginate(client, lambda l, o: _q_stream(stream_iri, is_workshop, l, o))

    if year is None:
        # Full stream — mirrors the database load exactly
        pub_nt    = await _paginate(client, lambda l, o: _q_stream_publications(stream_iri, l, o))
        author_nt = await _paginate(client, lambda l, o: _q_stream_authors(stream_iri, l, o))
        editor_nt = await _paginate(client, lambda l, o: _q_stream_editors(stream_iri, l, o))
        sig_nt    = await _paginate(client, lambda l, o: _q_stream_signatures(stream_iri, l, o))
        proc_nt   = await _paginate(client, lambda l, o: _q_stream_proceedings_titles(stream_iri, l, o))
        yoc = _extract_year_of_conference(proc_nt)
        parts = [stream_nt, pub_nt, author_nt, editor_nt, sig_nt, yoc]

    else:
        # Year-filtered: detect conference (has proceedings) vs journal
        procs = await _find_year_proceedings(client, stream_iri, year)

        if procs:
            # Conference / workshop: fetch via proceedings → publishedAsPartOf
            proc_nt   = await _paginate(client, lambda l, o: _q_conf_proceedings(procs, l, o))
            paper_nt  = await _paginate(client, lambda l, o: _q_conf_papers(procs, l, o))
            author_nt = await _paginate(client, lambda l, o: _q_conf_authors(procs, l, o))
            editor_nt = await _paginate(client, lambda l, o: _q_conf_editors(procs, l, o))
            sig_nt    = await _paginate(client, lambda l, o: _q_conf_signatures(procs, l, o))
            # Generate yearOfConference triples directly from the found proceedings
            yoc = "\n".join(
                f"<{p}> <https://ir.webis.de/kg#yearOfConference> \"{year}\" ."
                for p in procs
            )
            parts = [stream_nt, proc_nt, paper_nt, author_nt, editor_nt, sig_nt, yoc]

        else:
            # Journal: filter articles by yearOfPublication
            pub_nt    = await _paginate(client, lambda l, o: _q_journal_articles(stream_iri, year, l, o))
            author_nt = await _paginate(client, lambda l, o: _q_journal_authors(stream_iri, year, l, o))
            editor_nt = await _paginate(client, lambda l, o: _q_journal_editors(stream_iri, year, l, o))
            sig_nt    = await _paginate(client, lambda l, o: _q_journal_signatures(stream_iri, year, l, o))
            parts = [stream_nt, pub_nt, author_nt, editor_nt, sig_nt]

    return _dedup("\n".join(p for p in parts if p))


async def fetch_person(
    client: httpx.AsyncClient,
    person_iri: str,
    known_streams: list[str] | None = None,
) -> str:
    person_nt = await _paginate(client, lambda l, o: _q_entity(person_iri, l, o))
    parts = [person_nt]

    if known_streams:
        sv = _vals(known_streams)
        pub_nt    = await _paginate(client, lambda l, o: _q_person_publications(person_iri, sv, l, o))
        author_nt = await _paginate(client, lambda l, o: _q_person_authors(person_iri, sv, l, o))
        editor_nt = await _paginate(client, lambda l, o: _q_person_editors(person_iri, sv, l, o))
        sig_nt    = await _paginate(client, lambda l, o: _q_person_signatures(person_iri, sv, l, o))
        parts += [pub_nt, author_nt, editor_nt, sig_nt]
    return _dedup("\n".join(p for p in parts if p))


async def fetch_publication(client: httpx.AsyncClient, pub_iri: str) -> str:
    pub_nt    = await _paginate(client, lambda l, o: _q_entity(pub_iri, l, o))
    author_nt = await _paginate(client, lambda l, o: _q_pub_authors(pub_iri, l, o))
    editor_nt = await _paginate(client, lambda l, o: _q_pub_editors(pub_iri, l, o))
    sig_nt    = await _paginate(client, lambda l, o: _q_pub_signatures(pub_iri, l, o))
    return _dedup("\n".join(p for p in [pub_nt, author_nt, editor_nt, sig_nt] if p))
