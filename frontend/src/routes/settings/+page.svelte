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

	async function toggleLock() {
		await palette.setLocked(!palette.locked);
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
			<h1 class="text-2xl font-semibold text-app">Branding palette</h1>
			<p class="mt-1 text-sm text-muted">
				Default colours for new elements. Per-node overrides in the inspector
				(<code class="rounded bg-surface-2 px-1 py-0.5 text-xs">{'{fill:#…}'}</code>) still win —
				this palette only fills in what the DSL doesn't specify. Applies to your
				canvas, your SVG/PNG/PDF exports, and any diegrams you share.
			</p>
		</div>
		<div class="flex items-center gap-3 text-xs text-muted">
			<span role="status" aria-live="polite">
				{#if status === 'saving'}Saving…{/if}
				{#if status === 'saved'}<span class="text-ok">Saved</span>{/if}
				{#if status === 'error'}<span class="text-danger">Save failed</span>{/if}
			</span>
			<button type="button" onclick={resetAll} class="btn-secondary text-xs">
				Reset all
			</button>
		</div>
	</header>

	<!-- Brand lock -->
	<div class="panel mb-4 flex items-start gap-3 p-4">
		<button
			type="button"
			onclick={toggleLock}
			role="switch"
			aria-checked={!!palette.locked}
			aria-label="Enforce brand palette"
			class="toggle-track {palette.locked ? 'toggle-track-on' : ''} mt-0.5"
		>
			<span class="toggle-knob"></span>
		</button>
		<div class="min-w-0 flex-1">
			<div class="text-sm font-medium text-app">Enforce brand palette</div>
			<p class="mt-0.5 text-xs text-dim">
				When on, the editor's Inspector hides inline colour overrides — every node takes its
				colour from this palette. Keep off for creative freedom; turn on for agency / enterprise
				brand consistency.
			</p>
		</div>
	</div>

	<!-- Preset switcher -->
	<div class="panel mb-8 p-4">
		<div class="mb-3 flex items-end justify-between gap-3">
			<div>
				<h2 class="text-sm font-semibold text-app">Brand presets</h2>
				<p class="mt-1 text-xs text-dim">
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
					class="input-themed w-44 text-xs"
				/>
				<button
					type="submit"
					disabled={!newPresetName.trim()}
					class="btn-primary text-xs"
				>
					Save current as…
				</button>
			</form>
		</div>
		{#if palette.presets.length === 0}
			<p class="text-xs text-dim">No presets yet. Type a name and click "Save current as…" to create one.</p>
		{:else}
			<ul class="flex flex-wrap gap-2">
				{#each palette.presets as p (p.name)}
					<li class="badge {p.active ? 'badge-active' : ''}">
						<span class="font-medium text-app">{p.name}</span>
						{#if p.active}
							<span class="text-[10px] uppercase tracking-wider text-accent">active</span>
						{:else}
							<button
								type="button"
								onclick={() => activatePreset(p.name)}
								class="text-muted hover:text-app"
							>
								Activate
							</button>
						{/if}
						<button
							type="button"
							onclick={() => deletePreset(p.name)}
							title="Delete preset"
							aria-label={`Delete preset "${p.name}"`}
							class="text-dim hover:text-danger"
						>
							<span aria-hidden="true">×</span>
						</button>
					</li>
				{/each}
			</ul>
		{/if}
	</div>

	{#each PALETTE_SECTIONS as section}
		<div class="mb-8">
			<h2 class="mb-3 text-xs font-semibold uppercase tracking-wider text-dim">
				{section.title}
			</h2>
			<div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
				{#each section.keys as item}
					<div class="panel flex items-center gap-3 p-2">
						<input
							type="color"
							value={draft[item.key] || PALETTE_DEFAULTS[item.key] || '#888888'}
							oninput={(e) => onColorInput(item.key, e.currentTarget.value)}
							class="h-8 w-10 shrink-0 cursor-pointer rounded border border-app bg-transparent"
							aria-label={item.label}
						/>
						<div class="min-w-0 flex-1">
							<div class="truncate text-sm text-app">{item.label}</div>
							{#if item.hint}
								<div class="truncate font-mono text-[11px] text-dim">{item.hint}</div>
							{/if}
						</div>
						<input
							type="text"
							value={draft[item.key] ?? ''}
							oninput={(e) => onColorInput(item.key, e.currentTarget.value)}
							placeholder={PALETTE_DEFAULTS[item.key] || '(default)'}
							aria-label={`${item.label} hex value`}
							class="input-themed w-24 font-mono text-xs"
						/>
						{#if isOverridden(item.key)}
							<button
								type="button"
								onclick={() => resetKey(item.key)}
								title="Reset to default"
								aria-label={`Reset ${item.label} to default`}
								class="text-xs text-dim hover:text-app"
							>
								<span aria-hidden="true">↺</span>
							</button>
						{/if}
					</div>
				{/each}
			</div>
		</div>
	{/each}
</section>
