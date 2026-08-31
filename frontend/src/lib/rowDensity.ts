import { browser } from '$app/environment';

const STORAGE_KEY = 'ir-anthology-row-density';
export type Density = 'normal' | 'compact' | 'dense';

export function loadDensity(): Density {
	if (!browser) return 'normal';
	try {
		const stored = localStorage.getItem(STORAGE_KEY);
		if (stored === 'compact' || stored === 'dense' || stored === 'normal') return stored;
		return 'normal';
	} catch {
		return 'normal';
	}
}

export function saveDensity(density: Density): void {
	if (!browser) return;
	try {
		localStorage.setItem(STORAGE_KEY, density);
	} catch {
		// localStorage unavailable, silently fail
	}
}
