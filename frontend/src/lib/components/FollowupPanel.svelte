<script lang="ts">
	import { fetchFollowup, type FollowupQuestion } from '$lib/externalApi';

	let { sparqlData }: { sparqlData: { vars: string[]; bindings: Record<string, { type: string; value: string }>[] } } = $props();

	let questions = $state<FollowupQuestion[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	$effect(() => {
		loading = true;
		error = null;
		fetchFollowup(sparqlData)
			.then((res) => {
				questions = res.followup_questions;
				loading = false;
			})
			.catch((err) => {
				error = err instanceof Error ? err.message : 'Failed to load follow-up questions';
				loading = false;
			});
	});
</script>

<div class="border border-gray-200 rounded-lg p-4">
	<h3 class="text-base font-semibold mb-3">Follow-up Questions</h3>
	{#if loading}
		<div class="text-xs font-medium text-gray-500 uppercase">Loading follow-up questions...</div>
	{:else if error}
		<div class="text-sm text-red-600">{error}</div>
	{:else if questions.length === 0}
		<div class="text-sm text-gray-400 italic">No follow-up questions available</div>
	{:else}
		<ul class="flex flex-col gap-2 list-none p-0 m-0">
			{#each questions as q, i (i)}
				<li>
					<a
						href={q.url}
						target="_blank"
						rel="noopener noreferrer"
						class="link text-sm"
					>
						{q.question}
					</a>
				</li>
			{/each}
		</ul>
	{/if}
</div>
