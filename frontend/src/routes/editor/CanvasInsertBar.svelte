<script lang="ts">
	import Icon from '$lib/Icon.svelte';

	// Icon bar rendered above the canvas. Each button is draggable —
	// dragging it onto the xyflow viewport drops a new pinned node at the
	// drop point. The dragged payload is the shape keyword; the canvas's
	// drop handler does the actual coordinate math + DSL rewrite.
	const SHAPES: { id: string; icon: string; title: string }[] = [
		{ id: 'circle', icon: 'shape-circle', title: 'Drag onto canvas — start / end' },
		{ id: 'diamond', icon: 'shape-diamond', title: 'Drag onto canvas — decision' },
		{ id: 'stadium', icon: 'shape-stadium', title: 'Drag onto canvas — terminal' },
		{ id: 'rect', icon: 'shape-rect', title: 'Drag onto canvas — process' },
		{ id: 'rounded', icon: 'shape-rounded', title: 'Drag onto canvas — sub-process' },
		{ id: 'hexagon', icon: 'shape-hexagon', title: 'Drag onto canvas — preparation' },
		{ id: 'parallelogram', icon: 'shape-parallelogram', title: 'Drag onto canvas — data i/o' },
		{ id: 'cylinder', icon: 'shape-cylinder', title: 'Drag onto canvas — datastore' }
	];

	function onDragStart(e: DragEvent, shape: string) {
		if (!e.dataTransfer) return;
		e.dataTransfer.setData('application/x-dicegram-shape', shape);
		e.dataTransfer.effectAllowed = 'copy';
	}
</script>

<div
	class="flex items-center gap-1 border-b px-2 py-1 text-xs"
	style:background-color="var(--th-panel, #0a0a0a)"
	style:border-color="var(--th-panel-border, #262626)"
>
	<span
		class="mr-2 text-[10px] uppercase tracking-wider"
		style:color="var(--th-muted, #737373)"
	>
		Drag onto canvas
	</span>
	{#each SHAPES as s (s.id)}
		<button
			type="button"
			draggable="true"
			title={s.title}
			ondragstart={(e) => onDragStart(e, s.id)}
			class="flex h-6 w-6 items-center justify-center rounded hover:bg-neutral-800"
			style:color="var(--th-muted, #9ca3af)"
		>
			<Icon name={s.icon} size={14} />
		</button>
	{/each}
</div>
