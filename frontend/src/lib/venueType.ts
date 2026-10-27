// Venue-type chip colours, shared by the small badge in the DataTable's Entity cell
// and the title-sized VenueTypeBadge on the venue detail pages.
//
// The backend only ever binds VenueType as "Conference" or "Journal" (see
// sparqlTemplates.py) — the synthetic Workshops aggregate has no VenueType triple
// at all, so anything that isn't one of those two is treated as a workshop.
export function venueTypeColorClass(type: string): string {
	if (type === 'Conference') return 'bg-blue-100 text-blue-800';
	if (type === 'Journal') return 'bg-amber-100 text-amber-800';
	return 'bg-green-100 text-green-800';
}
