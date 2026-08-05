<script lang="ts">
	import Icon from '$lib/Icon.svelte';
	import {
		addNode,
		addEdge,
		addSwimlane,
		addBox,
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

	// Only these keywords declare a node. The previous `/^\s*\[\w+\]/` matched
	// ANY bracket keyword, so `[note]` and `[solid_line]` lines counted as
	// shapes — which let "+ Note" attach a note to a note, and made the
	// connector buttons emit an edge pointing at a note id, which the compiler
	// then pruned while reporting "unknown 'note_1'" about an id declared two
	// lines above.
	const SHAPE_IDS = new Set(SHAPE_GROUPS.flatMap((g) => g.shapes.map((s) => s.id)));

	function declaredNodeIds(): string[] {
		const ids: string[] = [];
		const re = /^\s*\[(\w+)\]\s+(\w+)\s+"/gm;
		for (const m of source.matchAll(re)) {
			if (SHAPE_IDS.has(m[1])) ids.push(m[2]);
		}
		return ids;
	}

	function lastTwoNodeIds(): [string, string] | null {
		const ids = declaredNodeIds();
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
	/** The swimlane a new box belongs to — the last one declared. */
	function nearestSwimlane(): string | null {
		const re = /^\s*swimlane\s+"([^"]+)"\s*\{/gm;
		let last: string | null = null;
		for (const m of source.matchAll(re)) last = m[1];
		return last;
	}

	function insertBox() {
		// Without passing `swimlane`, patch.ts's lane-placement branch was
		// unreachable, so this appended a tab-indented orphan *after* the
		// lane's closing brace and rendered nothing — despite the button
		// tooltip promising "inside the nearest swimlane".
		source = addBox(source, {
			label: nextLabel(source, 'box', 'Box'),
			swimlane: nearestSwimlane()
		});
	}
	function insertNote() {
		const ids = declaredNodeIds();
		if (ids.length === 0) return;
		source = addNote(source, 'Note text', ids[ids.length - 1]);
	}
</script>

<div class="border-b border-app bg-surface px-2 py-1">
	<!-- Row 1 — CONTAINERS: frame or annotate groups of nodes. -->
	<div class="flex flex-wrap items-center gap-0.5" aria-label="Insert container">
		<span class="mr-1 w-16 text-[9px] uppercase tracking-wider text-dim">Containers</span>
		<button
			type="button"
			onclick={insertSwimlane}
			title="Insert swimlane"
			class="btn-ghost text-[11px]"
		>
			+ Lane
		</button>
		<button
			type="button"
			onclick={insertBox}
			title="Insert box inside the nearest swimlane"
			class="btn-ghost text-[11px]"
		>
			+ Box
		</button>
		<button
			type="button"
			onclick={insertNote}
			title="Insert sticky note attached to the last shape"
			class="btn-ghost text-[11px]"
		>
			+ Note
		</button>
	</div>

	<!-- Row 2 — NODES (shapes), grouped by semantic cluster. -->
	<div class="mt-0.5 flex flex-wrap items-center gap-0.5" aria-label="Insert shape">
		<span class="mr-1 w-16 text-[9px] uppercase tracking-wider text-dim">Nodes</span>
		{#each SHAPE_GROUPS as group, gi (group.key)}
			{#if gi > 0}
				<span class="divider-v mx-1 h-4" aria-hidden="true"></span>
			{/if}
			{#each group.shapes as s (s.id)}
				<button
					type="button"
					onclick={() => insertShape(s.id)}
					title={s.title}
					aria-label={s.title}
					class="btn-icon"
				>
					<Icon name={s.icon} size={16} />
				</button>
			{/each}
		{/each}
	</div>

	<!-- Row 3 — CONNECTORS: link the last two shapes with a specific line + tip combo. -->
	<div class="mt-0.5 flex flex-wrap items-center gap-0.5" aria-label="Insert connector">
		<span class="mr-1 w-16 text-[9px] uppercase tracking-wider text-dim">Connectors</span>
		{#each CONNECTORS as c, ci (c.key)}
			{#if ci === 5}
				<span class="divider-v mx-1 h-4" aria-hidden="true"></span>
			{/if}
			<button
				type="button"
				onclick={() => insertConnector(c)}
				title={c.title}
				aria-label={c.title}
				class="btn-ghost min-w-[28px] text-center font-mono text-[12px]"
			>
				{c.glyph}
			</button>
		{/each}
	</div>
</div>
