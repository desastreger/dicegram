<script lang="ts">
	import Icon from '$lib/Icon.svelte';
	import type { ParentTarget } from '$lib/patch';
	import type { RenderResult, TreeEntry } from '$lib/render';
	import type { Theme } from '$lib/themes';
	import { buildTreeFallback } from '$lib/tree-fallback';

	let {
		result,
		theme,
		selectedId,
		onSelect,
		onSiblingMove,
		onReparent,
		onDropBefore,
		onDropAfter,
		onClose
	}: {
		result: RenderResult | null;
		theme: Theme;
		selectedId: string | null;
		onSelect: (id: string) => void;
		onSiblingMove: (id: string, direction: -1 | 1) => void;
		onReparent: (id: string, target: ParentTarget) => void;
		onDropBefore: (moveId: string, anchorId: string) => void;
		onDropAfter: (moveId: string, anchorId: string) => void;
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

	type DropPos = 'before' | 'into' | 'after';
	let hoveredId = $state<string | null>(null);
	let dragId = $state<string | null>(null);
	let dropTarget = $state<{ id: string; pos: DropPos } | null>(null);

	const selectableIds = $derived(
		flatTree.filter((f) => f.entry.kind === 'shape').map((f) => f.entry.id)
	);

	function focusRow(id: string) {
		// Focus the matching DOM row so subsequent arrow keys keep working.
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

	function entryTarget(entry: TreeEntry): ParentTarget {
		if (entry.kind === 'root') return { kind: 'root' };
		if (entry.kind === 'swimlane') return { kind: 'swimlane', name: entry.label };
		if (entry.kind === 'box') {
			// Box id format is 'box:<swimlane>::<label>' — recover swimlane from parent.
			const parent = entry.parent ? byId.get(entry.parent) : null;
			const swimlane =
				parent && parent.kind === 'swimlane' ? parent.label : null;
			return { kind: 'box', label: entry.label, swimlane };
		}
		return { kind: 'root' };
	}

	function isDescendantOf(candidateId: string, ancestorId: string): boolean {
		let cur: TreeEntry | undefined = byId.get(candidateId);
		while (cur && cur.parent) {
			if (cur.parent === ancestorId) return true;
			cur = byId.get(cur.parent);
		}
		return false;
	}

	function canDrop(entry: TreeEntry, pos: DropPos): boolean {
		if (!dragId) return false;
		if (dragId === entry.id) return false;
		if (isDescendantOf(entry.id, dragId)) return false;
		if (pos === 'into') {
			return (
				entry.kind === 'swimlane' || entry.kind === 'box' || entry.kind === 'root'
			);
		}
		// before/after: the anchor must be a shape line in the DSL (reorder only
		// makes sense among shapes).
		return entry.kind === 'shape';
	}

	function computeDropPos(
		e: DragEvent,
		entry: TreeEntry
	): DropPos {
		const el = e.currentTarget as HTMLElement;
		const rect = el.getBoundingClientRect();
		const ratio = (e.clientY - rect.top) / rect.height;
		const canInto =
			entry.kind === 'swimlane' || entry.kind === 'box' || entry.kind === 'root';
		if (canInto) {
			if (ratio < 0.3) return 'before';
			if (ratio > 0.7) return 'after';
			return 'into';
		}
		return ratio < 0.5 ? 'before' : 'after';
	}

	function handleDragStart(e: DragEvent, entry: TreeEntry) {
		if (entry.kind !== 'shape') {
			e.preventDefault();
			return;
		}
		dragId = entry.id;
		e.dataTransfer?.setData('text/plain', entry.id);
		if (e.dataTransfer) e.dataTransfer.effectAllowed = 'move';
	}

	function handleDragOver(e: DragEvent, entry: TreeEntry) {
		if (!dragId) return;
		const pos = computeDropPos(e, entry);
		if (!canDrop(entry, pos)) return;
		e.preventDefault();
		if (e.dataTransfer) e.dataTransfer.dropEffect = 'move';
		dropTarget = { id: entry.id, pos };
	}

	function handleDragLeave(entry: TreeEntry) {
		if (dropTarget?.id === entry.id) dropTarget = null;
	}

	function handleDrop(e: DragEvent, entry: TreeEntry) {
		e.preventDefault();
		const move = dragId ?? e.dataTransfer?.getData('text/plain') ?? null;
		const drop = dropTarget;
		dragId = null;
		dropTarget = null;
		if (!move || !drop) return;
		if (!canDrop(entry, drop.pos)) return;
		if (drop.pos === 'into') {
			onReparent(move, entryTarget(entry));
		} else if (drop.pos === 'before') {
			onDropBefore(move, entry.id);
		} else {
			onDropAfter(move, entry.id);
		}
	}

	function handleDragEnd() {
		dragId = null;
		dropTarget = null;
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
		onmouseleave={() => (hoveredId = null)}
	>
		{#each flatTree as { entry, depth } (entry.id)}
			{@const selectable = entry.kind === 'shape'}
			{@const isSelected = selectable && entry.id === selectedId}
			{@const dropHere = dropTarget?.id === entry.id}
			<div
				role={selectable ? 'treeitem' : 'group'}
				tabindex={selectable ? 0 : -1}
				aria-selected={isSelected}
				data-tree-id={entry.id}
				draggable={entry.kind === 'shape'}
				title={entry.label || entry.id}
				class="tree-row flex items-center gap-1 px-1 py-0.5 text-xs select-none transition-colors"
				class:dragging={dragId === entry.id}
				class:shape={selectable}
				style:padding-left="{4 + depth * 12}px"
				style:background-color={isSelected
					? theme.codeActiveLine
					: dropHere && dropTarget?.pos === 'into'
						? `${theme.accent}33`
						: 'transparent'}
				style:color={isSelected ? theme.text : theme.muted}
				style:box-shadow={dropHere && dropTarget?.pos === 'before'
					? `inset 0 2px 0 0 ${theme.accent}`
					: dropHere && dropTarget?.pos === 'after'
						? `inset 0 -2px 0 0 ${theme.accent}`
						: 'none'}
				onmouseenter={() => (hoveredId = entry.id)}
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
					} else if (e.key === 'Delete') {
						e.preventDefault();
						// delegate through select so the keydown on window picks it up
					}
				}}
				ondragstart={(e) => handleDragStart(e, entry)}
				ondragover={(e) => handleDragOver(e, entry)}
				ondragleave={() => handleDragLeave(entry)}
				ondrop={(e) => handleDrop(e, entry)}
				ondragend={handleDragEnd}
			>
				<Icon name={iconFor(entry)} size={12} />
				<span class="flex-1 truncate">{entry.label || entry.id}</span>
				{#if selectable && hoveredId === entry.id && dragId == null}
					<button
						type="button"
						title="Move up"
						draggable="false"
						onclick={(e) => {
							e.stopPropagation();
							onSiblingMove(entry.id, -1);
						}}
						class="rounded p-0.5 opacity-70 hover:opacity-100"
					>
						<Icon name="move-up" size={11} />
					</button>
					<button
						type="button"
						title="Move down"
						draggable="false"
						onclick={(e) => {
							e.stopPropagation();
							onSiblingMove(entry.id, 1);
						}}
						class="rounded p-0.5 opacity-70 hover:opacity-100"
					>
						<Icon name="move-down" size={11} />
					</button>
				{/if}
			</div>
		{/each}
	</div>
</aside>

<style>
	.tree-row {
		cursor: default;
	}
	.tree-row.shape {
		cursor: grab;
	}
	.tree-row.shape:active {
		cursor: grabbing;
	}
	.tree-row.dragging {
		opacity: 0.4;
	}
	.tree-row:hover {
		background-color: color-mix(in srgb, var(--th-panel-border, #404040) 25%, transparent);
	}
	.tree-row:focus-visible {
		outline: 2px solid var(--th-accent, #3b82f6);
		outline-offset: -2px;
	}
</style>
