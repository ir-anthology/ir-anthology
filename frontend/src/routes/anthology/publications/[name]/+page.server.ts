import { fetchBackend } from '$lib/sparql/fetch.server.js'
import { parseSparqlResult } from '$lib/helperFunctions.js';
export async function load({params}) {
    const data = parseSparqlResult(await fetchBackend("publications/"+params.name))[0];

    return {"publication": data};
}