<script lang="ts">
	import { useSvelteFlow } from '@xyflow/svelte';
	import { onMount } from 'svelte';

	// Mounted inside `<SvelteFlow>` so `useSvelteFlow()` picks up the
	// flow context. Listens for drop events on the flow's DOM wrapper and
	// reports the drop in world (flow) coordinates to the parent.
	let { onDropShape }: { onDropShape?: (shape: string, pos: { x: number; y: number }) => void } = $props();

	const flow = useSvelteFlow();

	function handleDragOver(e: DragEvent) {
		if (!e.dataTransfer) return;
		if (!Array.from(e.dataTransfer.types).includes('application/x-dicegram-shape')) return;
		e.preventDefault();
		e.dataTransfer.dropEffect = 'copy';
	}

	function handleDrop(e: DragEvent) {
		const shape = e.dataTransfer?.getData('application/x-dicegram-shape');
		if (!shape) return;
		e.preventDefault();
		const pos = flow.screenToFlowPosition({ x: e.clientX, y: e.clientY });
		onDropShape?.(shape, pos);
	}

	onMount(() => {
		const wrapper = document.querySelector<HTMLDivElement>('.svelte-flow');
		if (!wrapper) return;
		wrapper.addEventListener('dragover', handleDragOver);
		wrapper.addEventListener('drop', handleDrop);
		return () => {
			wrapper.removeEventListener('dragover', handleDragOver);
			wrapper.removeEventListener('drop', handleDrop);
		};
	});
</script>
