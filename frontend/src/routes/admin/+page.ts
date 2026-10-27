import { redirect } from '@sveltejs/kit';
import { resolve } from '$app/paths';
import { getUser } from '$lib/auth';

export const ssr = false;

export async function load() {
    const user = await getUser();
    if (!user || user.expired) {
        throw redirect(302, resolve('/login'));
    }
    return { user };
}