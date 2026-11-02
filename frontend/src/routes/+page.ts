import { redirect } from '@sveltejs/kit';
import { base } from '$app/paths';

export const prerender = true;

export function load() {
    redirect(308, `${base}/anthology`);
}
