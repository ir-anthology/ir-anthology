import { fetchDebug } from '$lib/sparql/fetch.server';

export async function load() {
    return fetchDebug();
}
