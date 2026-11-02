<script lang="ts">
	import { venueTypeColorClass } from '$lib/venueType';

	// Optional: the year page's load() has no else branch for an unrecognised venue
	// name, so `data.venueType` is legitimately `string | undefined` there. Render
	// nothing rather than a badge with a wrong default letter.
	let { type }: { type?: string } = $props();
</script>

<!--
	Title-sized counterpart to the small chip in DataTable's Entity column. w-9/h-9 is
	36px, exactly text-3xl's line-height, so the badge matches the height of the page
	titles it sits in front of. The parent <h1> aligns it with `items-start` rather
	than `items-center` so it stays on the first line when a long title wraps.
-->
{#if type}
	<span
		class="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-current/20 text-lg font-bold {venueTypeColorClass(type)}"
		title={type}
	>{type[0]}</span>
{/if}
