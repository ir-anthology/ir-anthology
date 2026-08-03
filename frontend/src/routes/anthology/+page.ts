import { fetchBackend } from '$lib/sparql/fetch.js'
import { DEBUG } from '$lib/sparql/fetch.js'
import { browser } from '$app/environment'
import { ENTITY_ENDPOINTS, resolveEntity, tableRequestParams } from '$lib/tableConfig'

export const prerender = true;

export async function load({ url }) {
    const entity = resolveEntity(browser ? url.searchParams.get('entity') : null);
    const params = tableRequestParams(browser ? url.searchParams.toString() : '');
    const endpoint = `${ENTITY_ENDPOINTS[entity]}?${params}`;
    if (DEBUG) console.log('[DEBUG] load:', entity, endpoint);
    const data = await fetchBackend(endpoint);
    if (DEBUG) console.log('[DEBUG] result:', data);
    return data;
}
