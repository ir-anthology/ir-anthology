import { fetchBackend } from '$lib/sparql/fetch.js'
import { DEBUG } from '$lib/sparql/fetch.js'
import { parseSparqlResult, getIDFromURI } from '$lib/helperFunctions.js';

export async function entries() {
    const [conferences, journals, workshops] = await Promise.all([
        fetchBackend("conferences"),
        fetchBackend("journals"),
        fetchBackend("workshops")
    ]);
    const ids = new Set<string>();
    for (const row of parseSparqlResult(conferences)) {
        if (row.stream) ids.add(getIDFromURI(row.stream));
    }
    for (const row of parseSparqlResult(journals)) {
        if (row.stream) ids.add(getIDFromURI(row.stream));
    }
    if (parseSparqlResult(workshops).length > 0) ids.add('workshops');
    return [...ids].map(name => ({ name }));
}

export async function load({ params }) {
    const name = params.name
    if (name === "workshops"){
        return loadWorkshops()
    } else if (name.includes('journals')) {
        return loadJournal(name)
    } else {
        return loadConference(name)
    }
}

async function loadConference(venueId: string) {
    if (DEBUG) console.log('[DEBUG] venue/loadConference:', venueId);
    const raw = parseSparqlResult(await fetchBackend("conferences/"+venueId))
    const streamTitle = raw[0]?.streamTitle ?? ''

    // Collect proceedings metadata (title + year) keyed by proceedings URI
    const procInfo = new Map<string, { title: string; year: string }>()
    // Count inproceedings per proceedings URI
    const paperCount = new Map<string, number>()
    // Count loose inproceedings (no proc link) per year
    const loosePapers = new Map<string, number>()

    for (const entry of raw) {
        const type = entry.type ?? ''
        const pub = entry.pub ?? ''
        const year = entry.year ?? ''
        if (type.endsWith('#Proceedings')) {
            procInfo.set(pub, { title: entry.title ?? '', year })
        } else {
            if (entry.proc) {
                paperCount.set(entry.proc, (paperCount.get(entry.proc) ?? 0) + 1)
            } else {
                loosePapers.set(year, (loosePapers.get(year) ?? 0) + 1)
            }
        }
    }

    const groupedByYear = new Map<string, { title: string; pub: string; count: number }[]>()

    for (const [procUri, { title, year }] of procInfo) {
        if (!groupedByYear.has(year)) groupedByYear.set(year, [])
        groupedByYear.get(year)!.push({ title, pub: procUri, count: paperCount.get(procUri) ?? 0 })
    }

    // Sort proceedings within each year alphabetically, then append loose papers last
    for (const entries of groupedByYear.values()) {
        entries.sort((a, b) => a.title.localeCompare(b.title))
    }

    for (const [year, count] of loosePapers) {
        if (!groupedByYear.has(year)) groupedByYear.set(year, [])
        groupedByYear.get(year)!.push({ title: '', pub: '', count })
    }

    const sorted = new Map([...groupedByYear.entries()].sort((a, b) => parseInt(b[0]) - parseInt(a[0])))
    const result = { type: 'conference', name: streamTitle, yearGroups: sorted, venue_id: venueId };
    if (DEBUG) console.log('[DEBUG] venue/loadConference →', result);
    return result;
}

async function loadJournal(id: string) {
    if (DEBUG) console.log('[DEBUG] venue/loadJournal:', id);
    const raw = parseSparqlResult(await fetchBackend("journals/"+id))
    const journalTitle = raw[0]?.journalTitle ?? ''
    const groupedByYear = new Map<string, { volume: string | null, number: string | null, count: number }[]>()
    for (const entry of raw) {
        const y = entry.year ?? ''
        if (!groupedByYear.has(y)) groupedByYear.set(y, [])
        groupedByYear.get(y)!.push({
            volume: entry.volume ?? "-1",
            number: entry.number ?? "0",
            count: parseInt(entry.count ?? '0', 10)
        })
    }
    const sorted = new Map([...groupedByYear.entries()].sort((a, b) => parseInt(b[0]) - parseInt(a[0])))
    const result = { type: 'journal', articles: sorted, journalTitle };
    if (DEBUG) console.log('[DEBUG] venue/loadJournal →', result);
    return result;
}

async function loadWorkshops() {
    if (DEBUG) console.log('[DEBUG] venue/loadWorkshops');
    const raw = parseSparqlResult(await fetchBackend("workshops/proceedings"))
    const streamTitle = raw[0]?.streamTitle ?? ''

    const procInfo = new Map<string, { title: string; year: string }>()
    const paperCount = new Map<string, number>()
    const loosePapers = new Map<string, number>()

    for (const entry of raw) {
        const type = entry.type ?? ''
        const pub = entry.pub ?? ''
        const year = entry.year ?? ''
        if (type.endsWith('#Proceedings')) {
            procInfo.set(pub, { title: entry.title ?? '', year })
        } else {
            if (entry.proc) {
                paperCount.set(entry.proc, (paperCount.get(entry.proc) ?? 0) + 1)
            } else {
                loosePapers.set(year, (loosePapers.get(year) ?? 0) + 1)
            }
        }
    }

    const groupedByYear = new Map<string, { title: string; pub: string; count: number }[]>()

    for (const [procUri, { title, year }] of procInfo) {
        if (!groupedByYear.has(year)) groupedByYear.set(year, [])
        groupedByYear.get(year)!.push({ title, pub: procUri, count: paperCount.get(procUri) ?? 0 })
    }

    for (const entries of groupedByYear.values()) {
        entries.sort((a, b) => a.title.localeCompare(b.title))
    }

    for (const [year, count] of loosePapers) {
        if (!groupedByYear.has(year)) groupedByYear.set(year, [])
        groupedByYear.get(year)!.push({ title: '', pub: '', count })
    }

    const sorted = new Map([...groupedByYear.entries()].sort((a, b) => parseInt(b[0]) - parseInt(a[0])))
    const result = { type: 'conference', name: streamTitle, yearGroups: sorted, venue_id: "workshops" };
    if (DEBUG) console.log('[DEBUG] venue/loadWorkshops →', result);
    return result;
}