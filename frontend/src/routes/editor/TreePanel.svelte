<script lang="ts">
	import Icon from '$lib/Icon.svelte';
	import type { RenderResult, TreeEntry } from '$lib/render';
	import type { Theme } from '$lib/themes';
	import { buildTreeFallback } from '$lib/tree-fallback';

	let {
		result,
		theme,
		selectedId,
		onSelect,
		onClose
	}: {
		result: RenderResult | null;
		theme: Theme;
		selectedId: string | null;
		onSelect: (id: string) => void;
		onClose: () => void;
	} = $props();

	const tree = $derived.by<TreeEntry[]>(() => {
		if (!result) return [];
		if (result.tree && result.tree.length > 0) return result.tree;
		return buildTreeFallback(result);
	});
	const byId = $derived(new Map(tree.map((t) => [t.id, t])));

	type RenderedEntry = { entry: TreeEntry; depth: number };
	const flatTree = $derived.by<RenderedEntry[]>(() => {
		const rootId = '__root__';
		const root = byId.get(rootId);
		if (!root) return [];
		const out: RenderedEntry[] = [];

		function walk(id: string, depth: number) {
			const n = byId.get(id);
			if (!n) return;
			if (id !== rootId) {
				if (n.kind === 'edge' || n.kind === 'note' || n.kind === 'group') return;
				out.push({ entry: n, depth });
			}
			for (const childId of n.children) {
				walk(childId, id === rootId ? 0 : depth + 1);
			}
		}

		walk(rootId, 0);
		return out;
	});

	const SHAPE_ICONS = new Set([
		'rect',
		'rounded',
		'diamond',
		'circle',
		'parallelogram',
		'hexagon',
		'cylinder',
		'stadium'
	]);

	function iconFor(entry: TreeEntry): string {
		switch (entry.kind) {
			case 'swimlane':
				return 'columns';
			case 'box':
				return 'folder';
			case 'group':
				return 'tag';
			case 'note':
				return 'file-text';
			case 'edge':
				return 'arrow-right';
			case 'shape': {
				const shape = entry.shape;
				if (shape && SHAPE_ICONS.has(shape)) return `shape-${shape}`;
				return 'shapes';
			}
			default:
				return 'shapes';
		}
	}

	const selectableIds = $derived(
		flatTree.filter((f) => f.entry.kind === 'shape').map((f) => f.entry.id)
	);

	function focusRow(id: string) {
		queueMicrotask(() => {
			const el = document.querySelector<HTMLElement>(`[data-tree-id="${CSS.escape(id)}"]`);
			el?.focus();
		});
	}

	function moveFocus(current: string, delta: -1 | 1) {
		if (selectableIds.length === 0) return;
		const idx = selectableIds.indexOf(current);
		const next =
			idx === -1
				? selectableIds[0]
				: selectableIds[(idx + delta + selectableIds.length) % selectableIds.length];
		onSelect(next);
		focusRow(next);
	}
</script>

<aside
	class="flex min-w-0 flex-col overflow-hidden border-r"
	style:background-color={theme.panel}
	style:border-color={theme.panelBorder}
>
	<div
		class="flex items-center justify-between border-b px-2 py-1.5 text-[11px] uppercase tracking-wide"
		style:border-color={theme.panelBorder}
		style:color={theme.muted}
	>
		<span class="flex items-center gap-1.5">
			<Icon name="tree" size={13} />
			Dicetree
		</span>
		<button
			type="button"
			onclick={onClose}
			title="Hide tree"
			class="rounded p-0.5 hover:text-neutral-100"
		>
			<Icon name="x" size={13} />
		</button>
	</div>

	<div
		role="tree"
		tabindex="-1"
		aria-label="Dicetree"
		class="flex-1 overflow-auto py-1"
		data-editor-scroll
	>
		{#each flatTree as { entry, depth } (entry.id)}
			{@const selectable = entry.kind === 'shape'}
			{@const isSelected = selectable && entry.id === selectedId}
			<div
				role={selectable ? 'treeitem' : 'group'}
				tabindex={selectable ? 0 : -1}
				aria-selected={isSelected}
				data-tree-id={entry.id}
				title={entry.label || entry.id}
				class="tree-row flex items-center gap-1 px-1 py-0.5 text-xs select-none transition-colors"
				class:shape={selectable}
				style:padding-left="{4 + depth * 12}px"
				style:background-color={isSelected ? theme.codeActiveLine : 'transparent'}
				style:color={isSelected ? theme.text : theme.muted}
				onclick={() => selectable && onSelect(entry.id)}
				onkeydown={(e) => {
					if (!selectable) return;
					if (e.key === 'Enter' || e.key === ' ') {
						e.preventDefault();
						onSelect(entry.id);
					} else if (e.key === 'ArrowDown') {
						e.preventDefault();
						moveFocus(entry.id, 1);
					} else if (e.key === 'ArrowUp') {
						e.preventDefault();
						moveFocus(entry.id, -1);
					}
				}}
			>
				<Icon name={iconFor(entry)} size={12} />
				<span class="flex-1 truncate">{entry.label || entry.id}</span>
			</div>
		{/each}
	</div>
</aside>

<style>
	.tree-row {
		cursor: default;
	}
	.tree-row.shape {
		cursor: pointer;
	}
	.tree-row:hover {
		background-color: color-mix(in srgb, var(--th-panel-border, #404040) 25%, transparent);
	}
	.tree-row:focus-visible {
		outline: 2px solid var(--th-accent, #3b82f6);
		outline-offset: -2px;
	}
</style>
