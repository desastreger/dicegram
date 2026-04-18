<script lang="ts">
	type LaneData = { name: string };
	let { data, width, height }: { data: LaneData; width?: number; height?: number } = $props();
</script>

<div class="lane" style:width="{width}px" style:height="{height}px">
	<div class="label">{data.name}</div>
</div>

<style>
	.lane {
		position: relative;
		background: var(--th-panel, rgba(30, 41, 59, 0.35));
		opacity: 0.5;
		border: 1px dashed var(--th-panel-border, #334155);
		border-radius: 10px;
		pointer-events: none;
	}
	.label {
		position: absolute;
		top: 6px;
		left: 12px;
		font-size: 11px;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--th-muted, #94a3b8);
	}
</style>
