import type { SparqlResult } from './sparql/fetch.js';

export function parseSparqlResult(result: SparqlResult): Record<string, string | null>[] {
    return result.bindings.map(binding => {
        const entry: Record<string, string | null> = {};
        for (const key of result.vars) {
            entry[key] = binding[key]?.value ?? null;
        }
        return entry;
    });
}

export function getIDFromURI(dblp_uri: string){
    return dblp_uri.replace("https://dblp.org/", "").replaceAll("/","+")
}

export function getURIFromID(ir_id: string){
    return "https://dblp.org/"+ir_id.replaceAll("+", "/")
}

export function decodeOrdered(raw: string | null, stripDisambig = false): string[] {
    if (!raw) return []
    return raw
        .split(', ')
        .map(entry => {
            const sep = entry.indexOf('@@')
            return { ord: parseInt(entry.slice(0, sep), 10), value: entry.slice(sep + 2) }
        })
        .sort((a, b) => a.ord - b.ord)
        .map(e => stripDisambig ? e.value.replace(/\s+\d+$/, '') : e.value)
}