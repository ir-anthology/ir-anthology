import { json } from '@sveltejs/kit';
import { fetchBackend } from '$lib/sparql/fetch.js';

export async function GET({ url }) {
    const data = await fetchBackend(`table?${url.searchParams}`);
    return json(data);
}