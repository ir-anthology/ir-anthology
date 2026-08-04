import { DEBUG } from '$lib/sparql/fetch';

const EXTERNAL_API_BASE = 'http://192.168.10.65:8080';

type SparqlEnvelope = { vars: string[]; bindings: Record<string, { type: string; value: string }>[] };

export type Observation = { title: string; description: string; evidence: string };
export type ObservationsResponse = { has_data: boolean; observations: Observation[]; note: string };

export type FollowupQuestion = { question: string; url: string };
export type FollowupResponse = { followup_questions: FollowupQuestion[] };

export type QueryAction = { title: string; url: string; primary: boolean };
export type QueryResponse = { supported: boolean; reason: string | null; actions: QueryAction[] };

export async function fetchObservations(sparqlData: SparqlEnvelope): Promise<ObservationsResponse> {
	if (DEBUG) console.log('[DEBUG] → POST', 'observations');
	const response = await fetch(`${EXTERNAL_API_BASE}/api/observations`, {
		method: 'POST',
		headers: { 'Content-Type': 'text/plain' },
		body: JSON.stringify(sparqlData),
		signal: AbortSignal.timeout(120000),
	});
	if (!response.ok) {
		throw new Error(`Observations request failed (${response.status})`);
	}
	const data = await response.json();
	if (DEBUG) console.log('[DEBUG] ←', 'observations', data);
	return data;
}

export async function fetchFollowup(sparqlData: SparqlEnvelope): Promise<FollowupResponse> {
	if (DEBUG) console.log('[DEBUG] → POST', 'followup');
	const response = await fetch(`${EXTERNAL_API_BASE}/api/followup`, {
		method: 'POST',
		headers: { 'Content-Type': 'text/plain' },
		body: JSON.stringify(sparqlData),
		signal: AbortSignal.timeout(120000),
	});
	if (!response.ok) {
		throw new Error(`Followup request failed (${response.status})`);
	}
	const data = await response.json();
	if (DEBUG) console.log('[DEBUG] ←', 'followup', data);
	return data;
}

export async function fetchQuery(query: string): Promise<QueryResponse> {
	if (DEBUG) console.log('[DEBUG] → POST', 'query', query);
	const response = await fetch(`${EXTERNAL_API_BASE}/api/query`, {
		method: 'POST',
		headers: { 'Content-Type': 'text/plain' },
		body: query,
		signal: AbortSignal.timeout(30000),
	});
	if (!response.ok) {
		throw new Error(`Query request failed (${response.status})`);
	}
	const data = await response.json();
	if (DEBUG) console.log('[DEBUG] ←', 'query', data);
	return data;
}
