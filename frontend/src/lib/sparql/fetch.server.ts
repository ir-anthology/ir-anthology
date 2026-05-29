import { error } from '@sveltejs/kit';
import * as testjson from '$lib/assets/firstQuery.json';

const SPARQL_ENDPOINT = 'http://database.ir-anthology.srv.webis.de/';

const VALID_ENTITIES = ['Author', 'Venue', 'Publication', 'Year', '2020s', '2010s', '2000s', 'Pre2000s'];

const TABLE_QUERY_TEMPLATE = `
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>

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
  ?publication_URI dblp:title ?publication_label ;
                   dblp:yearOfPublication ?year_label ;
                   dblp:authoredBy ?author_URI ;
                   dblp:publishedInStream ?venue_URI .

  OPTIONAL {
    ?venue_URI dblp:streamTitle ?venue_label .
  }
  OPTIONAL {
    ?author_URI dblp:primaryCreatorName ?author_label .
  }
  
  BIND(xsd:integer(STR(?year_label)) AS ?y)
  
  BIND(IF(?y >= 2020, ?year_label, ?unbound) AS ?2020s_label)
  BIND(IF(?y >= 2010 && ?y < 2020, ?year_label, ?unbound) AS ?2010s_label)
  BIND(IF(?y >= 2000 && ?y < 2010, ?year_label, ?unbound) AS ?2000s_label)
  BIND(IF(?y < 2000, ?year_label, ?unbound) AS ?Pre2000s_label)
  
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

// With the new scheme we can also distinguish between journal and conference
const ANTHOLOGY_QUERY_TEMPLATE = `
PREFIX dblp: <https://dblp.org/rdf/schema#>

SELECT DISTINCT ?venue_URI ?venue_label ?year_label
WHERE {
  ?publication_URI
      dblp:yearOfPublication ?year_label ;
      dblp:publishedInStream ?venue_URI .

  ?venue_URI
      a ?type ;
      dblp:streamTitle ?venue_label .

  VALUES ?type {
    dblp:Journal
    dblp:Conference
  }
}
ORDER BY ?venue_label ?year_label
`;

const YEARS_QUERY_TEMPLATE = `
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>

SELECT DISTINCT ?year_label ?title ?streamTitle ?pub WHERE{
VALUES ?stream {
<$VENUE_URI>
}
?pub dblp:yearOfPublication ?year_label ;
                 dblp:publishedInStream ?stream ;
                 dblp:title ?title ;
                 dblp:bibtexType bibtex:Proceedings .
?stream dblp:streamTitle ?streamTitle .
}
`;

//editor, title, series, volume, publisher, year, url, doi, isbn
const BIB_PROCEEDINGS_QUERY_TEMPLATE = `
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>

SELECT ?title ?series ?volume ?publisher ?doi ?isbn ?url ?pub ?month (GROUP_CONCAT(DISTINCT ?name; separator=", ") AS ?editors) WHERE{
  VALUES ?stream {
    <$VENUE_ID>
  }
  ?pub dblp:title ?title ;
       dblp:publishedInStream ?stream ;
	   dblp:bibtexType bibtex:Proceedings ;
	   dblp:yearOfPublication ?year ;
       dblp:editedBy ?editor .
  FILTER(STR(?year) = "$YEAR")

  OPTIONAL{?pub dblp:publishedInSeries ?series}
  OPTIONAL{?pub dblp:publishedInSeriesVolume ?volume}
  OPTIONAL{?pub dblp:publishedBy ?publisher}
  OPTIONAL{?pub dblp:doi ?doi}
  OPTIONAL{?pub dblp:isbn ?isbn}
  OPTIONAL{?pub dblp:primaryDocumentPage ?url}
  OPTIONAL{?pub dblp:monthOfPublication ?month}
  OPTIONAL{?editor dblp:primaryCreatorName ?name}
}
GROUP BY ?title ?series ?volume ?publisher ?doi ?isbn ?url ?pub ?month
`;

//author, editor, title, booktitle, series, pages, publisher, year, url, doi
const BIB_INPROCEEDINGS_FROM_PROCEEDINGS_TEMPLATE = `
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>

SELECT ?title ?booktitle ?series ?pages ?publisher ?doi ?url ?year ?book ?pub ?month (GROUP_CONCAT(DISTINCT ?name; separator=", ") AS ?authors) (GROUP_CONCAT(DISTINCT ?editorName; separator=", ") AS ?editors) WHERE{
  VALUES ?book {
    $BOOKS
  }
  ?book dblp:title ?booktitle ;
        dblp:editedBy ?editor .
  ?pub dblp:publishedAsPartOf ?book ;
       dblp:title ?title ;
       dblp:publishedInStream ?stream ;
	   dblp:bibtexType bibtex:Inproceedings ;
	   dblp:yearOfPublication ?year ;
       dblp:authoredBy ?author .

  OPTIONAL{?pub dblp:publishedInSeries ?series}
  OPTIONAL{?pub dblp:pagination ?pages}
  OPTIONAL{?book dblp:publishedBy ?publisher}
  OPTIONAL{?pub dblp:doi ?doi}
  OPTIONAL{?pub dblp:primaryDocumentPage ?url}
  OPTIONAL{?pub dblp:monthOfPublication ?month}
  OPTIONAL{?author dblp:primaryCreatorName ?name}
  OPTIONAL{?editor dblp:primaryCreatorName ?editorName}
}
GROUP BY ?title ?booktitle ?series ?pages ?publisher ?doi ?url ?year ?book ?pub ?month
`;

//author, editor, title, booktitle, series, pages, publisher, year, url, doi, month
const BIB_PUBLICATION_TEMPLATE = `
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>

SELECT ?title ?booktitle ?series ?pages ?publisher ?doi ?url ?year ?book ?pub ?streamTitle ?month ?volume ?number ?isbn ?bibtexType (GROUP_CONCAT(DISTINCT ?name; separator=", ") AS ?authors) (GROUP_CONCAT(DISTINCT STR(?author); separator=", ") AS ?authorIds) (GROUP_CONCAT(DISTINCT ?editorName; separator=", ") AS ?editors) (GROUP_CONCAT(DISTINCT STR(?editor); separator=", ") AS ?editorIds) WHERE{
  VALUES ?pub {
    <$PUBLICATION>
  }
  ?pub dblp:title ?title ;
       dblp:publishedInStream ?stream ;
	   dblp:bibtexType ?bibtexType ;
	   dblp:yearOfPublication ?year .

  ?stream dblp:streamTitle ?streamTitle .
  
  OPTIONAL{?pub dblp:publishedInSeries ?series}
  OPTIONAL{?pub dblp:pagination ?pages}
  OPTIONAL{?pub dblp:doi ?doi}
  OPTIONAL{?pub dblp:publishedBy ?publisher}
  OPTIONAL{?pub dblp:primaryDocumentPage ?url}
  OPTIONAL{?pub dblp:monthOfPublication ?month}
  OPTIONAL{?pub dblp:publishedInJournalVolume ?volume}
  OPTIONAL{?pub dblp:publishedInJournalVolumeIssue ?number}
  OPTIONAL{?pub dblp:pagination ?pages}
  OPTIONAL{?pub dblp:isbn ?isbn}
  OPTIONAL{?pub dblp:authoredBy ?author .
            ?author dblp:primaryCreatorName ?name}
  OPTIONAL{?pub dblp:editedBy ?editor .
           ?editor dblp:primaryCreatorName ?editorName}
  OPTIONAL{?pub dblp:publishedAsPartOf ?book.
           ?book dblp:title ?booktitle}
  OPTIONAL{?book dblp:editedBy ?editor .
           ?editor dblp:primaryCreatorName ?editorName}
  OPTIONAL{?book dblp:publishedBy ?publisher}
  OPTIONAL{?book dblp:publishedInSeries ?series}
}
GROUP BY ?title ?booktitle ?series ?pages ?publisher ?doi ?url ?year ?book ?pub ?streamTitle ?month ?volume ?number ?isbn ?bibtexType
`;

//author, ee/doi, title, year, journal, volume, url, pages, number, 
const BIB_ARTICLES_FROM_JOURNAL_TEMPLATE = `
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>

SELECT  (GROUP_CONCAT(DISTINCT ?name; separator=", ") AS ?authors)  ?title ?year ?journalTitle ?volume ?url ?pages ?number ?doi ?pub WHERE{
  VALUES ?journal {
    <$JOURNAL>
  }
  ?journal dblp:streamTitle ?journalTitle .
  ?pub dblp:publishedInStream ?journal ;
       dblp:title ?title ;
	   dblp:bibtexType bibtex:Article ;
	   dblp:yearOfPublication ?year ;
       dblp:authoredBy ?author .
  FILTER(STR(?year) = "$YEAR")
  OPTIONAL{?pub dblp:publishedInJournalVolume ?volume}
  OPTIONAL{?pub dblp:publishedInJournalVolumeIssue ?number}
  OPTIONAL{?pub dblp:pagination ?pages}
  OPTIONAL{?pub dblp:doi ?doi}
  OPTIONAL{?pub dblp:primaryDocumentPage ?url}
  OPTIONAL{?author dblp:primaryCreatorName ?name}
}
GROUP BY  ?title ?year ?journalTitle ?volume ?url ?pages ?number ?doi ?pub
`;

const PERSON_TEMPLATE = `
PREFIX dblp: <https://dblp.org/rdf/schema#>

SELECT  ?title ?year ?doi ?pub ?name WHERE{
  VALUES ?author {
    <$AUTHOR>
  }
  ?pub dblp:authoredBy ?author ;
	   dblp:bibtexType ?bibtexType ;
	   dblp:yearOfPublication ?year ;
       dblp:publishedInStream ?stream ;
       dblp:title ?title .

  OPTIONAL{?pub dblp:doi ?doi}
  OPTIONAL{?pub dblp:primaryDocumentPage ?url}
  OPTIONAL{?author dblp:primaryCreatorName ?name}
}
`;

const TOBEDELETED = `
SELECT *
WHERE {
  ?s ?p ?o
}
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

async function sparqlPost(query: string) {
    const sparqlURL = `${SPARQL_ENDPOINT}?query=${encodeURIComponent(query)}`;
    const response = await fetch(sparqlURL, {
        method: 'POST',
        headers: {
            'Accept': 'application/sparql-results+json',
            'Content-Type': 'application/sparql-query',
        },
        body: query,
    });
    if (!response.ok) {
        error(response.status, { message: 'Could not get resource from database' });
    }
    return response.json();
}

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
    console.log(query)
    const data = await sparqlPost(query);
    console.log(data)
    return { vars: data.head.vars, bindings: data.results.bindings };
}

export async function fetchSparqlAnthologyData() {
    const data = await sparqlPost(ANTHOLOGY_QUERY_TEMPLATE);
    return { vars: data.head.vars, bindings: data.results.bindings };
}

export async function fetchSparqlYearsForVenue(venue_uri: string) {
    const query = YEARS_QUERY_TEMPLATE.replace('$VENUE_URI', venue_uri);
    const data = await sparqlPost(query);
    return { vars: data.head.vars, bindings: data.results.bindings };
}

export async function fetchDebug() {
    return sparqlPost(TOBEDELETED);
}

export async function fetchDataForVenueYear(venue_id: string, year: string) {
    const query = BIB_PROCEEDINGS_QUERY_TEMPLATE.replace('$VENUE_ID', venue_id).replace('$YEAR', year);
    const data = await sparqlPost(query);
    return { vars: data.head.vars, bindings: data.results.bindings };
}

export async function fetchDataForInproceedingsFromProceedings(bookURIs: string) {
    const query = BIB_INPROCEEDINGS_FROM_PROCEEDINGS_TEMPLATE.replace('$BOOKS', bookURIs);
    const data = await sparqlPost(query);
    return { vars: data.head.vars, bindings: data.results.bindings };
}

export async function fetchDataForPublication(publication_uri: string) {
    const query = BIB_PUBLICATION_TEMPLATE.replace('$PUBLICATION', publication_uri);
    const data = await sparqlPost(query);
    return { vars: data.head.vars, bindings: data.results.bindings };
}

export async function fetchDataForJournalYear(journal_uri: string, year: string) {
    const query = BIB_ARTICLES_FROM_JOURNAL_TEMPLATE.replace('$JOURNAL', journal_uri).replace('$YEAR', year);
    const data = await sparqlPost(query);
    return { vars: data.head.vars, bindings: data.results.bindings };
}

export async function fetchDataForPerson(author_uri: string) {
    const query = PERSON_TEMPLATE.replace('$AUTHOR', author_uri);
    console.log(query)
    const data = await sparqlPost(query);
    return { vars: data.head.vars, bindings: data.results.bindings };
}