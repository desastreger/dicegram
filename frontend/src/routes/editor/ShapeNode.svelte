<script lang="ts">
	import { Handle, Position } from '@xyflow/svelte';
	import { palette } from '$lib/palette.svelte';

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
		// Set when the renderer detects any inline DSL `style:` keys on
		// this node — surfaced as a tiny "unique" indicator so authors can
		// spot which nodes have been detached from the active theme master.
		unique?: boolean;
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

	// Reading from `palette.current` here (rather than `palette.typeFill(...)`)
	// keeps the Svelte 5 reactive tracker watching every key on the resolved
	// palette object. Without the direct read, a swap of activeThemeId or a
	// hot-update of the static palette tables doesn't always re-trigger a
	// per-node $derived — type:process rects would stay on the previous
	// palette's node_fill.
	const fill = $derived.by(() => {
		if (data.fill) return data.fill;
		const cur = palette.current;
		const v = typeAttr ? cur[`type_${typeAttr}`] : '';
		return v && v.length ? v : cur.node_fill;
	});
	const stroke = $derived(
		data.stroke ??
			(priority === 'critical'
				? palette.current.priority_critical
				: priority === 'high'
					? palette.current.priority_high
					: status === 'blocked'
						? palette.current.status_blocked
						: status === 'complete'
							? palette.current.status_complete
							: palette.current.node_stroke)
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
		data.text ??
			(status === 'deprecated'
				? palette.current.status_deprecated_text
				: palette.current.node_text)
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
			? { bg: palette.current.status_complete || '#10b981', label: '●' }
			: status === 'complete'
				? { bg: palette.current.status_complete || '#10b981', label: '✓' }
				: status === 'blocked'
					? { bg: palette.current.status_blocked || '#ef4444', label: '!' }
					: status === 'deprecated'
						? { bg: palette.current.status_deprecated_text || '#71717a', label: '×' }
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
	{#if data.unique}
		<div class="unique-dot" title="Unique — overrides survive theme swaps"></div>
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

	/* Owner / tag pills sit just outside the shape edge. Both light and dark
	   themes need a readable surface here, so we drive every colour from
	   theme tokens. The hex fallbacks are defensive — if the theme variables
	   aren't wired in, we fall back to the dark-mode appearance. */
	.owner {
		position: absolute;
		bottom: -7px;
		right: 8px;
		background: var(--th-panel, var(--app-surface));
		border: 1px solid var(--th-panel-border, var(--app-border));
		color: var(--th-muted, var(--app-text-muted));
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
		background: var(--th-panel, var(--app-surface));
		border: 1px solid var(--th-panel-border, var(--app-border));
		color: var(--th-muted, var(--app-text-muted));
		font-size: 9px;
		padding: 0 5px;
		border-radius: 9999px;
		line-height: 14px;
	}

	/* Status badge — `bg` is a semantic colour (green=ok, red=blocked, etc.)
	   set inline. The 2px border is the *canvas* colour so the badge reads
	   as a "cut-out" disk in both modes. */
	.badge {
		position: absolute;
		top: -8px;
		left: -8px;
		width: 18px;
		height: 18px;
		border-radius: 9999px;
		color: var(--app-accent-text);
		font-size: 11px;
		font-weight: bold;
		display: flex;
		align-items: center;
		justify-content: center;
		border: 2px solid var(--th-canvas, var(--app-bg));
		pointer-events: none;
	}

	/* Tiny accent dot in the top-right corner indicating that this node has
	   inline style overrides — i.e. it has been "Made Unique" and won't
	   re-skin when the master theme changes. Tracks the active theme accent
	   so it reads in both light and dark modes. */
	.unique-dot {
		position: absolute;
		top: -4px;
		right: -4px;
		width: 8px;
		height: 8px;
		border-radius: 9999px;
		background: var(--th-accent, var(--app-accent));
		border: 1.5px solid var(--th-bg, var(--app-bg));
		pointer-events: none;
	}

	/* xyflow connection handles. Hidden by default so the four 8px dots
	   don't read as phantom arrowheads on every shape (UAT bug #21). They
	   fade in on hover or when the node is selected, which is when the
	   user is actually building or repointing connections. */
	:global(.handle) {
		width: 9px !important;
		height: 9px !important;
		background: var(--th-accent, var(--app-accent)) !important;
		border: 1.5px solid var(--th-canvas, var(--app-bg)) !important;
		opacity: 0;
		transform: scale(0.85);
		transition:
			opacity 0.15s var(--app-ease, ease-out),
			transform 0.15s var(--app-ease, ease-out);
	}

	.shape:hover :global(.handle),
	:global(.svelte-flow__node.selected .handle),
	:global(.svelte-flow__handle.connectingfrom),
	:global(.svelte-flow__handle.connectionindicator):hover {
		opacity: 1;
		transform: scale(1);
	}

	/* Selection ring. Boxes / rects / circles / stadiums / cylinders
	   pick up a clean 2px outline around the whole shape (UAT bug #7).
	   Clipped silhouettes (diamond / parallelogram / hexagon) can't carry
	   an outline, so we synthesize one with four offset drop-shadows that
	   form a 2px stroke along the shape's path. */
	:global(.svelte-flow__node.selected) .shape .bg {
		outline: 2.5px solid var(--th-accent, var(--app-accent));
		outline-offset: 3px;
		box-shadow: 0 0 0 5px color-mix(in srgb, var(--th-accent, var(--app-accent)) 18%, transparent);
	}
	:global(.svelte-flow__node.selected) .shape.clipped .bg {
		outline: none;
		box-shadow: none;
		filter:
			drop-shadow(2px 0 0 var(--th-accent, var(--app-accent)))
			drop-shadow(-2px 0 0 var(--th-accent, var(--app-accent)))
			drop-shadow(0 2px 0 var(--th-accent, var(--app-accent)))
			drop-shadow(0 -2px 0 var(--th-accent, var(--app-accent)))
			drop-shadow(0 0 6px color-mix(in srgb, var(--th-accent, var(--app-accent)) 25%, transparent));
	}
</style>
