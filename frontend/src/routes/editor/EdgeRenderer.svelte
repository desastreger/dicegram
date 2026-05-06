<script lang="ts">
	// Deterministic edge renderer. Consumes the backend's `EdgePlan`
	// (waypoints, label position, corner radius) and emits the SVG path.
	// No routing decisions happen here — the planner already decided
	// every coordinate.
	import { BaseEdge } from '@xyflow/svelte';
	import { roundedPolylinePath, type Point } from '$lib/edge-render';

	type Props = {
		id: string;
		// xyflow hands these in but we IGNORE them for path geometry —
		// the planner already produced the start/end coords. Kept on the
		// signature only because xyflow requires the prop shape.
		sourceX: number;
		sourceY: number;
		targetX: number;
		targetY: number;
		markerEnd?: string;
		markerStart?: string;
		style?: string;
		label?: string;
		data?: {
			waypoints?: Point[];
			labelX?: number | null;
			labelY?: number | null;
			labelAxis?: 'horizontal' | 'vertical';
			cornerRadius?: number;
			labelFill?: string;
			labelBg?: string;
			labelBorder?: string;
		};
	};

	let {
		id,
		sourceX,
		sourceY,
		targetX,
		targetY,
		markerEnd,
		markerStart,
		style,
		label,
		data
	}: Props = $props();

	void id;
	void sourceX;
	void sourceY;
	void targetX;
	void targetY;

	const points = $derived(data?.waypoints ?? []);
	const cornerRadius = $derived(data?.cornerRadius ?? 6);
	const pathD = $derived(roundedPolylinePath(points, cornerRadius));

	const labelFill = $derived(data?.labelFill ?? 'var(--th-text, var(--app-text))');
	const labelBg = $derived(data?.labelBg ?? 'var(--th-panel, var(--app-surface))');
	const labelBorder = $derived(
		data?.labelBorder ?? 'var(--th-panel-border, var(--app-border))'
	);
	const labelLines = $derived((label ?? '').split('\n'));
	const labelLineHeight = 14;
	const labelWidth = $derived(
		Math.max(30, Math.max(...labelLines.map((s) => s.length)) * 6 + 12)
	);
	const labelHeight = $derived(Math.max(16, labelLines.length * labelLineHeight + 4));
	const lx = $derived(data?.labelX ?? null);
	const ly = $derived(data?.labelY ?? null);
</script>

<BaseEdge {id} path={pathD} {markerEnd} {markerStart} {style} />

{#if label && labelLines.length > 0 && lx !== null && ly !== null}
	<g pointer-events="none">
		<rect
			x={lx - labelWidth / 2}
			y={ly - labelHeight / 2}
			width={labelWidth}
			height={labelHeight}
			rx="3"
			fill={labelBg}
			stroke={labelBorder}
			stroke-width="1"
		/>
		<text
			x={lx}
			y={ly - labelHeight / 2 + labelLineHeight - 3}
			text-anchor="middle"
			font-size="11"
			fill={labelFill}
		>
			{#each labelLines as line, i}
				<tspan x={lx} dy={i === 0 ? 0 : labelLineHeight}>{line}</tspan>
			{/each}
		</text>
	</g>
{/if}
