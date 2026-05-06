<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth } from '$lib/auth.svelte';
	import ConfirmDialog from '$lib/ConfirmDialog.svelte';
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

	// In-page confirm prompts (no native confirm() — blocks Playwright + OS chrome).
	let confirmDeleteOpen = $state(false);
	let confirmDeleteName = $state('');
	let confirmResetOpen = $state(false);

	// Account section (username + password reminder hint).
	let usernameDraft = $state('');
	let hintDraft = $state('');
	let accountStatus = $state<'idle' | 'saving' | 'saved' | 'error'>('idle');
	let accountStatusTimer: ReturnType<typeof setTimeout> | null = null;
	$effect(() => {
		if (auth.user) {
			usernameDraft = auth.user.username ?? '';
			hintDraft = auth.user.password_hint ?? '';
		}
	});

	function flashAccount(s: 'saved' | 'error') {
		accountStatus = s;
		if (accountStatusTimer) clearTimeout(accountStatusTimer);
		accountStatusTimer = setTimeout(() => (accountStatus = 'idle'), 1500);
	}

	async function saveUsername() {
		const v = usernameDraft.trim();
		if (!v || v === (auth.user?.username ?? '')) return;
		accountStatus = 'saving';
		try {
			await auth.updateUsername(v);
			flashAccount('saved');
		} catch {
			flashAccount('error');
		}
	}

	async function saveHint() {
		const v = hintDraft.trim();
		if (!v || v === (auth.user?.password_hint ?? '')) return;
		accountStatus = 'saving';
		try {
			await auth.updateHint(v);
			flashAccount('saved');
		} catch {
			flashAccount('error');
		}
	}

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

	function deletePreset(name: string) {
		confirmDeleteName = name;
		confirmDeleteOpen = true;
	}
	async function confirmDeletePreset() {
		const n = confirmDeleteName;
		if (!n) return;
		await palette.deletePreset(n);
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

	function resetAll() {
		confirmResetOpen = true;
	}
	async function confirmResetAll() {
		await palette.reset();
		draft = { ...palette.current };
		status = 'saved';
		setTimeout(() => (status = 'idle'), 1500);
	}

	// "Overridden" means the user has actually written a value for this key
	// — i.e. it's in `palette.userOverrides`. Comparing the resolved palette
	// against PALETTE_DEFAULTS (dark hex) misclassifies every Auto-theme key
	// as overridden, because Auto's palette returns `var(--app-…)` /
	// `color-mix(…)` strings that obviously don't equal a dark hex.
	function isOverridden(key: string): boolean {
		const v = palette.userOverrides[key];
		return Boolean(v && v.length > 0);
	}

	// `<input type="color">` only accepts a `#RRGGBB` literal — but the
	// Auto theme returns CSS like `var(--app-surface-2)` and
	// `color-mix(in srgb, …)` that the native swatch can't render. Resolve
	// any CSS colour to a hex by letting the browser do the parsing on an
	// off-document element. Cached because `getComputedStyle` triggers
	// layout work and we re-render this list every keystroke.
	const colorCache = new Map<string, string>();
	function resolveCssColor(value: string | undefined): string {
		if (!value) return '#888888';
		if (typeof document === 'undefined') return '#888888';
		const cached = colorCache.get(value);
		if (cached) return cached;
		const probe = document.createElement('span');
		probe.style.color = value;
		probe.style.display = 'none';
		document.body.appendChild(probe);
		const cs = getComputedStyle(probe).color;
		probe.remove();
		const m = cs.match(/^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/);
		if (!m) {
			colorCache.set(value, '#888888');
			return '#888888';
		}
		const toHex = (n: string) => Number(n).toString(16).padStart(2, '0');
		const hex = `#${toHex(m[1])}${toHex(m[2])}${toHex(m[3])}`;
		colorCache.set(value, hex);
		return hex;
	}
</script>

<svelte:head><title>Settings · Dicegram</title></svelte:head>

<section class="mx-auto max-w-3xl px-4 py-8">
	<!-- Account: display name + password hint. The hint is the bridge while
	     SMTP-driven recovery is offline — anyone with the user's email can
	     look it up on /forgot-password, so we surface it here so the user
	     knows exactly what's stored. -->
	<header class="mb-6">
		<h1 class="text-2xl font-semibold text-app">Account &amp; appearance</h1>
		<p class="mt-1 text-sm text-muted">
			Your display name, the password hint we'll show you on /forgot-password, and the brand
			colours every new diegram inherits.
		</p>
	</header>

	<div class="panel mb-8 p-5">
		<div class="mb-4 flex items-baseline justify-between gap-3">
			<div>
				<h2 class="text-sm font-semibold text-app">Account</h2>
				<p class="mt-1 text-xs text-dim">
					Username changes are visible in shared dicegrams. The hint is what /forgot-password
					shows when someone enters your email — make it personal but not literal.
				</p>
			</div>
			<span role="status" aria-live="polite" class="text-xs text-muted shrink-0">
				{#if accountStatus === 'saving'}Saving…{/if}
				{#if accountStatus === 'saved'}<span class="text-ok">Saved</span>{/if}
				{#if accountStatus === 'error'}<span class="text-danger">Save failed</span>{/if}
			</span>
		</div>

		<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
			<label class="flex flex-col gap-1">
				<span class="field-label">Username</span>
				<input
					type="text"
					maxlength="60"
					bind:value={usernameDraft}
					onblur={saveUsername}
					class="input-themed"
					placeholder={auth.user?.email ?? ''}
				/>
			</label>
			<label class="flex flex-col gap-1">
				<span class="field-label">Email</span>
				<input
					type="email"
					value={auth.user?.email ?? ''}
					disabled
					class="input-themed"
				/>
			</label>
			<label class="flex flex-col gap-1 sm:col-span-2">
				<span class="field-label">Password reminder</span>
				<input
					type="text"
					maxlength="140"
					bind:value={hintDraft}
					onblur={saveHint}
					placeholder="e.g. my dog's birthday + favourite city"
					class="input-themed"
				/>
				<span class="text-xs text-dim">
					Save the form by clicking outside the field. Email-based password reset is paused;
					this hint is the only nudge we can give you on /forgot-password.
				</span>
			</label>
		</div>
	</div>

	<header class="mb-6 flex items-end justify-between">
		<div>
			<h2 class="text-2xl font-semibold text-app">Branding palette</h2>
			<p class="mt-1 text-sm text-muted">
				Default colours for new elements. Per-node overrides in the inspector
				(<code class="rounded bg-surface-2 px-1 py-0.5 text-xs">{'{fill:#…}'}</code>) still win —
				this palette only fills in what the DSL doesn't specify. Applies to your
				canvas, your SVG/PNG/PDF exports, and any diegrams you share.
			</p>
		</div>
		<div class="flex shrink-0 items-center gap-3 text-xs text-muted">
			<span role="status" aria-live="polite">
				{#if status === 'saving'}Saving…{/if}
				{#if status === 'saved'}<span class="text-ok">Saved</span>{/if}
				{#if status === 'error'}<span class="text-danger">Save failed</span>{/if}
			</span>
			<button
				type="button"
				onclick={resetAll}
				class="btn-danger text-xs whitespace-nowrap"
			>
				Reset all colours
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

	<style>
		.swatch-default {
			border-style: dashed;
			background: color-mix(in srgb, var(--app-surface) 70%, transparent);
		}
	</style>

	{#each PALETTE_SECTIONS as section}
		<div class="mb-8">
			<h2 class="mb-3 text-xs font-semibold uppercase tracking-wider text-dim">
				{section.title}
			</h2>
			<div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
				{#each section.keys as item}
					{@const isOver = isOverridden(item.key)}
					<div class="panel flex items-center gap-3 p-2" class:swatch-default={!isOver}>
						<input
							type="color"
							value={resolveCssColor(draft[item.key] || PALETTE_DEFAULTS[item.key])}
							oninput={(e) => onColorInput(item.key, e.currentTarget.value)}
							class="h-8 w-10 shrink-0 cursor-pointer rounded border border-app bg-transparent"
							aria-label={item.label}
						/>
						<div class="min-w-0 flex-1">
							<div class="flex items-baseline gap-2">
								<span class="truncate text-sm text-app">{item.label}</span>
								{#if !isOver}
									<span class="text-[10px] uppercase tracking-wider text-dim">default</span>
								{/if}
							</div>
							{#if item.hint}
								<div class="truncate font-mono text-[11px] text-dim">{item.hint}</div>
							{/if}
						</div>
						<input
							type="text"
							value={isOver ? draft[item.key] : ''}
							oninput={(e) => onColorInput(item.key, e.currentTarget.value)}
							placeholder={resolveCssColor(PALETTE_DEFAULTS[item.key])}
							aria-label={`${item.label} hex value`}
							class="input-themed w-24 font-mono text-xs"
						/>
						{#if isOver}
							<button
								type="button"
								onclick={() => resetKey(item.key)}
								title="Reset to default"
								aria-label={`Reset ${item.label} to default`}
								class="btn-icon"
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

<ConfirmDialog
	bind:open={confirmDeleteOpen}
	title={`Delete preset "${confirmDeleteName}"?`}
	message="Removes the named brand preset from your account. Active palette colours are unaffected."
	confirmLabel="Delete preset"
	tone="danger"
	onConfirm={confirmDeletePreset}
/>

<ConfirmDialog
	bind:open={confirmResetOpen}
	title="Reset all branding colours?"
	message="Every override snaps back to the Dicegram defaults. Your saved presets are kept."
	confirmLabel="Reset colours"
	tone="danger"
	onConfirm={confirmResetAll}
/>
