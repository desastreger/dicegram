<script lang="ts">
	type Align = 'left' | 'center' | 'right';
	type LaneData = { name: string; titleAlign?: Align };
	let { data, width, height }: { data: LaneData; width?: number; height?: number } = $props();
	const align: Align = $derived(data.titleAlign ?? 'left');
</script>

<div class="lane" style:width="{width}px" style:height="{height}px">
	<div class="label" data-align={align}>{data.name}</div>
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
		font-size: 11px;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--th-muted, var(--app-text-muted));
	}
	/* Title alignment is toggleable via DSL `setting lane_title_align`
	   (global) or inline `swimlane "X" {title_align: …}` once that's
	   wired through the parser. */
	.label[data-align='left']   { left: 12px; }
	.label[data-align='center'] { left: 50%; transform: translateX(-50%); }
	.label[data-align='right']  { right: 12px; }
</style>
