// Response of GET /api/stats (backend main.read_stats): per entity, the number of
// rows of its unfiltered table, keyed like ENTITY_ENDPOINTS; plus the earliest year.
export type Stats = {
	counts: Record<string, number>;
	first_year: number;
};
