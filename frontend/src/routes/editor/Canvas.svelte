<script lang="ts">
	import {
		SvelteFlow,
		Background,
		Controls,
		MiniMap,
		MarkerType,
		ConnectionMode,
		type Node,
		type Edge
	} from '@xyflow/svelte';
	import '@xyflow/svelte/dist/style.css';
	import ShapeNode from './ShapeNode.svelte';
	import LaneNode from './LaneNode.svelte';
	import BoxNode from './BoxNode.svelte';
	import GroupOverlay from './GroupOverlay.svelte';
	import NoteNode from './NoteNode.svelte';
	import SmartEdge from './SmartEdge.svelte';
	import type { RenderResult, RenderNode } from '$lib/render';
	import type { Theme } from '$lib/themes';
	import type { Rect } from '$lib/obstacle-routing';

	import type { ParentTarget } from '$lib/patch';

	let {
		result,
		theme,
		selectedId,
		filter = '',
		onNodeMove,
		onNodeSelect,
		onConnect,
		onReparent
	}: {
		result: RenderResult | null;
		theme: Theme;
		selectedId?: string | null;
		filter?: string;
		onNodeMove?: (id: string, x: number, y: number) => void;
		onNodeSelect?: (id: string | null) => void;
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

	function centerOf(n: RenderNode | undefined) {
		if (!n) return { cx: 0, cy: 0 };
		return { cx: n.x + n.width / 2, cy: n.y + n.height / 2 };
	}

	function pickHandles(sx: number, sy: number, tx: number, ty: number, selfLoop = false) {
		if (selfLoop) {
			// Bow from right back to top so the loop visibly curls around the node.
			return { sourceHandle: 'r', targetHandle: 't' };
		}
		const dx = tx - sx;
		const dy = ty - sy;
		if (Math.abs(dx) > Math.abs(dy)) {
			return dx > 0
				? { sourceHandle: 'r', targetHandle: 'l' }
				: { sourceHandle: 'l', targetHandle: 'r' };
		}
		return dy > 0
			? { sourceHandle: 'b', targetHandle: 't' }
			: { sourceHandle: 't', targetHandle: 'b' };
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
			selectable: false,
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
				selectable: false,
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
				selectable: false,
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
			selectable: false,
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
			const { sourceHandle, targetHandle } = pickHandles(
				sx,
				sy,
				tx,
				ty,
				e.source === e.target
			);
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
			return {
				id: e.id,
				source: e.source,
				target: e.target,
				sourceHandle,
				targetHandle,
				type: 'smart',
				label: e.label || undefined,
				style: edgeDimmed ? `${baseStyle} opacity: 0.2;` : baseStyle,
				markerEnd: hasArrow(e.kind)
					? { type: MarkerType.ArrowClosed, color: strokeOverride || edgeColor }
					: undefined,
				data: { obstacles, labelFill: theme.text, labelBg: theme.panel }
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

	function handleNodeClick({ node }: { node: Node; event: MouseEvent | TouchEvent }) {
		if (!node || node.type !== 'shape') {
			onNodeSelect?.(null);
			return;
		}
		onNodeSelect?.(node.id);
	}

	function handlePaneClick() {
		onNodeSelect?.(null);
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

<div class="h-full w-full" style:background-color={theme.canvas}>
	<SvelteFlow
		bind:nodes
		bind:edges
		{nodeTypes}
		colorMode={theme.bg === '#ffffff' || theme.bg === '#fdf6e3' ? 'light' : 'dark'}
		fitView
		fitViewOptions={{ padding: 0.2 }}
		minZoom={0.1}
		maxZoom={2}
		connectionMode={ConnectionMode.Loose}
		proOptions={{ hideAttribution: true }}
		onnodedragstop={handleNodeDragStop}
		onnodeclick={handleNodeClick}
		onpaneclick={handlePaneClick}
		onconnect={handleConnect}
	>
		<Background patternColor={theme.gridDot} />
		<Controls />
		<MiniMap pannable zoomable />
	</SvelteFlow>
</div>
