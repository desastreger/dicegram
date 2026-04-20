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

	// — Row 1: containers / structural wrappers that frame nodes.
	// — Row 2: shapes (nodes), grouped by semantic cluster.
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

	// — Row 3: connectors. Each button inserts an edge between the last
	// two shapes with a specific (kind, end-decoration) pairing. Glyphs
	// use Unicode so no extra SVG work — they're the visual shorthand
	// authors already recognise from Mermaid / draw.io.
	type Kind = 'solid' | 'dashed' | 'thick' | 'solid_line' | 'dotted_line';
	const CONNECTORS: {
		key: string;
		glyph: string;
		title: string;
		kind: Kind;
		end?: string;
	}[] = [
		{ key: 'solid', glyph: '→', title: 'Solid arrow — sequence', kind: 'solid' },
		{ key: 'dashed', glyph: '⇢', title: 'Dashed arrow — message / conditional', kind: 'dashed' },
		{ key: 'thick', glyph: '⇒', title: 'Thick arrow — critical path', kind: 'thick' },
		{ key: 'line', glyph: '—', title: 'Line — association, no arrow', kind: 'solid_line' },
		{ key: 'dotted', glyph: '⋯', title: 'Dotted line — dependency, no arrow', kind: 'dotted_line' },
		{ key: 'circle', glyph: '●→', title: 'Circle tip — bulb / aggregation', kind: 'solid', end: 'circle' },
		{ key: 'diamond', glyph: '◆→', title: 'Diamond tip — composition-lite', kind: 'solid', end: 'diamond' },
		{ key: 'tee', glyph: '⊤', title: 'Tee tip — stop / must-not', kind: 'solid_line', end: 'tee' }
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

	function lastTwoNodeIds(): [string, string] | null {
		const ids: string[] = [];
		const re = /^\s*\[\w+\]\s+(\w+)\s+"/gm;
		for (const m of source.matchAll(re)) ids.push(m[1]);
		if (ids.length < 2) return null;
		return [ids[ids.length - 2], ids[ids.length - 1]];
	}

	function insertConnector(c: (typeof CONNECTORS)[number]) {
		const pair = lastTwoNodeIds();
		if (!pair) return;
		const [src, dst] = pair;
		const attrs: Record<string, string> = {};
		if (c.end) attrs.end = c.end;
		source = addEdge(source, { src, dst, kind: c.kind, attrs });
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
	<!-- Row 1 — CONTAINERS: frame or annotate groups of nodes. -->
	<div class="flex flex-wrap items-center gap-0.5" aria-label="Insert container">
		<span class="mr-1 w-16 text-[9px] uppercase tracking-wider text-neutral-600">Containers</span>
		<button
			type="button"
			onclick={insertSwimlane}
			title="Insert swimlane"
			class="rounded px-1.5 py-1 text-[11px] text-neutral-400 hover:bg-neutral-900 hover:text-white"
		>
			+ Lane
		</button>
		<button
			type="button"
			onclick={insertBox}
			title="Insert box inside the nearest swimlane"
			class="rounded px-1.5 py-1 text-[11px] text-neutral-400 hover:bg-neutral-900 hover:text-white"
		>
			+ Box
		</button>
		<button
			type="button"
			onclick={insertGroup}
			title="Insert group overlay"
			class="rounded px-1.5 py-1 text-[11px] text-neutral-400 hover:bg-neutral-900 hover:text-white"
		>
			+ Group
		</button>
		<button
			type="button"
			onclick={insertNote}
			title="Insert sticky note attached to the last shape"
			class="rounded px-1.5 py-1 text-[11px] text-neutral-400 hover:bg-neutral-900 hover:text-white"
		>
			+ Note
		</button>
	</div>

	<!-- Row 2 — NODES (shapes), grouped by semantic cluster. -->
	<div class="mt-0.5 flex flex-wrap items-center gap-0.5" aria-label="Insert shape">
		<span class="mr-1 w-16 text-[9px] uppercase tracking-wider text-neutral-600">Nodes</span>
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

	<!-- Row 3 — CONNECTORS: link the last two shapes with a specific line + tip combo. -->
	<div class="mt-0.5 flex flex-wrap items-center gap-0.5" aria-label="Insert connector">
		<span class="mr-1 w-16 text-[9px] uppercase tracking-wider text-neutral-600">Connectors</span>
		{#each CONNECTORS as c, ci (c.key)}
			{#if ci === 5}
				<span class="mx-1 h-4 w-px bg-neutral-800" aria-hidden="true"></span>
			{/if}
			<button
				type="button"
				onclick={() => insertConnector(c)}
				title={c.title}
				aria-label={c.title}
				class="min-w-[28px] rounded px-1.5 py-1 text-center font-mono text-[12px] text-neutral-400 hover:bg-neutral-900 hover:text-white"
			>
				{c.glyph}
			</button>
		{/each}
	</div>
</div>
