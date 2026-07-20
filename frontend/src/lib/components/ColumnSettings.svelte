<script lang="ts">
	import { browser } from '$app/environment';

	let { availableColumns, visibleColumns, onToggle, onReset }: {
		availableColumns: string[];
		visibleColumns: string[];
		onToggle: (column: string) => void;
		onReset: () => void;
	} = $props();

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

	function selectAll() {
		for (const col of availableColumns) {
			if (!visibleColumns.includes(col)) {
				onToggle(col);
			}
		}
	}

	function deselectAll() {
		for (const col of availableColumns) {
			if (visibleColumns.includes(col)) {
				onToggle(col);
			}
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
</script>

<div class="relative" bind:this={dropdownRef}>
	<button
		class="p-1.5 rounded hover:bg-gray-100 transition-colors"
		onclick={() => (isOpen = !isOpen)}
		aria-label="Column settings"
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
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				d="M9 4.5v15m6-15v15m-10.875 0h15.75c.621 0 1.125-.504 1.125-1.125V5.625c0-.621-.504-1.125-1.125-1.125H4.125C3.504 4.5 3 5.004 3 5.625v12.75c0 .621.504 1.125 1.125 1.125Z"
			/>
			<path stroke-linecap="round" d="M3 9.5h18" />
			<path fill="currentColor" stroke="none" d="M10 13h12l-6 9.6z" />
		</svg>
	</button>

	{#if isOpen}
		<div
			class="absolute right-0 mt-2 w-max min-w-56 bg-white rounded-lg shadow-lg border border-gray-200 z-50"
			role="menu"
			aria-orientation="vertical"
			aria-labelledby="column-settings-menu"
		>
			<div class="p-3">
				<div class="flex items-center justify-between mb-3">
					<span class="text-xs font-medium text-gray-500 tracking-wider uppercase"
						>Columns</span
					>
					<div class="flex gap-2">
						<button
							class="text-xs text-link hover:text-link-hover transition-colors"
							onclick={selectAll}>All</button
						>
						<span class="text-gray-300">|</span>
						<button
							class="text-xs text-link hover:text-link-hover transition-colors"
							onclick={deselectAll}>None</button
						>
					</div>
				</div>

				<div class="flex flex-col gap-1">
					{#each availableColumns as col (col)}
						<label
							class="flex items-center gap-2 px-2 py-1 rounded hover:bg-gray-50 cursor-pointer transition-colors"
						>
							<input
								type="checkbox"
								checked={visibleColumns.includes(col)}
								onchange={() => onToggle(col)}
								class="h-4 w-4 rounded border-gray-300 text-link focus:ring-link/30"
							/>
							<span class="text-sm text-gray-700">{col}</span>
						</label>
					{/each}
				</div>

				<div class="mt-3 pt-3 border-t border-gray-200">
					<button
						class="text-xs text-link hover:text-link-hover transition-colors"
						onclick={onReset}
					>
						Reset to defaults
					</button>
				</div>
			</div>
		</div>
	{/if}
</div>
