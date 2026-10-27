<script lang="ts">
	import DataTable from '$lib/components/DataTable.svelte';

    let {data} = $props();
</script>

<div class="w-max min-w-[min(64rem,100%)]">
    <DataTable vars={data.vars} bindings={data.bindings} />
</div>
