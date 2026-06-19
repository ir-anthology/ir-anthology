import { fetchBackend } from '$lib/sparql/fetch.js'
import { parseSparqlResult } from '$lib/helperFunctions.js';
export async function load({params}) {
    const response = await fetchBackend("publications/"+params.name);
    return { publication: parseSparqlResult(response)[0], bibtex: response.bibtex as string };
}