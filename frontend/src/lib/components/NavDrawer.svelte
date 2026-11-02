<script lang="ts">
    import { page } from '$app/state';
    import { goto } from '$app/navigation';
    import { resolve } from '$app/paths';
    import { browser } from '$app/environment';
    import { SvelteURLSearchParams } from 'svelte/reactivity';
    import { FILTERABLE_ENTITIES } from '$lib/tableConfig';
    import FilterField from './FilterField.svelte';

    let { open, topOffset }: { open: boolean; topOffset: number } = $props();

    // Mirrors anthology/+page.svelte's filter-parsing logic so active filters show up
    // here regardless of which page the drawer is rendered on.
    const filters: Record<string, string[]> = $derived.by(() => {
        if (!browser) return {};
        const result: Record<string, string[]> = {};
        const searchParams = page.url.searchParams;
        for (const key of searchParams.keys()) {
            if (!key.startsWith('filter_')) continue;
            const value = searchParams.get(key);
            if (value === null) continue;
            result[key.slice('filter_'.length)] = value.split(',');
        }
        return result;
    });
    const hasActiveFilters = $derived(Object.keys(filters).length > 0);

    let inputValues = $state<Record<string, string>>({
        venue: '',
        author: '',
        publication: '',
        year: ''
    });

    // Commit a field's value as a filter on Enter. Deliberately the same mechanism
    // the rest of the app already uses: a `filter_<Entity>` search param holding a
    // comma-separated list, which FilterField renders as individually removable
    // chips. These fields say "Add", so a value is APPENDED to whatever is already
    // filtered on that entity (like clicking a count cell does) rather than
    // replacing it the way the search bar does.
    async function addFilter(fieldKey: string) {
        const entity = FILTERABLE_ENTITIES.find((f) => f.toLowerCase() === fieldKey);
        const value = inputValues[fieldKey].trim();
        if (!entity || !value) return;

        const params = new SvelteURLSearchParams(page.url.searchParams.toString());
        const current = params.get(`filter_${entity}`);
        const values = current ? current.split(',') : [];
        inputValues[fieldKey] = '';
        // Re-adding something already filtered on would only duplicate the chip.
        if (values.includes(value)) return;

        values.push(value);
        params.set(`filter_${entity}`, values.join(','));
        await goto(resolve(`/anthology?${params.toString()}`));
    }

    // Clears ONLY the filters. Deliberately different from the ResetButton next to
    // the search bar, which goto()s a bare /anthology and so also drops the entity
    // selection and the sort — here everything except filter_* is carried over.
    async function clearFilters() {
        const params = new SvelteURLSearchParams(page.url.searchParams.toString());
        // snapshot the keys: deleting while iterating the live iterator skips entries
        for (const key of [...params.keys()]) {
            if (key.startsWith('filter_')) params.delete(key);
        }
        const query = params.toString();
        await goto(resolve(query ? `/anthology?${query}` : '/anthology'));
    }

    const fields: { key: string; placeholder: string }[] = [
        { key: 'venue', placeholder: 'Add venue' },
        { key: 'author', placeholder: 'Add author' },
        { key: 'publication', placeholder: 'Add paper' },
        { key: 'year', placeholder: 'Add year' }
    ];
</script>

<aside
    class="fixed left-0 bottom-0 z-40 w-64 flex flex-col bg-white border-r border-gray-200 shadow-sm overflow-y-auto transition-transform duration-200 {open
        ? 'translate-x-0'
        : '-translate-x-full'}"
    style="top: {topOffset}px"
    aria-label="Site navigation"
    aria-hidden={!open}
>
    <div class="p-2">
        <div class="border-b border-gray-100 pb-1 mb-1">
            <div class="flex items-center gap-1.5 px-1.5 pt-1 pb-0.5">
                <span class="flex-1 text-[10px] font-semibold tracking-wider uppercase text-gray-400">Filters</span>
                <button
                    type="button"
                    onclick={clearFilters}
                    disabled={!hasActiveFilters}
                    class="border border-gray-200 bg-white text-gray-500 text-[9px] tracking-wide uppercase rounded px-1.5 py-0.5 leading-normal hover:bg-gray-100 hover:text-gray-900 disabled:opacity-40 disabled:hover:bg-white disabled:hover:text-gray-500 disabled:cursor-default"
                    title="Clear all filters"
                >
                    reset
                </button>
            </div>

            <div class="px-1.5 pb-1">
                {#if hasActiveFilters}
                    {#each Object.keys(filters) as key (key)}
                        <FilterField {key} values={filters[key]} />
                    {/each}
                {/if}
            </div>

            {#each fields as field (field.key)}
                <div class="px-1.5 mt-1">
                    <div
                        class="flex items-center gap-1.5 px-1.5 border border-gray-200 rounded-lg bg-white focus-within:border-blue-300 focus-within:ring-2 focus-within:ring-blue-100 transition-colors"
                    >
                        <svg
                            class="w-3 h-3 shrink-0 text-gray-400"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="1.7"
                        >
                            {#if field.key === 'venue'}
                                <rect x="3" y="4" width="18" height="16" rx="2" /><path d="M3 10h18" />
                            {:else if field.key === 'author'}
                                <circle cx="12" cy="8" r="3.2" /><path
                                    d="M5 20c0-3.3 3.1-5.5 7-5.5s7 2.2 7 5.5"
                                />
                            {:else if field.key === 'publication'}
                                <path d="M6 3h8l4 4v14H6z" /><path d="M14 3v4h4" />
                            {:else}
                                <rect x="3" y="5" width="18" height="16" rx="2" /><path
                                    d="M3 10h18M8 3v4M16 3v4"
                                />
                            {/if}
                        </svg>
                        <input
                            type="text"
                            bind:value={inputValues[field.key]}
                            onkeydown={(e) => e.key === 'Enter' && addFilter(field.key)}
                            placeholder={field.placeholder}
                            autocomplete="off"
                            spellcheck="false"
                            class="flex-1 min-w-0 border-0 outline-none bg-transparent text-[11.5px] text-gray-900 placeholder-gray-400 py-1"
                        />
                        {#if inputValues[field.key]}
                            <button
                                type="button"
                                onclick={() => (inputValues[field.key] = '')}
                                class="text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-full text-xs leading-none px-1 py-0.5"
                                title="Clear"
                            >
                                &times;
                            </button>
                        {/if}
                    </div>
                </div>
            {/each}
        </div>

        <div class="text-[11px] font-semibold tracking-wider uppercase text-gray-400 px-2 pt-1 pb-1">Links</div>
        <a
            href={resolve('/community')}
            class="flex items-center gap-2.5 px-2 py-1.5 rounded-lg text-gray-700 no-underline hover:bg-gray-100 hover:text-gray-900 transition-colors"
        >
            <svg
                class="w-4 h-4 shrink-0"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.75"
                stroke-linecap="round"
                stroke-linejoin="round"
            >
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path
                    d="M22 21v-2a4 4 0 0 0-3-3.87"
                /><path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
            <span class="flex-1">Community</span>
        </a>
    </div>
</aside>
