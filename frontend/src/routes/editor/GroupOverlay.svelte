<script lang="ts">
	type GroupData = { name: string };
	let { data, width, height }: { data: GroupData; width?: number; height?: number } = $props();
</script>

<div class="overlay" style:width="{width}px" style:height="{height}px">
	<div class="label">{data.name}</div>
</div>

<style>
	/* Group overlay border + label. Both border and label colour come from
	   the dedicated `--th-group-border` / `--th-group-label` tokens so a
	   theme can pick a different group accent than the global one. The
	   pill background is the canvas colour so it cuts cleanly out of the
	   dashed border. */
	.overlay {
		position: relative;
		border: 1.5px dashed var(--th-group-border, var(--th-accent, var(--app-warn)));
		border-radius: var(--th-radius-lg, var(--app-radius-lg));
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
		color: var(--th-group-label, var(--th-accent, var(--app-warn)));
		background: var(--th-bg, var(--app-bg));
		padding: 1px 8px;
		border-radius: var(--th-radius-sm, var(--app-radius-sm));
	}
</style>
