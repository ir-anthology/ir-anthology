import { fetchBackend } from '$lib/sparql/fetch.js'
import { browser } from '$app/environment'
import { ENTITY_ENDPOINTS, resolveEntity, sanitizeTableParams } from '$lib/tableConfig'

export const prerender = true;

export async function load({ url }) {
    const entity = resolveEntity(browser ? url.searchParams.get('entity') : null);
    const params = sanitizeTableParams(browser ? url.searchParams.toString() : '');
    return fetchBackend(`${ENTITY_ENDPOINTS[entity]}?${params}`);
}
