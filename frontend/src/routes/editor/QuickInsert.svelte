<script lang="ts">
	import Icon from '$lib/Icon.svelte';
	import {
		addNode,
		addEdge,
		addSwimlane,
		addBox,
		addGroup,
		addNote,
		nextNodeName,
		nextLabel
	} from '$lib/patch';

	type Position = { x: number; y: number } | null;

	let {
		source = $bindable(''),
		/** Return the position where a new shape should be pinned (canvas
		 *  viewport centre) or null to let auto-layout place it. */
		positionFor = () => null as Position
	}: {
		source: string;
		positionFor?: () => Position;
	} = $props();

	// Semantic groups — each renders as its own cluster so the shape menu
	// reads as "here are the flow-control primitives, here are the work
	// shapes, here are the data shapes" instead of an undifferentiated
	// strip of eight icons.
	const SHAPE_GROUPS: { key: string; shapes: { id: string; icon: string; title: string }[] }[] = [
		{
			key: 'flow',
			shapes: [
				{ id: 'circle', icon: 'shape-circle', title: 'Circle — start / end' },
				{ id: 'diamond', icon: 'shape-diamond', title: 'Diamond — decision' },
				{ id: 'stadium', icon: 'shape-stadium', title: 'Stadium — terminal / boundary' }
			]
		},
		{
			key: 'process',
			shapes: [
				{ id: 'rect', icon: 'shape-rect', title: 'Rectangle — process / task' },
				{ id: 'rounded', icon: 'shape-rounded', title: 'Rounded — sub-process' },
				{ id: 'hexagon', icon: 'shape-hexagon', title: 'Hexagon — preparation' }
			]
		},
		{
			key: 'data',
			shapes: [
				{ id: 'parallelogram', icon: 'shape-parallelogram', title: 'Parallelogram — data i/o' },
				{ id: 'cylinder', icon: 'shape-cylinder', title: 'Cylinder — datastore' }
			]
		}
	];

	function insertShape(shape: string) {
		const name = nextNodeName(source);
		const label = name.charAt(0).toUpperCase() + name.slice(1);
		source = addNode(source, {
			name,
			shape,
			label,
			position: positionFor() ?? undefined
		});
	}

	function insertEdge() {
		// Connect the last two shapes — the most common follow-up to adding a shape.
		const ids: string[] = [];
		const re = /^\s*\[\w+\]\s+(\w+)\s+"/gm;
		for (const m of source.matchAll(re)) ids.push(m[1]);
		if (ids.length < 2) return;
		source = addEdge(source, { src: ids[ids.length - 2], dst: ids[ids.length - 1] });
	}

	function insertSwimlane() {
		source = addSwimlane(source, nextLabel(source, 'swimlane', 'Swimlane'));
	}

	function insertBox() {
		source = addBox(source, { label: nextLabel(source, 'box', 'Box') });
	}

	function insertGroup() {
		source = addGroup(source, nextLabel(source, 'group', 'Group'));
	}

	function insertNote() {
		const re = /^\s*\[\w+\]\s+(\w+)\s+"/gm;
		const ids: string[] = [];
		for (const m of source.matchAll(re)) ids.push(m[1]);
		if (ids.length === 0) return;
		source = addNote(source, 'Note text', ids[ids.length - 1]);
	}
</script>

<div class="border-b border-neutral-800 bg-neutral-950 px-2 py-1">
	<!-- Row 1: shape primitives, grouped by semantic cluster. -->
	<div class="flex flex-wrap items-center gap-0.5" aria-label="Insert shape">
		{#each SHAPE_GROUPS as group, gi (group.key)}
			{#if gi > 0}
				<span class="mx-1 h-4 w-px bg-neutral-800" aria-hidden="true"></span>
			{/if}
			{#each group.shapes as s (s.id)}
				<button
					type="button"
					onclick={() => insertShape(s.id)}
					title={s.title}
					aria-label={s.title}
					class="rounded p-1 text-neutral-400 hover:bg-neutral-900 hover:text-white"
				>
					<Icon name={s.icon} size={16} />
				</button>
			{/each}
		{/each}
	</div>

	<!-- Row 2: connectors + containers — the meta stuff that wraps or connects shapes. -->
	<div class="mt-0.5 flex flex-wrap items-center gap-0.5" aria-label="Insert connector or container">
		<button
			type="button"
			onclick={insertEdge}
			title="Connect the last two shapes"
			aria-label="Insert connection between the last two shapes"
			class="flex items-center gap-1 rounded px-1.5 py-1 text-[11px] text-neutral-400 hover:bg-neutral-900 hover:text-white"
		>
			<Icon name="arrow-right" size={14} />
			<span>Connect</span>
		</button>
		<span class="mx-1 h-4 w-px bg-neutral-800" aria-hidden="true"></span>
		<button
			type="button"
			onclick={insertSwimlane}
			title="Insert swimlane"
			aria-label="Insert swimlane"
			class="rounded px-1.5 py-1 text-[11px] text-neutral-400 hover:bg-neutral-900 hover:text-white"
		>
			+ Lane
		</button>
		<button
			type="button"
			onclick={insertBox}
			title="Insert box inside the nearest swimlane"
			aria-label="Insert box"
			class="rounded px-1.5 py-1 text-[11px] text-neutral-400 hover:bg-neutral-900 hover:text-white"
		>
			+ Box
		</button>
		<button
			type="button"
			onclick={insertGroup}
			title="Insert group overlay"
			aria-label="Insert group"
			class="rounded px-1.5 py-1 text-[11px] text-neutral-400 hover:bg-neutral-900 hover:text-white"
		>
			+ Group
		</button>
		<button
			type="button"
			onclick={insertNote}
			title="Insert sticky note attached to the last shape"
			aria-label="Insert note"
			class="rounded px-1.5 py-1 text-[11px] text-neutral-400 hover:bg-neutral-900 hover:text-white"
		>
			+ Note
		</button>
	</div>
</div>
