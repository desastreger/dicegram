<script lang="ts">
	type NoteData = { text: string };
	let { data, width, height }: { data: NoteData; width?: number; height?: number } = $props();
</script>

<div class="note" style:width="{width}px" style:height="{height}px">
	<div class="text">{data.text}</div>
</div>

<style>
	/* Sticky-note rendering. Every visible property is theme-driven so the
	   note adapts cleanly between light and dark — the warm-yellow hex
	   fallbacks only kick in if no theme is wired in. The drop shadow comes
	   from `--th-shadow-sm` so it softens to barely-there in light mode and
	   stays visible in dark mode. */
	.note {
		position: relative;
		background: var(--th-note-fill, color-mix(in oklab, var(--app-warn) 22%, var(--app-bg)));
		color: var(--th-note-text, var(--app-text));
		border: 1px solid var(--th-note-border, var(--app-warn));
		border-radius: var(--th-radius-sm, var(--app-radius-sm));
		padding: 8px 10px;
		font-size: 12px;
		line-height: 1.3;
		box-shadow: var(--th-shadow-sm, var(--app-shadow-sm));
		/* Centre the label both axes — labels inside any component should
		   read as one block rather than top-left text floating in a frame. */
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.text {
		white-space: pre-wrap;
		text-align: center;
	}
</style>
