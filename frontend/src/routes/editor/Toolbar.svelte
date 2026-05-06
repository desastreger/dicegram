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
		downloadProcessFlowCsv
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
		onDirectionChange,
		onLlmOpen
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
		const onKey = (e: KeyboardEvent) => {
			if (e.key === 'Escape') newOpen = false;
		};
		document.addEventListener('click', onDoc);
		document.addEventListener('keydown', onKey);
		return () => {
			document.removeEventListener('click', onDoc);
			document.removeEventListener('keydown', onKey);
		};
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
		const onKey = (e: KeyboardEvent) => {
			if (e.key === 'Escape') exportOpen = false;
		};
		document.addEventListener('click', onDocClick);
		document.addEventListener('keydown', onKey);
		return () => {
			document.removeEventListener('click', onDocClick);
			document.removeEventListener('keydown', onKey);
		};
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
		const onKey = (e: KeyboardEvent) => {
			if (e.key === 'Escape') shareOpen = false;
		};
		document.addEventListener('click', onDocClick);
		document.addEventListener('keydown', onKey);
		return () => {
			document.removeEventListener('click', onDocClick);
			document.removeEventListener('keydown', onKey);
		};
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
		kind: 'svg' | 'png' | 'pdf' | 'html' | 'process-flow' | 'copy-svg' | 'copy-dsl'
	) {
		exportOpen = false;
		const baseName = name || 'dicegram';
		try {
			if (kind === 'svg') await downloadSvg(baseName, source);
			else if (kind === 'png') await downloadPng(baseName, source);
			else if (kind === 'pdf') await downloadPdf(baseName, source);
			else if (kind === 'html') await downloadHtml(baseName, source);
			else if (kind === 'process-flow') {
				if (!result) throw new Error('nothing to export yet');
				downloadProcessFlowCsv(baseName, result);
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

<div class="dg-toolbar">
	<input
		type="text"
		bind:value={name}
		placeholder="Untitled dicegram"
		aria-label="Dicegram name"
		title="Dicegram name"
		class="dg-name input-themed numeric"
	/>

	<div class="dg-group">
		<button
			type="button"
			onclick={onSave}
			disabled={saving}
			title={saving ? 'Saving…' : 'Save (Ctrl+S)'}
			class="dg-btn-primary"
		>
			<Icon name="save" size={13} />
			<span class="dg-label">{saving ? 'Saving…' : 'Save'}</span>
		</button>
		<button
			type="button"
			onclick={onOpen}
			title="Open"
			class="btn-tactile"
		>
			<Icon name="folder-open" size={13} />
			<span class="dg-label">Open</span>
		</button>
		<div class="relative" bind:this={newRoot}>
			<button
				type="button"
				onclick={() => (newOpen = !newOpen)}
				aria-expanded={newOpen}
				title="New dicegram"
				class="btn-tactile"
			>
				<Icon name="file-plus" size={13} />
				<span class="dg-label">New</span>
				<Icon name="chevron-down" size={11} />
			</button>
			{#if newOpen}
				<div class="dg-pop menu-panel">
					{#each TEMPLATES as t (t.id)}
						<button
							type="button"
							onclick={() => pickNew(t)}
							class="dg-pop-item"
						>
							<div class="dg-pop-name">{t.name}</div>
							<div class="dg-pop-hint">{t.description}</div>
						</button>
					{/each}
				</div>
			{/if}
		</div>
	</div>

	<span class="dg-rule" aria-hidden="true"></span>

	<div role="group" aria-label="Layout direction" class="dg-segment">
		{#each DIRECTIONS as d (d.id)}
			{@const active = d.id === activeDirection}
			<button
				type="button"
				onclick={() => pickDirection(d.id)}
				aria-pressed={active}
				aria-label={`Layout direction: ${d.label.toLowerCase()}`}
				title={d.label}
				class="dg-seg-btn"
				class:dg-seg-on={active}
			>
				<Icon name={d.icon} size={13} />
			</button>
		{/each}
	</div>

	<span class="dg-rule" aria-hidden="true"></span>

	<button
		type="button"
		onclick={() => (treeOpen = !treeOpen)}
		aria-pressed={treeOpen}
		aria-label="Toggle dicetree"
		title="Dicetree (Ctrl+B)"
		class="btn-tactile"
	>
		<Icon name="tree" size={13} />
	</button>
	<button
		type="button"
		onclick={() => (settingsOpen = !settingsOpen)}
		aria-pressed={settingsOpen}
		aria-label="Toggle dicegram settings"
		title="Dicegram settings"
		class="btn-tactile"
	>
		<Icon name="settings" size={13} />
	</button>
	<button
		type="button"
		onclick={() => (inspectorOpen = !inspectorOpen)}
		aria-pressed={inspectorOpen}
		aria-label="Toggle inspector"
		title="Inspector (Ctrl+.)"
		class="btn-tactile"
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
			class="btn-tactile"
		>
			<Icon name="share" size={13} />
			<span class="dg-label">Share</span>
			<Icon name="chevron-down" size={11} />
		</button>
		{#if shareOpen && currentId != null}
			<div class="dg-pop menu-panel" style="width: 18rem; padding: 0.55rem;">
				{#if shareBusy && !shareSlug}
					<p class="dg-pop-hint" style="padding: 0.45rem 0.25rem;">Creating link…</p>
				{:else if shareError}
					<p class="dg-pop-hint text-danger" style="padding: 0.45rem 0.25rem;">{shareError}</p>
				{:else if shareUrl}
					<p class="eyebrow" style="font-size: 0.6rem; margin-bottom: 0.4rem; padding: 0 0.25rem;">
						Public read-only link
					</p>
					<input
						type="text"
						readonly
						value={shareUrl}
						aria-label="Share URL"
						class="input-themed numeric"
						style="width: 100%; font-family: var(--app-mono-font); font-size: 0.7rem; margin-bottom: 0.5rem;"
						onclick={(e) => (e.target as HTMLInputElement).select()}
					/>
					<div class="flex gap-1">
						<button
							type="button"
							onclick={copyShare}
							class="btn-tactile"
							style="flex: 1; justify-content: center;"
						>
							<Icon name={shareCopied ? 'check' : 'copy'} size={12} />
							{shareCopied ? 'Copied' : 'Copy link'}
						</button>
						<button
							type="button"
							onclick={revokeShare}
							disabled={shareBusy}
							class="btn-tactile dg-revoke"
							style="flex: 1; justify-content: center;"
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
			class="btn-tactile"
		>
			<Icon name="download" size={13} />
			<span class="dg-label">Export</span>
			<Icon name="chevron-down" size={11} />
		</button>
		{#if exportOpen}
			<div class="dg-pop menu-panel">
				<button type="button" onclick={() => doExport('svg')} class="menu-item">
					<Icon name="download" size={13} /> Download SVG
				</button>
				<button type="button" onclick={() => doExport('png')} class="menu-item">
					<Icon name="download" size={13} /> Download PNG
				</button>
				<button type="button" onclick={() => doExport('pdf')} class="menu-item">
					<Icon name="download" size={13} /> Download PDF
				</button>
				<button type="button" onclick={() => doExport('html')} class="menu-item">
					<Icon name="download" size={13} /> Download HTML
				</button>
				<button
					type="button"
					onclick={() => doExport('process-flow')}
					title="Process-flow CSV. Columns: Process Step ID, Description, Shape Type, Function Band, Phase, Next Step ID, Connector Label. Lossy: groups, notes, free positions and non-flow edges are dropped."
					class="menu-item"
				>
					<Icon name="download" size={13} /> Process-flow CSV
				</button>
				<div class="dg-divider"></div>
				<button type="button" onclick={() => doExport('copy-svg')} class="menu-item">
					<Icon name="copy" size={13} /> Copy SVG
				</button>
				<button type="button" onclick={() => doExport('copy-dsl')} class="menu-item">
					<Icon name="clipboard" size={13} /> Copy DSL
				</button>
				<button
					type="button"
					onclick={() => {
						exportOpen = false;
						onLlmOpen?.();
					}}
					class="menu-item"
				>
					<Icon name="sparkles" size={13} /> LLM prompt…
				</button>
			</div>
		{/if}
	</div>

	<button
		type="button"
		onclick={() => onLlmOpen?.()}
		title="Copy a ready-made prompt and open it in any chat model"
		class="btn-tactile"
	>
		<Icon name="sparkles" size={13} />
		<span class="dg-label">LLM prompt</span>
	</button>

	<div class="dg-status">
		<input
			type="search"
			bind:value={filter}
			placeholder="Filter  (owner:alice #tag …)"
			aria-label="Filter nodes by id, label, owner, type, status, tag"
			title={`Filter nodes (substring match). Supported keys:\n  owner: type: status: priority: shape: lane: box: tag:\n  #tag   free text matches id and label`}
			class="dg-filter input-themed numeric"
		/>
		{#if rendering}
			<span class="dg-meta">rendering…</span>
		{:else if errorCount > 0}
			<span class="dg-meta text-danger numeric">{errorCount} error{errorCount === 1 ? '' : 's'}</span>
		{:else}
			<span class="dg-meta numeric">{nodeCount} node{nodeCount === 1 ? '' : 's'}</span>
		{/if}
		{#if saveMsg}
			<span class="dg-meta text-ok">
				<Icon name="check" size={12} />
				{saveMsg}
			</span>
		{:else if autosaveStatus === 'saving'}
			<span class="dg-meta">Saving…</span>
		{:else if autosaveStatus === 'saved'}
			<span class="dg-meta">
				<Icon name="check" size={12} /> Saved
			</span>
		{/if}
	</div>
</div>

{#if copyToast}
	<div
		role="status"
		aria-live="polite"
		class="dg-copy-toast toast"
	>
		{copyToast}
	</div>
{/if}

<style>
	.dg-toolbar {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.35rem;
		padding: 0.4rem 0.6rem;
		background: var(--app-surface);
		border-bottom: 1px solid var(--app-border);
		font-size: 0.78rem;
	}

	.dg-name {
		height: 28px;
		width: 12rem;
		padding: 0.15rem 0.55rem;
		font-size: 0.78rem;
	}

	.dg-group {
		display: inline-flex;
		align-items: center;
		gap: 0.15rem;
	}

	/* The save button is the only chrome in the toolbar that uses the
	   accent fill — the rest sit on neutral surfaces so the brand colour
	   draws the eye to the primary action. UAT bug #6: was bg-blue-600
	   which the global override remapped, but the height didn't track
	   the rest of the toolbar. */
	.dg-btn-primary {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		height: 28px;
		padding: 0 0.7rem;
		background: var(--app-accent);
		color: var(--app-accent-text);
		border-radius: var(--app-radius-sm);
		font-size: 0.75rem;
		font-weight: 500;
		border: 1px solid transparent;
		transition:
			background-color var(--app-dur-fast) var(--app-ease),
			transform var(--app-dur-fast) var(--app-ease);
	}
	.dg-btn-primary:hover:not(:disabled) {
		background: color-mix(in srgb, var(--app-accent) 88%, var(--app-text) 12%);
	}
	.dg-btn-primary:active:not(:disabled) {
		transform: translateY(1px);
	}
	.dg-btn-primary:disabled {
		opacity: 0.55;
		cursor: not-allowed;
	}

	/* Override the .btn-tactile defaults to fit the toolbar height. */
	.dg-toolbar :global(.btn-tactile) {
		height: 28px;
		padding: 0 0.55rem;
		font-size: 0.75rem;
	}

	.dg-rule {
		height: 18px;
		width: 1px;
		background: var(--app-border);
		opacity: 0.7;
		margin: 0 0.15rem;
	}

	.dg-segment {
		display: inline-flex;
		overflow: hidden;
		border: 1px solid var(--app-border);
		border-radius: var(--app-radius-sm);
		height: 28px;
	}
	.dg-seg-btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0 0.5rem;
		color: var(--app-text-muted);
		background: transparent;
		border: 0;
		border-right: 1px solid var(--app-border);
		cursor: pointer;
		transition:
			background-color var(--app-dur-fast) var(--app-ease),
			color var(--app-dur-fast) var(--app-ease);
	}
	.dg-seg-btn:last-child { border-right: 0; }
	.dg-seg-btn:hover {
		background: var(--app-hover);
		color: var(--app-text);
	}
	.dg-seg-on {
		background: var(--app-accent-soft);
		color: var(--app-accent);
	}

	.dg-pop {
		position: absolute;
		left: 0;
		top: 100%;
		z-index: 30;
		margin-top: 0.3rem;
		min-width: 14rem;
	}
	.dg-pop-item {
		display: block;
		width: 100%;
		padding: 0.45rem 0.85rem;
		text-align: left;
		background: transparent;
		border: 0;
		color: var(--app-text);
		cursor: pointer;
		transition: background-color var(--app-dur-fast) var(--app-ease);
	}
	.dg-pop-item:hover { background: var(--app-hover); }
	.dg-pop-name { font-size: 0.78rem; font-weight: 500; }
	.dg-pop-hint { font-size: 0.7rem; color: var(--app-text-dim); margin-top: 0.1rem; }
	.dg-divider {
		height: 1px;
		background: var(--app-rule);
		margin: 0.25rem 0;
	}

	.dg-revoke {
		color: var(--app-danger);
		border-color: color-mix(in srgb, var(--app-danger) 35%, var(--app-border) 65%);
	}
	.dg-revoke:hover:not(:disabled) {
		background: color-mix(in srgb, var(--app-danger) 12%, var(--app-bg) 88%);
		border-color: var(--app-danger);
	}

	.dg-label {
		display: none;
	}
	@media (min-width: 768px) {
		.dg-label { display: inline; }
	}

	.dg-status {
		margin-left: auto;
		display: inline-flex;
		align-items: center;
		gap: 0.55rem;
		font-size: 0.7rem;
	}
	.dg-filter {
		height: 28px;
		width: 14rem;
		padding: 0.15rem 0.55rem;
		font-size: 0.7rem;
	}
	.dg-meta {
		display: inline-flex;
		align-items: center;
		gap: 0.25rem;
		color: var(--app-text-dim);
		white-space: nowrap;
	}

	.dg-copy-toast {
		position: fixed;
		bottom: 1rem;
		left: 50%;
		transform: translateX(-50%);
		z-index: 50;
		pointer-events: none;
	}
</style>
