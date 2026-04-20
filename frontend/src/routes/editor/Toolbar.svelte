<script lang="ts">
	import Icon from '$lib/Icon.svelte';
	import { getDirection, setDirection } from '$lib/patch';
	import {
		copyDsl,
		copyLlmPrompt,
		copySvg,
		downloadHtml,
		downloadPdf,
		downloadPng,
		downloadSvg,
		downloadVisioCsv
	} from '$lib/export';
	import type { RenderResult } from '$lib/render';
	import { TEMPLATES, type DicegramTemplate } from '$lib/templates';
	import { dicegrams as dicegramsApi } from '$lib/dicegrams';
	import { ApiError } from '$lib/api';

	let {
		source = $bindable(''),
		name = $bindable(''),
		result,
		currentId,
		rendering,
		saveMsg,
		saving,
		autosaveStatus = 'idle',
		settingsOpen = $bindable(false),
		inspectorOpen = $bindable(false),
		treeOpen = $bindable(false),
		filter = $bindable(''),
		onSave,
		onOpen,
		onNew,
		onDirectionChange
	}: {
		source: string;
		name: string;
		result: RenderResult | null;
		currentId: number | null;
		rendering: boolean;
		saveMsg: string | null;
		saving: boolean;
		autosaveStatus?: 'idle' | 'saving' | 'saved';
		settingsOpen: boolean;
		inspectorOpen: boolean;
		treeOpen: boolean;
		filter: string;
		onSave: () => void;
		onOpen: () => void;
		onNew: (template?: DicegramTemplate | null) => void;
		onDirectionChange?: (prevSource: string) => void;
		onLlmOpen?: () => void;
	} = $props();

	let newOpen = $state(false);
	let newRoot: HTMLDivElement | undefined = $state();

	$effect(() => {
		if (!newOpen) return;
		const onDoc = (e: MouseEvent) => {
			if (newRoot && !newRoot.contains(e.target as Node)) newOpen = false;
		};
		document.addEventListener('click', onDoc);
		return () => document.removeEventListener('click', onDoc);
	});

	function pickNew(template: DicegramTemplate | null) {
		newOpen = false;
		onNew(template);
	}

	let exportOpen = $state(false);
	let exportRoot: HTMLElement | undefined;

	$effect(() => {
		if (!exportOpen) return;
		const onDocClick = (e: MouseEvent) => {
			if (exportRoot && !exportRoot.contains(e.target as Node)) exportOpen = false;
		};
		document.addEventListener('click', onDocClick);
		return () => document.removeEventListener('click', onDocClick);
	});

	let shareOpen = $state(false);
	let shareRoot: HTMLElement | undefined;
	let shareSlug = $state<string | null>(null);
	let shareBusy = $state(false);
	let shareCopied = $state(false);
	let shareError = $state<string | null>(null);

	const shareUrl = $derived(
		shareSlug ? `${window.location.origin}/d/${shareSlug}` : null
	);

	$effect(() => {
		if (currentId == null) {
			shareSlug = null;
			shareError = null;
		}
	});

	$effect(() => {
		if (!shareOpen) return;
		const onDocClick = (e: MouseEvent) => {
			if (shareRoot && !shareRoot.contains(e.target as Node)) shareOpen = false;
		};
		document.addEventListener('click', onDocClick);
		return () => document.removeEventListener('click', onDocClick);
	});

	async function openShare() {
		if (currentId == null) return;
		shareOpen = !shareOpen;
		if (!shareOpen || shareSlug || shareBusy) return;
		shareBusy = true;
		shareError = null;
		try {
			const info = await dicegramsApi.share(currentId);
			shareSlug = info.slug;
		} catch (err) {
			shareError = err instanceof ApiError ? err.message : 'could not create share link';
		} finally {
			shareBusy = false;
		}
	}

	async function copyShare() {
		if (!shareUrl) return;
		try {
			await navigator.clipboard.writeText(shareUrl);
			shareCopied = true;
			setTimeout(() => (shareCopied = false), 1500);
		} catch {
			/* ignore */
		}
	}

	async function revokeShare() {
		if (currentId == null) return;
		shareBusy = true;
		shareError = null;
		try {
			await dicegramsApi.revoke(currentId);
			shareSlug = null;
		} catch (err) {
			shareError = err instanceof ApiError ? err.message : 'could not revoke';
		} finally {
			shareBusy = false;
		}
	}

	let copyToast = $state<string | null>(null);
	let copyToastTimer: ReturnType<typeof setTimeout> | null = null;
	function flashCopyToast(msg: string) {
		copyToast = msg;
		if (copyToastTimer) clearTimeout(copyToastTimer);
		copyToastTimer = setTimeout(() => (copyToast = null), 2400);
	}

	async function doExport(
		kind: 'svg' | 'png' | 'pdf' | 'html' | 'visio' | 'copy-svg' | 'copy-dsl'
	) {
		exportOpen = false;
		const baseName = name || 'dicegram';
		try {
			if (kind === 'svg') await downloadSvg(baseName, source);
			else if (kind === 'png') await downloadPng(baseName, source);
			else if (kind === 'pdf') await downloadPdf(baseName, source);
			else if (kind === 'html') await downloadHtml(baseName, source);
			else if (kind === 'visio') {
				if (!result) throw new Error('nothing to export yet');
				downloadVisioCsv(baseName, result);
			} else if (kind === 'copy-svg') {
				await copySvg(source);
				flashCopyToast('Copied SVG to clipboard');
			} else if (kind === 'copy-dsl') {
				await copyDsl(source);
				flashCopyToast('Copied DSL to clipboard');
			}
		} catch (err) {
			flashCopyToast('Copy failed — ' + (err instanceof Error ? err.message : String(err)));
		}
	}

	const DIRECTIONS: { id: string; icon: string; label: string }[] = [
		{ id: 'top-to-bottom', icon: 'arrow-down', label: 'Top to Bottom' },
		{ id: 'left-to-right', icon: 'arrow-right', label: 'Left to Right' },
		{ id: 'bottom-to-top', icon: 'arrow-up', label: 'Bottom to Top' },
		{ id: 'right-to-left', icon: 'arrow-left', label: 'Right to Left' }
	];

	const activeDirection = $derived(result?.direction ?? getDirection(source));
	const nodeCount = $derived(result?.nodes.length ?? 0);
	const errorCount = $derived(result?.errors.length ?? 0);

	function pickDirection(dir: string) {
		if (dir === activeDirection) return;
		const prev = source;
		source = setDirection(source, dir);
		// Always fire — listeners expect a full redraw signal on every
		// direction flip, not just when pins were stripped.
		onDirectionChange?.(prev);
	}
</script>

<div
	class="flex flex-wrap items-center gap-1.5 border-b border-neutral-800 bg-neutral-950 px-2 py-1 text-xs"
>
	<input
		type="text"
		bind:value={name}
		placeholder="Untitled dicegram"
		class="h-6 w-44 rounded border border-neutral-800 bg-neutral-900 px-2 text-xs text-neutral-100 placeholder:text-neutral-500 focus:border-blue-600 focus:outline-none"
	/>

	<div class="flex items-center gap-0.5">
		<button
			type="button"
			onclick={onSave}
			disabled={saving}
			title={saving ? 'Saving…' : 'Save (Ctrl+S)'}
			class="flex h-6 items-center gap-1 rounded bg-blue-600 px-2 text-white hover:bg-blue-500 disabled:opacity-50"
		>
			<Icon name="save" size={13} />
			<span class="hidden md:inline">{saving ? 'Saving…' : 'Save'}</span>
		</button>
		<button
			type="button"
			onclick={onOpen}
			title="Open"
			class="flex h-6 items-center gap-1 rounded border border-neutral-800 px-2 text-neutral-200 hover:bg-neutral-800"
		>
			<Icon name="folder-open" size={13} />
			<span class="hidden md:inline">Open</span>
		</button>
		<div class="relative" bind:this={newRoot}>
			<button
				type="button"
				onclick={() => (newOpen = !newOpen)}
				aria-expanded={newOpen}
				title="New dicegram"
				class="flex h-6 items-center gap-1 rounded border border-neutral-800 px-2 text-neutral-200 hover:bg-neutral-800"
			>
				<Icon name="file-plus" size={13} />
				<span class="hidden md:inline">New</span>
				<Icon name="chevron-down" size={11} />
			</button>
			{#if newOpen}
				<div
					class="absolute left-0 top-full z-30 mt-1 w-64 overflow-hidden rounded border border-neutral-800 bg-neutral-900 shadow-lg"
				>
					{#each TEMPLATES as t (t.id)}
						<button
							type="button"
							onclick={() => pickNew(t)}
							class="block w-full px-3 py-1.5 text-left text-neutral-200 hover:bg-neutral-800"
						>
							<div class="text-xs font-medium">{t.name}</div>
							<div class="mt-0.5 text-[10px] text-neutral-500">{t.description}</div>
						</button>
					{/each}
				</div>
			{/if}
		</div>
	</div>

	<span class="h-4 w-px bg-neutral-800"></span>

	<div class="flex overflow-hidden rounded border border-neutral-800">
		{#each DIRECTIONS as d (d.id)}
			{@const active = d.id === activeDirection}
			<button
				type="button"
				onclick={() => pickDirection(d.id)}
				aria-pressed={active}
				title={d.label}
				class="flex h-6 items-center justify-center border-r border-neutral-800 px-1.5 last:border-r-0 hover:bg-neutral-800 {active
					? 'bg-blue-700 text-white'
					: 'text-neutral-300'}"
			>
				<Icon name={d.icon} size={13} />
			</button>
		{/each}
	</div>

	<span class="h-4 w-px bg-neutral-800"></span>

	<button
		type="button"
		onclick={() => (treeOpen = !treeOpen)}
		aria-pressed={treeOpen}
		title="Dicetree"
		class="flex h-6 items-center gap-1 rounded border border-neutral-800 px-2 text-neutral-200 hover:bg-neutral-800 {treeOpen
			? 'bg-neutral-800'
			: ''}"
	>
		<Icon name="tree" size={13} />
	</button>
	<button
		type="button"
		onclick={() => (settingsOpen = !settingsOpen)}
		aria-pressed={settingsOpen}
		title="Settings"
		class="flex h-6 items-center gap-1 rounded border border-neutral-800 px-2 text-neutral-200 hover:bg-neutral-800 {settingsOpen
			? 'bg-neutral-800'
			: ''}"
	>
		<Icon name="settings" size={13} />
	</button>
	<button
		type="button"
		onclick={() => (inspectorOpen = !inspectorOpen)}
		aria-pressed={inspectorOpen}
		title="Inspector"
		class="flex h-6 items-center gap-1 rounded border border-neutral-800 px-2 text-neutral-200 hover:bg-neutral-800 {inspectorOpen
			? 'bg-neutral-800'
			: ''}"
	>
		<Icon name="panel-right" size={13} />
	</button>

	<div class="relative" bind:this={shareRoot}>
		<button
			type="button"
			onclick={openShare}
			disabled={currentId == null}
			aria-expanded={shareOpen}
			title={currentId == null ? 'Save the dicegram first to share it' : 'Share'}
			class="flex h-6 items-center gap-1 rounded border border-neutral-800 px-2 text-neutral-200 hover:bg-neutral-800 disabled:cursor-not-allowed disabled:opacity-50"
		>
			<Icon name="share" size={13} />
			<span class="hidden md:inline">Share</span>
			<Icon name="chevron-down" size={11} />
		</button>
		{#if shareOpen && currentId != null}
			<div
				class="absolute left-0 top-full z-20 mt-1 w-72 rounded border border-neutral-800 bg-neutral-900 p-2 shadow-lg"
			>
				{#if shareBusy && !shareSlug}
					<p class="px-1 py-2 text-xs text-neutral-400">Creating link…</p>
				{:else if shareError}
					<p class="px-1 py-2 text-xs text-red-400">{shareError}</p>
				{:else if shareUrl}
					<p class="px-1 pb-1 text-[10px] uppercase tracking-wide text-neutral-500">
						Public read-only link
					</p>
					<input
						type="text"
						readonly
						value={shareUrl}
						class="mb-2 w-full rounded border border-neutral-800 bg-neutral-950 px-2 py-1 font-mono text-[11px] text-neutral-200"
						onclick={(e) => (e.target as HTMLInputElement).select()}
					/>
					<div class="flex gap-1">
						<button
							type="button"
							onclick={copyShare}
							class="flex flex-1 items-center justify-center gap-1 rounded border border-neutral-800 px-2 py-1 text-xs text-neutral-200 hover:bg-neutral-800"
						>
							<Icon name={shareCopied ? 'check' : 'copy'} size={12} />
							{shareCopied ? 'Copied' : 'Copy link'}
						</button>
						<button
							type="button"
							onclick={revokeShare}
							disabled={shareBusy}
							class="flex flex-1 items-center justify-center gap-1 rounded border border-red-900 px-2 py-1 text-xs text-red-300 hover:bg-red-950 disabled:opacity-50"
						>
							<Icon name="trash" size={12} /> Revoke
						</button>
					</div>
				{/if}
			</div>
		{/if}
	</div>

	<div class="relative" bind:this={exportRoot}>
		<button
			type="button"
			onclick={() => (exportOpen = !exportOpen)}
			aria-expanded={exportOpen}
			title="Export"
			class="flex h-6 items-center gap-1 rounded border border-neutral-800 px-2 text-neutral-200 hover:bg-neutral-800"
		>
			<Icon name="download" size={13} />
			<span class="hidden md:inline">Export</span>
			<Icon name="chevron-down" size={11} />
		</button>
		{#if exportOpen}
			<div
				class="absolute left-0 top-full z-20 mt-1 w-48 overflow-hidden rounded border border-neutral-800 bg-neutral-900 shadow-lg"
			>
				<button
					type="button"
					onclick={() => doExport('svg')}
					class="flex w-full items-center gap-2 px-3 py-1 text-left text-neutral-200 hover:bg-neutral-800"
				>
					<Icon name="download" size={13} /> Download SVG
				</button>
				<button
					type="button"
					onclick={() => doExport('png')}
					class="flex w-full items-center gap-2 px-3 py-1 text-left text-neutral-200 hover:bg-neutral-800"
				>
					<Icon name="download" size={13} /> Download PNG
				</button>
				<button
					type="button"
					onclick={() => doExport('pdf')}
					class="flex w-full items-center gap-2 px-3 py-1 text-left text-neutral-200 hover:bg-neutral-800"
				>
					<Icon name="download" size={13} /> Download PDF
				</button>
				<button
					type="button"
					onclick={() => doExport('html')}
					class="flex w-full items-center gap-2 px-3 py-1 text-left text-neutral-200 hover:bg-neutral-800"
				>
					<Icon name="download" size={13} /> Download HTML
				</button>
				<button
					type="button"
					onclick={() => doExport('visio')}
					title="Visio Data Visualizer CSV. Lossy: groups, notes, free positions and non-flow edges are dropped."
					class="flex w-full items-center gap-2 px-3 py-1 text-left text-neutral-200 hover:bg-neutral-800"
				>
					<Icon name="download" size={13} /> Visio CSV
				</button>
				<div class="border-t border-neutral-800"></div>
				<button
					type="button"
					onclick={() => doExport('copy-svg')}
					class="flex w-full items-center gap-2 px-3 py-1 text-left text-neutral-200 hover:bg-neutral-800"
				>
					<Icon name="copy" size={13} /> Copy SVG
				</button>
				<button
					type="button"
					onclick={() => doExport('copy-dsl')}
					class="flex w-full items-center gap-2 px-3 py-1 text-left text-neutral-200 hover:bg-neutral-800"
				>
					<Icon name="clipboard" size={13} /> Copy DSL
				</button>
				<button
					type="button"
					onclick={() => {
						exportOpen = false;
						onLlmOpen?.();
					}}
					class="flex w-full items-center gap-2 px-3 py-1 text-left text-neutral-200 hover:bg-neutral-800"
				>
					<Icon name="sparkles" size={13} /> LLM prompt…
				</button>
			</div>
		{/if}
	</div>

	<button
		type="button"
		onclick={() => onLlmOpen?.()}
		title="Open the LLM prompt dialog (copy + quick-jump to Claude / ChatGPT / Gemini / …)"
		class="flex h-6 items-center gap-1 rounded border border-neutral-800 px-2 text-neutral-200 hover:bg-neutral-800"
	>
		<Icon name="sparkles" size={13} />
		<span class="hidden md:inline">LLM prompt</span>
	</button>

	<div class="ml-auto flex items-center gap-2 text-[11px]">
		<input
			type="text"
			bind:value={filter}
			placeholder="Filter  (owner:alice #tag …)"
			title={`Filter nodes (substring match). Supported keys:\n  owner: type: status: priority: shape: lane: box: tag:\n  #tag   free text matches id and label`}
			class="h-6 w-56 rounded border border-neutral-800 bg-neutral-900 px-2 text-[11px] text-neutral-100 placeholder:text-neutral-500 focus:border-blue-600 focus:outline-none"
		/>
		{#if rendering}
			<span class="text-neutral-400">rendering…</span>
		{:else if errorCount > 0}
			<span class="text-red-400">{errorCount} error{errorCount === 1 ? '' : 's'}</span>
		{:else}
			<span class="text-neutral-500">{nodeCount} node{nodeCount === 1 ? '' : 's'}</span>
		{/if}
		{#if saveMsg}
			<span class="flex items-center gap-1 text-green-400">
				<Icon name="check" size={12} />
				{saveMsg}
			</span>
		{:else if autosaveStatus === 'saving'}
			<span class="text-neutral-500">Saving…</span>
		{:else if autosaveStatus === 'saved'}
			<span class="flex items-center gap-1 text-neutral-400">
				<Icon name="check" size={12} /> Saved
			</span>
		{/if}
	</div>
</div>

{#if copyToast}
	<div
		role="status"
		aria-live="polite"
		class="pointer-events-none fixed bottom-4 left-1/2 z-50 -translate-x-1/2 rounded-md border border-neutral-700 bg-neutral-900 px-3 py-1.5 text-xs text-neutral-100 shadow-lg"
	>
		{copyToast}
	</div>
{/if}
