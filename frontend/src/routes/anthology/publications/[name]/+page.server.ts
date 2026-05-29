import { fetchDataForPublication } from '$lib/sparql/fetch.server.js'
import { parseSparqlResult, getURIFromID } from '$lib/helperFunctions.js';
export async function load({params}) {
    const uri = getURIFromID(params.name) 
    const data = parseSparqlResult(await fetchDataForPublication(uri))[0];
    console.log(data)

    return {"publication": data};
}