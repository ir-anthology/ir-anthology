// Single source of truth for the table entities and their backend endpoints.
// Adding a new entity means adding
// one entry here — dropdown options, endpoint routing, and cell clickability
// all derive from this map.
export const ENTITY_ENDPOINTS: Record<string, string> = {
	Author: 'table/authors',
	Venue: 'table/venues',
	Year: 'table/years',
	Publication: 'table/publications',
};

export const DEFAULT_ENTITY = 'Venue';

// filter_<X> params the backend templates bind a label variable for
const FILTERABLE_ENTITIES = ['Author', 'Venue', 'Publication', 'Year'];

export function resolveEntity(param: string | null): string {
	return param !== null && param in ENTITY_ENDPOINTS ? param : DEFAULT_ENTITY;
}

// Strips params the per-entity endpoints don't understand: the entity selector
// itself and filter keys without a matching label variable (e.g. old decade
// filters), which would otherwise make the SPARQL query fail.
export function sanitizeTableParams(source: string): URLSearchParams {
	const params = new URLSearchParams(source);
	params.delete('entity');
	for (const key of [...params.keys()]) {
		if (key.startsWith('filter_') && !FILTERABLE_ENTITIES.includes(key.slice('filter_'.length))) {
			params.delete(key);
		}
	}
	return params;
}
