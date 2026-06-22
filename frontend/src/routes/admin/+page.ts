import { redirect } from '@sveltejs/kit';
import { getUser } from '$lib/auth';

export const ssr = false;

export async function load() {
    const user = await getUser();
    if (!user || user.expired) {
        throw redirect(302, '/login');
    }
    return { user };
}