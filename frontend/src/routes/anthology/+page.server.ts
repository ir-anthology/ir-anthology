import { fetchSparqlAnthologyData } from '$lib/sparql/fetch.server';
import { parseSparqlResult, getIDFromURI } from '$lib/helperFunctions';

export async function load() {
    const data = parseSparqlResult(await fetchSparqlAnthologyData());

    const venueMap = new Map<string, { years: Set<string>; label: string; id: string }>();

    for (const binding of data) {
        const venueName = binding.venue_URI;
        if (venueName === null) continue;

        if (!venueMap.has(venueName)) {
            const dblpId = getIDFromURI(binding.venue_URI ?? '');
            venueMap.set(venueName, {
                years: new Set(),
                label: dblpId.split('+').at(-1)?.toUpperCase() ?? '',
                id: dblpId
            });
        }

        if (binding.year_label !== null) {
            venueMap.get(venueName)!.years.add(binding.year_label);
        }
    }

    const venues = [...venueMap.values()].map(v => ({ ...v, years: [...v.years] }));

    return { venues };
}
