<script lang="ts">
	import { BaseEdge } from '@xyflow/svelte';
	import { polylineToPath, routeAround, type Rect } from '$lib/obstacle-routing';

	type Props = {
		id: string;
		sourceX: number;
		sourceY: number;
		targetX: number;
		targetY: number;
		markerEnd?: string;
		style?: string;
		label?: string;
		data?: { obstacles?: Rect[]; labelFill?: string; labelBg?: string };
	};

	let {
		id,
		sourceX,
		sourceY,
		targetX,
		targetY,
		markerEnd,
		style,
		label,
		data
	}: Props = $props();

	const obstacles = $derived(data?.obstacles ?? []);

	const waypoints = $derived(
		routeAround(
			{ x: sourceX, y: sourceY },
			{ x: targetX, y: targetY },
			obstacles
		)
	);

	const pathD = $derived(polylineToPath(waypoints));

	const midpoint = $derived.by(() => {
		if (waypoints.length === 0) return { x: sourceX, y: sourceY };
		const mid = waypoints[Math.floor(waypoints.length / 2)];
		return mid;
	});

	const labelFill = $derived(data?.labelFill ?? '#e5e7eb');
	const labelBg = $derived(data?.labelBg ?? '#0f172a');
	const estWidth = $derived(Math.max(30, (label?.length ?? 0) * 6 + 10));
</script>

<BaseEdge {id} path={pathD} {markerEnd} {style} />

{#if label}
	<g pointer-events="none">
		<rect
			x={midpoint.x - estWidth / 2}
			y={midpoint.y - 8}
			width={estWidth}
			height="14"
			rx="3"
			fill={labelBg}
			opacity="0.85"
		/>
		<text
			x={midpoint.x}
			y={midpoint.y + 3}
			text-anchor="middle"
			font-size="11"
			fill={labelFill}>{label}</text
		>
	</g>
{/if}
