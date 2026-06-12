import { error } from '@sveltejs/kit';

//const BACKEND_ENDPOINT = 'https://backend-ir-anthology.srv.webis.de/api/';
const BACKEND_ENDPOINT = 'http://localhost:8000/api/'

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