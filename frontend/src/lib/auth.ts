import { UserManager, WebStorageStateStore } from 'oidc-client-ts';
import { browser } from '$app/environment';
import { base } from '$app/paths';

// Replace with your GitLab instance URL if self-hosted
const GITLAB = 'https://git.webis.de';

export const userManager = browser ? new UserManager({
    authority: GITLAB,
    client_id: '88b027bbd3071aaf8a1aead13c46288fbdcdace35eaa8a3c32d0c4f372bf8feb',
    redirect_uri: window.location.origin + base + '/callback',
    scope: 'openid profile',
    extraQueryParams: {
        claims: JSON.stringify({ id_token: { groups_direct: null }, userinfo: { groups_direct: null } }),
    },
    userStore: new WebStorageStateStore({ store: window.localStorage }),
}) : null;

export const login  = () => userManager?.signinRedirect();
export const logout = () => userManager?.signoutRedirect();
export const getUser = () => userManager?.getUser();
export const getToken = () => getUser().then(u => u?.access_token ?? null);
export const getIdToken = () => getUser()?.then(u => u?.id_token ?? null);