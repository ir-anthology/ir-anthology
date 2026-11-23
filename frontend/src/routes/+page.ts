import { browser } from '$app/environment';
import { fetchBackend } from '$lib/sparql/fetch';
import type { Stats } from '$lib/stats';

// Prerendered with the totals of build time, so the page shows numbers immediately;
// the page then refreshes them in the browser (see +page.svelte).
export const prerender = true;

export async function load() {
	try {
		const stats: Stats = await fetchBackend('stats');
		return { stats, fetchedInBrowser: browser };
	} catch {
		// A landing page without numbers beats a failed build or an error page.
		return { stats: null, fetchedInBrowser: browser };
	}
}
