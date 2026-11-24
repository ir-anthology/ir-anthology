<script module lang="ts">
	// The count-up plays once per browser-tab session: coming back from the matrix
	// (or reloading) shows the numbers straight away. sessionStorage is cleared when
	// the tab closes; the module variable covers browsers where it throws (e.g.
	// storage blocked), for as long as the app stays loaded.
	const COUNTED_UP_KEY = 'ir-anthology:landing-counted-up';
	let countedUp = false;

	function hasCountedUp(): boolean {
		if (countedUp) return true;
		try {
			return sessionStorage.getItem(COUNTED_UP_KEY) === '1';
		} catch {
			return false;
		}
	}

	function markCountedUp() {
		countedUp = true;
		try {
			sessionStorage.setItem(COUNTED_UP_KEY, '1');
		} catch {
			// the module variable still covers this page load
		}
	}
</script>

<script lang="ts">
	import { onMount, untrack } from 'svelte';
	import { browser } from '$app/environment';
	import { Tween, prefersReducedMotion } from 'svelte/motion';
	import { quartOut } from 'svelte/easing';
	import { resolve } from '$app/paths';
	import { fetchBackend } from '$lib/sparql/fetch';
	import { groupDigits } from '$lib/helperFunctions';
	import { ENTITY_LABELS } from '$lib/tableConfig';
	import type { Stats } from '$lib/stats';

	let { data } = $props();

	// Order of the 2x2 grid: reading order left to right, top to bottom.
	const ENTITIES = ['Publication', 'Venue', 'Author', 'Year'];

	// The prerendered numbers are from build time. On a full page load, fetch the
	// current ones once; on client-side navigation load() already ran in the browser.
	let fresh = $state<Stats | null>(null);
	const stats = $derived(fresh ?? data.stats);

	// Count-up animation: every number runs from 0 to its value, fast at first and
	// slowing down towards the end. The prerendered HTML keeps the real numbers (for
	// search engines and visitors without JavaScript) but hides them until the page is
	// mounted, so they don't flash before the count starts at 0 (see .count-up below).
	const COUNT_UP_MS = 1800;
	const counters = Object.fromEntries(ENTITIES.map((e) => [e, new Tween(0, { easing: quartOut })]));
	let mounted = $state(false);
	// Decided once per visit of the page, so fresh numbers arriving during the first
	// count-up don't cut it short.
	const skipCountUp = browser && hasCountedUp();

	// Runs again when the fresh numbers arrive: then the count continues from where it is.
	$effect(() => {
		if (!stats) return;
		const duration = skipCountUp || prefersReducedMotion.current ? 0 : COUNT_UP_MS;
		const counts = stats.counts;
		untrack(() => {
			if (duration > 0) markCountedUp();
			for (const [entity, counter] of Object.entries(counters)) {
				counter.set(counts[entity], { duration });
			}
		});
	});

	onMount(async () => {
		mounted = true;
		if (data.fetchedInBrowser) return;
		try {
			fresh = await fetchBackend('stats', 1);
		} catch {
			// keep the build-time numbers
		}
	});
</script>

<svelte:head>
	<title>IR Anthology</title>
	<meta
		name="description"
		content={stats
			? `The IR Anthology: ${groupDigits(String(stats.counts.Publication))} information retrieval publications by ${groupDigits(String(stats.counts.Author))} authors, from ${stats.first_year} to today.`
			: 'The IR Anthology: information retrieval research publications, authors and venues.'}
	/>
	<noscript
		><style>
			.count-up {
				visibility: visible !important;
			}
		</style></noscript
	>
</svelte:head>

<section class="flex flex-1 flex-col items-center justify-center px-2 py-12 text-center sm:py-16">
	<h1 class="m-0 text-5xl font-bold tracking-tight text-gray-900 sm:text-6xl">
		The <span class="text-[#951515]">IR</span> Anthology
	</h1>
	<p class="mt-4 mb-0 text-2xl text-gray-600">Information is nothing without retrieval</p>

	<nav
		aria-label="Browse the anthology"
		class="mt-10 grid w-full max-w-md grid-cols-2 gap-3 sm:mt-12 sm:gap-4"
	>
		{#each ENTITIES as entity (entity)}
			<a
				href={resolve(`/anthology?entity=${entity}`)}
				class="btn-outline group flex flex-col items-center gap-1 px-4 py-5 text-gray-900 no-underline transition-colors focus-visible:ring-2 focus-visible:ring-link/30 focus-visible:outline-none sm:py-6"
			>
				{#if stats}
					<!-- Screen readers get the final number, not the moving one. -->
					<span class="sr-only">{groupDigits(String(stats.counts[entity]))}</span>
					<span
						aria-hidden="true"
						class="count-up text-3xl font-semibold tabular-nums"
						style:visibility={mounted ? 'visible' : 'hidden'}
						>{groupDigits(
							String(mounted ? Math.round(counters[entity].current) : stats.counts[entity])
						)}</span
					>
				{:else}
					<span class="my-1 h-7 w-20 animate-pulse rounded bg-gray-200" aria-hidden="true"></span>
				{/if}
				<span class="text-xl text-gray-600 group-hover:text-link">
					{ENTITY_LABELS[entity]}
					<span
						aria-hidden="true"
						class="inline-block transition-transform group-hover:translate-x-0.5">→</span
					>
				</span>
			</a>
		{/each}
	</nav>
</section>
