<script lang="ts">
	import type { RenderNode } from '$lib/render';

	let { node }: { node: RenderNode } = $props();

	const padding = 4;
	const width = $derived(Math.max(40, node.width));
	const height = $derived(Math.max(30, node.height));
	const vbW = $derived(width + padding * 2);
	const vbH = $derived(height + padding * 2);
	const x = padding;
	const y = padding;
	const w = $derived(width);
	const h = $derived(height);
	const cx = $derived(x + w / 2);
	const cy = $derived(y + h / 2);

	const typeAttr = $derived(node.attrs?.type ?? '');
	const status = $derived(node.attrs?.status ?? '');
	const priority = $derived(node.attrs?.priority ?? '');

	const fill = $derived(
		node.style?.fill ??
			(typeAttr === 'start'
				? '#064e3b'
				: typeAttr === 'end'
					? '#3f1d1d'
					: typeAttr === 'decision'
						? '#3a2f0b'
						: typeAttr === 'datastore'
							? '#0c3a5c'
							: '#1f2937')
	);
	const stroke = $derived(
		node.style?.stroke ??
			(priority === 'critical'
				? '#ef4444'
				: priority === 'high'
					? '#f59e0b'
					: status === 'blocked'
						? '#ef4444'
						: status === 'complete'
							? '#10b981'
							: '#64748b')
	);
	const strokeWidth = $derived(
		node.style?.stroke_width && Number.isFinite(Number(node.style.stroke_width))
			? Number(node.style.stroke_width)
			: priority === 'critical'
				? 3
				: priority === 'high'
					? 2.25
					: 1.5
	);
	const textColor = $derived(
		node.style?.text ?? (status === 'deprecated' ? '#71717a' : '#e5e7eb')
	);
	const fontSize = $derived(
		node.style?.font_size && Number.isFinite(Number(node.style.font_size))
			? Number(node.style.font_size)
			: 13
	);
	const opacity = $derived(
		node.style?.opacity && Number.isFinite(Number(node.style.opacity))
			? Number(node.style.opacity)
			: status === 'draft'
				? 0.7
				: 1
	);
	const dasharray = $derived(status === 'draft' ? '6 4' : '');

	function rectRx(): number {
		if (node.style?.rx && Number.isFinite(Number(node.style.rx))) return Number(node.style.rx);
		if (node.shape === 'rounded') return 14;
		if (node.shape === 'stadium') return h / 2;
		return 4;
	}

	function diamondPts() {
		return `${cx},${y} ${x + w},${cy} ${cx},${y + h} ${x},${cy}`;
	}
	function parallelogramPts() {
		const skew = w * 0.15;
		return `${x + skew},${y} ${x + w},${y} ${x + w - skew},${y + h} ${x},${y + h}`;
	}
	function hexagonPts() {
		const side = w * 0.12;
		return (
			`${x + side},${y} ${x + w - side},${y} ${x + w},${cy} ` +
			`${x + w - side},${y + h} ${x + side},${y + h} ${x},${cy}`
		);
	}

	const labelLines = $derived(node.label.split('\n'));
</script>

<div class="preview-wrap">
	<svg
		viewBox="0 0 {vbW} {vbH}"
		preserveAspectRatio="xMidYMid meet"
		xmlns="http://www.w3.org/2000/svg"
	>
		<g
			fill={fill}
			stroke={stroke}
			stroke-width={strokeWidth}
			stroke-dasharray={dasharray || undefined}
			opacity={opacity}
		>
			{#if node.shape === 'rect' || node.shape === 'rounded' || node.shape === 'stadium'}
				<rect {x} {y} width={w} height={h} rx={rectRx()} />
			{:else if node.shape === 'circle'}
				<ellipse {cx} {cy} rx={w / 2} ry={h / 2} />
			{:else if node.shape === 'diamond'}
				<polygon points={diamondPts()} />
			{:else if node.shape === 'parallelogram'}
				<polygon points={parallelogramPts()} />
			{:else if node.shape === 'hexagon'}
				<polygon points={hexagonPts()} />
			{:else if node.shape === 'cylinder'}
				{@const cap = h * 0.15}
				<g>
					<ellipse {cx} cy={y + cap} rx={w / 2} ry={cap} />
					<rect {x} y={y + cap} width={w} height={h - 2 * cap} />
					<path
						d={`M ${x} ${y + cap} L ${x} ${y + h - cap} A ${w / 2} ${cap} 0 0 0 ${x + w} ${y + h - cap} L ${x + w} ${y + cap}`}
					/>
				</g>
			{:else}
				<rect {x} {y} width={w} height={h} />
			{/if}
		</g>
		{#each labelLines as line, i}
			<text
				x={cx}
				y={cy - ((labelLines.length - 1) * (fontSize * 1.25)) / 2 + i * (fontSize * 1.25) + fontSize * 0.38}
				text-anchor="middle"
				fill={textColor}
				font-size={fontSize}
				font-family="-apple-system, Segoe UI, sans-serif"
				text-decoration={status === 'deprecated' ? 'line-through' : undefined}>{line}</text
			>
		{/each}
	</svg>
</div>

<style>
	.preview-wrap {
		display: flex;
		align-items: center;
		justify-content: center;
		max-height: calc((100vh - var(--header-h, 40px)) * 0.3);
		padding: 10px 14px;
		border-bottom: 1px solid #262626;
		background: #0a0a0a;
	}
	.preview-wrap svg {
		max-width: 100%;
		max-height: 100%;
		width: auto;
		height: auto;
	}
</style>
