<script lang="ts">
	// Shared "ⓘ" hint icon: the tooltip is the native title attribute, same as the
	// search bar's help icon this was extracted from. `text` may contain \n — browsers
	// render newlines inside a title tooltip.
	let { text, class: className = 'h-5 w-5' }: { text: string; class?: string } = $props();
</script>

<span
	class="inline-flex shrink-0 cursor-help items-center text-gray-400"
	title={text}
	aria-label={text}
	role="img"
>
	<svg class={className} fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
		<path
			stroke-linecap="round"
			stroke-linejoin="round"
			d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
		></path>
	</svg>
</span>
