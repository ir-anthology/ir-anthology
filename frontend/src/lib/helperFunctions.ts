import type { SparqlResult } from './sparql/fetch.server.js';

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