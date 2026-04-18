<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { ApiError } from '$lib/api';
	import { auth } from '$lib/auth.svelte';
	import { dicegrams as api, type Dicegram } from '$lib/dicegrams';
	import {
		addEdge,
		findNodeLineIndex,
		getSetting,
		moveNodeAfter,
		moveNodeAmongSiblings,
		moveNodeBefore,
		removeNode,
		reparentNode,
		setNodePosition,
		type ParentTarget
	} from '$lib/patch';
	import { onMount } from 'svelte';
	import { renderDsl, type RenderResult, type RenderNode } from '$lib/render';
	import { getTheme, type Theme } from '$lib/themes';
	import { TEMPLATES, DEFAULT_TEMPLATE_ID, type DicegramTemplate } from '$lib/templates';
	import { buildTreeFallback } from '$lib/tree-fallback';
	import Canvas from './Canvas.svelte';
	import CodeEditor from './CodeEditor.svelte';
	import Toolbar from './Toolbar.svelte';
	import SettingsPane from './SettingsPane.svelte';
	import Inspector from './Inspector.svelte';
	import TreePanel from './TreePanel.svelte';
	import Icon from '$lib/Icon.svelte';

	const DEFAULT_TEMPLATE =
		TEMPLATES.find((t) => t.id === DEFAULT_TEMPLATE_ID) ?? TEMPLATES[0];

	let source = $state(DEFAULT_TEMPLATE.source);
	let name = $state('Untitled dicegram');
	let currentId = $state<number | null>(null);
	let result = $state<RenderResult | null>(null);
	let rendering = $state(false);
	let renderError = $state<string | null>(null);
	let saving = $state(false);
	let saveMsg = $state<string | null>(null);
	let myDicegrams = $state<Dicegram[]>([]);
	let showOpen = $state(false);
	let settingsOpen = $state(false);
	let inspectorOpen = $state(false);
	let treeOpen = $state(false);
	let filter = $state('');
	let selectedNodeId = $state<string | null>(null);
	let debounceTimer: ReturnType<typeof setTimeout> | undefined;
	let preNormalizeSource = $state<string | null>(null);
	let normalizeToast = $state<string | null>(null);
	let normalizeToastTimer: ReturnType<typeof setTimeout> | null = null;

	$effect(() => {
		if (!auth.loading && !auth.user) goto('/login');
	});

	$effect(() => {
		const src = source;
		clearTimeout(debounceTimer);
		debounceTimer = setTimeout(async () => {
			rendering = true;
			try {
				const res = await renderDsl(src);
				result = res;
				renderError = null;
				if (res.source_changed && res.normalized_source !== src) {
					preNormalizeSource = src;
					const count = res.notices.length;
					normalizeToast =
						count === 1
							? `1 auto-fix applied: ${res.notices[0].message}`
							: `${count} auto-fixes applied`;
					if (normalizeToastTimer) clearTimeout(normalizeToastTimer);
					normalizeToastTimer = setTimeout(() => {
						normalizeToast = null;
						preNormalizeSource = null;
					}, 6000);
					source = res.normalized_source;
				}
			} catch (err) {
				renderError = err instanceof ApiError ? err.message : 'render failed';
			} finally {
				rendering = false;
			}
		}, 250);
	});

	function undoNormalize() {
		if (!preNormalizeSource) return;
		source = preNormalizeSource;
		preNormalizeSource = null;
		normalizeToast = null;
		if (normalizeToastTimer) clearTimeout(normalizeToastTimer);
	}

	const selectedNode = $derived<RenderNode | null>(
		selectedNodeId && result
			? (result.nodes.find((n) => n.id === selectedNodeId) ?? null)
			: null
	);

	const theme = $derived<Theme>(getTheme(getSetting(source, 'color_scheme')));

	const themeVars = $derived(
		`--th-bg:${theme.bg};--th-panel:${theme.panel};--th-panel-border:${theme.panelBorder};` +
			`--th-text:${theme.text};--th-muted:${theme.muted};--th-accent:${theme.accent};` +
			`--th-canvas:${theme.canvas};--th-grid-dot:${theme.gridDot};` +
			`--th-node-fill:${theme.nodeFill};--th-node-stroke:${theme.nodeStroke};--th-node-text:${theme.nodeText};` +
			`--th-edge:${theme.edge};` +
			`--th-code-bg:${theme.codeBg};--th-code-text:${theme.codeText};--th-code-gutter:${theme.codeGutter};--th-code-active:${theme.codeActiveLine};`
	);

	const revealLine = $derived(
		selectedNodeId ? findNodeLineIndex(source, selectedNodeId) + 1 || null : null
	);

	function writePosition(id: string, x: number, y: number) {
		source = setNodePosition(source, id, x, y);
	}

	function handleNodeSelect(id: string | null) {
		selectedNodeId = id;
		if (id) {
			inspectorOpen = true;
			settingsOpen = false;
		}
	}

	function handleConnect(src: string, dst: string) {
		source = addEdge(source, { src, dst, kind: 'solid' });
	}

	function handleReparent(id: string, target: ParentTarget) {
		source = reparentNode(source, id, target);
	}

	function handleSiblingMove(id: string, direction: -1 | 1) {
		source = moveNodeAmongSiblings(source, id, direction);
	}

	function handleDropBefore(moveId: string, anchorId: string) {
		source = moveNodeBefore(source, moveId, anchorId);
	}

	function handleDropAfter(moveId: string, anchorId: string) {
		source = moveNodeAfter(source, moveId, anchorId);
	}

	function isEditableTarget(target: EventTarget | null): boolean {
		if (!(target instanceof HTMLElement)) return false;
		const tag = target.tagName.toLowerCase();
		if (tag === 'input' || tag === 'textarea' || tag === 'select') return true;
		if (target.isContentEditable) return true;
		if (target.closest('.cm-editor')) return true;
		return false;
	}

	function handleKeydown(e: KeyboardEvent) {
		// Ctrl/Cmd+S saves from anywhere in the editor.
		if ((e.ctrlKey || e.metaKey) && !e.shiftKey && !e.altKey && e.key.toLowerCase() === 's') {
			e.preventDefault();
			save();
			return;
		}
		if (isEditableTarget(e.target)) return;
		// Delete removes the selected shape when focus is on the canvas or
		// body. We avoid Backspace because Windows uses it for "navigate back"
		// in some contexts.
		if (e.key === 'Delete' && selectedNodeId) {
			const onCanvas = (e.target as HTMLElement | null)?.closest('.svelte-flow');
			if (!onCanvas && document.activeElement && document.activeElement !== document.body)
				return;
			e.preventDefault();
			const id = selectedNodeId;
			stashUndo(`Deleted "${id}"`);
			source = removeNode(source, id);
			selectedNodeId = null;
		}
	}

	function stashUndo(message: string) {
		preNormalizeSource = source;
		normalizeToast = message;
		if (normalizeToastTimer) clearTimeout(normalizeToastTimer);
		normalizeToastTimer = setTimeout(() => {
			normalizeToast = null;
			preNormalizeSource = null;
		}, 5000);
	}

	onMount(() => {
		window.addEventListener('keydown', handleKeydown);
		return () => window.removeEventListener('keydown', handleKeydown);
	});

	// Load a dicegram referenced by ?id= on the URL.
	let lastLoadedId: number | null = null;
	$effect(() => {
		const raw = page.url.searchParams.get('id');
		if (!raw || !auth.user) return;
		const id = Number(raw);
		if (!Number.isFinite(id) || id === lastLoadedId) return;
		lastLoadedId = id;
		api
			.get(id)
			.then((d) => {
				currentId = d.id;
				name = d.name;
				source = d.source;
				savedSourceSnapshot = d.source;
				selectedNodeId = null;
			})
			.catch((err) => {
				const m = err instanceof ApiError ? err.message : 'could not load dicegram';
				showSaveToast({ kind: 'error', message: m }, 5000);
			});
	});

	function handleSelectionChange(newId: string | null) {
		selectedNodeId = newId;
	}

	function toggleSettings() {
		settingsOpen = !settingsOpen;
		if (settingsOpen) inspectorOpen = false;
	}

	function toggleInspector() {
		inspectorOpen = !inspectorOpen;
		if (inspectorOpen) settingsOpen = false;
	}

	let saveToast = $state<{ kind: 'ok' | 'error'; message: string } | null>(null);
	let saveToastTimer: ReturnType<typeof setTimeout> | null = null;
	function showSaveToast(t: { kind: 'ok' | 'error'; message: string }, ms = 3500) {
		saveToast = t;
		if (saveToastTimer) clearTimeout(saveToastTimer);
		saveToastTimer = setTimeout(() => {
			saveToast = null;
		}, ms);
	}

	async function save() {
		if (!auth.user) return;
		saving = true;
		saveMsg = null;
		try {
			if (currentId) {
				const d = await api.update(currentId, { name, source });
				currentId = d.id;
				savedSourceSnapshot = d.source;
				showSaveToast({ kind: 'ok', message: `Saved "${d.name}"` });
			} else {
				const d = await api.create({ name, source });
				currentId = d.id;
				savedSourceSnapshot = d.source;
				showSaveToast({ kind: 'ok', message: `Created "${d.name}"` });
			}
			saveMsg = 'saved';
			setTimeout(() => (saveMsg = null), 2500);
		} catch (err) {
			const message = err instanceof ApiError ? err.message : 'save failed';
			saveMsg = message;
			showSaveToast({ kind: 'error', message: `Save failed: ${message}` }, 6000);
		} finally {
			saving = false;
		}
	}

	async function openList() {
		myDicegrams = await api.list();
		showOpen = true;
	}

	async function load(d: Dicegram) {
		if (dirty) stashUndo(`Opened "${d.name}" — unsaved changes stashed`);
		currentId = d.id;
		name = d.name;
		source = d.source;
		savedSourceSnapshot = d.source;
		showOpen = false;
		selectedNodeId = null;
	}

	function newDicegram(template: DicegramTemplate | null = null) {
		if (dirty) stashUndo('Started new dicegram — unsaved changes stashed');
		currentId = null;
		const pick = template ?? TEMPLATES.find((t) => t.id === 'empty') ?? TEMPLATES[0];
		name = template && template.id !== 'empty' ? `${template.name}` : 'Untitled dicegram';
		source = pick.source;
		savedSourceSnapshot = '';
		selectedNodeId = null;
	}

	const rightPaneOpen = $derived(settingsOpen || inspectorOpen);
	const leftTreeOpen = $derived(treeOpen);

	let savedSourceSnapshot = $state<string>('');
	const dirty = $derived(currentId != null && source !== savedSourceSnapshot);

	$effect(() => {
		const base = name || 'Untitled';
		document.title = `${dirty ? '• ' : ''}${base} — Dicegram`;
	});

	function handleTreeSelect(id: string) {
		handleNodeSelect(id);
	}
</script>

<div class="flex h-[calc(100vh-var(--header-h))] flex-col" style={themeVars}>
	<Toolbar
		bind:source
		bind:name
		bind:settingsOpen={
			() => settingsOpen,
			(v) => {
				settingsOpen = v;
				if (v) inspectorOpen = false;
			}
		}
		bind:inspectorOpen={
			() => inspectorOpen,
			(v) => {
				inspectorOpen = v;
				if (v) settingsOpen = false;
			}
		}
		bind:treeOpen
		bind:filter
		{result}
		{currentId}
		{rendering}
		{saveMsg}
		{saving}
		onSave={save}
		onOpen={openList}
		onNew={newDicegram}
		onDirectionChange={(prev) => {
			preNormalizeSource = prev;
			normalizeToast = 'Direction changed — stripped pins';
			if (normalizeToastTimer) clearTimeout(normalizeToastTimer);
			normalizeToastTimer = setTimeout(() => {
				normalizeToast = null;
				preNormalizeSource = null;
			}, 5000);
		}}
	/>

	<div
		class="grid flex-1 overflow-hidden"
		style:grid-template-columns={leftTreeOpen
			? '220px minmax(320px,2fr) minmax(0,3fr)'
			: 'minmax(320px,2fr) minmax(0,3fr)'}
	>
		{#if leftTreeOpen}
			<TreePanel
				{result}
				{theme}
				selectedId={selectedNodeId}
				onSelect={handleTreeSelect}
				onSiblingMove={handleSiblingMove}
				onReparent={handleReparent}
				onDropBefore={handleDropBefore}
				onDropAfter={handleDropAfter}
				onClose={() => (treeOpen = false)}
			/>
		{/if}
		<section
			class="relative flex flex-col border-r"
			style:background-color={theme.codeBg}
			style:border-color={theme.panelBorder}
		>
			<CodeEditor
				bind:value={source}
				{theme}
				{revealLine}
				onNodeClick={handleNodeSelect}
			/>
			{#if result?.errors?.length}
				<div
					class="pointer-events-none absolute bottom-2 left-2 right-2 rounded border border-red-900 bg-red-950/85 px-2 py-1 text-[11px] text-red-200 shadow"
				>
					line {result.errors[0].line}:{result.errors[0].column}:
					{result.errors[0].message}
				</div>
			{/if}
		</section>
		<section
			class="relative min-w-0 transition-[padding-right]"
			style:padding-right={rightPaneOpen ? '340px' : '0'}
			style:background-color={theme.canvas}
		>
			<Canvas
				{result}
				{theme}
				{filter}
				selectedId={selectedNodeId}
				onNodeMove={writePosition}
				onNodeSelect={handleNodeSelect}
				onConnect={handleConnect}
				onReparent={handleReparent}
			/>
			{#if renderError}
				<div
					class="pointer-events-none absolute left-4 top-4 rounded bg-red-900/80 px-3 py-2 text-sm text-red-100 shadow"
				>
					{renderError}
				</div>
			{/if}
		</section>
	</div>
</div>

<SettingsPane bind:source bind:open={settingsOpen} {result} onClose={() => (settingsOpen = false)} />

<Inspector
	bind:source
	bind:open={inspectorOpen}
	selected={selectedNode}
	{result}
	onClose={() => (inspectorOpen = false)}
	onSelectionChange={handleSelectionChange}
	onReparent={handleReparent}
	onSiblingMove={handleSiblingMove}
/>

{#if normalizeToast}
	<div
		class="fixed bottom-4 left-1/2 z-50 flex -translate-x-1/2 items-center gap-3 rounded-md border border-neutral-700 bg-neutral-900/95 px-3 py-1.5 text-xs text-neutral-100 shadow-lg"
	>
		<Icon name="sparkles" size={13} />
		<span>{normalizeToast}</span>
		{#if preNormalizeSource}
			<button
				type="button"
				onclick={undoNormalize}
				class="rounded border border-neutral-700 px-2 py-0.5 text-[11px] text-neutral-300 hover:bg-neutral-800"
			>
				Undo
			</button>
		{/if}
	</div>
{/if}

{#if saveToast}
	<div
		class="fixed bottom-14 left-1/2 z-50 flex -translate-x-1/2 items-center gap-3 rounded-md border px-3 py-1.5 text-xs shadow-lg {saveToast.kind ===
		'error'
			? 'border-red-900 bg-red-950/95 text-red-100'
			: 'border-green-900 bg-green-950/95 text-green-100'}"
	>
		<Icon name={saveToast.kind === 'error' ? 'x' : 'check'} size={13} />
		<span>{saveToast.message}</span>
		{#if saveToast.kind === 'ok'}
			<button
				type="button"
				onclick={() => goto('/dicegrams')}
				class="rounded border border-green-800 px-2 py-0.5 text-[11px] text-green-200 hover:bg-green-900"
			>
				View in Dicegrams
			</button>
		{/if}
	</div>
{/if}

{#if showOpen}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
		onclick={() => (showOpen = false)}
		onkeydown={(e) => e.key === 'Escape' && (showOpen = false)}
		role="button"
		tabindex="-1"
	>
		<div
			class="w-[480px] max-w-[90vw] rounded-lg border border-neutral-800 bg-neutral-950 p-4 shadow-xl"
			onclick={(e) => e.stopPropagation()}
			onkeydown={(e) => e.stopPropagation()}
			role="dialog"
			tabindex="-1"
		>
			<h2 class="mb-3 text-lg font-semibold text-neutral-100">Your dicegrams</h2>
			{#if myDicegrams.length === 0}
				<p class="text-sm text-neutral-400">No saved dicegrams yet.</p>
			{:else}
				<ul class="flex max-h-96 flex-col gap-1 overflow-auto">
					{#each myDicegrams as d (d.id)}
						<li>
							<button
								onclick={() => load(d)}
								class="flex w-full items-center justify-between rounded px-3 py-2 text-left text-sm text-neutral-200 hover:bg-neutral-800"
							>
								<span class="truncate">{d.name}</span>
								<span class="ml-3 text-xs text-neutral-500"
									>{new Date(d.updated_at).toLocaleDateString()}</span
								>
							</button>
						</li>
					{/each}
				</ul>
			{/if}
			<div class="mt-4 flex justify-end">
				<button
					onclick={() => (showOpen = false)}
					class="rounded border border-neutral-700 px-3 py-1 text-sm text-neutral-200 hover:bg-neutral-800"
				>
					Close
				</button>
			</div>
		</div>
	</div>
{/if}
