<script lang="ts">
    import {page} from '$app/state'
	import { SvelteURLSearchParams } from 'svelte/reactivity';
	import { goto } from '$app/navigation';
    import {navigating} from '$app/state'
    import { resolve } from '$app/paths';
    import { fetchBackend } from '$lib/sparql/fetch';
    import { getIDFromURI, slugifyName, decodeYearCounts } from '$lib/helperFunctions';
    import { browser } from '$app/environment';
    import { DEFAULT_COLUMNS, ALL_COLUMNS, loadPreferences, savePreferences } from '$lib/columnPreferences';
    import ColumnSettings from './ColumnSettings.svelte';

    const COLUMN_WIDTHS: Record<string, string> = {
		Entity: 'w-auto min-w-[200px] max-w-md',
		Publication: 'w-24',
		Venue: 'w-24',
		Author: 'w-24',
		Year: 'w-20',
		'2020s': 'w-20',
		'2010s': 'w-20',
		'2000s': 'w-20',
		Pre2000s: 'w-24'
	};

    let {vars, bindings } = $props();

    let rows: typeof bindings = $state([...bindings]);
    let currentPage = $state(1);
    let exhausted = $state(false);
    let loadingMore = $state(false);
    let sentinel: HTMLElement | null = $state(null);

    $effect(() => {
        rows = [...bindings];
        currentPage = 1;
        exhausted = false;
    });

    $effect(() => {
        const observer = new IntersectionObserver(async ([entry]) => {
            if (!entry.isIntersecting || exhausted || loadingMore) return;
            const nextPage = currentPage + 1;
            const params = new SvelteURLSearchParams(page.url.searchParams.toString());
            params.set('page', String(nextPage));
            loadingMore = true;
            const data = await fetchBackend(`table?${params}`);
            loadingMore = false;
            if (data.bindings.length === 0) { exhausted = true; return; }
            rows.push(...data.bindings);
            currentPage = nextPage;
        });
        if (sentinel) observer.observe(sentinel);
        return () => observer.disconnect();
    });

    const _searchParams = $derived(browser ? page.url.searchParams : new URLSearchParams());

    const current_entity:string = $derived(_searchParams.get("entity") ?? "Venue");

    const current_sort_by:string = $derived(_searchParams.get("sort_by") ?? "Publication");

    const current_order:string = $derived(_searchParams.get("order") ?? "desc");

    const HIDDEN_COLUMNS = ['URI'];
    let userPrefs = $state(loadPreferences());

    let previousEntity: string | null = null;
    $effect(() => {
        if (previousEntity !== null && previousEntity !== current_entity) {
            userPrefs = { ...userPrefs, [current_entity]: DEFAULT_COLUMNS[current_entity] ?? [] };
            savePreferences(userPrefs);
        }
        previousEntity = current_entity;
    });

    let visibleColumns = $derived.by(() => {
        const prefs = userPrefs[current_entity] ?? DEFAULT_COLUMNS[current_entity];
        const withoutFiltered = prefs.filter((col) => !_searchParams.has(`filter_${col === 'Years' ? 'Year' : col}`));
        return ['Entity', ...withoutFiltered];
    });
    let columns = $derived(vars.filter((v) => visibleColumns.includes(v) && !HIDDEN_COLUMNS.includes(v)) ?? []);
    const entityOptions = $derived(ALL_COLUMNS);

    const yearsList: number[] = $derived.by(() => {
        if (!columns.includes('Years')) return [];
        let min = Infinity, max = -Infinity;
        for (const row of rows) {
            for (const year of decodeYearCounts(row['Years']?.value).keys()) {
                if (year < min) min = year;
                if (year > max) max = year;
            }
        }
        if (min === Infinity) return [];
        return Array.from({ length: max - min + 1 }, (_, i) => max - i);
    });

    function handleEntityChange(col: string){
        const new_params = new SvelteURLSearchParams(page.url.searchParams.toString())
        new_params.set("entity", col)
        goto(resolve(`/anthology?${new_params.toString()}`))
    }

    function handleSortClick(col: string){
        const new_params = new SvelteURLSearchParams(page.url.searchParams.toString())

        const new_order = current_sort_by === col && current_order === "desc" ? "asc" : "desc"
        new_params.set("order", new_order)
        new_params.set("sort_by", col)
        goto(resolve(`/anthology?${new_params.toString()}`))
    }

    function handleCellClick(col:string, row, year?: number){
        const entityTitle = row['Entity']?.value;
		if (!entityTitle) return;
        const new_params = new SvelteURLSearchParams(page.url.searchParams.toString())
        const old_value = new_params.get(`filter_${current_entity}`)
        if(old_value === null || old_value.includes(entityTitle)){
            new_params.set(`filter_${current_entity}`, entityTitle)
        } else {
            new_params.set(`filter_${current_entity}`, entityTitle+`,${old_value}`)
        }
        if (year !== undefined) new_params.set('filter_Year', String(year))
        new_params.set('entity', col)
        goto(resolve(`/anthology?${new_params.toString()}`))
    }

    function buildURL(uri: string, entityName: string = ''): string{
        switch(current_entity){
            case "Publication":
                return "/anthology/publications/"+getIDFromURI(uri)
            case "Venue":
                return "/anthology/venues/"+getIDFromURI(uri)
            case "Author":
                return "/anthology/people/"+slugifyName(entityName)+"/"+getIDFromURI(uri)
            default:
                return ""
        }
    }

    function handleColumnToggle(column: string) {
        const currentPrefs = userPrefs[current_entity] ?? DEFAULT_COLUMNS[current_entity];
        let newPrefs: string[];
        if (currentPrefs.includes(column)) {
            newPrefs = currentPrefs.filter((c) => c !== column);
        } else {
            newPrefs = [...currentPrefs, column];
        }
        userPrefs = { ...userPrefs, [current_entity]: newPrefs };
        savePreferences(userPrefs);
    }

    function handleResetDefaults() {
        userPrefs = { ...userPrefs, [current_entity]: DEFAULT_COLUMNS[current_entity] };
        savePreferences(userPrefs);
    }

    function venueDisplayLabel(value: string | null | undefined, uri: string | null | undefined): string {
        if (value) {
            const matches = [...value.matchAll(/\(([^)]+)\)/g)];
            if (matches.length > 0) return matches[matches.length - 1][1];
        }
        if (uri) {
            var last = uri.split('/').filter(Boolean).at(-1)?.toUpperCase();
            if (last?.includes("WORKSHOPS")) {last = last.replaceAll("+", "/")} ;
            if (last) return last;
        }
        return value ?? '-';
    }
</script>

<section class="bg-white rounded-lg shadow">
    <table class="min-w-full divide-y divide-gray-200 table-fixed">
        <thead class="bg-gray-50 sticky z-10" style="top: var(--table-top, 0px)">
            <tr>
                {#each columns as col (col)}
                    {#if col === 'Years'}
                        {#each yearsList as year (year)}
                            <th
                                class="bg-gray-50 w-9 px-0.5 text-xm font-medium text-gray-500 whitespace-nowrap {year % 10 === 9 ? 'border-l border-gray-300' : ''}"
                                title={String(year)}
                            >{String(year % 100).padStart(2, '0')}</th>
                        {/each}
                    {:else}
                        <th class="bg-gray-50 {COLUMN_WIDTHS[col] ?? 'w-24'} whitespace-nowrap">
                            <div class="flex items-center gap-1 {col === 'Entity' ? 'justify-start pl-4' : 'justify-center'}">
                                {#if col === 'Entity'}
                                    <div class="relative inline-flex items-center shrink-0">
                                        <select
                                            class="appearance-none min-w-30 text-sm font-medium tracking-wider cursor-pointer border border-gray-300 rounded px-2 pr-6 py-0.5 bg-white focus:outline-none focus:ring-2 focus:ring-link/30 focus:border-link transition-colors {current_entity === col ? 'text-link font-semibold' : 'text-gray-600 hover:bg-gray-100 hover:border-gray-400'}"
                                            value={current_entity}
                                            onchange={(e) => handleEntityChange(e.currentTarget.value)}
                                        >
                                            {#each entityOptions as opt (opt)}
                                                <option value={opt}>{opt}</option>
                                            {/each}
                                        </select>
                                        <svg class="absolute right-1.5 w-3 h-3 pointer-events-none {current_entity === col ? 'text-link' : 'text-gray-400'}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                            <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd" />
                                        </svg>
                                    </div>
                                    <ColumnSettings
                                        {visibleColumns}
                                        onToggle={handleColumnToggle}
                                        onReset={handleResetDefaults}
                                    />
                                {:else}
                                    <span class="text-xm font-medium tracking-wider text-gray-500">{col}</span>
                                {/if}
                                <button
                                    class="text-xm cursor-pointer shrink-0 {current_sort_by === col ? 'text-gray-600' : 'text-gray-400'}"
                                    onclick={() => handleSortClick(col)}
                                >{current_sort_by === col ? (current_order === 'asc' ? '↑' : '↓') : '↕'}</button>
                            </div>
                        </th>
                    {/if}
                {/each}
            </tr>
        </thead>
        <tbody>
            {#if navigating.to}
                <tr>
                    <td class="px-4 py-1.5 text-left text-xs font-medium text-gray-500 uppercase">
                        Loading...
                    </td>
                </tr>
            {:else if rows.length === 0}
                <tr>
                    <td class="px-4 py-1.5 text-left text-xs font-medium text-gray-500 uppercase">
                        No data
                    </td>
                </tr>
            {:else}
                {#each rows as row, i (row)}
                    <tr class={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        {#each columns as col (col)}
                            {@const cellData = row[col]}
                            {#if col === 'Years'}
                                {@const yearCounts = decodeYearCounts(row['Years']?.value)}
                                {#each yearsList as year (year)}
                                    {@const count = yearCounts.get(year)}
                                    {@const border = year % 10 === 9 ? 'border-l border-gray-300' : ''}
                                    {#if count !== undefined}
                                        <td
                                            class="link px-0.5 text-sm text-center cursor-pointer hover:bg-gray-100 transition-colors {border}"
                                            onclick={() => handleCellClick('Publication', row, year)}
                                            role="button"
                                            tabindex="0"
                                            onkeydown={(e) => e.key === 'Enter' && handleCellClick('Publication', row, year)}
                                        >{count}</td>
                                    {:else}
                                        <td class="px-0.5 text-sm text-center {border}"></td>
                                    {/if}
                                {/each}
                            {:else if col === 'Entity'}
                                <td
									class="px-4 py-1.5 text-sm text-gray-900 wrap-break-word {COLUMN_WIDTHS[col] ??
										'w-24'}"
								>
									{#if row['URI']?.value}
										<a
											href={buildURL(row['URI'].value, row['Entity']?.value ?? '')}
											target="_blank"
											rel="noopener noreferrer"
											class="link"
										>
											{current_entity === 'Venue' ? venueDisplayLabel(cellData.value, row['URI']?.value) : (cellData.value ?? '-')}
										</a>
									{:else}
										{current_entity === 'Venue' ? venueDisplayLabel(cellData.value, undefined) : (cellData.value ?? '-')}
									{/if}
								</td>
                            {:else if cellData?.value}
                                <td
                                    class="link px-4 py-1.5 text-sm text-center cursor-pointer hover:bg-gray-100 transition-colors {COLUMN_WIDTHS[
                                            col
                                        ] ?? 'w-24'}"
                                        onclick={() => handleCellClick(col, row)}
                                        role="button"
                                        tabindex="0"
                                        onkeydown={(e) => e.key === 'Enter' && handleCellClick(col, row)}
                                    >{cellData.value}</td>
                            {:else}
                                <td class="px-4 py-1.5 text-sm text-gray-400 text-center {COLUMN_WIDTHS[col] ?? 'w-24'}">
									-
								</td>
                            {/if}
                        {/each}
                    </tr>
                {/each}
                {#if loadingMore}
                    <tr>
                        <td colspan={columns.includes('Years') ? columns.length - 1 + yearsList.length : columns.length} class="px-4 py-1.5 text-center text-xs text-gray-400">
                            Loading...
                        </td>
                    </tr>
                {/if}
                <tr><td bind:this={sentinel}></td></tr>
            {/if}
        </tbody>
    </table>
</section>
