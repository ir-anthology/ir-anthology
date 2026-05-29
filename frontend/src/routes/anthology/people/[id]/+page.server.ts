import { fetchDataForPerson } from '$lib/sparql/fetch.server.js'
import { getURIFromID, parseSparqlResult } from '$lib/helperFunctions.js';

export async function load({ params }){
    const uri = getURIFromID(params.id)
    console.log(uri)
    const data = parseSparqlResult(await fetchDataForPerson(uri));
    console.log(data)
    return {"pubs": data}
}