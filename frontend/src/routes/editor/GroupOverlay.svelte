<script lang="ts">
	type GroupData = { name: string };
	let { data, width, height }: { data: GroupData; width?: number; height?: number } = $props();
</script>

<div class="overlay" style:width="{width}px" style:height="{height}px">
	<div class="label">{data.name}</div>
</div>

<style>
	.overlay {
		position: relative;
		border: 1.5px dashed var(--th-accent, #f59e0b);
		border-radius: 12px;
		background: transparent;
		pointer-events: none;
	}
	.label {
		position: absolute;
		top: -10px;
		left: 16px;
		font-size: 10px;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: var(--th-accent, #f59e0b);
		background: var(--th-bg, #0a0a0a);
		padding: 1px 8px;
		border-radius: 4px;
	}
</style>
