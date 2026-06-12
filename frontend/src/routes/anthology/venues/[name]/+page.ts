import { fetchBackend } from '$lib/sparql/fetch.js'
import { parseSparqlResult } from '$lib/helperFunctions.js';

export async function load({ params }) {
    const name = params.name

    if (name.includes('journals')) {
        return loadJournal(name)
    } else {
        return loadConference(name)
    }
}

async function loadConference(venueId: string) {
    const raw = parseSparqlResult(await fetchBackend("conferences/"+venueId))
    const streamTitle = raw[0]?.streamTitle ?? ''
    const groupedByYear = new Map<string, { title: string, pub: string, count: number }[]>()
    for (const entry of raw) {
        const y = entry.year ?? ''
        if (!groupedByYear.has(y)) groupedByYear.set(y, [])
        groupedByYear.get(y)!.push({
            title: entry.title ?? '',
            pub: entry.pub ?? '',
            count: parseInt(entry.count ?? '0', 10)
        })
    }
    const sorted = new Map([...groupedByYear.entries()].sort((a, b) => parseInt(b[0]) - parseInt(a[0])))
    return { type: 'conference', name: streamTitle, yearGroups: sorted, venue_id: venueId }
}

async function loadJournal(id: string) {
    const raw = parseSparqlResult(await fetchBackend("journals/"+id))
    const journalTitle = raw[0]?.journalTitle ?? ''
    const groupedByYear = new Map<string, { volume: string | null, number: string | null, count: number }[]>()
    for (const entry of raw) {
        const y = entry.year ?? ''
        if (!groupedByYear.has(y)) groupedByYear.set(y, [])
        groupedByYear.get(y)!.push({
            volume: entry.volume,
            number: entry.number,
            count: parseInt(entry.count ?? '0', 10)
        })
    }
    const sorted = new Map([...groupedByYear.entries()].sort((a, b) => parseInt(b[0]) - parseInt(a[0])))
    return { type: 'journal', articles: sorted, journalTitle }
}
