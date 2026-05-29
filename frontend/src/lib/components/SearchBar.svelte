<script lang="ts">
    import {page} from '$app/state'
	import { SvelteURLSearchParams } from 'svelte/reactivity';
	import { goto } from '$app/navigation';
    import { resolve } from '$app/paths';

    const current_entity = $derived(page.url.searchParams.get("entity") ?? "Author"); //TODO declare defaults somewhere

    let searchValue:string | null = $state(null);

    async function handleKeydown(e: KeyboardEvent){
        if (e.key !== 'Enter' || searchValue === null) return
        const values = searchValue.split(',').map((p) => p.trim()).filter(Boolean);
		if (values.length === 0) return;
        const new_params = new SvelteURLSearchParams(page.url.searchParams.toString())
        new_params.set(`filter_${current_entity}`, values.join(","))
		searchValue = '';
        await goto(resolve(`/?${new_params.toString()}`))
    }
</script>

<div class="relative flex-1">
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
        class="block w-full pl-12 pr-4 py-3 rounded-full border border-gray-300 bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-700 placeholder-gray-400"
    />
</div>