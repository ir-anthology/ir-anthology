<script lang="ts">
	import { goto } from "$app/navigation";
    import { resolve } from '$app/paths';
</script>

<button
    onclick={() => goto(resolve('/'))}
    class="p-2 rounded-full bg-gray-100 hover:bg-gray-200 transition"
    title="Reset filters"
>
    <svg class="h-6 w-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
        ></path>
    </svg>
</button>