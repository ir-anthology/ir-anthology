import { fetchBackend } from '$lib/sparql/fetch.js';

export async function load() {
    return fetchBackend('debug');
}
