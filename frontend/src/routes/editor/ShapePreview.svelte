<script lang="ts">
	import type { RenderNode } from '$lib/render';
	import { palette } from '$lib/palette.svelte';

	let { node }: { node: RenderNode } = $props();

	// Preview viewport bounds. Node is rendered at its natural pixel size and
	// uniformly transform-scaled to fit — so border widths, clip paths, font
	// sizes, and corner radii all scale together and the preview looks
	// identical to the canvas render of the same node.
	const MAX_W = 260;
	const MAX_H = 140;
	const MIN_W = 40;
	const MIN_H = 30;

	const natW = $derived(Math.max(MIN_W, node.width));
	const natH = $derived(Math.max(MIN_H, node.height));
	const scale = $derived(Math.min(MAX_W / natW, MAX_H / natH));
	const boxW = $derived(natW * scale);
	const boxH = $derived(natH * scale);

	// — Same derivations as ShapeNode.svelte so preview matches the canvas.
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

	const typeAttr = $derived(node.attrs?.type ?? '');
	const status = $derived(node.attrs?.status ?? '');
	const priority = $derived(node.attrs?.priority ?? '');
	const owner = $derived(node.attrs?.owner ?? '');
	const tags = $derived(
		(node.attrs?.tags ?? '')
			.split(',')
			.map((t) => t.trim())
			.filter(Boolean)
	);

	const fill = $derived(node.style?.fill ?? palette.typeFill(typeAttr));
	const stroke = $derived(
		node.style?.stroke ??
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
		node.style?.stroke_width && Number.isFinite(Number(node.style.stroke_width))
			? Number(node.style.stroke_width)
			: priority === 'critical'
				? 3
				: priority === 'high'
					? 2.25
					: 1.5
	);
	const textColor = $derived(
		node.style?.text ??
			(status === 'deprecated'
				? palette.current.status_deprecated_text
				: palette.current.node_text)
	);
	const fontSize = $derived(
		node.style?.font_size && Number.isFinite(Number(node.style.font_size))
			? `${Number(node.style.font_size)}px`
			: '13px'
	);
	const fontFamily = $derived(node.style?.font_family ?? 'inherit');
	const opacity = $derived(
		node.style?.opacity && Number.isFinite(Number(node.style.opacity))
			? Number(node.style.opacity)
			: status === 'draft'
				? 0.7
				: 1
	);
	const textDecoration = $derived(status === 'deprecated' ? 'line-through' : 'none');
	const borderStyle = $derived(status === 'draft' ? 'dashed' : 'solid');
	const clip = $derived(clipPaths[node.shape] ?? 'none');
	const clipped = $derived(node.shape in clipPaths);
	const radius = $derived(
		node.style?.rx && `${node.style.rx}`.length
			? /[0-9]+$/.test(`${node.style.rx}`)
				? `${node.style.rx}px`
				: `${node.style.rx}`
			: (defaultRadius[node.shape] ?? '4px')
	);

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

<div class="preview-wrap">
	<div class="preview-frame" style:width="{boxW}px" style:height="{boxH}px">
		<div
			class="preview-inner"
			style:width="{natW}px"
			style:height="{natH}px"
			style:transform="scale({scale})"
		>
			<div
				class="shape"
				class:clipped
				style:width="{natW}px"
				style:height="{natH}px"
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
				<div class="label" style:text-decoration={textDecoration}>{node.label}</div>
				{#if owner}<div class="owner" title="owner">{owner}</div>{/if}
				{#if tags.length}
					<div class="tags" title={tags.join(', ')}>
						{#each tags.slice(0, 3) as tag}
							<span class="tag">#{tag}</span>
						{/each}
						{#if tags.length > 3}<span class="tag">+{tags.length - 3}</span>{/if}
					</div>
				{/if}
				{#if statusBadge}
					<div class="badge" style:background={statusBadge.bg}>{statusBadge.label}</div>
				{/if}
			</div>
		</div>
	</div>
</div>

<style>
	/* Layout for the preview pane itself. */
	.preview-wrap {
		display: flex;
		align-items: center;
		justify-content: center;
		max-height: calc((100vh - var(--header-h, 40px)) * 0.3);
		padding: 18px 14px;
		border-bottom: 1px solid var(--th-panel-border, #262626);
		background: var(--th-canvas, #0a0a0a);
	}
	.preview-frame {
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: visible;
	}
	.preview-inner {
		transform-origin: top left;
	}

	/* Shape visuals — kept in lockstep with ShapeNode.svelte. */
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
</style>
