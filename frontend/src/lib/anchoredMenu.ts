/**
 * Positions a dropdown panel against the viewport instead of against its parent,
 * so it is always fully on screen.
 *
 * The table's column/density menus live inside the frozen Entity <th>, which is
 * `sticky ... z-20` and therefore opens a stacking context. Two things follow
 * from that, and both were visible before this existed:
 *   - a plain `absolute ... z-50` panel still paints BELOW the sidebar, because
 *     the whole <th> subtree is capped at the th's z-20 while the sidebar is
 *     z-40 in the root stacking context;
 *   - `right-0` anchors the panel's right edge to the button and grows leftwards,
 *     which runs off the left edge of the window now that the table sits flush
 *     against it when the sidebar is closed.
 * Moving the node to <body> escapes the stacking context, and placing it from the
 * anchor's viewport rect makes the result independent of the sidebar.
 */
export type AnchoredMenuParams = {
	/** The trigger the panel hangs off. */
	anchor: HTMLElement | null | undefined;
	/** Keep at least this many px between the panel and the window edge. */
	margin?: number;
	/** Gap between trigger and panel. */
	offset?: number;
};

export function anchoredMenu(node: HTMLElement, params: AnchoredMenuParams) {
	let { anchor, margin = 8, offset = 8 } = params;

	// Portal out of the sticky <th>'s stacking context. Svelte removes the node
	// with node.remove(), which does not care which parent it ended up in.
	document.body.appendChild(node);

	function place() {
		if (!anchor?.isConnected) return;
		const a = anchor.getBoundingClientRect();

		// Never let the panel be wider or taller than the window.
		node.style.maxWidth = `${window.innerWidth - 2 * margin}px`;
		node.style.maxHeight = `${window.innerHeight - 2 * margin}px`;

		const { offsetWidth: w, offsetHeight: h } = node;

		// Grow rightwards from the trigger: that is into the table, away from the
		// sidebar. Then clamp, so a narrow window pulls it back on screen.
		const left = Math.min(Math.max(a.left, margin), Math.max(margin, window.innerWidth - w - margin));

		// Below the trigger, flipping above only if that would overflow.
		let top = a.bottom + offset;
		if (top + h > window.innerHeight - margin) {
			const above = a.top - h - offset;
			top = above >= margin ? above : Math.max(margin, window.innerHeight - h - margin);
		}

		node.style.left = `${Math.round(left)}px`;
		node.style.top = `${Math.round(top)}px`;
	}

	place();

	// The panel's own size settles after layout (w-max), and the table scrolls
	// horizontally inside the page, so watch both.
	const resizeObserver = new ResizeObserver(place);
	resizeObserver.observe(node);
	window.addEventListener('resize', place);
	window.addEventListener('scroll', place, true);

	return {
		update(next: AnchoredMenuParams) {
			({ anchor, margin = 8, offset = 8 } = next);
			place();
		},
		destroy() {
			resizeObserver.disconnect();
			window.removeEventListener('resize', place);
			window.removeEventListener('scroll', place, true);
			node.remove();
		}
	};
}
