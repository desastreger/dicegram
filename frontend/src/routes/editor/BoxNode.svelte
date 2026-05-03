<script lang="ts">
	// Container box (`box "Label" { … }`). Both fill and stroke fall back to
	// theme tokens when the author hasn't pinned an inline colour, so a box
	// re-skins automatically when the user swaps light ↔ dark. Inline DSL
	// styles (`{fill:#abc}`) still win.
	type BoxData = { label: string; fill?: string; stroke?: string };
	let { data, width, height }: { data: BoxData; width?: number; height?: number } = $props();
	const fill = $derived(
		data.fill ?? 'var(--th-panel-muted, var(--th-panel, var(--app-surface-2)))'
	);
	const stroke = $derived(data.stroke ?? 'var(--th-panel-border, var(--app-border))');
</script>

<div
	class="box"
	style:width="{width}px"
	style:height="{height}px"
	style:background={fill}
	style:border-color={stroke}
>
	<div class="label">{data.label}</div>
</div>

<style>
	.box {
		position: relative;
		border-width: 1px;
		border-style: solid;
		border-radius: var(--th-radius-md, 8px);
		pointer-events: none;
	}
	/* The corner label sits inside the top edge. It's a tiny pill so it
	   needs to read against the canvas behind it — both colour AND
	   background come from theme tokens. */
	.label {
		position: absolute;
		top: 4px;
		left: 10px;
		font-size: 10px;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--th-muted, var(--app-text-muted));
		background: var(--th-bg, var(--app-bg));
		padding: 1px 6px;
		border-radius: var(--th-radius-sm, var(--app-radius-sm));
	}
</style>
