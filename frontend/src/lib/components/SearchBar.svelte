<script lang="ts">
    import {page} from '$app/state'
	import { SvelteURLSearchParams } from 'svelte/reactivity';
	import { goto } from '$app/navigation';
    import { resolve } from '$app/paths';
    import { browser } from '$app/environment';
    import { FILTERABLE_ENTITIES } from '$lib/tableConfig';

    const current_entity = $derived(browser ? (page.url.searchParams.get("entity") ?? "Venue") : "Venue");

    let searchValue:string | null = $state(null);

    // Parts written as "author=xy" (also venue/publication/year, case-insensitive)
    // filter that entity; plain parts filter the current entity as before.
    function parseSearchParts(input: string): Record<string, string[]> {
        const grouped: Record<string, string[]> = {};
        for (const part of input.split(',').map((p) => p.trim()).filter(Boolean)) {
            let entity = current_entity;
            let value = part;
            const eq = part.indexOf('=');
            if (eq > 0) {
                const key = part.slice(0, eq).trim().toLowerCase();
                const match = FILTERABLE_ENTITIES.find((f) => f.toLowerCase() === key);
                if (match) {
                    entity = match;
                    value = part.slice(eq + 1).trim();
                }
            }
            if (!value) continue;
            (grouped[entity] ??= []).push(value);
        }
        return grouped;
    }

    async function handleKeydown(e: KeyboardEvent){
        if (e.key !== 'Enter' || searchValue === null) return
        const grouped = parseSearchParts(searchValue);
		if (Object.keys(grouped).length === 0) return;
        const new_params = new SvelteURLSearchParams(page.url.searchParams.toString())
        for (const [entity, values] of Object.entries(grouped)) {
            new_params.set(`filter_${entity}`, values.join(","))
        }
		searchValue = '';
        await goto(resolve(`/anthology?${new_params.toString()}`))
    }

    const helpText = $derived(
        `Type to search the current entity column (${current_entity}).\n` +
        `Search a different entity with entity=value, e.g. author=smith or year=2023.\n` +
        `Available entities: ${FILTERABLE_ENTITIES.map((f) => f.toLowerCase()).join(', ')}.`
    );
</script>

<div class="relative w-140 max-w-full">
    <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
        <svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            ></path>
        </svg>
    </div>
    <input
        type="text"
        onkeydown={handleKeydown}
        bind:value={searchValue}
        placeholder="Search {current_entity}s..."
        class="block w-full pl-12 pr-10 py-3 rounded-full border border-gray-300 bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-700 placeholder-gray-400"
    />
    <div
        class="absolute inset-y-0 right-0 pr-4 flex items-center cursor-help"
        title={helpText}
    >
        <svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
            ></path>
        </svg>
    </div>
</div>