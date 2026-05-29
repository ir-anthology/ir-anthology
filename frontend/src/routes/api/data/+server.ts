import { json } from '@sveltejs/kit';
import { fetchSparqlTableData } from '$lib/sparql/fetch.server';

export async function GET({ url }) {
    const data = await fetchSparqlTableData(url.searchParams);
    return json(data);
}