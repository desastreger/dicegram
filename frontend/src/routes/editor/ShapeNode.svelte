<script lang="ts">
	import { Handle, Position } from '@xyflow/svelte';

	type ShapeData = {
		shape: string;
		label: string;
		fill?: string;
		stroke?: string;
		text?: string;
		rx?: string;
		font_size?: string;
		font_family?: string;
		opacity?: string;
		stroke_width?: string;
		attrs?: Record<string, string>;
		dimmed?: boolean;
	};

	let { data, width, height }: { data: ShapeData; width?: number; height?: number } = $props();

	const clipPaths: Record<string, string> = {
		diamond: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)',
		parallelogram: 'polygon(15% 0%, 100% 0%, 85% 100%, 0% 100%)',
		hexagon: 'polygon(12% 0%, 88% 0%, 100% 50%, 88% 100%, 12% 100%, 0% 50%)'
	};

	const defaultRadius: Record<string, string> = {
		rect: '4px',
		rounded: '14px',
		circle: '50% / 50%',
		stadium: '9999px',
		cylinder: '18px / 40%'
	};

	const status = $derived(data.attrs?.status ?? '');
	const priority = $derived(data.attrs?.priority ?? '');
	const typeAttr = $derived(data.attrs?.type ?? '');
	const owner = $derived(data.attrs?.owner ?? '');
	const tags = $derived(
		(data.attrs?.tags ?? '')
			.split(',')
			.map((t) => t.trim())
			.filter(Boolean)
	);

	const fill = $derived(
		data.fill ??
			(typeAttr === 'start'
				? '#064e3b'
				: typeAttr === 'end'
					? '#3f1d1d'
					: typeAttr === 'decision'
						? '#3a2f0b'
						: typeAttr === 'datastore'
							? '#0c3a5c'
							: 'var(--th-node-fill, #1f2937)')
	);
	const stroke = $derived(
		data.stroke ??
			(priority === 'critical'
				? '#ef4444'
				: priority === 'high'
					? '#f59e0b'
					: status === 'blocked'
						? '#ef4444'
						: status === 'complete'
							? '#10b981'
							: 'var(--th-node-stroke, #64748b)')
	);
	const strokeWidth = $derived(
		data.stroke_width != null && data.stroke_width !== ''
			? Number(data.stroke_width)
			: priority === 'critical'
				? 3
				: priority === 'high'
					? 2.25
					: 1.5
	);
	const textColor = $derived(
		data.text ?? (status === 'deprecated' ? '#71717a' : 'var(--th-node-text, #e5e7eb)')
	);
	const fontSize = $derived(
		data.font_size != null && data.font_size !== '' ? `${Number(data.font_size)}px` : '13px'
	);
	const fontFamily = $derived(data.font_family ?? 'inherit');
	const rawOpacity = $derived(
		data.opacity != null && data.opacity !== ''
			? Number(data.opacity)
			: status === 'draft'
				? 0.7
				: 1
	);
	const opacity = $derived(data.dimmed ? rawOpacity * 0.2 : rawOpacity);
	const textDecoration = $derived(status === 'deprecated' ? 'line-through' : 'none');
	const borderStyle = $derived(status === 'draft' ? 'dashed' : 'solid');
	const clip = $derived(clipPaths[data.shape] ?? 'none');
	const radius = $derived(
		data.rx != null && data.rx !== ''
			? /[0-9]+$/.test(data.rx)
				? `${data.rx}px`
				: data.rx
			: (defaultRadius[data.shape] ?? '4px')
	);
	const clipped = $derived(data.shape in clipPaths);

	const statusBadge = $derived(
		status === 'active'
			? { bg: '#10b981', label: '●' }
			: status === 'complete'
				? { bg: '#10b981', label: '✓' }
				: status === 'blocked'
					? { bg: '#ef4444', label: '!' }
					: status === 'deprecated'
						? { bg: '#71717a', label: '×' }
						: null
	);
</script>

<div
	class="shape"
	class:clipped
	style:width="{width}px"
	style:height="{height}px"
	style:--fill={fill}
	style:--stroke={stroke}
	style:--stroke-width="{strokeWidth}px"
	style:--text={textColor}
	style:--clip={clip}
	style:--radius={radius}
	style:--opacity={opacity}
	style:--border-style={borderStyle}
	style:--font-size={fontSize}
	style:--font-family={fontFamily}
>
	<div class="bg"></div>
	<div class="label" style:text-decoration={textDecoration}>{data.label}</div>

	{#if owner}
		<div class="owner" title="owner">{owner}</div>
	{/if}
	{#if tags.length}
		<div class="tags" title={tags.join(', ')}>
			{#each tags.slice(0, 3) as tag}
				<span class="tag">#{tag}</span>
			{/each}
			{#if tags.length > 3}
				<span class="tag">+{tags.length - 3}</span>
			{/if}
		</div>
	{/if}
	{#if statusBadge}
		<div class="badge" style:background={statusBadge.bg}>{statusBadge.label}</div>
	{/if}

	<Handle type="source" position={Position.Top} id="t" class="handle" />
	<Handle type="source" position={Position.Bottom} id="b" class="handle" />
	<Handle type="source" position={Position.Left} id="l" class="handle" />
	<Handle type="source" position={Position.Right} id="r" class="handle" />
</div>

<style>
	.shape {
		position: relative;
		color: var(--text);
		font-size: var(--font-size);
		font-family: var(--font-family);
		line-height: 1.25;
		opacity: var(--opacity);
	}

	.bg {
		position: absolute;
		inset: 0;
		background: var(--fill);
		border: var(--stroke-width) var(--border-style) var(--stroke);
		border-radius: var(--radius);
	}

	.shape.clipped .bg {
		clip-path: var(--clip);
		border: none;
		padding: var(--stroke-width);
		background:
			linear-gradient(var(--fill), var(--fill)) padding-box,
			var(--stroke);
	}

	.label {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 8px 14px;
		text-align: center;
		white-space: pre-wrap;
		pointer-events: none;
	}

	.owner {
		position: absolute;
		bottom: -7px;
		right: 8px;
		background: #0f172a;
		border: 1px solid #334155;
		color: #cbd5e1;
		font-size: 10px;
		padding: 1px 6px;
		border-radius: 9999px;
		pointer-events: none;
	}

	.tags {
		position: absolute;
		bottom: -7px;
		left: 8px;
		display: flex;
		gap: 3px;
		pointer-events: none;
	}

	.tag {
		background: var(--th-panel, #1e293b);
		border: 1px solid var(--th-panel-border, #334155);
		color: var(--th-muted, #94a3b8);
		font-size: 9px;
		padding: 0 5px;
		border-radius: 9999px;
		line-height: 14px;
	}

	.badge {
		position: absolute;
		top: -8px;
		left: -8px;
		width: 18px;
		height: 18px;
		border-radius: 9999px;
		color: white;
		font-size: 11px;
		font-weight: bold;
		display: flex;
		align-items: center;
		justify-content: center;
		border: 2px solid #0a0a0a;
		pointer-events: none;
	}

	:global(.handle) {
		width: 8px !important;
		height: 8px !important;
		background: #64748b !important;
		border: 1.5px solid #0f172a !important;
		opacity: 0.45;
		transition: opacity 0.15s;
	}

	.shape:hover :global(.handle),
	:global(.svelte-flow__node.selected .handle) {
		opacity: 1;
	}

	:global(.svelte-flow__node.selected) .shape .bg {
		outline: 2px solid var(--th-accent, #3b82f6);
		outline-offset: 2px;
	}
	:global(.svelte-flow__node.selected) .shape.clipped .bg {
		outline: none;
		filter: drop-shadow(0 0 0 var(--th-accent, #3b82f6))
			drop-shadow(0 0 2px var(--th-accent, #3b82f6));
	}
</style>
