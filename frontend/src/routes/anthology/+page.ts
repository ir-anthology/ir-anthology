import { fetchBackend } from '$lib/sparql/fetch.js'
import { parseSparqlResult, getIDFromURI } from '$lib/helperFunctions';

export async function load() {
    const data = parseSparqlResult(await fetchBackend("anthology"));

    const venueMap = new Map<string, { years: Set<string>; label: string; id: string; type:string}>();

    for (const binding of data) {
        const venueName = binding.stream;
        if (venueName === null) continue;

        if (!venueMap.has(venueName)) {
            const dblpId = getIDFromURI(binding.stream ?? '');
            venueMap.set(venueName, {
                years: new Set(),
                label: dblpId.split('+').at(-1)?.toUpperCase() ?? '',
                id: dblpId,
                type: binding.type?.split("#")[1] ?? '',
            });
        }

        if (binding.year_label !== null) {
            venueMap.get(venueName)!.years.add(binding.year_label);
        }
    }

    const venues = [...venueMap.values()].map(v => ({ ...v, years: [...v.years] }));

    return { venues };
}
