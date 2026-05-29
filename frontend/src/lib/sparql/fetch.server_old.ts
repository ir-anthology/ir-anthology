import { error } from '@sveltejs/kit';
import * as testjson from '$lib/assets/firstQuery.json';

const SPARQL_ENDPOINT = 'https://webislab33.medien.uni-weimar.de/sparql/';

const VALID_ENTITIES = ['Author', 'Venue', 'Publication', 'Year', '2020s', '2010s', '2000s', 'Pre2000s'];

const TABLE_QUERY_TEMPLATE = `
PREFIX ex: <https://ir.webis.de/kg/>

SELECT (?entity_label AS ?Entity)
 (?entity_URI AS ?URI)
  (COUNT(DISTINCT ?publication_label) AS ?Publication)
  (COUNT(DISTINCT ?venue_label)       AS ?Venue)
  (COUNT(DISTINCT ?author_label)      AS ?Author)
  (COUNT(DISTINCT ?year_label)        AS ?Year)
  (COUNT(DISTINCT ?2020s_label)       AS ?2020s)
  (COUNT(DISTINCT ?2010s_label)       AS ?2010s)
  (COUNT(DISTINCT ?2000s_label)       AS ?2000s)
  (COUNT(DISTINCT ?Pre2000s_label)    AS ?Pre2000s)
WHERE {
  VALUES ?entityType { "$ENTITY_TYPE" }
  ?publication_URI ex:type  "Publication" ;
                   ex:label ?publication_label ;
                   ex:isConnectedTo ?year_URI .

  OPTIONAL {
    ?publication_URI ex:isConnectedTo ?venue_URI .
    ?venue_URI ex:type  "Venue" ;
               ex:label ?venue_label .
  }
  OPTIONAL {
    ?publication_URI ex:isConnectedTo ?author_URI .
    ?author_URI ex:type  "Author" ;
                ex:label ?author_label .
  }
  OPTIONAL {
    ?year_URI ex:type  "Year" ;
              ex:label ?year_label .
  }
  OPTIONAL {
    ?2020s_URI ex:type  "2020s" ;
               ex:label ?2020s_label .
    ?publication_URI ex:isConnectedTo ?2020s_URI .
  }
  OPTIONAL {
    ?2010s_URI ex:type  "2010s" ;
               ex:label ?2010s_label .
    ?publication_URI ex:isConnectedTo ?2010s_URI .
  }
  OPTIONAL {
    ?2000s_URI ex:type  "2000s" ;
               ex:label ?2000s_label .
    ?publication_URI ex:isConnectedTo ?2000s_URI .
  }
  OPTIONAL {
    ?Pre2000s_URI ex:type  "Pre2000s" ;
                  ex:label ?Pre2000s_label .
    ?publication_URI ex:isConnectedTo ?Pre2000s_URI .
  }

  $FILTERS

  BIND(
    IF(?entityType = "Publication", ?publication_URI,
    IF(?entityType = "Venue",       ?venue_URI,
    IF(?entityType = "Year",        ?year_URI,
    IF(?entityType = "2020s",       ?2020s_URI,
    IF(?entityType = "2010s",       ?2010s_URI,
    IF(?entityType = "2000s",       ?2000s_URI,
    IF(?entityType = "Pre2000s",    ?Pre2000s_URI,
                                    ?author_URI)))))))
  AS ?entity_URI)
  BIND(
    IF(?entityType = "Publication", ?publication_label,
    IF(?entityType = "Venue",       ?venue_label,
    IF(?entityType = "Year",        ?year_label,
    IF(?entityType = "2020s",       ?2020s_label,
    IF(?entityType = "2010s",       ?2010s_label,
    IF(?entityType = "2000s",       ?2000s_label,
    IF(?entityType = "Pre2000s",    ?Pre2000s_label,
                                    ?author_label)))))))
  AS ?entity_label)

}
GROUP BY ?entity_label ?entity_URI
HAVING (BOUND(?entity_label) && BOUND(?entity_URI))
$ORDER
LIMIT $LIMIT
OFFSET $OFFSET
`;

const ANTHOLOGY_QUERY_TEMPLATE = `
PREFIX ex: <https://ir.webis.de/kg/>

SELECT ?venue_URI ?venue_label WHERE{
    ?venue_URI ex:type  "Venue" ;
               ex:label ?venue_label .
}
`;

const YEARS_QUERY_TEMPLATE = `
PREFIX ex: <https://ir.webis.de/kg/>

SELECT DISTINCT ?year_label WHERE{
?publication_URI ex:type  "Publication" ;
        ex:isConnectedTo ?year_URI ;
        ex:isConnectedTo ?venue_URI .
?venue_URI ex:type  "Venue" ;
            ex:label "$VENUE_LABEL" .

?year_URI ex:type  "Year" ;
            ex:label ?year_label .
}
`;

const TOBEDELETED = `
SELECT ?p (COUNT(*) AS ?count)
WHERE {
  ?s ?p ?o
}
GROUP BY ?p
ORDER BY DESC(?count)
LIMIT 50
`

function parseOrder(sort_by: string, order: string): string {
    if (!sort_by) return 'ORDER BY DESC(?Publication)';
    const direction = order === 'asc' ? 'ASC' : 'DESC';
    return `ORDER BY ${direction}(?${sort_by})`;
}

function getLabelVar(entityType: string) {
    return `?${entityType.toLowerCase()}_label`;
}

function getUriVar(entityType: string) {
    return `?${entityType.toLowerCase()}_URI`;
}

function buildFilters(searchParams: URLSearchParams, filterMode = 'label'): string {
    const filters: Record<string, string[]> = {};
    for (const key of searchParams.keys()) {
        if (!key.startsWith('filter_')) continue;
        const value = searchParams.get(key);
        if (value === null) continue;
        filters[key.slice('filter_'.length)] = value.split(',');
    }

    if (Object.keys(filters).length === 0) return '';

    const filterClauses: string[] = [];
    for (const [key, values] of Object.entries(filters)) {
        if (!values || values.length === 0) continue;
        if (filterMode === 'uri') {
            const uriVar = getUriVar(key);
            if (!uriVar) continue;
            const uriValues = values.filter((v) => v.startsWith('http://') || v.startsWith('https://'));
            if (uriValues.length > 0) {
                filterClauses.push(`FILTER(${uriVar} IN (${uriValues.map((v) => `<${v}>`).join(',')}))`);
            }
        } else {
            const labelVar = getLabelVar(key);
            if (!labelVar) continue;
            const containsClauses = values.map((v) => {
                const str = String(v).toLowerCase().replace(/'/g, "\\'");
                return `CONTAINS(LCASE(${labelVar}), LCASE("${str}"))`;
            });
            filterClauses.push(`FILTER(${containsClauses.join(' || ')})`);
        }
    }

    return filterClauses.join('\n  ');
}

export type SparqlResult = {
    vars: string[];
    bindings: Record<string, { type: string; value: string }>[];
};

export async function fetchSparqlTableData(searchParams: URLSearchParams): Promise<SparqlResult> {
    if (searchParams.keys().toArray().length === 0) {
        return { vars: testjson.head.vars, bindings: testjson.results.bindings as SparqlResult['bindings'] };
    }

    let entity = searchParams.get('entity') ?? 'Author';
    const sort_by = searchParams.get('sort_by') ?? 'Publication';
    const order = searchParams.get('order') ?? 'desc';
    const page = parseInt(searchParams.get('page') ?? '1', 10);
    const limit = parseInt(searchParams.get('limit') ?? '50', 10);

    entity = VALID_ENTITIES.includes(entity) ? entity : 'Author';
    const orderClause = parseOrder(sort_by, order);
    const offset = (page - 1) * limit;
    const filters = buildFilters(searchParams);

    const query = TABLE_QUERY_TEMPLATE
        .replace('$ENTITY_TYPE', entity)
        .replace('$FILTERS', filters)
        .replace('$ORDER', orderClause)
        .replace('$LIMIT', String(limit))
        .replace('$OFFSET', String(offset));

    const sparqlURL = `${SPARQL_ENDPOINT}?query=${encodeURIComponent(query)}`;
    const response = await fetch(sparqlURL, {
        method: 'GET',
        headers: {
            Accept: 'application/sparql-results+json',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
    });

    if (!response.ok) {
        error(response.status, { message: 'Could not get resource from database' });
    }

    const data = await response.json();
    return { vars: data.head.vars, bindings: data.results.bindings };
}


export async function fetchSparqlAnthologyData(){
    const query = ANTHOLOGY_QUERY_TEMPLATE
    const sparqlURL = `${SPARQL_ENDPOINT}?query=${encodeURIComponent(query)}`;
    const response = await fetch(sparqlURL, {
        method: 'GET',
        headers: {
            Accept: 'application/sparql-results+json',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
    });

    if (!response.ok) {
        error(response.status, { message: 'Could not get resource from database' });
    }

    const data = await response.json();
    return { vars: data.head.vars, bindings: data.results.bindings };
}

export async function fetchSparqlYearsForVenue(venue_label: string){
    const query = YEARS_QUERY_TEMPLATE.replace("$VENUE_LABEL", venue_label)
    const sparqlURL = `${SPARQL_ENDPOINT}?query=${encodeURIComponent(query)}`;
    const response = await fetch(sparqlURL, {
        method: 'GET',
        headers: {
            Accept: 'application/sparql-results+json',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
    });

    if (!response.ok) {
        error(response.status, { message: 'Could not get resource from database' });
    }

    const data = await response.json();
    return { vars: data.head.vars, bindings: data.results.bindings };
}

export async function fetchDebug() {
    const sparqlURL = `${SPARQL_ENDPOINT}?query=${encodeURIComponent(TOBEDELETED)}`;
    const response = await fetch(sparqlURL, {
        method: 'GET',
        headers: {
            Accept: 'application/sparql-results+json',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
    });

    if (!response.ok) {
        error(response.status, { message: 'Could not get resource from database' });
    }

    const data = await response.json();
    return data;
}