<script lang="ts">
	type NoteData = { text: string };
	let { data, width, height }: { data: NoteData; width?: number; height?: number } = $props();
</script>

<div class="note" style:width="{width}px" style:height="{height}px">
	<div class="text">{data.text}</div>
</div>

<style>
	.note {
		position: relative;
		background: #fde68a;
		color: #422006;
		border: 1px solid #b45309;
		border-radius: 4px;
		padding: 8px 10px;
		font-size: 12px;
		line-height: 1.3;
		box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.4);
	}
	.text {
		white-space: pre-wrap;
	}
</style>
