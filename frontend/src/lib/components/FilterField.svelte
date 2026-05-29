<script lang="ts">
	import { goto } from "$app/navigation";
    import { page } from "$app/state";
	import { SvelteURLSearchParams } from "svelte/reactivity";
    import { resolve } from '$app/paths';

    let {key, values} = $props()
    let pendingRemoval = $state<number | null>(null)
    const localValues = $derived(
        pendingRemoval !== null ? values.filter((_: string, i: number) => i !== pendingRemoval) : values
    )

    function removeFilter(index: number) {
        pendingRemoval = index
        const remaining = values.filter((_: string, i: number) => i !== index)
        const new_params = new SvelteURLSearchParams(page.url.searchParams.toString())
        if (remaining.length === 0) {
            new_params.delete(`filter_${key}`)
        } else {
            new_params.set(`filter_${key}`, remaining.join(","))
        }
        goto(resolve(`/?${new_params.toString()}`))
        pendingRemoval = null
    }
</script>

<div class="flex flex-wrap gap-2 mb-2 items-center">
    <span class="text-sm text-gray-600 font-medium">{key}:</span>
    {#each localValues as value, index (index)}
        <div class="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-blue-100 text-blue-800 text-sm">
            <span>{decodeURIComponent(value)}</span>
            <button
                type="button"
                onclick={() => removeFilter(index)}
                class="ml-1 text-blue-600 hover:text-blue-800 font-bold leading-none"
                aria-label="Remove filter"
            >
                &times;
            </button>
        </div>
    {/each}
</div>