import { error } from '@sveltejs/kit';

const BACKEND_ENDPOINT = 'https://backend-ir-anthology.srv.webis.de/api/';

export async function fetchBackend(resource: string) {
    const response = await fetch(BACKEND_ENDPOINT+resource, {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
        },
    });
    if (!response.ok) {
        error(response.status, { message: 'Could not get resource from backend' });
    }
    return response.json();
}
export type SparqlResult = {
    vars: string[];
    bindings: Record<string, { type: string; value: string }>[];
};

export type ImportResult = { filename: string; triples: number; live_applied: boolean };

export async function importFromDblp(
    iri: string,
    type: string,
    year?: number,
    token?: string | null,
): Promise<ImportResult> {
    const body: Record<string, unknown> = { iri, type };
    if (year !== undefined) body.year = year;

    const res = await fetch(BACKEND_ENDPOINT + 'admin/import', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(body),
    });

    if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail?.detail ?? `Request failed (${res.status})`);
    }
    return res.json();
}

export async function fetchPatches(token?: string | null): Promise<string[]> {
    const res = await fetch(BACKEND_ENDPOINT + 'admin/patches', {
        headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
    });
    if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail?.detail ?? `Request failed (${res.status})`);
    }
    const data = await res.json();
    return data.patches;
}

export async function importCustomWorkshop(
    abbreviation: string,
    title: string,
    year?: number,
    token?: string | null,
): Promise<ImportResult> {
    const body: Record<string, unknown> = { abbreviation, title };
    if (year !== undefined) body.year = year;

    const res = await fetch(BACKEND_ENDPOINT + 'admin/workshop/custom', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(body),
    });

    if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail?.detail ?? `Request failed (${res.status})`);
    }
    return res.json();
}