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

// Must match the default_sort/default_order each backend endpoint applies when
// no sort params are present — only used for the header sort indicators.
const ENTITY_DEFAULT_SORT: Record<string, { sort_by: string; order: string }> = {
	Author: { sort_by: 'Publications', order: 'desc' },
	Venue: { sort_by: 'Entity', order: 'asc' },
	Year: { sort_by: 'Entity', order: 'desc' },
	Publication: { sort_by: 'Year', order: 'desc' },
};

// With active filters the backend defaults to sorting by Entity instead
// (desc for years, asc otherwise).
export function entityDefaultSort(entity: string, filtered: boolean): { sort_by: string; order: string } {
	if (filtered) return { sort_by: 'Entity', order: entity === 'Year' ? 'desc' : 'asc' };
	return ENTITY_DEFAULT_SORT[entity];
}

// Column headers are plural (counts) or value columns; entity names, URL params,
// and filter keys stay singular. This maps a column to the entity it represents.
const COLUMN_ENTITY: Record<string, string> = {
	Publications: 'Publication',
	Venues: 'Venue',
	Authors: 'Author',
	Years: 'Year',
	Venue: 'Venue',
	Year: 'Year',
};

export function columnEntity(col: string): string {
	return COLUMN_ENTITY[col] ?? col;
}

// filter_<X> params the backend templates bind a label variable for
export const FILTERABLE_ENTITIES = ['Author', 'Venue', 'Publication', 'Year'];

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

// Builds the query params for a table request. The backend applies exactly what it
// receives (no sorting policy there), so when the page URL carries no explicit sort,
// the entity's default is injected here. Runs identically in the browser and during
// prerendering (where the source is always the empty string).
export function tableRequestParams(source: string): URLSearchParams {
	const entity = resolveEntity(new URLSearchParams(source).get('entity'));
	const params = sanitizeTableParams(source);
	if (!params.has('sort_by')) {
		const filtered = FILTERABLE_ENTITIES.some((f) => params.has(`filter_${f}`));
		const def = entityDefaultSort(entity, filtered);
		params.set('sort_by', def.sort_by);
		params.set('order', def.order);
	}
	return params;
}
