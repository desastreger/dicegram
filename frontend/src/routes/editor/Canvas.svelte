<script lang="ts">
	import {
		SvelteFlow,
		Background,
		Controls,
		MiniMap,
		ConnectionMode,
		MarkerType,
		type Node,
		type Edge,
		type EdgeMarker
	} from '@xyflow/svelte';
	import '@xyflow/svelte/dist/style.css';
	import ShapeNode from './ShapeNode.svelte';
	import LaneNode from './LaneNode.svelte';
	import BoxNode from './BoxNode.svelte';
	import GroupOverlay from './GroupOverlay.svelte';
	import NoteNode from './NoteNode.svelte';
	import SmartEdge from './SmartEdge.svelte';
	import CanvasFocus from './CanvasFocus.svelte';
	import ViewportRegister from './ViewportRegister.svelte';
	import type { RenderResult, RenderNode } from '$lib/render';
	import type { Theme } from '$lib/themes';
	import type { Rect } from '$lib/obstacle-routing';

	import type { ParentTarget } from '$lib/patch';

	let {
		result,
		theme,
		selectedId,
		filter = '',
		lineStyle = 'orthogonal',
		focusId = null,
		focusTrigger = 0,
		fitAllTrigger = 0,
		onNodeMove,
		onNodeSelect,
		onNodeDblClick,
		onEdgeSelect,
		onObjectSelect,
		onConnect,
		onReparent
	}: {
		result: RenderResult | null;
		theme: Theme;
		selectedId?: string | null;
		filter?: string;
		lineStyle?: 'orthogonal' | 'curved' | 'straight';
		focusId?: string | null;
		focusTrigger?: number;
		fitAllTrigger?: number;
		onNodeMove?: (id: string, x: number, y: number) => void;
		onNodeSelect?: (id: string | null) => void;
		onNodeDblClick?: (id: string) => void;
		onEdgeSelect?: (id: string | null) => void;
		onObjectSelect?: (
			kind: 'swimlane' | 'box' | 'group' | 'note' | null,
			index: number
		) => void;
		onConnect?: (source: string, target: string) => void;
		onReparent?: (id: string, target: ParentTarget) => void;
	} = $props();

	function tokenMatches(n: RenderNode, t: string): boolean {
		const kv = /^(\w+):(.+)$/.exec(t);
		if (kv) {
			const key = kv[1].toLowerCase();
			const val = kv[2].toLowerCase();
			const contains = (hay: string) => hay.toLowerCase().includes(val);
			if (key === 'owner') return contains(n.attrs.owner ?? '');
			if (key === 'type') return contains(n.attrs.type ?? '');
			if (key === 'status') return contains(n.attrs.status ?? '');
			if (key === 'priority') return contains(n.attrs.priority ?? '');
			if (key === 'shape') return contains(n.shape);
			if (key === 'tag' || key === 'tags') {
				const tags = (n.attrs.tags ?? '')
					.toLowerCase()
					.split(',')
					.map((s) => s.trim());
				return tags.some((tag) => tag.includes(val));
			}
			if (key === 'lane' || key === 'swimlane') {
				return contains(n.swimlane ?? '');
			}
			if (key === 'box') return contains(n.box ?? '');
		}
		if (t.startsWith('#')) {
			const tag = t.slice(1).toLowerCase();
			const tags = (n.attrs.tags ?? '')
				.toLowerCase()
				.split(',')
				.map((s) => s.trim());
			return tags.some((x) => x.includes(tag));
		}
		const needle = t.toLowerCase();
		return n.id.toLowerCase().includes(needle) || n.label.toLowerCase().includes(needle);
	}

	function matchNode(n: RenderNode, query: string): boolean {
		const trimmed = query.trim();
		if (!trimmed) return true;
		return trimmed.split(/\s+/).every((tok) => tokenMatches(n, tok));
	}

	let nodes = $state.raw<Node[]>([]);
	let edges = $state.raw<Edge[]>([]);

	const nodeTypes = {
		shape: ShapeNode,
		lane: LaneNode,
		box: BoxNode,
		group: GroupOverlay,
		note: NoteNode
	};

	const edgeTypes = {
		smart: SmartEdge
	};

	function edgeStyle(kind: string): { strokeDasharray?: string; strokeWidth: number } {
		switch (kind) {
			case 'dashed':
				return { strokeDasharray: '6 4', strokeWidth: 1.5 };
			case 'thick':
				return { strokeWidth: 3 };
			case 'dotted_line':
				return { strokeDasharray: '2 4', strokeWidth: 1.5 };
			case 'solid_line':
				return { strokeWidth: 1.5 };
			default:
				return { strokeWidth: 1.5 };
		}
	}

	function hasArrow(kind: string): boolean {
		return kind === 'solid' || kind === 'dashed' || kind === 'thick';
	}

	// For `arrow` / `open_arrow` we use xyflow's built-in MarkerType — it
	// auto-creates the marker inside its own SVG defs, which is the most
	// reliable cross-browser path (no dependence on context-stroke or on
	// a globally-mounted defs block being reachable from xyflow's SVG).
	// For the decorative terminators (circle/diamond/tee/square) we keep
	// the custom markers published by EdgeMarkers.svelte.
	function customMarkerUrl(name: string): string {
		return `url(#dcg-${name})`;
	}

	function endMarkerFor(
		kind: string,
		endAttr: string | undefined | null,
		stroke: string
	): string | EdgeMarker | undefined {
		const attr = (endAttr ?? '').trim().toLowerCase();
		const effective = attr || (hasArrow(kind) ? 'arrow' : 'none');
		if (effective === 'none') return undefined;
		if (effective === 'arrow')
			return { type: MarkerType.ArrowClosed, color: stroke, width: 18, height: 18 };
		if (effective === 'open_arrow')
			return { type: MarkerType.Arrow, color: stroke, width: 20, height: 20 };
		if (effective === 'circle') return customMarkerUrl('circle');
		if (effective === 'diamond') return customMarkerUrl('diamond');
		if (effective === 'tee') return customMarkerUrl('tee');
		if (effective === 'square') return customMarkerUrl('square');
		return undefined;
	}

	function startMarkerFor(
		startAttr: string | undefined | null,
		stroke: string
	): string | EdgeMarker | undefined {
		const attr = (startAttr ?? '').trim().toLowerCase();
		if (!attr || attr === 'none') return undefined;
		if (attr === 'arrow')
			return { type: MarkerType.ArrowClosed, color: stroke, width: 18, height: 18, orient: 'auto-start-reverse' };
		if (attr === 'open_arrow')
			return { type: MarkerType.Arrow, color: stroke, width: 20, height: 20, orient: 'auto-start-reverse' };
		if (attr === 'circle') return customMarkerUrl('circle');
		if (attr === 'diamond') return customMarkerUrl('diamond');
		if (attr === 'tee') return customMarkerUrl('tee');
		if (attr === 'square') return customMarkerUrl('square');
		return undefined;
	}

	function centerOf(n: RenderNode | undefined) {
		if (!n) return { cx: 0, cy: 0 };
		return { cx: n.x + n.width / 2, cy: n.y + n.height / 2 };
	}

	function pickHandles(
		sx: number,
		sy: number,
		tx: number,
		ty: number,
		direction: string,
		selfLoop = false
	) {
		if (selfLoop) {
			// Bow from right back to top so the loop visibly curls around the node.
			return { sourceHandle: 'r', targetHandle: 't' };
		}
		const horizontal = direction === 'left-to-right' || direction === 'right-to-left';
		const dx = tx - sx;
		const dy = ty - sy;
		// Geometry-based: whichever axis has the larger |delta| wins.
		// A vertically-offset pair connects top↔bottom even under a
		// horizontal chart, which matches user expectation ("a connector
		// coming from above should enter the top, not the left").
		// Tie-break toward the chart axis.
		if (Math.abs(dx) > Math.abs(dy) || (Math.abs(dx) === Math.abs(dy) && horizontal)) {
			return dx >= 0
				? { sourceHandle: 'r', targetHandle: 'l' }
				: { sourceHandle: 'l', targetHandle: 'r' };
		}
		return dy >= 0
			? { sourceHandle: 'b', targetHandle: 't' }
			: { sourceHandle: 't', targetHandle: 'b' };
	}

	// Normalize a caller-supplied port to the canonical 't/b/l/r'.
	function normPort(p: string | null | undefined): 't' | 'b' | 'l' | 'r' | null {
		if (!p) return null;
		const s = p.trim().toLowerCase();
		if (s === 't' || s === 'top' || s === 'n' || s === 'north') return 't';
		if (s === 'b' || s === 'bottom' || s === 's' || s === 'south') return 'b';
		if (s === 'l' || s === 'left' || s === 'w' || s === 'west') return 'l';
		if (s === 'r' || s === 'right' || s === 'e' || s === 'east') return 'r';
		return null;
	}

	$effect(() => {
		if (!result) {
			nodes = [];
			edges = [];
			return;
		}

		const dimmedIds = new Set<string>();
		for (const n of result.nodes) {
			if (!matchNode(n, filter)) dimmedIds.add(n.id);
		}
		const filtering = filter.trim().length > 0;
		const liveLanes = new Set<string>();
		const liveBoxes = new Set<string>();
		for (const n of result.nodes) {
			if (dimmedIds.has(n.id)) continue;
			if (n.swimlane) liveLanes.add(n.swimlane);
			if (n.box) liveBoxes.add(n.box);
		}

		const dimStyle = 'opacity: 0.25;';

		const laneNodes: Node[] = result.lanes.map((l, i) => ({
			id: `__lane_${i}`,
			type: 'lane',
			position: { x: l.x, y: l.y },
			width: l.width,
			height: l.height,
			data: { name: l.name },
			draggable: false,
			selectable: true,
			zIndex: -100,
			deletable: false,
			style: filtering && !liveLanes.has(l.name) ? dimStyle : undefined
		}));

		const boxNodes: Node[] = result.boxes
			.filter((b) => b.x != null && b.y != null && b.width != null && b.height != null)
			.map((b, i) => ({
				id: `__box_${i}`,
				type: 'box',
				position: { x: b.x as number, y: b.y as number },
				width: b.width as number,
				height: b.height as number,
				data: { label: b.label, fill: b.style.fill, stroke: b.style.stroke },
				draggable: false,
				selectable: true,
				zIndex: -50,
				deletable: false,
				style: filtering && !liveBoxes.has(b.label) ? dimStyle : undefined
			}));

		const groupNodes: Node[] = result.groups
			.filter((g) => g.x != null && g.y != null && g.width != null && g.height != null)
			.map((g, i) => ({
				id: `__group_${i}`,
				type: 'group',
				position: { x: g.x as number, y: g.y as number },
				width: g.width as number,
				height: g.height as number,
				data: { name: g.name },
				draggable: false,
				selectable: true,
				zIndex: 50,
				deletable: false
			}));

		const noteNodes: Node[] = result.notes.map((n, i) => ({
			id: `__note_${i}`,
			type: 'note',
			position: { x: n.x, y: n.y },
			width: n.width,
			height: n.height,
			data: { text: n.text, target: n.target },
			draggable: false,
			selectable: true,
			zIndex: 10,
			deletable: false
		}));

		const shapeNodes: Node[] = result.nodes.map((n) => {
			const matched = !dimmedIds.has(n.id);
			return {
				id: n.id,
				type: 'shape',
				position: { x: n.x, y: n.y },
				width: n.width,
				height: n.height,
				selected: n.id === selectedId,
				data: {
					shape: n.shape,
					label: n.label,
					fill: n.style.fill,
					stroke: n.style.stroke,
					text: n.style.text,
					rx: n.style.rx,
					font_size: n.style.font_size,
					font_family: n.style.font_family,
					opacity: n.style.opacity,
					stroke_width: n.style.stroke_width,
					attrs: n.attrs,
					dimmed: !matched
				},
				draggable: true,
				selectable: true
			};
		});

		nodes = [...laneNodes, ...boxNodes, ...shapeNodes, ...noteNodes, ...groupNodes];

		const edgeColor = theme.edge;
		const styleFor = (kind: string, override?: string) => {
			const s = edgeStyle(kind);
			const color = override || edgeColor;
			return `stroke: ${color}; stroke-width: ${s.strokeWidth}${s.strokeDasharray ? `; stroke-dasharray: ${s.strokeDasharray}` : ''};`;
		};

		const nodeById = new Map(result.nodes.map((n) => [n.id, n]));

		const shapeRects = new Map<string, Rect>(
			result.nodes.map((n) => [n.id, { x: n.x, y: n.y, w: n.width, h: n.height }])
		);
		const boxRects: Array<Rect & { members: string[] }> = result.boxes
			.filter(
				(b) => b.x != null && b.y != null && b.width != null && b.height != null
			)
			.map((b) => ({
				x: b.x as number,
				y: b.y as number,
				w: b.width as number,
				h: b.height as number,
				members: b.members
			}));

		const dataEdges: Edge[] = result.edges.map((e) => {
			const s = nodeById.get(e.source);
			const t = nodeById.get(e.target);
			const { cx: sx, cy: sy } = centerOf(s);
			const { cx: tx, cy: ty } = centerOf(t);
			const auto = pickHandles(sx, sy, tx, ty, result.direction, e.source === e.target);
			// Explicit port authored in DSL (`A@r -> B@l`) always wins over
			// the smart picker.
			const explicitSource = normPort(e.source_port);
			const explicitTarget = normPort(e.target_port);
			const sourceHandle = explicitSource ?? auto.sourceHandle;
			const targetHandle = explicitTarget ?? auto.targetHandle;
			const strokeOverride = e.attrs?.color;
			const edgeDimmed = dimmedIds.has(e.source) || dimmedIds.has(e.target);

			const obstacles: Rect[] = [];
			for (const [id, r] of shapeRects) {
				if (id === e.source || id === e.target) continue;
				obstacles.push({ x: r.x - 4, y: r.y - 4, w: r.w + 8, h: r.h + 8 });
			}
			for (const b of boxRects) {
				if (b.members.includes(e.source) || b.members.includes(e.target)) continue;
				obstacles.push({ x: b.x, y: b.y, w: b.w, h: b.h });
			}

			const baseStyle = styleFor(e.kind, strokeOverride);
			const edgeColour = strokeOverride || edgeColor;
			const opacityAttr = e.attrs?.opacity;
			const opacityStyle = (() => {
				const n = opacityAttr ? Number(opacityAttr) : NaN;
				if (!Number.isFinite(n) || n < 0 || n > 1) return '';
				return ` opacity: ${n};`;
			})();
			return {
				id: e.id,
				source: e.source,
				target: e.target,
				sourceHandle,
				targetHandle,
				type: 'smart',
				label: e.label || undefined,
				style:
					(edgeDimmed ? `${baseStyle} opacity: 0.2;` : baseStyle) + opacityStyle,
				markerEnd: endMarkerFor(e.kind, e.attrs?.end, edgeColour),
				markerStart: startMarkerFor(e.attrs?.start, edgeColour),
				data: {
					obstacles,
					labelFill: theme.text,
					labelBg: theme.panel,
					lineStyle,
					axis:
						result.direction === 'left-to-right' ||
						result.direction === 'right-to-left'
							? 'horizontal'
							: 'vertical'
				}
			};
		});

		const noteEdges: Edge[] = result.notes.map((n, i) => ({
			id: `__nedge_${i}`,
			source: n.target,
			target: `__note_${i}`,
			type: 'straight',
			style: `stroke: ${theme.muted}; stroke-width: 1; stroke-dasharray: 3 3;`,
			selectable: false,
			deletable: false,
			markerEnd: undefined,
			zIndex: 5
		}));

		edges = [...dataEdges, ...noteEdges];
	});

	function containerAt(px: number, py: number): ParentTarget {
		if (!result) return { kind: 'root' };
		let best: ParentTarget = { kind: 'root' };
		let bestArea = Infinity;
		for (const b of result.boxes) {
			if (
				b.x == null ||
				b.y == null ||
				b.width == null ||
				b.height == null
			)
				continue;
			if (
				px >= b.x &&
				px <= b.x + b.width &&
				py >= b.y &&
				py <= b.y + b.height
			) {
				const area = b.width * b.height;
				if (area < bestArea) {
					best = { kind: 'box', label: b.label, swimlane: b.swimlane };
					bestArea = area;
				}
			}
		}
		if (bestArea !== Infinity) return best;
		for (const l of result.lanes) {
			if (
				px >= l.x &&
				px <= l.x + l.width &&
				py >= l.y &&
				py <= l.y + l.height
			) {
				const area = l.width * l.height;
				if (area < bestArea) {
					best = { kind: 'swimlane', name: l.name };
					bestArea = area;
				}
			}
		}
		return best;
	}

	function sameTarget(a: ParentTarget, b: ParentTarget): boolean {
		if (a.kind !== b.kind) return false;
		if (a.kind === 'swimlane' && b.kind === 'swimlane') return a.name === b.name;
		if (a.kind === 'box' && b.kind === 'box')
			return a.label === b.label && a.swimlane === b.swimlane;
		return true;
	}

	function currentParent(id: string): ParentTarget {
		const n = result?.nodes.find((x) => x.id === id);
		if (!n) return { kind: 'root' };
		if (n.box) return { kind: 'box', label: n.box, swimlane: n.swimlane };
		if (n.swimlane) return { kind: 'swimlane', name: n.swimlane };
		return { kind: 'root' };
	}

	function handleNodeDragStop({
		targetNode
	}: {
		targetNode: Node | null;
		nodes: Node[];
		event: MouseEvent | TouchEvent;
	}) {
		if (!targetNode || targetNode.type !== 'shape') return;
		const { x, y } = targetNode.position;
		onNodeMove?.(targetNode.id, x, y);
		const w = (targetNode.width as number | undefined) ?? 0;
		const h = (targetNode.height as number | undefined) ?? 0;
		const dropped = containerAt(x + w / 2, y + h / 2);
		const current = currentParent(targetNode.id);
		if (!sameTarget(dropped, current) && onReparent) {
			onReparent(targetNode.id, dropped);
		}
	}

	const CONTAINER_KINDS = new Set(['lane', 'box', 'group', 'note']);
	const OBJECT_ID_RE = /^__(lane|box|group|note)_(\d+)$/;

	function handleNodeClick({ node }: { node: Node; event: MouseEvent | TouchEvent }) {
		if (!node) {
			onNodeSelect?.(null);
			onObjectSelect?.(null, -1);
			return;
		}
		if (node.type === 'shape') {
			onNodeSelect?.(node.id);
			onObjectSelect?.(null, -1);
			return;
		}
		if (CONTAINER_KINDS.has(node.type as string)) {
			const m = OBJECT_ID_RE.exec(node.id);
			if (!m) return;
			const rawKind = m[1] as 'lane' | 'box' | 'group' | 'note';
			const kind = rawKind === 'lane' ? 'swimlane' : rawKind;
			onNodeSelect?.(null);
			onObjectSelect?.(kind, Number(m[2]));
		}
	}

	function handleCanvasDblClick(e: MouseEvent) {
		const t = e.target as HTMLElement | null;
		const nodeEl = t?.closest('[data-id]');
		if (!nodeEl) return;
		const id = nodeEl.getAttribute('data-id');
		if (!id || id.startsWith('__')) return;
		onNodeDblClick?.(id);
	}

	function handleEdgeClick({ edge }: { edge: { id: string }; event: MouseEvent }) {
		onEdgeSelect?.(edge.id);
	}

	function handlePaneClick() {
		onNodeSelect?.(null);
		onEdgeSelect?.(null);
		onObjectSelect?.(null, -1);
	}

	function handleConnect(connection: {
		source: string | null;
		target: string | null;
		sourceHandle?: string | null;
		targetHandle?: string | null;
	}) {
		if (!connection?.source || !connection?.target) return;
		if (connection.source.startsWith('__') || connection.target.startsWith('__')) return;
		onConnect?.(connection.source, connection.target);
	}
</script>

<div class="h-full w-full" style:background-color={theme.canvas} ondblclick={handleCanvasDblClick} role="presentation">
	<SvelteFlow
		bind:nodes
		bind:edges
		{nodeTypes}
		{edgeTypes}
		colorMode={theme.bg === '#ffffff' || theme.bg === '#fdf6e3' ? 'light' : 'dark'}
		fitView
		fitViewOptions={{ padding: 0.2 }}
		minZoom={0.1}
		maxZoom={2}
		connectionMode={ConnectionMode.Loose}
		proOptions={{ hideAttribution: true }}
		onnodedragstop={handleNodeDragStop}
		onnodeclick={handleNodeClick}
		onedgeclick={handleEdgeClick}
		onpaneclick={handlePaneClick}
		onconnect={handleConnect}
	>
		<Background patternColor={theme.gridDot} />
		<Controls />
		<MiniMap pannable zoomable />
		<CanvasFocus {focusId} trigger={focusTrigger} {fitAllTrigger} />
		<ViewportRegister />
	</SvelteFlow>
</div>
