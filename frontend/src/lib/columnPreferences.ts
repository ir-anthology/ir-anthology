import { browser } from '$app/environment';

const STORAGE_KEY = 'ir-anthology-column-preferences';

// prefs[entity] stores an explicit column selection; a missing key means
// "all columns the entity's endpoint returns". Stale entries (removed columns,
// old entities) are neutralized by intersecting with the available columns
// at render time
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
