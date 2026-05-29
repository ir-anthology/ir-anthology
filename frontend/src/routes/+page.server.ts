import { fetchSparqlTableData } from '$lib/sparql/fetch.server';

export async function load({ url }) {
    return fetchSparqlTableData(url.searchParams);
}
