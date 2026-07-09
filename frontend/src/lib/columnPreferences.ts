import { browser } from '$app/environment';

const STORAGE_KEY = 'ir-anthology-column-preferences';

export const DEFAULT_COLUMNS: Record<string, string[]> = {
	Author: ['Publication', 'Venue', 'Years'],
	Venue: ['Publication', 'Author', 'Years'],
	Publication: ['Author', 'Years'],
	Year: ['Publication', 'Author', 'Venue'],
	'2020s': ['Publication', 'Author', 'Venue'],
	'2010s': ['Publication', 'Author', 'Venue'],
	'2000s': ['Publication', 'Author', 'Venue'],
	Pre2000s: ['Publication', 'Author', 'Venue'],
};

export const ALL_COLUMNS = ['Publication', 'Venue', 'Author', 'Year', '2020s', '2010s', '2000s', 'Pre2000s', 'Years'];

export function getVisibleColumns(entity: string, userPrefs?: Record<string, string[]>): string[] {
	const prefs = userPrefs?.[entity] ?? DEFAULT_COLUMNS[entity] ?? ALL_COLUMNS;
	return prefs.filter((col) => ALL_COLUMNS.includes(col));
}

export function loadPreferences(): Record<string, string[]> {
	if (!browser) return {};
	try {
		const stored = localStorage.getItem(STORAGE_KEY);
		if (!stored) return {};
		const parsed = JSON.parse(stored);
		if (typeof parsed !== 'object' || parsed === null) return {};
		return parsed;
	} catch {
		return {};
	}
}

export function savePreferences(prefs: Record<string, string[]>): void {
	if (!browser) return;
	try {
		localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
	} catch {
		// localStorage unavailable, silently fail
	}
}
