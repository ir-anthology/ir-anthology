<script lang="ts">
    import {page} from '$app/state'
	import { SvelteURLSearchParams } from 'svelte/reactivity';
	import { goto } from '$app/navigation';
    import {navigating} from '$app/state'
    import { resolve } from '$app/paths';
    import { fetchBackend } from '$lib/sparql/fetch';
    import { getIDFromURI, slugifyName, decodeYearCounts, decodeOrdered } from '$lib/helperFunctions';
    import { browser } from '$app/environment';
    import { loadPreferences, savePreferences } from '$lib/columnPreferences';
    import { loadDensity, saveDensity, type Density } from '$lib/rowDensity';
    import { ENTITY_ENDPOINTS, FILTERABLE_ENTITIES, entityDefaultSort, resolveEntity, tableRequestParams, columnEntity } from '$lib/tableConfig';
    import ColumnSettings from './ColumnSettings.svelte';
    import RowDensity from './RowDensity.svelte';

    // Presentation hints only — any column without an entry gets the w-24 fallback,
    // so new backend columns render without frontend changes.
    const COLUMN_WIDTHS: Record<string, string> = {
		Entity: 'w-auto min-w-[200px] max-w-md',
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
            const params = tableRequestParams(page.url.searchParams.toString());
            params.set('page', String(nextPage));
            loadingMore = true;
            const data = await fetchBackend(`${ENTITY_ENDPOINTS[current_entity]}?${params}`);
            loadingMore = false;
            if (data.bindings.length === 0) { exhausted = true; return; }
            rows.push(...data.bindings);
            currentPage = nextPage;
        });
        if (sentinel) observer.observe(sentinel);
        return () => observer.disconnect();
    });

    const _searchParams = $derived(browser ? page.url.searchParams : new URLSearchParams());

    const current_entity:string = $derived(resolveEntity(_searchParams.get("entity")));

    const hasActiveFilters = $derived(FILTERABLE_ENTITIES.some((f) => _searchParams.has(`filter_${f}`)));

    const current_sort_by:string = $derived(_searchParams.get("sort_by") ?? entityDefaultSort(current_entity, hasActiveFilters).sort_by);

    const current_order:string = $derived(_searchParams.get("order") ?? entityDefaultSort(current_entity, hasActiveFilters).order);

    const HIDDEN_COLUMNS = ['URI', 'VenueURI', 'VenueType', 'authors', 'authorIds'];
    let userPrefs = $state(loadPreferences());
    let density: Density = $state(loadDensity());

    let previousEntity: string | null = null;
    $effect(() => {
        if (previousEntity !== null && previousEntity !== current_entity) {
            resetPreferences();
        }
        previousEntity = current_entity;
    });

    function resetPreferences() {
        const rest = { ...userPrefs };
        delete rest[current_entity];
        userPrefs = rest;
        savePreferences(userPrefs);
    }

    // Columns are fully driven by the vars the entity's endpoint returns.
    const availableColumns: string[] = $derived(vars.filter((v: string) => v !== 'Entity' && !HIDDEN_COLUMNS.includes(v)));
    let visibleColumns = $derived.by(() => {
        const prefs = userPrefs[current_entity];
        if (prefs) {
            // an explicit selection from the column settings wins over filter-hiding
            return ['Entity', ...prefs.filter((col) => availableColumns.includes(col))];
        }
        // default: all available columns, minus those whose entity has an active filter
        return ['Entity', ...availableColumns.filter((col) => !_searchParams.has(`filter_${columnEntity(col)}`))];
    });
    let columns = $derived(vars.filter((v: string) => visibleColumns.includes(v)) ?? []);
    const entityOptions = Object.keys(ENTITY_ENDPOINTS);

    const hasYearsMatrix = $derived(columns.includes('Years'));

    const yearsList: number[] = $derived.by(() => {
        if (!hasYearsMatrix) return [];
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
        // a sort column of the old entity may not exist in the new entity's query
        new_params.delete("sort_by")
        new_params.delete("order")
        new_params.set("entity", col)
        goto(resolve(`/anthology?${new_params.toString()}`))
    }

    function handleSortClick(col: string){
        const new_params = new SvelteURLSearchParams(page.url.searchParams.toString())

        // first click sorts desc for year-valued columns and asc for everything else;
        // clicking the active column again flips the direction
        const target = col === 'Entity' ? current_entity : columnEntity(col);
        const initial = target === 'Year' ? 'desc' : 'asc';
        const flipped = initial === 'desc' ? 'asc' : 'desc';
        const new_order = current_sort_by === col && current_order === initial ? flipped : initial;
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
        new_params.delete('sort_by')
        new_params.delete('order')
        new_params.set('entity', columnEntity(col))
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
        // base the first explicit selection on what is currently shown, so checking
        // a filter-hidden column adds it instead of removing it
        const currentPrefs = userPrefs[current_entity] ?? visibleColumns.filter((c) => c !== 'Entity');
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
        resetPreferences();
    }

    function handleDensityChange(d: Density) {
        density = d;
        saveDensity(d);
    }

    // Extract abbreviation for the Venue (either last term in parentheses or uppercased last part from uri)
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
    <table class="min-w-full divide-y divide-gray-200 table-fixed" data-density={density}>
        <thead class="bg-gray-50 sticky z-10 border-b-2 border-gray-300 shadow-[0_2px_3px_-1px_rgba(0,0,0,0.12)]" style="top: var(--table-top, 0px)">
            <tr>
                {#each columns as col (col)}
                    {#if col === 'Years'}
                        <th
                            colspan={yearsList.length}
                            class="bg-gray-50 px-2 pt-1 text-sm font-medium tracking-wider text-gray-500 whitespace-nowrap text-left border-l border-gray-300"
                        >Publications per year</th>
                    {:else}
                        <th rowspan={hasYearsMatrix ? 2 : undefined} class="{col === 'Entity' ? 'bg-slate-50 sticky left-0 z-20 border-r border-gray-200 transition-colors' : 'bg-gray-50'} {COLUMN_WIDTHS[col] ?? 'w-24'} whitespace-nowrap">
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
                                {:else}
                                    <span class="text-sm font-medium tracking-wider text-gray-500">{col}</span>
                                {/if}
                                <button
                                    class="p-1 rounded hover:bg-gray-100 transition-colors cursor-pointer shrink-0"
                                    onclick={() => handleSortClick(col)}
                                    aria-label="Sort by {col}"
                                >
                                    <svg class="w-2.5 h-3.5" viewBox="0 0 10 14">
                                        <polygon points="5,0 10,5.5 0,5.5" class={current_sort_by === col && current_order === 'asc' ? 'fill-link' : 'fill-gray-300'} />
                                        <polygon points="5,14 10,8.5 0,8.5" class={current_sort_by === col && current_order === 'desc' ? 'fill-link' : 'fill-gray-300'} />
                                    </svg>
                                </button>
                                {#if col === 'Entity'}
                                    <ColumnSettings
                                        {availableColumns}
                                        {visibleColumns}
                                        onToggle={handleColumnToggle}
                                        onReset={handleResetDefaults}
                                    />
                                    <RowDensity {density} onChange={handleDensityChange} />
                                {/if}
                            </div>
                        </th>
                    {/if}
                {/each}
            </tr>
            {#if hasYearsMatrix}
                <tr>
                    {#each yearsList as year (year)}
                        <th
                            class="bg-gray-50 w-9 px-0.5 pb-1 text-sm font-medium text-gray-500 whitespace-nowrap {year % 10 === 9 ? 'border-l border-gray-300' : ''}"
                            title={String(year)}
                        >{String(year % 100).padStart(2, '0')}</th>
                    {/each}
                </tr>
            {/if}
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
                            {@const cellDisplay = col === 'Venue' && row['VenueURI']?.value
                                ? venueDisplayLabel(cellData?.value, row['VenueURI'].value)
                                : cellData?.value}
                            {#if col === 'Years'}
                                {@const yearCounts = decodeYearCounts(row['Years']?.value)}
                                {#each yearsList as year (year)}
                                    {@const count = yearCounts.get(year)}
                                    {@const border = year % 10 === 9 ? 'border-l border-gray-300' : ''}
                                    {#if count !== undefined}
                                        <td
                                            class="link px-0.5 text-sm text-center cursor-pointer hover:bg-gray-100 transition-colors {border}"
                                            title="{count} publication{count === 1 ? '' : 's'} in {year}"
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
                                {@const authors = decodeOrdered(row['authors']?.value ?? null, true)}
                                {@const authorIds = decodeOrdered(row['authorIds']?.value ?? null)}
                                <td
									class="sticky left-0 z-5 border-r border-gray-200 {i % 2 === 0 ? 'bg-white' : 'bg-gray-50'} px-4 py-1.5 text-sm text-gray-900 wrap-break-word {COLUMN_WIDTHS[col] ??
										'w-24'}"
								>
									{#if current_entity === 'Venue' && (row['VenueType']?.value || row['URI']?.value === 'https://dblp.org/workshops')}
										{@const type = row['VenueType']?.value || 'Workshop'}
										<span
											class="mr-1 align-middle inline-flex rounded border border-current/20 px-1 py-0.5 text-[10px] font-bold {type === 'Conference' ? 'bg-blue-100 text-blue-800' : type === 'Journal' ? 'bg-amber-100 text-amber-800' : 'bg-green-100 text-green-800'}"
											title={type}
										>{type[0]}</span>
									{/if}
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
									{#if authors.length > 0}
										<div class="text-sm mt-0.5">
											{#each authors as author, i (i)}
												{#if i > 0}<span class="text-gray-400 px-1.5"> | </span>{/if}{#if authorIds[i]}<a href={resolve(`/anthology/people/${slugifyName(author)}/${getIDFromURI(authorIds[i])}`)} class="link italic text-xs">{author}</a>{:else}{author}{/if}
											{/each}
										</div>
									{/if}
								</td>
                            {:else if cellDisplay && ENTITY_ENDPOINTS[columnEntity(col)]}
                                <td
                                    class="link px-4 py-1.5 text-sm text-center cursor-pointer hover:bg-gray-100 transition-colors {COLUMN_WIDTHS[
                                            col
                                        ] ?? 'w-24'}"
                                        onclick={() => handleCellClick(col, row)}
                                        role="button"
                                        tabindex="0"
                                        onkeydown={(e) => e.key === 'Enter' && handleCellClick(col, row)}
                                    >{cellDisplay}</td>
                            {:else if cellDisplay}
                                <td class="px-4 py-1.5 text-sm text-center {COLUMN_WIDTHS[col] ?? 'w-24'}">{cellDisplay}</td>
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

<style>
	table[data-density='compact'] tbody td {
		padding-block: 0.25rem;
		font-size: 0.8125rem;
	}
	table[data-density='dense'] tbody td {
		padding-block: 0.0625rem;
		font-size: 0.75rem;
	}
	table[data-density='compact'] tbody td span.inline-flex,
	table[data-density='dense'] tbody td span.inline-flex {
		font-size: 9px;
		padding-block: 0;
	}
</style>
