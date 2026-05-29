<script lang="ts">
	import DataTable from '$lib/components/DataTable.svelte';
	import ResetButton from '$lib/components/ResetButton.svelte';
    import SearchBar from '$lib/components/SearchBar.svelte';
    import { page } from '$app/state';
	import FilterField from '$lib/components/FilterField.svelte';

    const filters:Record<string, string[]> = $derived.by(() => {
        const result:Record<string, string[]> = {};
        const searchParams:URLSearchParams = page.url.searchParams;
        const keys = searchParams.keys().toArray();
        for(const key in keys){
            const valueKey = keys[key]
            if (!valueKey.startsWith("filter_")) continue
            const value = searchParams.get(valueKey);
            if (value === null) continue;
            result[valueKey.slice("filter_".length)] = value.split(",");
        }
        return result;
    })

    

    let {data} = $props();
</script>

<section class="mb-6">
	<div class="relative flex items-center gap-4">
        <SearchBar /> <ResetButton />
	</div>
</section>

<section class="mb-4 min-h-8">
	{#if Object.keys(filters).length === 0}
		<div class="text-sm text-gray-400 italic">No active filters</div>
	{:else}
		{#each Object.keys(filters) as key (key)}
			<FilterField key = {key} values = {filters[key]} />
		{/each}
	{/if}
</section>

<DataTable vars = {data.vars} bindings = {data.bindings} />