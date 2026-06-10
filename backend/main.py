from fastapi import FastAPI, HTTPException, Query, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated
from pydantic import BaseModel
from enum import Enum
import sparqlTemplates
import httpx
from contextlib import asynccontextmanager

SPARQL_ENDPOINT = "https://database-ir-anthology.srv.webis.de/"

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
    allow_methods=["GET"],
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

@app.get("/api/anthology")
async def read_anthology(client: httpx.AsyncClient = Depends(get_client)):
    data = await sparql_post(sparqlTemplates.ANTHOLOGY_QUERY_TEMPLATE, client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/conferences/{id}")
async def read_conference(id: str, client: httpx.AsyncClient = Depends(get_client)):
    data = await sparql_post(sparqlTemplates.VENUE_PROCEEDINGS_TEMPLATE.replace('$VENUE_URI', get_uri_from_id(id)), client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/conferences/{id}/{year}/inproceedings")
async def read_conference(id: str, year: int, client: httpx.AsyncClient = Depends(get_client)):
    data = await sparql_post(sparqlTemplates.INPROCEEDINGS_FROM_PROCEEDINGS_TEMPLATE.replace('$VENUE_ID', get_uri_from_id(id)).replace('$YEAR', str(year)), client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/conferences/{id}/{year}/proceedings")
async def read_conference_year(id: str, year: int, client: httpx.AsyncClient = Depends(get_client)):
    data = await sparql_post(sparqlTemplates.PROCEEDINGS_QUERY_TEMPLATE.replace('$VENUE_ID', get_uri_from_id(id)).replace('$YEAR', str(year)), client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/journals/{id}")
async def read_journal(id: str, client: httpx.AsyncClient = Depends(get_client)):
    data = await sparql_post(sparqlTemplates.JOURNAL_OVERVIEW_TEMPLATE.replace('$JOURNAL', get_uri_from_id(id)), client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/journals/{id}/{year}")
async def read_journal_year(id: str, year: int, client: httpx.AsyncClient = Depends(get_client)):
    data = await sparql_post(sparqlTemplates.ARTICLES_FROM_JOURNAL_TEMPLATE.replace('$JOURNAL', get_uri_from_id(id)).replace('$YEAR', str(year)), client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/people/{id}")
async def read_venue(id: str, client: httpx.AsyncClient = Depends(get_client)):
    data = await sparql_post(sparqlTemplates.PERSON_TEMPLATE.replace('$AUTHOR', get_uri_from_id(id)), client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

@app.get("/api/publications/{id}")
async def read_venue(id: str, client: httpx.AsyncClient = Depends(get_client)):
    query = sparqlTemplates.BIB_PUBLICATION_TEMPLATE.replace('$PUBLICATION', get_uri_from_id(id))
    print(query)
    data = await sparql_post(query, client)
    return {"vars": data["head"]["vars"], "bindings": data["results"]["bindings"]}

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
            print(contains_string)
            filter_clauses.append(f"FILTER({contains_string})")

    print(filter_clauses)
    filter_string = f"{filter_clauses[0]}"
    for i in range(1, len(filter_clauses)):
        filter_string += f"\n  {filter_clauses[i]}"
    print(filter_string)
    return filter_string;

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
