import { fetchBackend } from '$lib/sparql/fetch.js'
import { parseSparqlResult, decodeOrdered } from '$lib/helperFunctions.js';

export async function load({ params }) {
    const data = parseSparqlResult(await fetchBackend("people/"+params.id));
    const name = data[0]?.name ?? ''
    const groupedByYear = new Map<string, Record<string, string | null>[]>()
    for (const pub of data) {
        pub.authors = decodeOrdered(pub.authors, true).join(', ')
        pub.authorIds = decodeOrdered(pub.authorIds).join(', ')

        if (pub.booktitle == null && pub.streamTitle != null) {
            let label = pub.streamTitle + ' ' + pub.year
            if (pub.journalVolume != null) label += ' Volume ' + pub.journalVolume
            if (pub.journalNumber != null) label += ' Issue ' + pub.journalNumber
            pub.booktitle = label
        }

        const y = pub.year ?? ''
        if (!groupedByYear.has(y)) groupedByYear.set(y, [])
        groupedByYear.get(y)!.push(pub)
    }
    const sorted = new Map([...groupedByYear.entries()].sort((a, b) => parseInt(b[0]) - parseInt(a[0])))
    return { name, pubsByYear: sorted }
}
