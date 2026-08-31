<script lang="ts">
	import { browser } from '$app/environment';
	import type { Density } from '$lib/rowDensity';

	let { density, onChange }: { density: Density; onChange: (d: Density) => void } = $props();

	let isOpen = $state(false);
	let dropdownRef: HTMLElement | null = $state(null);

	function handleClickOutside(event: MouseEvent) {
		if (dropdownRef && !dropdownRef.contains(event.target as Node)) {
			isOpen = false;
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			isOpen = false;
		}
	}

	$effect(() => {
		if (browser) {
			document.addEventListener('click', handleClickOutside);
			document.addEventListener('keydown', handleKeydown);
			return () => {
				document.removeEventListener('click', handleClickOutside);
				document.removeEventListener('keydown', handleKeydown);
			};
		}
	});

	const options: { value: Density; label: string }[] = [
		{ value: 'normal', label: 'Normal' },
		{ value: 'compact', label: 'Compact' },
		{ value: 'dense', label: 'Dense' }
	];
</script>

<div class="relative" bind:this={dropdownRef}>
	<button
		class="p-1.5 rounded hover:bg-gray-100 transition-colors"
		onclick={() => (isOpen = !isOpen)}
		aria-label="Row density"
		aria-expanded={isOpen}
		aria-haspopup="true"
	>
		<svg
			class="h-4 w-4 text-gray-500"
			xmlns="http://www.w3.org/2000/svg"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			stroke-width="1.5"
		>
			<path stroke-linecap="round" d="M3.5 6h17M3.5 12h17M3.5 18h17" />
		</svg>
	</button>

	{#if isOpen}
		<div
			class="absolute right-0 mt-2 w-max min-w-40 bg-white rounded-lg shadow-lg border border-gray-200 z-50"
			role="menu"
			aria-orientation="vertical"
			aria-labelledby="row-density-menu"
		>
			<div class="p-3">
				<span class="text-xs font-medium text-gray-500 tracking-wider uppercase">Row density</span>
				<div class="flex flex-col gap-1 mt-2">
					{#each options as opt (opt.value)}
						<button
							class="text-left text-sm px-2 py-1 rounded transition-colors {density === opt.value
								? 'bg-blue-100 text-blue-800 font-medium'
								: 'text-gray-700 hover:bg-gray-50'}"
							onclick={() => {
								onChange(opt.value);
								isOpen = false;
							}}
						>{opt.label}</button>
					{/each}
				</div>
			</div>
		</div>
	{/if}
</div>
