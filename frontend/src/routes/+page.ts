import { fetchBackend } from '$lib/sparql/fetch.js'

export async function load({ url }) {
    return fetchBackend(`table?${url.searchParams}`);
}
