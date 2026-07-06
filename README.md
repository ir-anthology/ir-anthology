# IR Anthology

The IR Anthology is a grassroots initative run entirely by contributions from volunteers, powered by data from [DBLP](https://dblp.org).

## Structure

Three independently deployable components:

| Directory | Stack | Deployed as |
|---|---|---|
| `frontend/` | SvelteKit 5, TypeScript, Tailwind CSS 4 | Prerendered static build |
| `backend/` | FastAPI, Python 3.14, uvicorn | Docker image |
| `database/` | [QLever SPARQL engine](https://github.com/ad-freiburg/qlever) | Docker image |

## Development Setup

**Prerequisites:** [VS Code](https://code.visualstudio.com/) with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers), or [GitHub Codespaces](https://github.com/features/codespaces).

Open the repository in VS Code and choose **Reopen in Container** when prompted. The devcontainer (`.devcontainer/`) sets everything up automatically:

- Node.js 24 and Python 3.14 are included in the base image
- `PostCreate.sh` installs the `qlever` CLI and `fastapi[standard]` via pip
- Environment variables `DATA_PATH` and `SPARQL_ACCESS_TOKEN=1234` are pre-set
- Port 7016 (QLever SPARQL endpoint) is forwarded to the host

### Database

Run from the `database/` directory. The `Qleverfile` in that directory configures all options.

```sh
# First time only — downloads data from sparql.dblp.org (~15 min) and builds the index:
qlever get-data
qlever index

# Every time — starts the SPARQL server on localhost:7016:
qlever start
```

### Backend

Run from the `backend/` directory. The API is served on `localhost:8000` and queries the local QLever instance at `localhost:7016`.

```sh
fastapi dev main.py
```

### Frontend

Run from the `frontend/` directory.

```sh
pnpm install --frozen-lockfile  # first time only
pnpm run dev --host             # dev server on localhost:5173
```

The frontend dev server calls the **production backend** (`https://backend-ir-anthology.web.webis.de/api/`) by default — the endpoint is hardcoded in `src/lib/sparql/fetch.ts`. Starting the local backend is only necessary when developing backend features.
