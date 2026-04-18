<script lang="ts">
	import Icon from '$lib/Icon.svelte';
	import Dropdown from '$lib/Dropdown.svelte';
	import { setEdgeLabel, setEdgeKind, removeEdge } from '$lib/patch';
	import type { RenderResult } from '$lib/render';

	let {
		source = $bindable(''),
		selectedEdgeId,
		result,
		onSelectionChange
	}: {
		source: string;
		selectedEdgeId: string | null;
		result: RenderResult | null;
		onSelectionChange: (id: string | null) => void;
	} = $props();

	const ordinal = $derived.by(() => {
		if (!selectedEdgeId) return -1;
		const m = /^e(\d+)$/.exec(selectedEdgeId);
		return m ? Number(m[1]) : -1;
	});

	const edge = $derived(
		ordinal >= 0 ? (result?.edges?.[ordinal] ?? null) : null
	);

	let labelDraft = $state('');
	let lastId: string | null = null;
	$effect(() => {
		if (edge && selectedEdgeId !== lastId) {
			lastId = selectedEdgeId;
			labelDraft = edge.label ?? '';
		}
	});

	const kindOptions = [
		{ value: 'solid', label: 'solid ( → )' },
		{ value: 'dashed', label: 'dashed ( ⇢ )' },
		{ value: 'thick', label: 'thick ( ⇒ )' },
		{ value: 'solid_line', label: 'solid line (no arrow)' },
		{ value: 'dotted_line', label: 'dotted line (no arrow)' }
	];

	const currentKind = $derived(edge?.kind ?? 'solid');

	function commitLabel() {
		if (ordinal < 0) return;
		source = setEdgeLabel(source, ordinal, labelDraft);
	}

	function commitKind(value: string) {
		if (ordinal < 0) return;
		source = setEdgeKind(source, ordinal, value);
	}

	let confirmDelete = $state(false);
	let confirmTimer: ReturnType<typeof setTimeout> | null = null;
	function handleDelete() {
		if (ordinal < 0) return;
		if (!confirmDelete) {
			confirmDelete = true;
			if (confirmTimer) clearTimeout(confirmTimer);
			confirmTimer = setTimeout(() => (confirmDelete = false), 3000);
			return;
		}
		if (confirmTimer) clearTimeout(confirmTimer);
		confirmDelete = false;
		source = removeEdge(source, ordinal);
		onSelectionChange(null);
	}

	function onLabelKey(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			(e.currentTarget as HTMLElement).blur();
			commitLabel();
		}
	}
</script>

{#if !edge}
	<div class="p-5 text-center text-[11px] text-neutral-500">
		Edge not found — it may have been removed.
	</div>
{:else}
	<div class="mt-2 mb-1 px-3 text-[10px] uppercase tracking-wide text-neutral-500">
		Edge
	</div>
	<div class="space-y-1 px-3">
		<div class="flex items-center gap-2">
			<label class="w-14 text-[11px] text-neutral-400">From</label>
			<span class="flex-1 truncate font-mono text-[11px] text-neutral-200">{edge.source}</span>
		</div>
		<div class="flex items-center gap-2">
			<label class="w-14 text-[11px] text-neutral-400">To</label>
			<span class="flex-1 truncate font-mono text-[11px] text-neutral-200">{edge.target}</span>
		</div>
		<div class="flex items-center gap-2">
			<label class="w-14 text-[11px] text-neutral-400">Kind</label>
			<div class="flex-1">
				<Dropdown value={currentKind} options={kindOptions} onchange={commitKind} />
			</div>
		</div>
		<div class="flex items-start gap-2">
			<label class="w-14 pt-1 text-[11px] text-neutral-400">Label</label>
			<input
				type="text"
				class="h-6 flex-1 rounded border border-neutral-800 bg-neutral-900 px-1.5 text-xs text-neutral-100"
				bind:value={labelDraft}
				onblur={commitLabel}
				onkeydown={onLabelKey}
			/>
		</div>
	</div>

	<div class="mt-4 px-3 pb-4">
		<button
			type="button"
			onclick={handleDelete}
			class="flex w-full items-center justify-center gap-1 rounded border border-red-900 px-2 py-1 text-xs text-red-300 hover:bg-red-950"
		>
			<Icon name="trash" size={12} />
			{confirmDelete ? 'Click again to confirm' : 'Delete edge'}
		</button>
	</div>
{/if}
