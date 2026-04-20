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
	import { downloadSvg } from '$lib/export';
	import { renderDsl, type RenderResult, type RenderNode } from '$lib/render';
	import { getTheme, type Theme } from '$lib/themes';
	import { theme as appTheme } from '$lib/theme.svelte';
	import { TEMPLATES, DEFAULT_TEMPLATE_ID, type DicegramTemplate } from '$lib/templates';
	import { buildTreeFallback } from '$lib/tree-fallback';
	import Canvas from './Canvas.svelte';
	import CodeEditor from './CodeEditor.svelte';
	import EdgeMarkers from './EdgeMarkers.svelte';
	import QuickInsert from './QuickInsert.svelte';
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

	const demoMode = $derived(page.url.searchParams.get('demo') === '1');

	$effect(() => {
		if (demoMode) return;
		if (!auth.loading && !auth.user) {
			const here = page.url.pathname + page.url.search;
			goto(`/login?next=${encodeURIComponent(here)}`);
		}
	});

	const DEMO_STORAGE_KEY = 'dicegram:demo:source';
	const DRAFT_STORAGE_KEY = 'dicegram:editor:draft';
	let demoHydrated = false;
	let draftHydrated = false;

	$effect(() => {
		if (!demoMode || demoHydrated) return;
		demoHydrated = true;
		try {
			const stored = localStorage.getItem(DEMO_STORAGE_KEY);
			if (stored && stored.length > 0) source = stored;
			name = 'Demo dicegram';
		} catch {
			/* ignore */
		}
	});

	$effect(() => {
		if (!demoMode) return;
		try {
			localStorage.setItem(DEMO_STORAGE_KEY, source);
		} catch {
			/* ignore */
		}
	});

	// Logged-in drafts (no id yet): mirror source to localStorage so a
	// refresh doesn't discard the user's work before they've saved. Cleared
	// once the draft becomes a real diegram (currentId set).
	$effect(() => {
		if (demoMode || draftHydrated) return;
		if (currentId != null) return;
		draftHydrated = true;
		try {
			const stored = localStorage.getItem(DRAFT_STORAGE_KEY);
			if (stored && stored.length > 0 && stored !== DEFAULT_TEMPLATE.source) {
				source = stored;
			}
		} catch {
			/* ignore */
		}
	});

	$effect(() => {
		if (demoMode) return;
		if (currentId != null) {
			try {
				localStorage.removeItem(DRAFT_STORAGE_KEY);
			} catch {
				/* ignore */
			}
			return;
		}
		try {
			localStorage.setItem(DRAFT_STORAGE_KEY, source);
		} catch {
			/* ignore */
		}
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

	// An explicit `setting color_scheme <id>` in the DSL wins; otherwise the
	// editor canvas follows the app-wide light/dark toggle in the top nav.
	const theme = $derived<Theme>(
		(() => {
			const explicit = getSetting(source, 'color_scheme');
			if (explicit) return getTheme(explicit);
			return getTheme(appTheme.current === 'light' ? 'light' : 'default-dark');
		})()
	);

	const lineStyle = $derived<'orthogonal' | 'curved' | 'straight'>(
		(() => {
			const v = getSetting(source, 'line_style');
			return v === 'curved' || v === 'straight' ? v : 'orthogonal';
		})()
	);

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
		const mod = e.ctrlKey || e.metaKey;
		const key = e.key.toLowerCase();
		// Ctrl/Cmd+S saves from anywhere in the editor.
		if (mod && !e.shiftKey && !e.altKey && key === 's') {
			e.preventDefault();
			save();
			return;
		}
		// Ctrl/Cmd+Z / Ctrl+Shift+Z for global undo/redo outside CodeMirror.
		if (mod && key === 'z') {
			if (isEditableTarget(e.target)) return; // CodeMirror owns its history
			e.preventDefault();
			if (e.shiftKey) redo();
			else undo();
			return;
		}
		// Ctrl+N new dicegram
		if (mod && !e.shiftKey && !e.altKey && key === 'n') {
			e.preventDefault();
			newDicegram();
			return;
		}
		// Ctrl+O open list
		if (mod && !e.shiftKey && !e.altKey && key === 'o') {
			e.preventDefault();
			openList();
			return;
		}
		// Ctrl+E export SVG (default action)
		if (mod && !e.shiftKey && !e.altKey && key === 'e') {
			e.preventDefault();
			quickExportSvg();
			return;
		}
		// Ctrl+B toggle tree pane
		if (mod && !e.shiftKey && !e.altKey && key === 'b') {
			if (isEditableTarget(e.target)) return;
			e.preventDefault();
			treeOpen = !treeOpen;
			return;
		}
		// Ctrl+. toggle inspector
		if (mod && !e.shiftKey && !e.altKey && key === '.') {
			e.preventDefault();
			inspectorOpen = !inspectorOpen;
			if (inspectorOpen) settingsOpen = false;
			return;
		}
		// Ctrl+F focus filter input
		if (mod && !e.shiftKey && !e.altKey && key === 'f') {
			e.preventDefault();
			focusFilterInput();
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
		const beforeUnload = (e: BeforeUnloadEvent) => {
			if (!dirty) return;
			e.preventDefault();
			e.returnValue = '';
		};
		window.addEventListener('beforeunload', beforeUnload);
		return () => {
			window.removeEventListener('keydown', handleKeydown);
			window.removeEventListener('beforeunload', beforeUnload);
		};
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
		if (demoMode) {
			showSaveToast(
				{ kind: 'error', message: 'Sign up to save — demo diegrams live in your browser only.' },
				5000
			);
			return;
		}
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

	// Silent debounced autosave for logged-in users with an existing dicegram.
	// For users WITHOUT an id yet, the first real edit auto-creates a
	// diegram so refresh lands on a stable URL and autosave takes over.
	let autosaveTimer: ReturnType<typeof setTimeout> | undefined;
	let autosaveStatus = $state<'idle' | 'saving' | 'saved'>('idle');
	let autosaveStatusTimer: ReturnType<typeof setTimeout> | null = null;
	let autoCreating = false;

	$effect(() => {
		const _deps = source + '\u0000' + name;
		void _deps;
		if (demoMode) return;
		if (!auth.user) return;
		// Logged-in & saved diegram → classic autosave.
		if (currentId != null) {
			if (!dirty) return;
			clearTimeout(autosaveTimer);
			autosaveTimer = setTimeout(runAutosave, 2000);
			return;
		}
		// Logged-in but nothing saved yet → auto-create once the source
		// differs from the shipped default template. Guard against a
		// double-create race with `autoCreating`.
		if (autoCreating) return;
		if (source === DEFAULT_TEMPLATE.source) return;
		clearTimeout(autosaveTimer);
		autosaveTimer = setTimeout(autoCreateDiegram, 1500);
	});

	async function autoCreateDiegram() {
		if (demoMode || !auth.user || currentId != null || autoCreating) return;
		if (source === DEFAULT_TEMPLATE.source) return;
		autoCreating = true;
		autosaveStatus = 'saving';
		try {
			// Singular instance = "dicegram" (plural is "diegrams").
			const defaultName = name && name.trim().length > 0 ? name : 'Untitled dicegram';
			const d = await api.create({ name: defaultName, source });
			currentId = d.id;
			name = d.name;
			savedSourceSnapshot = d.source;
			autosaveStatus = 'saved';
			// Stabilize the URL so refresh lands back on this diegram.
			try {
				const url = new URL(window.location.href);
				url.searchParams.set('id', String(d.id));
				history.replaceState(null, '', url.toString());
			} catch {
				/* history API unavailable — autosave still works */
			}
			try {
				localStorage.removeItem(DRAFT_STORAGE_KEY);
			} catch {
				/* ignore */
			}
			if (autosaveStatusTimer) clearTimeout(autosaveStatusTimer);
			autosaveStatusTimer = setTimeout(() => (autosaveStatus = 'idle'), 1500);
		} catch {
			autosaveStatus = 'idle';
		} finally {
			autoCreating = false;
		}
	}

	async function runAutosave() {
		if (!auth.user || currentId == null || !dirty) return;
		autosaveStatus = 'saving';
		try {
			const d = await api.update(currentId, { name, source });
			savedSourceSnapshot = d.source;
			autosaveStatus = 'saved';
			if (autosaveStatusTimer) clearTimeout(autosaveStatusTimer);
			autosaveStatusTimer = setTimeout(() => {
				autosaveStatus = 'idle';
			}, 1500);
		} catch (err) {
			autosaveStatus = 'idle';
			const message = err instanceof ApiError ? err.message : 'autosave failed';
			showSaveToast({ kind: 'error', message: `Autosave failed: ${message}` }, 5000);
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

	// Global undo/redo stack. Snapshots happen after 400ms of `source`
	// stability so rapid typing in CodeMirror collapses into one step —
	// CodeMirror's own Ctrl+Z still handles in-editor history live.
	let undoStack = $state<string[]>([]);
	let redoStack = $state<string[]>([]);
	// svelte-ignore state_referenced_locally
	let lastSnapshot = $state<string>(source);
	let snapshotTimer: ReturnType<typeof setTimeout> | null = null;

	$effect(() => {
		const current = source;
		if (current === lastSnapshot) return;
		const previous = lastSnapshot;
		if (snapshotTimer) clearTimeout(snapshotTimer);
		snapshotTimer = setTimeout(() => {
			lastSnapshot = source;
			if (previous) {
				undoStack = [...undoStack.slice(-49), previous];
				redoStack = [];
			}
		}, 400);
	});

	function undo() {
		if (undoStack.length === 0) return;
		const next = undoStack[undoStack.length - 1];
		undoStack = undoStack.slice(0, -1);
		redoStack = [...redoStack.slice(-49), source];
		lastSnapshot = next;
		source = next;
	}

	function redo() {
		if (redoStack.length === 0) return;
		const next = redoStack[redoStack.length - 1];
		redoStack = redoStack.slice(0, -1);
		undoStack = [...undoStack.slice(-49), source];
		lastSnapshot = next;
		source = next;
	}

	let canvasFocusId = $state<string | null>(null);
	let canvasFocusTrigger = $state(0);
	let canvasFitAllTrigger = $state(0);

	function handleTreeSelect(id: string) {
		handleNodeSelect(id);
		canvasFocusId = id;
		canvasFocusTrigger += 1;
	}

	let selectedEdgeId = $state<string | null>(null);
	let selectedObjectKind = $state<'swimlane' | 'box' | 'group' | 'note' | null>(null);
	let selectedObjectIndex = $state<number>(-1);
	let labelFocusTrigger = $state(0);

	function clearAuxSelection() {
		selectedEdgeId = null;
		selectedObjectKind = null;
		selectedObjectIndex = -1;
	}

	function handleNodeDblClick(id: string) {
		handleNodeSelect(id);
		clearAuxSelection();
		inspectorOpen = true;
		settingsOpen = false;
		labelFocusTrigger += 1;
	}

	function handleEdgeSelect(id: string | null) {
		selectedEdgeId = id;
		if (id) {
			selectedNodeId = null;
			selectedObjectKind = null;
			selectedObjectIndex = -1;
			inspectorOpen = true;
			settingsOpen = false;
		}
	}

	function handleObjectSelect(
		kind: 'swimlane' | 'box' | 'group' | 'note' | null,
		index: number
	) {
		selectedObjectKind = kind;
		selectedObjectIndex = index;
		if (kind) {
			selectedNodeId = null;
			selectedEdgeId = null;
			inspectorOpen = true;
			settingsOpen = false;
		}
	}

	async function quickExportSvg() {
		try {
			await downloadSvg(name || 'dicegram', source);
		} catch (err) {
			showSaveToast(
				{ kind: 'error', message: err instanceof Error ? err.message : 'export failed' },
				5000
			);
		}
	}

	function focusFilterInput() {
		const el = document.querySelector<HTMLInputElement>(
			'input[placeholder^="Filter"]'
		);
		if (el) {
			el.focus();
			el.select();
		}
	}
</script>

<EdgeMarkers />

<div class="flex h-[calc(100vh-var(--header-h))] flex-col" style={themeVars}>
	{#if demoMode}
		<div
			class="flex items-center justify-center gap-3 border-b border-blue-800/60 bg-blue-950/50 px-3 py-1 text-[11px] text-blue-100"
		>
			<span>Demo mode — your changes stay in this browser only.</span>
			<a
				href="/signup"
				class="rounded border border-blue-700 px-2 py-0.5 text-[11px] font-medium text-blue-50 hover:bg-blue-900"
			>
				Sign up to save
			</a>
		</div>
	{/if}
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
		{autosaveStatus}
		onSave={save}
		onOpen={openList}
		onNew={newDicegram}
		onDirectionChange={(prev) => {
			const stripped = /@\(\s*-?\d+/.test(prev);
			preNormalizeSource = prev;
			normalizeToast = stripped
				? 'Direction changed — stripped pins, redrawn'
				: 'Direction changed — redrawn';
			if (normalizeToastTimer) clearTimeout(normalizeToastTimer);
			normalizeToastTimer = setTimeout(() => {
				normalizeToast = null;
				preNormalizeSource = null;
			}, 5000);
			// Full redraw: refit the viewport so xyflow doesn't sit on empty
			// space left behind by the old orientation.
			canvasFitAllTrigger += 1;
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
			<QuickInsert bind:source />
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
			class="relative flex min-w-0 flex-col transition-[padding-right]"
			style:padding-right={rightPaneOpen ? '340px' : '0'}
			style:background-color={theme.canvas}
		>
			<QuickInsert bind:source />
			<Canvas
				{result}
				{theme}
				{filter}
				{lineStyle}
				selectedId={selectedNodeId}
				focusId={canvasFocusId}
				focusTrigger={canvasFocusTrigger}
				fitAllTrigger={canvasFitAllTrigger}
				onNodeMove={writePosition}
				onNodeSelect={handleNodeSelect}
				onNodeDblClick={handleNodeDblClick}
				onEdgeSelect={handleEdgeSelect}
				onObjectSelect={handleObjectSelect}
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
	{selectedEdgeId}
	{selectedObjectKind}
	{selectedObjectIndex}
	{result}
	{labelFocusTrigger}
	onClose={() => (inspectorOpen = false)}
	onSelectionChange={handleSelectionChange}
	onEdgeSelectionChange={(id) => (selectedEdgeId = id)}
	onObjectSelectionChange={handleObjectSelect}
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
				View in Diegrams
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
			<h2 class="mb-3 text-lg font-semibold text-neutral-100">Your diegrams</h2>
			{#if myDicegrams.length === 0}
				<p class="text-sm text-neutral-400">No saved diegrams yet.</p>
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
