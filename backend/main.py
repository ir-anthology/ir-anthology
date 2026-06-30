from fastapi import FastAPI, HTTPException, Query, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated
from pydantic import BaseModel
from enum import Enum
import sparqlTemplates
import bibtex as bibtex_helper
import auth_utils
import patches as patch_store
import dblp_fetch
import httpx
import os
from contextlib import asynccontextmanager

SPARQL_ENDPOINT = "https://database-ir-anthology.srv.webis.de/"
SPARQL_ACCESS_TOKEN = os.environ.get("SPARQL_ACCESS_TOKEN", "")

VALID_ENTITIES = ['Author', 'Venue', 'Publication', 'Year', '2020s', '2010s', '2000s', 'Pre2000s']

class Entities(str, Enum):
    author = "Author"
    venue = "Venue"
    publication = "Publication"
    year = "Year"
    twenty_twenties = "2020s"
    twenty_tens = "2010s"
    two_thousands = "2000s"
    pre_two_thousands = "Pre2000s"

class FilterParams(BaseModel):
    entity: Entities | None = "Author"
    sort_by: str | None = "Publication"
    order: str | None = "DESC"
    page: int | None = 1
    limit: int | None = 50

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

@app.get("/api/table")
async def read_table_data(filter_query: Annotated[FilterParams, Query()], client: httpx.AsyncClient = Depends(get_client), *, request: Request):
    extra = {
        k: v for k, v in request.query_params.items()
        if k not in filter_query.model_dump().keys()
    }
    order_clause = parse_order(filter_query.sort_by, filter_query.order)
    offset = (filter_query.page - 1) * filter_query.limit
    filters = build_filters(extra)
    query = sparqlTemplates.TABLE_QUERY_TEMPLATE.replace("$ENTITY_TYPE", filter_query.entity)
    query = query.replace('$FILTERS', filters)
    query = query.replace('$ORDER', order_clause)
    query = query.replace('$LIMIT', str(filter_query.limit))
    query = query.replace('$OFFSET', str(offset))
    data = await sparql_post(query, client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/conferences/overview")
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
    query = sparqlTemplates.PROCEEDINGS_QUERY_TEMPLATE.replace('$VENUE_ID', get_uri_from_id(id)).replace('$YEAR', str(year))
    data = await sparql_post(query, client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/workshops/overview")
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

@app.get("/api/journals/overview")
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
    query = sparqlTemplates.ARTICLES_FROM_JOURNAL_TEMPLATE.replace('$JOURNAL', get_uri_from_id(id)).replace('$YEAR', str(year))
    data = await sparql_post(query, client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/people/{id}")
async def read_venue(id: str, client: httpx.AsyncClient = Depends(get_client)):
    query = sparqlTemplates.PERSON_TEMPLATE.replace('$AUTHOR', get_uri_from_id(id))
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

def parse_order(sort_by: str | None, order: str) -> str:
    if sort_by is None:
        return 'ORDER BY DESC(?Publication)'
    
    direction = "ASC" if order == 'ASC' else 'DESC'
    return f"ORDER BY {direction}(?{sort_by})"

def get_label_var(entity_type: str) -> str:
    return f"?{entity_type.lower()}_label"

def get_uri_var(entity_type: str) -> str:
    return f"?{entity_type.lower()}_URI"

def build_filters(search_params: dict[str, str], filter_mode = 'label') -> str :
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
        if filter_mode == 'uri':
            uri_var = get_uri_var(key)
            uri_values = []
            for v in values:
                if v.startswith("http://") or v.startswith("https://"):
                    uri_values.append(v)
            if len(uri_values) > 0:
                in_string = f"<{uri_values[0]}>"
                for i in range(1, len(uri_values)):
                    in_string+= f",<{uri_values[i]}>"
                filter_clauses.append(f"FILTER({uri_var} IN ({in_string}))")
        else :
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


class CustomWorkshopRequest(BaseModel):
    abbreviation: str
    title: str
    year: int | None = None


@app.get("/api/admin/patches")
async def get_patches(_user: dict = Depends(auth_utils.require_admin)):
    return {"patches": patch_store.list_patches()}


@app.post("/api/admin/import")
async def import_from_dblp(
    body: ImportRequest,
    _user: dict = Depends(auth_utils.require_admin),
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
    return {"filename": filename, "triples": triple_count, "live_applied": live_ok}


@app.post("/api/admin/workshop/custom")
async def add_custom_workshop(
    body: CustomWorkshopRequest,
    _user: dict = Depends(auth_utils.require_admin),
    client: httpx.AsyncClient = Depends(get_client),
):
    nt = await dblp_fetch.fetch_custom_workshop(client, body.abbreviation, body.title, body.year)
    if not nt.strip():
        raise HTTPException(404, "No proceedings found on DBLP matching the given name/abbreviation")

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
