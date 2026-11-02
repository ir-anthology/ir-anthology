<script lang="ts">
	import { browser } from '$app/environment';
	import { anchoredMenu } from '$lib/anchoredMenu';
	import type { Density } from '$lib/rowDensity';

	let { density, onChange }: { density: Density; onChange: (d: Density) => void } = $props();

	let isOpen = $state(false);
	let dropdownRef: HTMLElement | null = $state(null);
	let anchorRef: HTMLElement | null = $state(null);
	let menuRef: HTMLElement | null = $state(null);

	function handleClickOutside(event: MouseEvent) {
		const target = event.target as Node;
		// menuRef is portaled to <body>, so it is NOT inside dropdownRef
		if (dropdownRef?.contains(target) || menuRef?.contains(target)) return;
		isOpen = false;
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
		bind:this={anchorRef}
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
			<circle cx="11" cy="11" r="7" />
			<path stroke-linecap="round" d="M21 21l-4.35-4.35" />
			<path stroke-linecap="round" d="M11 8v6M8 11h6" />
		</svg>
	</button>

	{#if isOpen}
		<div
			bind:this={menuRef}
			use:anchoredMenu={{ anchor: anchorRef }}
			class="fixed w-max min-w-40 overflow-y-auto bg-white rounded-lg shadow-lg border border-gray-200 z-[60]"
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
