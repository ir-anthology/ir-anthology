<script lang="ts">
    import {page} from '$app/state'
	import { SvelteURLSearchParams } from 'svelte/reactivity';
	import { goto } from '$app/navigation';
    import {navigating} from '$app/state'
    import { resolve } from '$app/paths';
    import { fetchBackend } from '$lib/sparql/fetch';

    const COLUMN_WIDTHS: Record<string, string> = {
		Entity: 'w-auto min-w-[100px]',
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

    const current_entity:string = $derived(page.url.searchParams.get("entity") ?? "Author");

    const current_sort_by:string = $derived(page.url.searchParams.get("sort_by") ?? "Publication");

    const current_order:string = $derived(page.url.searchParams.get("order") ?? "desc");

    const HIDDEN_COLUMNS = ['URI'];
    let columns = $derived(vars.filter((v) => !HIDDEN_COLUMNS.includes(v)) ?? []);

    function handleEntityChange(col: string){
        const new_params = new SvelteURLSearchParams(page.url.searchParams.toString())
        new_params.set("entity", col)
        goto(resolve(`/?${new_params.toString()}`))
    }

    function handleSortClick(col: string){
        const new_params = new SvelteURLSearchParams(page.url.searchParams.toString())

        const new_order = current_sort_by === col && current_order === "desc" ? "asc" : "desc"
        new_params.set("order", new_order)
        new_params.set("sort_by", col)
        goto(resolve(`/?${new_params.toString()}`))
    }

    function handleCellClick(col:string, row){
        const entityTitle = row['Entity']?.value;
		if (!entityTitle) return;
        const new_params = new SvelteURLSearchParams(page.url.searchParams.toString())
        const old_value = new_params.get(`filter_${current_entity}`)
        if(old_value === null || old_value.includes(entityTitle)){
            new_params.set(`filter_${current_entity}`, entityTitle)
        } else {
            new_params.set(`filter_${current_entity}`, entityTitle+`,${old_value}`)
        }
        new_params.set('entity', col)
        goto(resolve(`/?${new_params.toString()}`))
    }
</script>

<section class="bg-white rounded-lg shadow overflow-x-auto">
    <table class="min-w-full divide-y divide-gray-200 table-fixed">
        <thead class="bg-gray-50">
            <tr>
                {#each columns as col (col)}
                        <th class="{COLUMN_WIDTHS[col] ?? 'w-24'} whitespace-nowrap">
                            <div class="flex items-center justify-center gap-1">
                                <button
                                    class="text-xs font-medium tracking-wider cursor-pointer {current_entity === col ? 'font-bold text-blue-700' : 'text-gray-500'}"
                                    onclick={() => handleEntityChange(col)}
                                >{col}</button>
                                <button
                                    class="text-2xl cursor-pointer shrink-0 {current_sort_by === col ? 'text-blue-600' : 'text-gray-400 hover:text-gray-600'}"
                                    onclick={() => handleSortClick(col)}
                                >{current_sort_by === col ? (current_order === 'asc' ? '▲' : '▼') : '↕'}</button>
                            </div>
                        </th>
                {/each}
            </tr>
        </thead>
        <tbody>
            {#if navigating.to}
                <tr>
                    <td class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Loading...
                    </td>
                </tr>
            {:else if rows.length === 0}
                <tr>
                    <td class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        No data
                    </td>
                </tr>
            {:else}
                {#each rows as row, i (row)}
                    <tr class={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        {#each columns as col (col)}
                            {@const cellData = row[col]}
                            {#if col === 'Entity'}
                                <td
									class="px-4 py-3 text-sm text-gray-900 wrap-break-word {COLUMN_WIDTHS[col] ??
										'w-24'}"
								>
									{#if row['URI']?.value}
										<a
											href={row['URI'].value}
											target="_blank"
											rel="noopener noreferrer"
											class="text-blue-600 hover:underline"
										>
											{cellData.value ?? '-'}
										</a>
									{:else}
										{cellData.value ?? '-'}
									{/if}
								</td>
                            {:else if cellData?.value}
                                <td
                                    class="px-4 py-3 text-sm text-blue-600 text-center cursor-pointer hover:bg-gray-100 hover:underline transition-colors {COLUMN_WIDTHS[
                                            col
                                        ] ?? 'w-24'}"
                                        onclick={() => handleCellClick(col, row)}
                                        role="button"
                                        tabindex="0"
                                        onkeydown={(e) => e.key === 'Enter' && handleCellClick(col, row)}
                                    >{cellData.value}</td>
                            {:else}
                                <td class="px-4 py-3 text-sm text-gray-400 text-center {COLUMN_WIDTHS[col] ?? 'w-24'}">
									-
								</td>
                            {/if}
                        {/each}
                    </tr>
                {/each}
                {#if loadingMore}
                    <tr>
                        <td colspan={columns.length} class="px-4 py-3 text-center text-xs text-gray-400">
                            Loading...
                        </td>
                    </tr>
                {/if}
                <tr><td bind:this={sentinel}></td></tr>
            {/if}
        </tbody>
    </table>
</section>
