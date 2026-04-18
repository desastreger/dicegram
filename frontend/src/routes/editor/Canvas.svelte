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
	import type { RenderResult, RenderNode } from '$lib/render';
	import type { Theme } from '$lib/themes';

	let {
		result,
		theme,
		selectedId,
		onNodeMove,
		onNodeSelect,
		onConnect
	}: {
		result: RenderResult | null;
		theme: Theme;
		selectedId?: string | null;
		onNodeMove?: (id: string, x: number, y: number) => void;
		onNodeSelect?: (id: string | null) => void;
		onConnect?: (source: string, target: string) => void;
	} = $props();

	let nodes = $state.raw<Node[]>([]);
	let edges = $state.raw<Edge[]>([]);

	const nodeTypes = {
		shape: ShapeNode,
		lane: LaneNode,
		box: BoxNode,
		group: GroupOverlay,
		note: NoteNode
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

	function pickHandles(sx: number, sy: number, tx: number, ty: number) {
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
			deletable: false
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
				deletable: false
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

		const shapeNodes: Node[] = result.nodes.map((n) => ({
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
				attrs: n.attrs
			},
			draggable: true,
			selectable: true
		}));

		nodes = [...laneNodes, ...boxNodes, ...shapeNodes, ...noteNodes, ...groupNodes];

		const edgeColor = theme.edge;
		const styleFor = (kind: string, override?: string) => {
			const s = edgeStyle(kind);
			const color = override || edgeColor;
			return `stroke: ${color}; stroke-width: ${s.strokeWidth}${s.strokeDasharray ? `; stroke-dasharray: ${s.strokeDasharray}` : ''};`;
		};

		const nodeById = new Map(result.nodes.map((n) => [n.id, n]));

		const dataEdges: Edge[] = result.edges.map((e) => {
			const s = nodeById.get(e.source);
			const t = nodeById.get(e.target);
			const { cx: sx, cy: sy } = centerOf(s);
			const { cx: tx, cy: ty } = centerOf(t);
			const { sourceHandle, targetHandle } = pickHandles(sx, sy, tx, ty);
			const strokeOverride = e.attrs?.color;

			return {
				id: e.id,
				source: e.source,
				target: e.target,
				sourceHandle,
				targetHandle,
				type: 'smoothstep',
				pathOptions: { borderRadius: 10, offset: 20 },
				label: e.label || undefined,
				style: styleFor(e.kind, strokeOverride),
				markerEnd: hasArrow(e.kind)
					? { type: MarkerType.ArrowClosed, color: strokeOverride || edgeColor }
					: undefined,
				labelStyle: `fill: ${theme.text}; font-size: 11px;`,
				labelBgStyle: `fill: ${theme.panel};`,
				labelBgPadding: [4, 2] as [number, number],
				labelBgBorderRadius: 3
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

	function handleNodeDragStop({
		targetNode
	}: {
		targetNode: Node | null;
		nodes: Node[];
		event: MouseEvent | TouchEvent;
	}) {
		if (!targetNode || targetNode.type !== 'shape') return;
		onNodeMove?.(targetNode.id, targetNode.position.x, targetNode.position.y);
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
