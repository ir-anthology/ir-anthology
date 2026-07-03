import { error } from '@sveltejs/kit';

const BACKEND_ENDPOINT = 'https://backend-ir-anthology.web.webis.de/api/';
export async function fetchBackend(resource: string, retries = 3) {
    let lastStatus = 500;
    for (let attempt = 0; attempt < retries; attempt++) {
        if (attempt > 0) await new Promise(r => setTimeout(r, 500 * attempt));
        try {
            const response = await fetch(BACKEND_ENDPOINT + resource, {
                method: 'GET',
                headers: { 'Accept': 'application/json' },
                signal: AbortSignal.timeout(30000),
            });
            if (response.ok) return response.json();
            lastStatus = response.status;
        } catch {
            // network error, retry
        }
    }
    error(lastStatus, { message: `Could not get resource ${resource} from backend after ${retries} attempts` });
}
export type SparqlResult = {
    vars: string[];
    bindings: Record<string, { type: string; value: string }>[];
};

export type ImportResult = { filename: string; triples: number; live_applied: boolean };

export type PatchRecord = {
    filename: string;
    timestamp?: string;
    user_name?: string;
    user_email?: string;
    action?: string;
    details?: Record<string, unknown>;
    triples?: number;
    live_applied?: boolean;
};
export type WorkshopProceeding = { proc: string; title: string; year: string };

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

export async function fetchPatches(token?: string | null): Promise<PatchRecord[]> {
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

export async function previewCustomWorkshop(
    abbreviation: string,
    title: string,
    year?: number,
    token?: string | null,
): Promise<{ proceedings: WorkshopProceeding[] }> {
    const body: Record<string, unknown> = { abbreviation, title };
    if (year !== undefined) body.year = year;

    const res = await fetch(BACKEND_ENDPOINT + 'admin/workshop/custom/preview', {
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

export async function importCustomWorkshop(
    abbreviation: string,
    title: string,
    year: number | undefined,
    proc_iris: string[],
    token?: string | null,
): Promise<ImportResult> {
    const body: Record<string, unknown> = { abbreviation, title, proc_iris };
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