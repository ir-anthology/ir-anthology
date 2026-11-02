import { fetchBackend } from '$lib/sparql/fetch.js'
import { parseSparqlResult, getIDFromURI } from '$lib/helperFunctions.js';

export async function entries() {
    const data = parseSparqlResult(await fetchBackend("publications"));
    return data
        .filter(row => row.pub)
        .map(row => ({ name: getIDFromURI(row.pub!) }));
}

export async function load({params}) {
    const response = await fetchBackend("publications/"+params.name);
    return { publication: parseSparqlResult(response)[0], bibtex: response.bibtex as string };
}