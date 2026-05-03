<script lang="ts">
	type LaneData = { name: string };
	let { data, width, height }: { data: LaneData; width?: number; height?: number } = $props();
</script>

<div class="lane" style:width="{width}px" style:height="{height}px">
	<div class="label">{data.name}</div>
</div>

<style>
	/* Swimlane backdrop. Theme-driven so the half-opaque panel-muted reads
	   correctly on both warm-cream and slate-dark canvases. */
	.lane {
		position: relative;
		background: var(--th-panel-muted, var(--th-panel, var(--app-surface-2)));
		opacity: 0.5;
		border: 1px dashed var(--th-panel-border, var(--app-border));
		border-radius: var(--th-radius-md, var(--app-radius));
		pointer-events: none;
	}
	.label {
		position: absolute;
		top: 6px;
		left: 12px;
		font-size: 11px;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--th-muted, var(--app-text-muted));
	}
</style>
