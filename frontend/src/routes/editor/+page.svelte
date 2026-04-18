<script lang="ts">
	import { goto } from '$app/navigation';
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
	import Canvas from './Canvas.svelte';
	import CodeEditor from './CodeEditor.svelte';
	import Toolbar from './Toolbar.svelte';
	import SettingsPane from './SettingsPane.svelte';
	import Inspector from './Inspector.svelte';
	import TreePanel from './TreePanel.svelte';
	import Icon from '$lib/Icon.svelte';

	const DEFAULT_SOURCE = `direction top-to-bottom
setting color_scheme gruvbox

// A meta-Dicegram: the loop we use to build Dicegram itself.

swimlane "User" {
	[circle] spark "Spark" step:0 type:start
	[rounded] ask "Describe\\nthe feature" step:1 type:process owner:"you" status:active
	[diamond] happy "Happy?" step:8 type:decision priority:high
}

swimlane "Claude" {
	box "Think" {fill: rgba(56, 70, 95, 0.25)} {
		[rect] plan "Draft a plan" step:2 type:process
		[rect] scope "Scope & trade-offs" step:3 type:process
	}
	box "Make" {fill: rgba(40, 70, 56, 0.25)} {
		[rect] edit "Edit code" step:4 type:automated status:active
		[hexagon] check "Typecheck + run" step:5 type:automated priority:critical
	}
}

swimlane "Repo" {
	[cylinder] dsl "Canonical DSL" step:6 type:datastore
	[rect] commit "Commit & push" step:7 type:automated
	[circle] ship "Shipped" step:9 type:end
}

spark -> ask
ask -> plan : "prompt"
plan -> scope
scope -> edit
edit ==> check : "verify"
check -> dsl : "writes"
dsl -> commit
commit -> happy : "review"
happy -> ask : "redirect"
happy -> ship : "yes"

note "The DSL is the\\nsource of truth" [dsl]
group "inner loop" { plan scope edit check }
`;

	let source = $state(DEFAULT_SOURCE);
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
		if (isEditableTarget(e.target)) return;
		if ((e.key === 'Delete' || e.key === 'Backspace') && selectedNodeId) {
			e.preventDefault();
			source = removeNode(source, selectedNodeId);
			selectedNodeId = null;
		}
	}

	onMount(() => {
		window.addEventListener('keydown', handleKeydown);
		return () => window.removeEventListener('keydown', handleKeydown);
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

	async function save() {
		if (!auth.user) return;
		saving = true;
		saveMsg = null;
		try {
			if (currentId) {
				const d = await api.update(currentId, { name, source });
				currentId = d.id;
			} else {
				const d = await api.create({ name, source });
				currentId = d.id;
			}
			saveMsg = 'saved';
			setTimeout(() => (saveMsg = null), 1500);
		} catch (err) {
			saveMsg = err instanceof ApiError ? err.message : 'save failed';
		} finally {
			saving = false;
		}
	}

	async function openList() {
		myDicegrams = await api.list();
		showOpen = true;
	}

	async function load(d: Dicegram) {
		currentId = d.id;
		name = d.name;
		source = d.source;
		showOpen = false;
		selectedNodeId = null;
	}

	function newDicegram() {
		currentId = null;
		name = 'Untitled dicegram';
		source = DEFAULT_SOURCE;
		selectedNodeId = null;
	}

	const rightPaneOpen = $derived(settingsOpen || inspectorOpen);
	const leftTreeOpen = $derived(treeOpen);

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
		{result}
		{currentId}
		{rendering}
		{saveMsg}
		{saving}
		onSave={save}
		onOpen={openList}
		onNew={newDicegram}
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
