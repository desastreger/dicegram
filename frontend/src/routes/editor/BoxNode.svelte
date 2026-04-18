<script lang="ts">
	type BoxData = { label: string; fill?: string; stroke?: string };
	let { data, width, height }: { data: BoxData; width?: number; height?: number } = $props();
	const fill = $derived(data.fill ?? 'var(--th-panel, rgba(56, 70, 95, 0.25))');
	const stroke = $derived(data.stroke ?? 'var(--th-panel-border, #475569)');
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
		border-radius: 8px;
		pointer-events: none;
	}
	.label {
		position: absolute;
		top: 4px;
		left: 10px;
		font-size: 10px;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--th-muted, #cbd5e1);
		background: var(--th-bg, rgba(15, 23, 42, 0.85));
		padding: 1px 6px;
		border-radius: 4px;
	}
</style>
