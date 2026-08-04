<script lang="ts">
	import { fetchQuery, type QueryAction } from '$lib/externalApi';

	let queryText = $state('');
	let actions = $state<QueryAction[]>([]);
	let supported = $state<boolean | null>(null);
	let reason = $state<string | null>(null);
	let loading = $state(false);
	let error = $state<string | null>(null);

	async function handleSubmit() {
		const trimmed = queryText.trim();
		if (!trimmed) return;
		loading = true;
		error = null;
		actions = [];
		supported = null;
		reason = null;
		try {
			const res = await fetchQuery(trimmed);
			actions = res.actions;
			supported = res.supported;
			reason = res.reason;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to process query';
		} finally {
			loading = false;
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			handleSubmit();
		}
	}
</script>

<div class="border border-gray-200 rounded-lg p-4">
	<h3 class="text-base font-semibold mb-3">Query</h3>
	<div class="flex gap-2 mb-3">
		<input
			type="text"
			bind:value={queryText}
			onkeydown={handleKeydown}
			placeholder="Ask about publications, authors, venues..."
			class="flex-1 border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-link/30 focus:border-link"
		/>
		<button
			onclick={handleSubmit}
			disabled={loading || !queryText.trim()}
			class="bg-gray-800 text-white text-sm rounded px-4 py-1.5 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-pointer transition-colors"
		>
			{loading ? '...' : 'Go'}
		</button>
	</div>
	{#if error}
		<div class="text-sm text-red-600">{error}</div>
	{:else if supported === false}
		<div class="text-sm text-gray-500 italic">{reason ?? 'Query not supported'}</div>
	{:else if actions.length > 0}
		<ul class="flex flex-col gap-2 list-none p-0 m-0">
			{#each actions as action, i (i)}
				<li>
					<a
						href={action.url}
						target="_blank"
						rel="noopener noreferrer"
						class="link text-sm"
					>
						{action.title}
					</a>
				</li>
			{/each}
		</ul>
	{/if}
</div>
