<script lang="ts">
	import { fetchObservations, type Observation } from '$lib/externalApi';

	let { sparqlData }: { sparqlData: { vars: string[]; bindings: Record<string, { type: string; value: string }>[] } } = $props();

	let observations = $state<Observation[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	$effect(() => {
		loading = true;
		error = null;
		fetchObservations(sparqlData)
			.then((res) => {
				observations = res.observations;
				loading = false;
			})
			.catch((err) => {
				error = err instanceof Error ? err.message : 'Failed to load observations';
				loading = false;
			});
	});
</script>

<div class="border border-gray-200 rounded-lg p-4">
	<h3 class="text-base font-semibold mb-3">Observations</h3>
	{#if loading}
		<div class="text-xs font-medium text-gray-500 uppercase">Loading observations...</div>
	{:else if error}
		<div class="text-sm text-red-600">{error}</div>
	{:else if observations.length === 0}
		<div class="text-sm text-gray-400 italic">No observations available</div>
	{:else}
		<div class="flex flex-col gap-4">
			{#each observations as obs, i (i)}
				<div class="flex flex-col gap-1">
					<h4 class="text-sm font-semibold text-gray-900">{obs.title}</h4>
					<p class="text-sm text-gray-700">{obs.description}</p>
					{#if obs.evidence}
						<span class="text-xs text-gray-500">{obs.evidence}</span>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>
