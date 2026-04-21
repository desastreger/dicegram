<script lang="ts">
	import Icon from '$lib/Icon.svelte';
	import Dropdown from '$lib/Dropdown.svelte';
	import {
		setEdgeLabel,
		setEdgeKind,
		setEdgePort,
		setEdgeAttr,
		removeEdge
	} from '$lib/patch';
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

	const portOptions = [
		{ value: '', label: 'auto (by geometry)' },
		{ value: 't', label: 'top' },
		{ value: 'b', label: 'bottom' },
		{ value: 'l', label: 'left' },
		{ value: 'r', label: 'right' }
	];

	const endOptions = [
		{ value: 'none', label: 'none' },
		{ value: 'arrow', label: 'arrow ▸' },
		{ value: 'open_arrow', label: 'open arrow ▹' },
		{ value: 'circle', label: 'circle ●' },
		{ value: 'diamond', label: 'diamond ◆' },
		{ value: 'tee', label: 'tee |' },
		{ value: 'square', label: 'square ▪' }
	];

	const currentKind = $derived(edge?.kind ?? 'solid');
	const currentSourcePort = $derived(edge?.source_port ?? '');
	const currentTargetPort = $derived(edge?.target_port ?? '');
	const defaultEnd = $derived(
		edge && ['solid', 'dashed', 'thick'].includes(edge.kind) ? 'arrow' : 'none'
	);
	const currentEndDeco = $derived(edge?.attrs?.end ?? defaultEnd);
	const currentStartDeco = $derived(edge?.attrs?.start ?? 'none');
	let opacityDraft = $state('');
	$effect(() => {
		if (edge && selectedEdgeId !== lastId) opacityDraft = edge.attrs?.opacity ?? '';
	});

	function commitLabel() {
		if (ordinal < 0) return;
		source = setEdgeLabel(source, ordinal, labelDraft);
	}

	function commitKind(value: string) {
		if (ordinal < 0) return;
		source = setEdgeKind(source, ordinal, value);
	}

	function commitSourcePort(value: string) {
		if (ordinal < 0) return;
		source = setEdgePort(source, ordinal, 'source', value || null);
	}

	function commitTargetPort(value: string) {
		if (ordinal < 0) return;
		source = setEdgePort(source, ordinal, 'target', value || null);
	}

	function commitStartDeco(value: string) {
		if (ordinal < 0) return;
		source = setEdgeAttr(source, ordinal, 'start', value === 'none' ? null : value);
	}

	function commitEndDeco(value: string) {
		if (ordinal < 0) return;
		// Drop the attr when it matches the kind's implicit default so the
		// DSL stays minimal.
		const drop = value === defaultEnd;
		source = setEdgeAttr(source, ordinal, 'end', drop ? null : value);
	}

	function commitOpacity() {
		if (ordinal < 0) return;
		const v = opacityDraft.trim();
		if (v === '') {
			source = setEdgeAttr(source, ordinal, 'opacity', null);
			return;
		}
		const n = Number(v);
		if (!Number.isFinite(n) || n < 0 || n > 1) return;
		source = setEdgeAttr(source, ordinal, 'opacity', n.toString());
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
	<!-- Line style is the primary "type" control for a connector — same
	     logical slot nodes reserve for Shape, so users always find the
	     type selector at the top of the panel. -->
	<div class="mt-2 mb-1 px-3 text-[10px] uppercase tracking-wide text-neutral-500">
		Line style
	</div>
	<div class="px-3">
		<Dropdown value={currentKind} options={kindOptions} onchange={commitKind} />
	</div>

	<div class="mt-3 mb-1 px-3 text-[10px] uppercase tracking-wide text-neutral-500">
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

	<div class="mt-3 mb-1 px-3 text-[10px] uppercase tracking-wide text-neutral-500">
		Ports
	</div>
	<div class="space-y-1 px-3">
		<div class="flex items-center gap-2">
			<label class="w-14 text-[11px] text-neutral-400">From</label>
			<div class="flex-1">
				<Dropdown value={currentSourcePort} options={portOptions} onchange={commitSourcePort} />
			</div>
		</div>
		<div class="flex items-center gap-2">
			<label class="w-14 text-[11px] text-neutral-400">To</label>
			<div class="flex-1">
				<Dropdown value={currentTargetPort} options={portOptions} onchange={commitTargetPort} />
			</div>
		</div>
	</div>

	<div class="mt-3 mb-1 px-3 text-[10px] uppercase tracking-wide text-neutral-500">
		Tips
	</div>
	<div class="space-y-1 px-3">
		<div class="flex items-center gap-2">
			<label class="w-14 text-[11px] text-neutral-400">Start</label>
			<div class="flex-1">
				<Dropdown value={currentStartDeco} options={endOptions} onchange={commitStartDeco} />
			</div>
		</div>
		<div class="flex items-center gap-2">
			<label class="w-14 text-[11px] text-neutral-400">End</label>
			<div class="flex-1">
				<Dropdown value={currentEndDeco} options={endOptions} onchange={commitEndDeco} />
			</div>
		</div>
		<div class="flex items-center gap-2">
			<label class="w-14 text-[11px] text-neutral-400">Opacity</label>
			<input
				type="number"
				step="0.05"
				min="0"
				max="1"
				placeholder="1.0"
				class="h-6 flex-1 rounded border border-neutral-800 bg-neutral-900 px-1.5 font-mono text-[11px] text-neutral-100"
				bind:value={opacityDraft}
				onblur={commitOpacity}
				onkeydown={(e) => {
					if (e.key === 'Enter') {
						(e.currentTarget as HTMLElement).blur();
						commitOpacity();
					}
				}}
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
