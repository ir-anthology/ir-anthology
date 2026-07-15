import { fetchBackend } from '$lib/sparql/fetch.js'
import { browser } from '$app/environment'
import { ENTITY_ENDPOINTS, resolveEntity, tableRequestParams } from '$lib/tableConfig'

export const prerender = true;

export async function load({ url }) {
    const entity = resolveEntity(browser ? url.searchParams.get('entity') : null);
    const params = tableRequestParams(browser ? url.searchParams.toString() : '');
    return fetchBackend(`${ENTITY_ENDPOINTS[entity]}?${params}`);
}
