import { fetchBackend } from '$lib/sparql/fetch.js'
import { DEBUG } from '$lib/sparql/fetch.js'
import { parseSparqlResult, getIDFromURI } from '$lib/helperFunctions.js';

export async function entries() {
    const data = parseSparqlResult(await fetchBackend("publications"));
    return data
        .filter(row => row.pub)
        .map(row => ({ name: getIDFromURI(row.pub!) }));
}

export async function load({params}) {
    if (DEBUG) console.log('[DEBUG] publication/load:', params.name);
    const response = await fetchBackend("publications/"+params.name);
    const result = { publication: parseSparqlResult(response)[0], bibtex: response.bibtex as string };
    if (DEBUG) console.log('[DEBUG] publication/load →', result);
    return result;
}