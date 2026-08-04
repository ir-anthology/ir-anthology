<script lang="ts">
	import ObservationsPanel from './ObservationsPanel.svelte';
	import FollowupPanel from './FollowupPanel.svelte';
	import QueryBox from './QueryBox.svelte';
	let { sparqlData, onclose }: { sparqlData: { vars: string[]; bindings: Record<string, { type: string; value: string }>[] }; onclose: () => void } = $props();
</script>

<aside class="fixed top-[70px] right-0 bottom-0 w-96 bg-white border-l border-gray-200 shadow-lg z-30 flex flex-col">
	<header class="flex items-center justify-between px-4 py-3 border-b border-gray-200">
		<h2 class="text-base font-semibold text-gray-900">AI Insights</h2>
		<button
			onclick={onclose}
			class="p-1 rounded hover:bg-gray-100 transition-colors"
			aria-label="Close AI panel"
		>
			<svg class="h-5 w-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
			</svg>
		</button>
	</header>
	<div class="flex-1 overflow-y-auto p-4 flex flex-col gap-6">
		<ObservationsPanel {sparqlData} />
		<FollowupPanel {sparqlData} />
		<QueryBox />
	</div>
</aside>
