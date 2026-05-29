import { fetchSparqlYearsForVenue } from '$lib/sparql/fetch.server.js'
import { getURIFromID, parseSparqlResult } from '$lib/helperFunctions.js';

export async function load({ params }){
    const uri = getURIFromID(params.name)
    const data = parseSparqlResult(await fetchSparqlYearsForVenue(uri));
    const years = data.map((val) =>{
            return val.year_label
        });
    const titles = data.map((val) =>{
        return val.title
    });
    const uris = data.map((val) =>{
        return val.pub
    });
    return {"name": data[0]?.streamTitle ?? "TODO Show error 404", "years": years, "titles": titles, "venue_id": params.name, "uris": uris}
}