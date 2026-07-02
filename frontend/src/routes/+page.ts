import { fetchBackend } from '$lib/sparql/fetch.js'
import { browser } from '$app/environment'

export const prerender = true;

export async function load({ url }) {
    const params = browser ? url.searchParams.toString() : '';
    return fetchBackend(`table?${params}`);
}
