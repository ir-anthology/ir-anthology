from fastapi import FastAPI, HTTPException, Query, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated
from pydantic import BaseModel
import sparqlTemplates
import bibtex as bibtex_helper
import auth_utils
import patches as patch_store
import dblp_fetch
import httpx
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

SPARQL_ENDPOINT = "https://database-ir-anthology.srv.webis.de/"
SPARQL_ACCESS_TOKEN = os.environ.get("SPARQL_ACCESS_TOKEN", "")

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.client = httpx.AsyncClient(timeout=60.0)
    yield
    await app.state.client.aclose()

def get_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.client

def get_uri_from_id(ir_id: str):
    return "https://dblp.org/" + ir_id.replace("+", "/")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"https://.*\.webis\.de|http://localhost(:\d+)?",
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

WORKSHOPS_VENUE_URI = "https://dblp.org/workshops"

YEAR_SEED_VARS = {"Author": "?author_URI", "Venue": "?stream_URI"}

def build_year_seed(entity: str, bindings: list) -> str | None:
    """Build the $SEED clause for the *_YEAR_COUNTS templates from the URIs of one result page.

    The seed restricts the per-year aggregation to the entities on the current page.
    It must target a raw triple-pattern variable (see YEAR_SEED_VARS) — a VALUES on
    the BIND-computed ?entity_URI is not pushed down by the SPARQL engine, which
    would force aggregation over all ~100k entities (seconds instead of ~0.2s).

    Venue is special: the "Workshops" row uses the synthetic WORKSHOPS_VENUE_URI,
    which matches no triple. It is expressed as a UNION branch matching all
    ex:Workshop streams instead; the query body then collapses those back onto the
    synthetic URI. Returns None if the page contains no seedable URIs.
    """
    uris = [b["URI"]["value"] for b in bindings if b.get("URI", {}).get("type") == "uri"]
    if len(uris) == 0:
        return None
    if entity == "Venue":
        streams = [u for u in uris if u != WORKSHOPS_VENUE_URI]
        clauses = []
        if streams:
            values = " ".join(f"<{u}>" for u in streams)
            clauses.append(f"{{ VALUES ?stream_URI {{ {values} }} }}")
        if WORKSHOPS_VENUE_URI in uris:
            clauses.append("{ ?stream_URI a ex:Workshop . }")
        return " UNION ".join(clauses)
    values = " ".join(f"<{u}>" for u in uris)
    return f"VALUES {YEAR_SEED_VARS[entity]} {{ {values} }}"

class TableParams(BaseModel):
    sort_by: str | None = "Publication"
    order: str | None = "DESC"
    page: int | None = 1
    limit: int | None = 50

async def _run_table_page(template: str, params: TableParams, request: Request, client: httpx.AsyncClient, allowed_sorts: set[str], default_sort: str = "Publication") -> tuple[list, list, str]:
    """Run one page query of a per-entity table template; returns (vars, bindings, filters).

    allowed_sorts must list the variables the template projects; unknown sort_by values
    fall back to the default sort instead of producing an invalid SPARQL query.
    """
    extra = {
        k: v for k, v in request.query_params.items()
        if k not in params.model_dump().keys()
    }
    filters = build_filters(extra)
    query = (template
             .replace('$FILTERS', filters)
             .replace('$ORDER', parse_order(params.sort_by, params.order, allowed_sorts, default_sort))
             .replace('$LIMIT', str(params.limit))
             .replace('$OFFSET', str((params.page - 1) * params.limit)))
    data = await sparql_post(query, client)
    return data["head"]["vars"], data["results"]["bindings"], filters

async def _merge_year_counts(entity: str, years_template: str, filters: str, bindings: list, client: httpx.AsyncClient):
    """Merge a ?Years binding into each page row via a seeded per-year count query (see build_year_seed)."""
    seed = build_year_seed(entity, bindings)
    if seed is None:
        return
    years_query = years_template.replace('$SEED', seed).replace('$FILTERS', filters)
    years_data = await sparql_post(years_query, client)
    years_by_uri = {r["URI"]["value"]: r["Years"] for r in years_data["results"]["bindings"]}
    for b in bindings:
        uri = b.get("URI", {}).get("value")
        if uri in years_by_uri:
            b["Years"] = years_by_uri[uri]

@app.get("/api/table/authors")
async def read_table_authors(params: Annotated[TableParams, Query()], client: httpx.AsyncClient = Depends(get_client), *, request: Request):
    vars, bindings, filters = await _run_table_page(sparqlTemplates.AUTHOR_TABLE_TEMPLATE, params, request, client, {"Entity", "Publication", "Venue"})
    await _merge_year_counts("Author", sparqlTemplates.AUTHOR_YEAR_COUNTS_TEMPLATE, filters, bindings, client)
    return {"vars": vars + ["Years"], "bindings": bindings}

@app.get("/api/table/venues")
async def read_table_venues(params: Annotated[TableParams, Query()], client: httpx.AsyncClient = Depends(get_client), *, request: Request):
    vars, bindings, filters = await _run_table_page(sparqlTemplates.VENUE_TABLE_TEMPLATE, params, request, client, {"Entity", "Publication", "Author"})
    await _merge_year_counts("Venue", sparqlTemplates.VENUE_YEAR_COUNTS_TEMPLATE, filters, bindings, client)
    return {"vars": vars + ["Years"], "bindings": bindings}

@app.get("/api/table/years")
async def read_table_years(params: Annotated[TableParams, Query()], client: httpx.AsyncClient = Depends(get_client), *, request: Request):
    vars, bindings, _ = await _run_table_page(sparqlTemplates.YEARS_TABLE_TEMPLATE, params, request, client, {"Entity", "Publication", "Venue", "Author"})
    return {"vars": vars, "bindings": bindings}

@app.get("/api/table/publications")
async def read_table_publications(params: Annotated[TableParams, Query()], client: httpx.AsyncClient = Depends(get_client), *, request: Request):
    vars, bindings, _ = await _run_table_page(sparqlTemplates.PUBLICATION_TABLE_TEMPLATE, params, request, client, {"Entity", "Year", "Author"}, default_sort="Year")
    return {"vars": vars, "bindings": bindings}

@app.get("/api/conferences")
async def read_conferences_overview(client: httpx.AsyncClient = Depends(get_client)):
    query = sparqlTemplates.ANTHOLOGY_CONFERENCES_QUERY_TEMPLATE
    data = await sparql_post(query, client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/conferences/{id}")
async def read_conference(id: str, client: httpx.AsyncClient = Depends(get_client)):
    query = sparqlTemplates.VENUE_PROCEEDINGS_TEMPLATE.replace('$VENUE_URI', get_uri_from_id(id))
    data = await sparql_post(query, client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/conferences/{id}/{year}/inproceedings")
async def read_conference_year_inproceedings(id: str, year: int, client: httpx.AsyncClient = Depends(get_client)):
    query = sparqlTemplates.INPROCEEDINGS_FROM_PROCEEDINGS_TEMPLATE.replace('$VENUE_ID', get_uri_from_id(id)).replace('$YEAR', str(year))
    data = await sparql_post(query, client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/conferences/{id}/{year}/proceedings")
async def read_conference_year_proceedings(id: str, year: int, client: httpx.AsyncClient = Depends(get_client)):
    query = sparqlTemplates.VENUE_YEAR_PROCEEDINGS_QUERY_TEMPLATE.replace('$VENUE_ID', get_uri_from_id(id)).replace('$YEAR', str(year))
    data = await sparql_post(query, client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/conferences/{id}/{year}/loose")
async def read_conference_year_loose(id: str, year: int, client: httpx.AsyncClient = Depends(get_client)):
    query = (sparqlTemplates.CONFERENCE_LOOSE_PAPERS_TEMPLATE
             .replace('$VENUE_ID', get_uri_from_id(id))
             .replace('$YEAR', str(year)))
    data = await sparql_post(query, client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/workshops")
async def read_workshops_overview(client: httpx.AsyncClient = Depends(get_client)):
    query = sparqlTemplates.ANTHOLOGY_WORKSHOPS_QUERY_TEMPLATE
    data = await sparql_post(query, client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/workshops/proceedings")
async def read_workshops_proceedings(client: httpx.AsyncClient = Depends(get_client)):
    query = sparqlTemplates.WORKSHOPS_PROCEEDINGS_TEMPLATE
    data = await sparql_post(query, client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/workshops/{year}/inproceedings")
async def read_conference(year: int, client: httpx.AsyncClient = Depends(get_client)):
    query = sparqlTemplates.WORKSHOPS_INPROCEEDINGS_FROM_PROCEEDINGS_TEMPLATE.replace('$YEAR', str(year))
    data = await sparql_post(query, client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/workshops/{year}/proceedings")
async def read_conference_year(year: int, client: httpx.AsyncClient = Depends(get_client)):
    query = sparqlTemplates.WORKSHOPS_YEAR_PROCEEDINGS_QUERY_TEMPLATE.replace('$YEAR', str(year))
    data = await sparql_post(query, client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/workshops/{year}/loose")
async def read_workshops_year_loose(year: int, client: httpx.AsyncClient = Depends(get_client)):
    query = sparqlTemplates.WORKSHOPS_LOOSE_PAPERS_TEMPLATE.replace('$YEAR', str(year))
    data = await sparql_post(query, client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/journals")
async def read_journals_overview(client: httpx.AsyncClient = Depends(get_client)):
    query = sparqlTemplates.ANTHOLOGY_JOURNALS_QUERY_TEMPLATE
    data = await sparql_post(query, client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/journals/{id}")
async def read_journal(id: str, client: httpx.AsyncClient = Depends(get_client)):
    query = sparqlTemplates.JOURNAL_OVERVIEW_TEMPLATE.replace('$JOURNAL', get_uri_from_id(id))
    data = await sparql_post(query, client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/journals/{id}/{year}")
async def read_journal_year(id: str, year: int, client: httpx.AsyncClient = Depends(get_client)):
    query = sparqlTemplates.JOURNAL_YEAR_TEMPLATE.replace('$JOURNAL', get_uri_from_id(id)).replace('$YEAR', str(year))
    data = await sparql_post(query, client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/people")
async def read_people(client: httpx.AsyncClient = Depends(get_client)):
    query = sparqlTemplates.PEOPLE_TEMPLATE
    data = await sparql_post(query, client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/people/{id}")
async def read_person(id: str, client: httpx.AsyncClient = Depends(get_client)):
    query = sparqlTemplates.PERSON_TEMPLATE.replace('$AUTHOR', get_uri_from_id(id))
    data = await sparql_post(query, client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/publications")
async def read_publications(client: httpx.AsyncClient = Depends(get_client)):
    query = sparqlTemplates.PUBLICATIONS_TEMPLATE
    data = await sparql_post(query, client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/publications/{id}")
async def read_publication(id: str, client: httpx.AsyncClient = Depends(get_client)):
    query = sparqlTemplates.BIB_PUBLICATION_TEMPLATE.replace('$PUBLICATION', get_uri_from_id(id))
    data = await sparql_post(query, client)
    vars_ = data["head"]["vars"]
    bindings = data["results"]["bindings"]
    flat = bibtex_helper.bindings_to_dict(vars_, bindings)
    return {"vars": vars_, "bindings": bindings, "bibtex": bibtex_helper.create_bibtex(flat)}

def parse_order(sort_by: str | None, order: str, allowed: set[str] | None = None, default: str = "Publication") -> str:
    if sort_by is None or (allowed is not None and sort_by not in allowed):
        return f'ORDER BY DESC(?{default})'

    direction = "ASC" if (order or '').upper() == 'ASC' else 'DESC'
    return f"ORDER BY {direction}(?{sort_by})"

def get_label_var(entity_type: str) -> str:
    return f"?{entity_type.lower()}_label"

def build_filters(search_params: dict[str, str]) -> str :
    filters: dict[str, list[str]] = {}
    for key in search_params:
        if not key.startswith('filter_'):
            continue
        value = search_params[key];
        if value is None:
            continue
        filters[key[len('filter_'):]] = value.split(',')

    if len(filters) == 0:
        return ''

    filter_clauses: list[str] = []
    for key in filters:
        values = filters[key]
        if  len(values) == 0:
            continue;
        label_var = get_label_var(key)
        contains_clauses = []
        for v in values:
            contains_clauses.append(f'CONTAINS(LCASE({label_var}), LCASE("{v.lower().replace("'", "\\'")}"))')
        contains_string = f"{contains_clauses[0]}"
        for i in range(1, len(contains_clauses)):
            contains_string +=  f" || {contains_clauses[i]}"
        filter_clauses.append(f"FILTER({contains_string})")

    filter_string = f"{filter_clauses[0]}"
    for i in range(1, len(filter_clauses)):
        filter_string += f"\n  {filter_clauses[i]}"
    return filter_string;


class ImportRequest(BaseModel):
    iri: str
    type: str   # "journal" | "conference" | "workshop" | "person" | "publication"
    year: int | None = None


class CustomWorkshopPreviewRequest(BaseModel):
    abbreviation: str
    title: str
    year: int | None = None


class CustomWorkshopRequest(BaseModel):
    abbreviation: str
    title: str
    year: int | None = None
    proc_iris: list[str]


@app.post("/api/admin/workshop/custom/preview")
async def preview_custom_workshop(
    body: CustomWorkshopPreviewRequest,
    _user: dict = Depends(auth_utils.require_admin),
    client: httpx.AsyncClient = Depends(get_client),
) -> dict:
    proceedings = await dblp_fetch._find_proceedings_by_title(
        client, body.title, body.abbreviation, body.year
    )
    return {"proceedings": proceedings}


@app.get("/api/admin/patches")
async def get_patches(_user: dict = Depends(auth_utils.require_admin)):
    return {"patches": patch_store.list_patches()}


@app.post("/api/admin/import")
async def import_from_dblp(
    body: ImportRequest,
    user: dict = Depends(auth_utils.require_admin),
    client: httpx.AsyncClient = Depends(get_client),
):
    if body.type in ("journal", "conference"):
        nt = await dblp_fetch.fetch_stream(client, body.iri, body.year, is_workshop=False)
    elif body.type == "workshop":
        nt = await dblp_fetch.fetch_stream(client, body.iri, body.year, is_workshop=True)
    elif body.type == "person":
        streams_resp = await sparql_post(
            "PREFIX dblp: <https://dblp.org/rdf/schema#>\nSELECT ?stream WHERE { ?stream a dblp:Stream }",
            client,
        )
        known_streams = [b["stream"]["value"] for b in streams_resp["results"]["bindings"]]
        nt = await dblp_fetch.fetch_person(client, body.iri, known_streams)
    elif body.type == "publication":
        nt = await dblp_fetch.fetch_publication(client, body.iri)
    else:
        raise HTTPException(400, f"Unknown type '{body.type}'")

    if not nt.strip():
        raise HTTPException(404, "No triples found for the given IRI — check that it exists in DBLP")

    slug = body.iri.rstrip("/").split("/")[-1]
    if body.year:
        slug += f"-{body.year}"
    filename = patch_store.save_patch(slug, nt)

    sparql = patch_store.nt_to_sparql_insert(nt)
    live_ok = True
    try:
        await sparql_update(sparql, client)
    except HTTPException:
        live_ok = False

    triple_count = sum(1 for line in nt.splitlines() if line.strip())
    patch_store.save_patch_meta(filename, {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_name": user.get("name", ""),
        "user_email": user.get("email", ""),
        "action": "import",
        "details": {"type": body.type, "iri": body.iri, "year": body.year},
        "triples": triple_count,
        "live_applied": live_ok,
    })
    return {"filename": filename, "triples": triple_count, "live_applied": live_ok}


@app.post("/api/admin/workshop/custom")
async def add_custom_workshop(
    body: CustomWorkshopRequest,
    user: dict = Depends(auth_utils.require_admin),
    client: httpx.AsyncClient = Depends(get_client),
):
    if not body.proc_iris:
        raise HTTPException(400, "No proceedings selected")
    nt = await dblp_fetch.fetch_custom_workshop(client, body.abbreviation, body.title, body.proc_iris)
    if not nt.strip():
        raise HTTPException(404, "No triples found for the given proceedings")

    slug = f"custom-workshop-{body.abbreviation}"
    if body.year:
        slug += f"-{body.year}"
    filename = patch_store.save_patch(slug, nt)

    sparql = patch_store.nt_to_sparql_insert(nt)
    live_ok = True
    try:
        await sparql_update(sparql, client)
    except HTTPException:
        live_ok = False

    triple_count = sum(1 for line in nt.splitlines() if line.strip())
    patch_store.save_patch_meta(filename, {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_name": user.get("name", ""),
        "user_email": user.get("email", ""),
        "action": "custom_workshop",
        "details": {
            "abbreviation": body.abbreviation,
            "title": body.title,
            "year": body.year,
            "proc_iris": body.proc_iris,
        },
        "triples": triple_count,
        "live_applied": live_ok,
    })
    return {"filename": filename, "triples": triple_count, "live_applied": live_ok}


async def sparql_update(query: str, client: httpx.AsyncClient) -> None:
    url = SPARQL_ENDPOINT
    if SPARQL_ACCESS_TOKEN:
        url += f"?access-token={SPARQL_ACCESS_TOKEN}"
    response = await client.post(
        url,
        headers={"Content-Type": "application/sparql-update"},
        content=query,
    )
    if not response.is_success:
        raise HTTPException(500, f"Database update failed: {response.text}")


async def sparql_post(query: str, client: httpx.AsyncClient) -> dict:
    response = await client.post(
        SPARQL_ENDPOINT,
        headers={
            "Accept": "application/sparql-results+json",
            "Content-Type": "application/sparql-query",
        },
        content=query,
    )
    if not response.is_success:
        raise HTTPException(response.status_code, "Could not get resource from database")
    return response.json()
