<script lang="ts">
	import Icon from '$lib/Icon.svelte';
	import { addNode, addSwimlane, getDirection, setDirection } from '$lib/patch';
	import { copyDsl, copyLlmPrompt, copySvg, downloadPng, downloadSvg } from '$lib/export';
	import type { RenderResult } from '$lib/render';

	let {
		source = $bindable(''),
		name = $bindable(''),
		result,
		currentId,
		rendering,
		saveMsg,
		saving,
		settingsOpen = $bindable(false),
		inspectorOpen = $bindable(false),
		onSave,
		onOpen,
		onNew
	}: {
		source: string;
		name: string;
		result: RenderResult | null;
		currentId: number | null;
		rendering: boolean;
		saveMsg: string | null;
		saving: boolean;
		settingsOpen: boolean;
		inspectorOpen: boolean;
		onSave: () => void;
		onOpen: () => void;
		onNew: () => void;
	} = $props();

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

	async function doExport(kind: 'svg' | 'png' | 'copy-svg' | 'copy-dsl' | 'copy-llm') {
		exportOpen = false;
		const baseName = name || 'dicegram';
		try {
			if (kind === 'svg') await downloadSvg(baseName, source);
			else if (kind === 'png') await downloadPng(baseName, source);
			else if (kind === 'copy-svg') await copySvg(source);
			else if (kind === 'copy-dsl') await copyDsl(source);
			else if (kind === 'copy-llm') await copyLlmPrompt(source);
		} catch (err) {
			console.error('export failed', err);
			alert('Export failed: ' + (err instanceof Error ? err.message : String(err)));
		}
	}

	const DIRECTIONS: { id: string; icon: string; label: string }[] = [
		{ id: 'top-to-bottom', icon: 'arrow-down', label: 'Top to Bottom' },
		{ id: 'left-to-right', icon: 'arrow-right', label: 'Left to Right' },
		{ id: 'bottom-to-top', icon: 'arrow-up', label: 'Bottom to Top' },
		{ id: 'right-to-left', icon: 'arrow-left', label: 'Right to Left' }
	];

	const SHAPES: { id: string; label: string }[] = [
		{ id: 'rect', label: 'Rectangle' },
		{ id: 'rounded', label: 'Rounded' },
		{ id: 'diamond', label: 'Diamond' },
		{ id: 'circle', label: 'Circle' },
		{ id: 'parallelogram', label: 'Parallelogram' },
		{ id: 'hexagon', label: 'Hexagon' },
		{ id: 'cylinder', label: 'Cylinder' },
		{ id: 'stadium', label: 'Stadium' }
	];

	let insertOpen = $state(false);
	let insertRoot: HTMLDivElement | undefined = $state();

	const activeDirection = $derived(result?.direction ?? getDirection(source));
	const nodeCount = $derived(result?.nodes.length ?? 0);
	const errorCount = $derived(result?.errors.length ?? 0);

	function nextNodeName(): string {
		const ids = new Set((result?.nodes ?? []).map((n) => n.id));
		let n = 1;
		while (ids.has(`node${n}`)) n++;
		return `node${n}`;
	}

	function nextStep(): number {
		const steps = (result?.nodes ?? []).map((n) => {
			const s = n.attrs?.step;
			return s != null ? Number(s) : 0;
		});
		return Math.max(0, ...steps) + 1;
	}

	function pickShape(shape: string) {
		insertOpen = false;
		const name = nextNodeName();
		source = addNode(source, { name, shape, step: nextStep() });
	}

	function promptSwimlane() {
		const laneName = window.prompt('Swimlane name');
		if (laneName && laneName.trim()) {
			source = addSwimlane(source, laneName.trim());
		}
	}

	function pickDirection(dir: string) {
		if (dir === activeDirection) return;
		source = setDirection(source, dir);
	}

	function handleDocClick(e: MouseEvent) {
		if (!insertOpen) return;
		if (insertRoot && !insertRoot.contains(e.target as Node)) insertOpen = false;
	}

	$effect(() => {
		document.addEventListener('click', handleDocClick);
		return () => document.removeEventListener('click', handleDocClick);
	});
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
		<button
			type="button"
			onclick={onNew}
			title="New dicegram"
			class="flex h-6 items-center gap-1 rounded border border-neutral-800 px-2 text-neutral-200 hover:bg-neutral-800"
		>
			<Icon name="file-plus" size={13} />
			<span class="hidden md:inline">New</span>
		</button>
	</div>

	<span class="h-4 w-px bg-neutral-800"></span>

	<div class="relative" bind:this={insertRoot}>
		<button
			type="button"
			onclick={() => (insertOpen = !insertOpen)}
			aria-expanded={insertOpen}
			title="Insert shape"
			class="flex h-6 items-center gap-1 rounded border border-neutral-800 px-2 text-neutral-200 hover:bg-neutral-800"
		>
			<Icon name="shapes" size={13} />
			<span class="hidden md:inline">Insert</span>
			<Icon name="chevron-down" size={11} />
		</button>
		{#if insertOpen}
			<div
				class="absolute left-0 top-full z-20 mt-1 w-44 overflow-hidden rounded border border-neutral-800 bg-neutral-900 shadow-lg"
			>
				{#each SHAPES as s (s.id)}
					<button
						type="button"
						onclick={() => pickShape(s.id)}
						class="block w-full px-3 py-1 text-left text-neutral-200 hover:bg-neutral-800"
					>
						{s.label}
					</button>
				{/each}
			</div>
		{/if}
	</div>

	<button
		type="button"
		onclick={promptSwimlane}
		title="Add swimlane"
		class="flex h-6 items-center gap-1 rounded border border-neutral-800 px-2 text-neutral-200 hover:bg-neutral-800"
	>
		<Icon name="columns" size={13} />
		<span class="hidden lg:inline">Swimlane</span>
	</button>

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
					onclick={() => doExport('copy-llm')}
					class="flex w-full items-center gap-2 px-3 py-1 text-left text-neutral-200 hover:bg-neutral-800"
				>
					<Icon name="sparkles" size={13} /> Copy LLM prompt
				</button>
			</div>
		{/if}
	</div>

	<div class="ml-auto flex items-center gap-2 text-[11px]">
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
		{/if}
	</div>
</div>
