# IR Anthology — Frontend

SvelteKit 5 static site for the IR Anthology. Built with the static adapter: all `/anthology/*` pages and the home page are prerendered to HTML at build time; the admin, login, and callback routes run client-side only via the `404.html` SPA fallback.

## Tech stack

| Concern | Tool |
|---|---|
| Framework | SvelteKit 2 + Svelte 5 (runes mode) |
| Language | TypeScript 6, strict mode |
| Styling | Tailwind CSS 4 |
| Package manager | pnpm 11 |
| Node version | 24.16.0 (pinned in `package.json`) |
| Build output | `@sveltejs/adapter-static`, fallback `404.html` |
| Auth | `oidc-client-ts` — GitLab OIDC |

## Project structure

```
src/
├── lib/
│   ├── auth.ts               OIDC userManager + login/logout helpers
│   ├── helperFunctions.ts    getIDFromURI, slugifyName, parseSparqlResult, …
│   ├── sparql/
│   │   └── fetch.ts          fetchBackend() + typed admin API wrappers
│   └── components/
│       ├── DataTable.svelte  home page entity table
│       ├── SearchBar.svelte  entity/sort selector
│       ├── FilterField.svelte
│       └── ResetButton.svelte
└── routes/
    ├── +layout.svelte        nav bar, footer, OIDC user state
    ├── +page.{svelte,ts}     home — prerendered
    ├── anthology/
    │   ├── +layout.ts        export const prerender = true  (cascades to all sub-routes)
    │   ├── +page.{svelte,ts} venue table
    │   ├── venues/[name]/
    │   ├── venues/[name]/[year]/
    │   ├── people/[name]/[id]/
    │   ├── publications/[name]/
    │   └── info/credits/
    ├── admin/                ssr = false, requires GitLab admin group
    ├── login/                ssr = false
    └── callback/             ssr = false, completes OIDC flow → /admin
```

## Configuration

### Backend endpoint

All data fetches go through `src/lib/sparql/fetch.ts`:

```ts
const BACKEND_ENDPOINT = 'https://backend-ir-anthology.web.webis.de/api/';
```

This is hardcoded. The dev server uses the **production backend** — there is no dev proxy. To target a local backend, change this constant temporarily; do not commit the change.

### Base path

GitHub Pages serves the site from a subpath. The build reads `BASE_PATH` from the environment and passes it to SvelteKit's `paths.base`:

```sh
BASE_PATH=/my-subpath pnpm build
```

The GitHub Actions workflow sets this automatically via `actions/configure-pages`. Leave it unset for a root-path deployment.

## Commands

```sh
pnpm install --frozen-lockfile   # install dependencies (exact versions from lockfile)
pnpm run dev --host              # dev server on localhost:5173
pnpm build                       # prerender + static build → build/
pnpm preview                     # serve build/ locally
pnpm check                       # svelte-check (TypeScript + Svelte diagnostics)
pnpm lint                        # prettier + eslint
pnpm format                      # auto-format with prettier
pnpm test                        # vitest (unit + browser/component tests via Playwright)
```

### Offline install

Every dependency is committed in `.pnpm-store/` (`storeDir` in `pnpm-workspace.yaml`), so
the frontend can be installed without npm — with no network at all, or after packages
have disappeared from the registry. Node 24.16.0 is the only prerequisite; pnpm itself is
vendored too and is run straight from the store:

```sh
node .pnpm-store/v11/links/@/pnpm/11.0.9/69b4330841477b4191f1e88a72413980ce1c09d4f6922c493cf13b8109a4a84c/node_modules/pnpm/bin/pnpm.mjs \
  install --frozen-lockfile --offline
```

Use that path rather than a globally installed `pnpm`: a newer global pnpm first tries to
switch to the pinned 11.0.9, and newer pnpm 11 releases (e.g. 11.7) also check package
release dates against the registry before installing — both need the network.

The store only covers what was installed when it was last committed. After changing
dependencies, run an online `pnpm install` and commit the new files under `.pnpm-store/`
together with `pnpm-lock.yaml` — including `v11/index.db`, without which pnpm cannot find
any of them. Bumping `packageManager` also needs the new pnpm's `links/@/pnpm/<version>/`
directory committed and the path above updated.

## Prerendering

`svelte.config.js` options:

```js
prerender: {
    concurrency: 50,  // simultaneous page renders
    crawl: false,     // only render URLs declared in entries()
    handleHttpError: ({ path, message }) => console.warn(...)
}
```

Because `crawl: false`, every dynamic route must export an `entries()` function in its `+page.ts` that returns all parameter combinations. The four dynamic route groups each call the backend to enumerate their pages:

| Route | entries() fetches |
|---|---|
| `venues/[name]` | `conferences`, `journals`, `workshops` |
| `venues/[name]/[year]` | all of the above |
| `people/[name]/[id]` | `people` |
| `publications/[name]` | `publications` |

The **backend must be reachable** when `pnpm build` runs. If a page fails to render, `handleHttpError` logs a warning and the build continues — the page is simply omitted from the output.

## Authentication

The admin panel is protected by GitLab OIDC (`git.webis.de`). Auth state is stored in `localStorage` via `oidc-client-ts` and is never sent to the SvelteKit server.

- **Login** — `src/lib/auth.ts` → `userManager.signinRedirect()` → GitLab → `/callback` → `/admin`
- **Logout** — `removeUser()` clears localStorage and fires `userUnloaded` (updates nav immediately), then `signoutRedirect()` invalidates the GitLab session
- **Admin check** — the `groups_direct` claim in the OIDC token must include `auth/auth-webis-admin`

## ID encoding

DBLP URIs (`https://dblp.org/rec/...`) are encoded as route parameters by replacing `/` with `+`. The helpers in `src/lib/helperFunctions.ts` handle the conversion:

```ts
getIDFromURI('https://dblp.org/rec/conf/sigir/Smith23')
// → 'rec+conf+sigir+Smith23'

getURIFromID('rec+conf+sigir+Smith23')
// → 'https://dblp.org/rec/conf/sigir/Smith23'
```

Author URLs use a human-readable slug as the first segment (`/people/[name]/[id]`), generated by `slugifyName()` which lowercases, strips diacritics, and replaces spaces with hyphens.
