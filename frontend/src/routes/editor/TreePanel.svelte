<script lang="ts">
	import Icon from '$lib/Icon.svelte';
	import type { RenderResult, TreeEntry } from '$lib/render';
	import type { Theme } from '$lib/themes';

	let {
		result,
		theme,
		selectedId,
		onSelect,
		onSiblingMove,
		onClose
	}: {
		result: RenderResult | null;
		theme: Theme;
		selectedId: string | null;
		onSelect: (id: string) => void;
		onSiblingMove: (id: string, direction: -1 | 1) => void;
		onClose: () => void;
	} = $props();

	const tree = $derived(result?.tree ?? []);
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
				const shape = (entry as unknown as { shape?: string }).shape;
				if (shape && SHAPE_ICONS.has(shape)) return `shape-${shape}`;
				return 'shapes';
			}
			default:
				return 'shapes';
		}
	}

	let hoveredId = $state<string | null>(null);
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
			Scene tree
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

	<div class="flex-1 overflow-auto py-1">
		{#each flatTree as { entry, depth } (entry.id)}
			{@const selectable = entry.kind === 'shape'}
			{@const isSelected = selectable && entry.id === selectedId}
			<div
				class="group flex items-center gap-1 px-1 py-0.5 text-xs"
				role="treeitem"
				aria-selected={isSelected}
				style:padding-left="{4 + depth * 12}px"
				style:background-color={isSelected ? theme.codeActiveLine : 'transparent'}
				style:color={isSelected ? theme.text : theme.muted}
				onmouseenter={() => (hoveredId = entry.id)}
				onmouseleave={() => (hoveredId = null)}
			>
				<Icon name={iconFor(entry)} size={12} />
				<button
					type="button"
					class="flex-1 truncate text-left"
					disabled={!selectable}
					onclick={() => selectable && onSelect(entry.id)}
					style:cursor={selectable ? 'pointer' : 'default'}
				>
					{entry.label || entry.id}
				</button>
				{#if selectable && hoveredId === entry.id}
					<button
						type="button"
						title="Move up among siblings"
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
						title="Move down among siblings"
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
