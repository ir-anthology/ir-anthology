<script lang="ts">
	import { ALL_COLUMNS, DEFAULT_COLUMNS } from '$lib/columnPreferences';
	import { browser } from '$app/environment';

	let { visibleColumns, onToggle, onReset }: {
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
		for (const col of ALL_COLUMNS) {
			if (!visibleColumns.includes(col)) {
				onToggle(col);
			}
		}
	}

	function deselectAll() {
		for (const col of ALL_COLUMNS) {
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
			viewBox="0 0 20 20"
			fill="currentColor"
		>
			<path
				fill-rule="evenodd"
				d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z"
				clip-rule="evenodd"
			/>
		</svg>
	</button>

	{#if isOpen}
		<div
			class="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 z-50"
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
					{#each ALL_COLUMNS as col (col)}
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
