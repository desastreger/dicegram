<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth } from '$lib/auth.svelte';
	import {
		palette,
		PALETTE_DEFAULTS,
		PALETTE_SECTIONS
	} from '$lib/palette.svelte';

	// Local working copy so color inputs feel snappy; PUT on commit.
	let draft = $state<Record<string, string>>({ ...palette.current });
	let saveTimer: ReturnType<typeof setTimeout> | null = null;
	let status = $state<'idle' | 'saving' | 'saved' | 'error'>('idle');
	let newPresetName = $state('');

	// Redirect anon visitors to login — palette is account-level.
	onMount(() => {
		if (!auth.loading && !auth.user) {
			goto('/login?next=/settings');
		}
		draft = { ...palette.current };
	});

	$effect(() => {
		if (palette.loaded) draft = { ...palette.current };
	});

	async function savePreset() {
		const n = newPresetName.trim();
		if (!n) return;
		await palette.savePreset(n);
		newPresetName = '';
	}

	async function activatePreset(name: string) {
		await palette.activatePreset(name);
		draft = { ...palette.current };
	}

	async function deletePreset(name: string) {
		if (!confirm(`Delete preset "${name}"?`)) return;
		await palette.deletePreset(name);
	}

	function onColorInput(key: string, value: string) {
		draft = { ...draft, [key]: value };
		queueSave();
	}

	function resetKey(key: string) {
		draft = { ...draft, [key]: PALETTE_DEFAULTS[key] };
		queueSave();
	}

	function queueSave() {
		status = 'saving';
		if (saveTimer) clearTimeout(saveTimer);
		saveTimer = setTimeout(async () => {
			try {
				await palette.save(draft);
				status = 'saved';
				setTimeout(() => (status = 'idle'), 1500);
			} catch {
				status = 'error';
			}
		}, 400);
	}

	async function resetAll() {
		if (!confirm('Reset all branding colours to the defaults?')) return;
		await palette.reset();
		draft = { ...palette.current };
		status = 'saved';
		setTimeout(() => (status = 'idle'), 1500);
	}

	function isOverridden(key: string): boolean {
		return draft[key] && draft[key] !== PALETTE_DEFAULTS[key];
	}
</script>

<svelte:head><title>Settings · Dicegram</title></svelte:head>

<section class="mx-auto max-w-3xl px-4 py-8">
	<header class="mb-6 flex items-end justify-between">
		<div>
			<h1 class="text-2xl font-semibold">Branding palette</h1>
			<p class="mt-1 text-sm text-neutral-400">
				Default colours for new elements. Per-node overrides in the inspector
				(<code class="rounded bg-neutral-900 px-1 py-0.5 text-xs">{'{fill:#…}'}</code>) still win —
				this palette only fills in what the DSL doesn't specify. Applies to your
				canvas, your SVG/PNG/PDF exports, and any diegrams you share.
			</p>
		</div>
		<div class="flex items-center gap-3 text-xs text-neutral-400">
			{#if status === 'saving'}<span>Saving…</span>{/if}
			{#if status === 'saved'}<span class="text-emerald-400">Saved</span>{/if}
			{#if status === 'error'}<span class="text-red-400">Save failed</span>{/if}
			<button
				onclick={resetAll}
				class="rounded border border-neutral-700 px-2 py-1 text-neutral-300 hover:bg-neutral-900 hover:text-white"
			>
				Reset all
			</button>
		</div>
	</header>

	<!-- Preset switcher -->
	<div class="mb-8 rounded border border-neutral-800 bg-neutral-950 p-4">
		<div class="mb-3 flex items-end justify-between gap-3">
			<div>
				<h2 class="text-sm font-semibold text-neutral-200">Brand presets</h2>
				<p class="mt-1 text-xs text-neutral-500">
					Save your current colours as a named preset, then switch between presets with one click.
				</p>
			</div>
			<form
				class="flex items-center gap-2"
				onsubmit={(e) => {
					e.preventDefault();
					savePreset();
				}}
			>
				<input
					type="text"
					bind:value={newPresetName}
					placeholder="e.g. Enterprise Blue"
					maxlength="60"
					class="w-44 rounded border border-neutral-800 bg-neutral-900 px-2 py-1 text-xs text-neutral-100 focus:border-neutral-600 focus:outline-none"
				/>
				<button
					type="submit"
					disabled={!newPresetName.trim()}
					class="rounded bg-blue-600 px-3 py-1 text-xs font-medium text-white hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
				>
					Save current as…
				</button>
			</form>
		</div>
		{#if palette.presets.length === 0}
			<p class="text-xs text-neutral-500">No presets yet. Type a name and click "Save current as…" to create one.</p>
		{:else}
			<ul class="flex flex-wrap gap-2">
				{#each palette.presets as p (p.name)}
					<li
						class="flex items-center gap-2 rounded border px-2 py-1 text-xs {p.active
							? 'border-blue-500 bg-blue-950/40 text-blue-200'
							: 'border-neutral-800 bg-neutral-900 text-neutral-200'}"
					>
						<span class="font-medium">{p.name}</span>
						{#if p.active}
							<span class="text-[10px] uppercase tracking-wider text-blue-400">active</span>
						{:else}
							<button
								type="button"
								onclick={() => activatePreset(p.name)}
								class="text-neutral-400 hover:text-white"
							>
								Activate
							</button>
						{/if}
						<button
							type="button"
							onclick={() => deletePreset(p.name)}
							title="Delete preset"
							class="text-neutral-500 hover:text-red-400"
						>
							×
						</button>
					</li>
				{/each}
			</ul>
		{/if}
	</div>

	{#each PALETTE_SECTIONS as section}
		<div class="mb-8">
			<h2 class="mb-3 text-xs font-semibold uppercase tracking-wider text-neutral-500">
				{section.title}
			</h2>
			<div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
				{#each section.keys as item}
					<div class="flex items-center gap-3 rounded border border-neutral-800 bg-neutral-950 p-2">
						<input
							type="color"
							value={draft[item.key] || PALETTE_DEFAULTS[item.key] || '#1f2937'}
							oninput={(e) => onColorInput(item.key, e.currentTarget.value)}
							class="h-8 w-10 shrink-0 cursor-pointer rounded border border-neutral-700 bg-transparent"
							aria-label={item.label}
						/>
						<div class="min-w-0 flex-1">
							<div class="truncate text-sm text-neutral-100">{item.label}</div>
							{#if item.hint}
								<div class="truncate font-mono text-[11px] text-neutral-500">{item.hint}</div>
							{/if}
						</div>
						<input
							type="text"
							value={draft[item.key] ?? ''}
							oninput={(e) => onColorInput(item.key, e.currentTarget.value)}
							placeholder={PALETTE_DEFAULTS[item.key] || '(default)'}
							class="w-24 rounded border border-neutral-800 bg-neutral-900 px-2 py-1 font-mono text-xs text-neutral-200 focus:border-neutral-600 focus:outline-none"
						/>
						{#if isOverridden(item.key)}
							<button
								onclick={() => resetKey(item.key)}
								title="Reset to default"
								class="text-xs text-neutral-500 hover:text-neutral-200"
							>
								↺
							</button>
						{/if}
					</div>
				{/each}
			</div>
		</div>
	{/each}
</section>
