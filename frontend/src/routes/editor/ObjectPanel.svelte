<script lang="ts" module>
	export type ObjectKind = 'swimlane' | 'box' | 'group' | 'note';
</script>

<script lang="ts">
	import Icon from '$lib/Icon.svelte';
	import {
		setSwimlaneName,
		removeSwimlane,
		setBoxLabel,
		setBoxStyle,
		removeBox,
		setGroupName,
		removeGroup,
		setNoteText,
		setNoteTarget,
		removeNote
	} from '$lib/patch';
	import { draftField } from '$lib/draft-field.svelte';
	import type { RenderResult } from '$lib/render';

	let {
		source = $bindable(''),
		kind,
		index,
		result,
		onSelectionChange
	}: {
		source: string;
		kind: ObjectKind;
		index: number;
		result: RenderResult | null;
		onSelectionChange: (kind: ObjectKind | null, index: number) => void;
	} = $props();

	const lane = $derived(kind === 'swimlane' ? (result?.lanes?.[index] ?? null) : null);
	const box = $derived(kind === 'box' ? (result?.boxes?.[index] ?? null) : null);
	const group = $derived(kind === 'group' ? (result?.groups?.[index] ?? null) : null);
	const note = $derived(kind === 'note' ? (result?.notes?.[index] ?? null) : null);

	// Local drafts per kind. Each re-seeds from the live render value
	// whenever it changes (canvas edit, code edit, ...) EXCEPT while that
	// field has focus — the old "seed once when kind:index changes"
	// effect left a stale draft after any OUT-OF-BAND change, and a later
	// blur silently wrote it back over the real value.
	const laneNameDraft = draftField(() => lane?.name ?? '');
	const boxLabelDraft = draftField(() => box?.label ?? '');
	const boxFillDraft = draftField(() => String(box?.style?.fill ?? ''));
	const boxStrokeDraft = draftField(() => String(box?.style?.stroke ?? ''));
	const boxTextDraft = draftField(() => String(box?.style?.text ?? ''));
	const groupNameDraft = draftField(() => group?.name ?? '');
	const noteTextDraft = draftField(() => note?.text ?? '');
	const noteTargetDraft = draftField(() => note?.target ?? '');

	let confirmDelete = $state(false);
	let confirmTimer: ReturnType<typeof setTimeout> | null = null;
	function askDelete(fn: () => void) {
		if (!confirmDelete) {
			confirmDelete = true;
			if (confirmTimer) clearTimeout(confirmTimer);
			confirmTimer = setTimeout(() => (confirmDelete = false), 3000);
			return;
		}
		if (confirmTimer) clearTimeout(confirmTimer);
		confirmDelete = false;
		fn();
	}

	function onTextKey(e: KeyboardEvent, commit: () => void) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			(e.currentTarget as HTMLElement).blur();
			commit();
		}
	}

	// swimlane
	function commitLaneName() {
		if (!lane) return;
		source = setSwimlaneName(source, lane.name, laneNameDraft.value);
	}
	function deleteSwimlane() {
		if (!lane) return;
		askDelete(() => {
			source = removeSwimlane(source, lane.name);
			onSelectionChange(null, -1);
		});
	}

	// box
	function commitBoxLabel() {
		if (!box) return;
		source = setBoxLabel(source, box.label, boxLabelDraft.value, box.swimlane);
	}
	function commitBoxStyle(key: 'fill' | 'stroke' | 'text', value: string) {
		if (!box) return;
		source = setBoxStyle(source, box.label, box.swimlane, key, value);
	}
	function deleteBox() {
		if (!box) return;
		askDelete(() => {
			source = removeBox(source, box.label, box.swimlane);
			onSelectionChange(null, -1);
		});
	}

	// group
	function commitGroupName() {
		if (!group) return;
		source = setGroupName(source, group.name, groupNameDraft.value);
	}
	function deleteGroup() {
		if (!group) return;
		askDelete(() => {
			source = removeGroup(source, group.name);
			onSelectionChange(null, -1);
		});
	}

	// note
	function commitNoteText() {
		source = setNoteText(source, index, noteTextDraft.value);
	}
	function commitNoteTarget() {
		source = setNoteTarget(source, index, noteTargetDraft.value);
	}
	function deleteNote() {
		askDelete(() => {
			source = removeNote(source, index);
			onSelectionChange(null, -1);
		});
	}
</script>

{#if kind === 'swimlane' && lane}
	<div class="mt-2 mb-1 px-3 text-[10px] uppercase tracking-wide text-neutral-500">Swimlane</div>
	<div class="space-y-1 px-3">
		<div class="flex items-center gap-2">
			<label class="w-14 text-[11px] text-neutral-400">Name</label>
			<input
				type="text"
				class="h-6 flex-1 rounded border border-neutral-800 bg-neutral-900 px-1.5 text-xs text-neutral-100"
				bind:value={laneNameDraft.value}
				onfocus={laneNameDraft.onfocus}
				onblur={() => {
					laneNameDraft.onblur();
					commitLaneName();
				}}
				onkeydown={(e) => onTextKey(e, commitLaneName)}
			/>
		</div>
	</div>
	<div class="mt-4 px-3 pb-4">
		<button
			type="button"
			onclick={deleteSwimlane}
			class="flex w-full items-center justify-center gap-1 rounded border border-red-900 px-2 py-1 text-xs text-red-300 hover:bg-red-950"
		>
			<Icon name="trash" size={12} />
			{confirmDelete ? 'Click again — removes lane and contents' : 'Delete swimlane'}
		</button>
	</div>
{:else if kind === 'box' && box}
	<div class="mt-2 mb-1 px-3 text-[10px] uppercase tracking-wide text-neutral-500">Box</div>
	<div class="space-y-1 px-3">
		<div class="flex items-center gap-2">
			<label class="w-14 text-[11px] text-neutral-400">Label</label>
			<input
				type="text"
				class="h-6 flex-1 rounded border border-neutral-800 bg-neutral-900 px-1.5 text-xs text-neutral-100"
				bind:value={boxLabelDraft.value}
				onfocus={boxLabelDraft.onfocus}
				onblur={() => {
					boxLabelDraft.onblur();
					commitBoxLabel();
				}}
				onkeydown={(e) => onTextKey(e, commitBoxLabel)}
			/>
		</div>
		<div class="flex items-center gap-2">
			<label class="w-14 text-[11px] text-neutral-400">Lane</label>
			<span class="flex-1 truncate font-mono text-[11px] text-neutral-400">
				{box.swimlane ?? '(root)'}
			</span>
		</div>
		<div class="flex items-center gap-2">
			<label class="w-14 text-[11px] text-neutral-400">Fill</label>
			<input
				type="text"
				placeholder="e.g. rgba(40,70,56,0.25)"
				class="h-6 flex-1 rounded border border-neutral-800 bg-neutral-900 px-1.5 font-mono text-[11px] text-neutral-100"
				bind:value={boxFillDraft.value}
				onfocus={boxFillDraft.onfocus}
				onblur={() => {
					boxFillDraft.onblur();
					commitBoxStyle('fill', boxFillDraft.value);
				}}
				onkeydown={(e) => onTextKey(e, () => commitBoxStyle('fill', boxFillDraft.value))}
			/>
		</div>
		<div class="flex items-center gap-2">
			<label class="w-14 text-[11px] text-neutral-400">Stroke</label>
			<input
				type="text"
				placeholder="e.g. #475569"
				class="h-6 flex-1 rounded border border-neutral-800 bg-neutral-900 px-1.5 font-mono text-[11px] text-neutral-100"
				bind:value={boxStrokeDraft.value}
				onfocus={boxStrokeDraft.onfocus}
				onblur={() => {
					boxStrokeDraft.onblur();
					commitBoxStyle('stroke', boxStrokeDraft.value);
				}}
				onkeydown={(e) => onTextKey(e, () => commitBoxStyle('stroke', boxStrokeDraft.value))}
			/>
		</div>
		<div class="flex items-center gap-2">
			<label class="w-14 text-[11px] text-neutral-400">Text</label>
			<input
				type="text"
				placeholder="e.g. #cbd5e1"
				class="h-6 flex-1 rounded border border-neutral-800 bg-neutral-900 px-1.5 font-mono text-[11px] text-neutral-100"
				bind:value={boxTextDraft.value}
				onfocus={boxTextDraft.onfocus}
				onblur={() => {
					boxTextDraft.onblur();
					commitBoxStyle('text', boxTextDraft.value);
				}}
				onkeydown={(e) => onTextKey(e, () => commitBoxStyle('text', boxTextDraft.value))}
			/>
		</div>
	</div>
	<div class="mt-4 px-3 pb-4">
		<button
			type="button"
			onclick={deleteBox}
			class="flex w-full items-center justify-center gap-1 rounded border border-red-900 px-2 py-1 text-xs text-red-300 hover:bg-red-950"
		>
			<Icon name="trash" size={12} />
			{confirmDelete ? 'Click again — removes box and contents' : 'Delete box'}
		</button>
	</div>
{:else if kind === 'group' && group}
	<div class="mt-2 mb-1 px-3 text-[10px] uppercase tracking-wide text-neutral-500">Group</div>
	<div class="space-y-1 px-3">
		<div class="flex items-center gap-2">
			<label class="w-14 text-[11px] text-neutral-400">Name</label>
			<input
				type="text"
				class="h-6 flex-1 rounded border border-neutral-800 bg-neutral-900 px-1.5 text-xs text-neutral-100"
				bind:value={groupNameDraft.value}
				onfocus={groupNameDraft.onfocus}
				onblur={() => {
					groupNameDraft.onblur();
					commitGroupName();
				}}
				onkeydown={(e) => onTextKey(e, commitGroupName)}
			/>
		</div>
		<div class="flex items-start gap-2">
			<label class="w-14 pt-1 text-[11px] text-neutral-400">Members</label>
			<span class="flex-1 font-mono text-[11px] text-neutral-400">
				{group.members.length > 0 ? group.members.join(', ') : '(empty)'}
			</span>
		</div>
	</div>
	<div class="mt-4 px-3 pb-4">
		<button
			type="button"
			onclick={deleteGroup}
			class="flex w-full items-center justify-center gap-1 rounded border border-red-900 px-2 py-1 text-xs text-red-300 hover:bg-red-950"
		>
			<Icon name="trash" size={12} /> {confirmDelete ? 'Click again to confirm' : 'Delete group'}
		</button>
	</div>
{:else if kind === 'note' && note}
	<div class="mt-2 mb-1 px-3 text-[10px] uppercase tracking-wide text-neutral-500">Note</div>
	<div class="space-y-1 px-3">
		<div class="flex items-start gap-2">
			<label class="w-14 pt-1 text-[11px] text-neutral-400">Text</label>
			<textarea
				rows="3"
				class="flex-1 resize-y rounded border border-neutral-800 bg-neutral-900 px-1.5 py-1 text-xs text-neutral-100"
				bind:value={noteTextDraft.value}
				onfocus={noteTextDraft.onfocus}
				onblur={() => {
					noteTextDraft.onblur();
					commitNoteText();
				}}
			></textarea>
		</div>
		<div class="flex items-center gap-2">
			<label class="w-14 text-[11px] text-neutral-400">Target</label>
			<input
				type="text"
				class="h-6 flex-1 rounded border border-neutral-800 bg-neutral-900 px-1.5 font-mono text-[11px] text-neutral-100"
				bind:value={noteTargetDraft.value}
				onfocus={noteTargetDraft.onfocus}
				onblur={() => {
					noteTargetDraft.onblur();
					commitNoteTarget();
				}}
				onkeydown={(e) => onTextKey(e, commitNoteTarget)}
			/>
		</div>
	</div>
	<div class="mt-4 px-3 pb-4">
		<button
			type="button"
			onclick={deleteNote}
			class="flex w-full items-center justify-center gap-1 rounded border border-red-900 px-2 py-1 text-xs text-red-300 hover:bg-red-950"
		>
			<Icon name="trash" size={12} /> {confirmDelete ? 'Click again to confirm' : 'Delete note'}
		</button>
	</div>
{:else}
	<div class="p-5 text-center text-[11px] text-neutral-500">
		Object not found — it may have been removed.
	</div>
{/if}
