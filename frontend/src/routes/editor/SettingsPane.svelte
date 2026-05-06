<script lang="ts">
	import * as patch from '$lib/patch';
	import Icon from '$lib/Icon.svelte';
	import Dropdown from '$lib/Dropdown.svelte';
	import ConfirmDialog from '$lib/ConfirmDialog.svelte';
	import { THEMES, THEME_IDS, DEFAULT_THEME_ID } from '$lib/themes';
	import { palette, PALETTE_SECTIONS, themePalette } from '$lib/palette.svelte';
	import type { RenderResult } from '$lib/render';

	// In-page confirm — never use native window.confirm() (UAT blocker, OS chrome).
	let confirmResetOpen = $state(false);

	type Props = {
		source?: string;
		result: RenderResult | null;
		open?: boolean;
		onClose: () => void;
	};

	let {
		source = $bindable(''),
		result,
		open = $bindable(false),
		onClose
	}: Props = $props();

	const NUMBER_KEYS: Array<{ key: string; label: string; def: number }> = [
		{ key: 'node_width', label: 'Node width', def: 160 },
		{ key: 'node_height', label: 'Node height', def: 70 },
		{ key: 'h_gap', label: 'Horizontal gap', def: 60 },
		{ key: 'v_gap', label: 'Vertical gap', def: 80 },
		{ key: 'swimlane_gap', label: 'Swimlane gap', def: 40 },
		{ key: 'container_padding', label: 'Container padding', def: 32 },
		{ key: 'snap_grid', label: 'Snap grid', def: 10 }
	];

	const TOGGLE_KEYS: Array<{ key: string; label: string; hint?: string }> = [
		{ key: 'auto_capitalize', label: 'Auto-capitalize labels' },
		{ key: 'show_step_bands', label: 'Show step bands' },
		{
			key: 'free_placement',
			label: 'Free placement mode',
			hint: 'Off (default): compiler forces canonical shapes and lane alignment. On: keep exactly what you typed.'
		}
	];

	const DIRECTIONS: Array<{ id: string; icon: string; label: string }> = [
		{ id: 'top-to-bottom', icon: 'arrow-down', label: 'Top to Bottom' },
		{ id: 'left-to-right', icon: 'arrow-right', label: 'Left to Right' },
		{ id: 'bottom-to-top', icon: 'arrow-up', label: 'Bottom to Top' },
		{ id: 'right-to-left', icon: 'arrow-left', label: 'Right to Left' }
	];

	const LINE_STYLES: Array<{ value: string; label: string }> = [
		{ value: 'orthogonal', label: 'Orthogonal (default)' },
		{ value: 'curved', label: 'Curved' },
		{ value: 'straight', label: 'Straight (direct)' }
	];
	const DEFAULT_LINE_STYLE = 'orthogonal';

	// Palette tokens stored as `setting palette_<key> <color>` so a single
	// Dicegram can deviate from its theme without touching the user's
	// global brand palette.
	const PALETTE_OVERRIDE_KEYS = PALETTE_SECTIONS.flatMap((s) => s.keys.map((k) => `palette_${k.key}`));

	const ALL_SETTING_KEYS = [
		'color_scheme',
		'line_style',
		'font_family',
		...NUMBER_KEYS.map((n) => n.key),
		...TOGGLE_KEYS.map((t) => t.key),
		...PALETTE_OVERRIDE_KEYS
	];

	const themeId = $derived(patch.getSetting(source, 'color_scheme') ?? DEFAULT_THEME_ID);
	const lineStyleId = $derived(patch.getSetting(source, 'line_style') ?? DEFAULT_LINE_STYLE);
	const fontFamilyValue = $derived(patch.getSetting(source, 'font_family') ?? '');
	const direction = $derived(patch.getDirection(source));

	// Resolved baseline for the active theme — shown as the "default" swatch
	// in the palette-override pickers so the user can see what they're
	// deviating from.
	const themeBaseline = $derived(themePalette(themeId));
	const userBaseline = $derived(palette.userOverrides);

	function paletteOverride(key: string): string {
		return patch.getSetting(source, `palette_${key}`) ?? '';
	}

	function effectivePaletteValue(key: string): string {
		const override = paletteOverride(key);
		if (override) return override;
		const userVal = userBaseline[key];
		if (userVal) return userVal;
		return themeBaseline[key] || '#000000';
	}

	function commitPaletteOverride(key: string, raw: string) {
		const v = (raw ?? '').trim();
		if (!v) {
			source = patch.removeSetting(source, `palette_${key}`);
			return;
		}
		// Permissive: accept #abc, #aabbcc, rgb(...), hsl(...)
		const isHex = /^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$/.test(v);
		if (isHex) {
			source = patch.setSetting(source, `palette_${key}`, v.startsWith('#') ? v : `#${v}`);
		} else if (/^(rgb|hsl)/.test(v)) {
			source = patch.setSetting(source, `palette_${key}`, v);
		}
	}

	function clearPaletteOverride(key: string) {
		source = patch.removeSetting(source, `palette_${key}`);
	}

	function commitFontFamily(raw: string) {
		const v = (raw ?? '').trim();
		if (!v) source = patch.removeSetting(source, 'font_family');
		else source = patch.setSetting(source, 'font_family', v);
	}

	function clearAllPaletteOverrides() {
		let next = source;
		for (const k of PALETTE_OVERRIDE_KEYS) {
			next = patch.removeSetting(next, k);
		}
		source = next;
	}

	const hasAnyPaletteOverride = $derived(
		PALETTE_OVERRIDE_KEYS.some((k) => patch.getSetting(source, k) != null)
	);

	let paletteOpen = $state(false);
	const numberValues = $derived(
		Object.fromEntries(
			NUMBER_KEYS.map((n) => {
				const raw = patch.getSetting(source, n.key);
				const parsed = raw != null ? Number(raw) : NaN;
				return [n.key, Number.isFinite(parsed) ? parsed : n.def];
			})
		) as Record<string, number>
	);
	const toggleValues = $derived(
		Object.fromEntries(
			TOGGLE_KEYS.map((t) => {
				const raw = patch.getSetting(source, t.key);
				return [t.key, raw === '1' || raw === 'true'];
			})
		) as Record<string, boolean>
	);

	const debounceTimers = new Map<string, ReturnType<typeof setTimeout>>();

	function scheduleNumberWrite(key: string, value: number) {
		const existing = debounceTimers.get(key);
		if (existing) clearTimeout(existing);
		const t = setTimeout(() => {
			source = patch.setSetting(source, key, value);
			debounceTimers.delete(key);
		}, 200);
		debounceTimers.set(key, t);
	}

	function setTheme(id: string) {
		source = patch.setSetting(source, 'color_scheme', id);
	}

	function setLineStyle(id: string) {
		if (id === DEFAULT_LINE_STYLE) source = patch.removeSetting(source, 'line_style');
		else source = patch.setSetting(source, 'line_style', id);
	}

	function setDir(id: string) {
		source = patch.setDirection(source, id);
	}

	function setToggle(key: string, checked: boolean) {
		source = patch.setSetting(source, key, checked ? 1 : 0);
	}

	function resetDefaults() {
		confirmResetOpen = true;
	}
	function applyResetDefaults() {
		let next = source;
		for (const key of ALL_SETTING_KEYS) {
			next = patch.removeSetting(next, key);
		}
		source = next;
	}

	function handleClose() {
		open = false;
		onClose();
	}
</script>

{#if open}
	<aside class="dg-settings">
		<div class="dg-settings-head">
			<h2 class="dg-settings-title">
				<Icon name="settings" size={13} /> Dicegram settings
			</h2>
			<button
				type="button"
				class="btn-icon"
				aria-label="Close settings"
				onclick={handleClose}
			>
				<Icon name="x" size={14} />
			</button>
		</div>

		<div class="dg-section">Theme</div>
		<div class="px-3">
			<Dropdown
				value={themeId}
				options={THEME_IDS.map((id) => ({ value: id, label: THEMES[id].label }))}
				onchange={setTheme}
			/>
			<p class="mt-1 text-[10px] leading-snug text-neutral-500">
				The theme is the master. Non-unique nodes re-skin instantly when you swap it.
			</p>
		</div>

		<div class="dg-section">
			Font family
		</div>
		<div class="px-3">
			<input
				type="text"
				placeholder="(theme default)"
				aria-label="Font family"
				class="dg-set-input"
				value={fontFamilyValue}
				onchange={(e) => commitFontFamily((e.currentTarget as HTMLInputElement).value)}
			/>
			<p class="dg-help">
				Applies to every node label without an inline font_family override.
			</p>
		</div>

		<!-- Per-Dicegram palette overrides — these stack on top of the
		     theme baseline + the user's brand palette, so a single Dicegram
		     can deviate without leaving the theme or touching their saved
		     brand colors. -->
		<div class="dg-section dg-section-row">
			<button
				type="button"
				class="dg-section-trigger"
				aria-expanded={paletteOpen}
				onclick={() => (paletteOpen = !paletteOpen)}
			>
				<Icon name={paletteOpen ? 'chevron-down' : 'chevron-right'} size={11} />
				Palette overrides
			</button>
			{#if hasAnyPaletteOverride}
				<button
					type="button"
					class="dg-set-mini"
					title="Clear every per-Dicegram palette override"
					onclick={clearAllPaletteOverrides}
				>
					Clear all
				</button>
			{/if}
		</div>
		{#if paletteOpen}
			<div class="px-3">
				{#each PALETTE_SECTIONS as section (section.title)}
					<div class="dg-pal-section">
						{section.title}
					</div>
					<div class="space-y-1">
						{#each section.keys as item (item.key)}
							{@const overrideVal = paletteOverride(item.key)}
							{@const effective = effectivePaletteValue(item.key)}
							<div class="flex items-center gap-2">
								<label
									class="dg-pal-label"
									title={item.hint ?? item.label}
								>
									{item.label}
								</label>
								<input
									type="color"
									class="dg-set-color"
									value={effective}
									onchange={(e) =>
										commitPaletteOverride(item.key, (e.currentTarget as HTMLInputElement).value)}
									aria-label="{item.label} colour"
								/>
								<input
									type="text"
									placeholder="auto"
									aria-label="{item.label} hex value"
									class="dg-set-input dg-set-input-mono"
									value={overrideVal}
									onchange={(e) =>
										commitPaletteOverride(item.key, (e.currentTarget as HTMLInputElement).value)}
								/>
								<button
									type="button"
									class="dg-set-mini-x"
									disabled={!overrideVal}
									onclick={() => clearPaletteOverride(item.key)}
									aria-label="Clear {item.label} override"
									title="Drop this override (revert to theme + user brand)"
								>
									<Icon name="x" size={10} />
								</button>
							</div>
						{/each}
					</div>
				{/each}
			</div>
		{/if}

		<div class="dg-section">Direction</div>
		<div class="px-3">
			<div class="dg-set-segment">
				{#each DIRECTIONS as d (d.id)}
					<button
						type="button"
						title={d.label}
						aria-pressed={direction === d.id}
						aria-label={`Layout direction: ${d.label.toLowerCase()}`}
						class="dg-set-seg-btn"
						class:dg-set-seg-on={direction === d.id}
						onclick={() => setDir(d.id)}
					>
						<Icon name={d.icon} size={13} />
					</button>
				{/each}
			</div>
		</div>

		<div class="dg-section">Line style</div>
		<div class="px-3">
			<Dropdown value={lineStyleId} options={LINE_STYLES} onchange={setLineStyle} />
			<p class="dg-help">
				Orthogonal routes around obstacles with right-angle bends. Curved draws a smooth bezier. Straight is a direct diagonal.
			</p>
		</div>

		<div class="dg-section">Layout</div>
		<div class="space-y-1 px-3">
			{#each NUMBER_KEYS as n (n.key)}
				<label class="dg-num-row">
					<span class="dg-num-label">{n.label}</span>
					<span class="dg-num-input-wrap">
						<input
							type="number"
							aria-label={n.label}
							class="dg-num-input numeric"
							value={numberValues[n.key]}
							oninput={(e) => {
								const v = Number((e.currentTarget as HTMLInputElement).value);
								if (Number.isFinite(v)) scheduleNumberWrite(n.key, v);
							}}
						/>
						<span class="dg-num-suffix" aria-hidden="true">px</span>
					</span>
				</label>
			{/each}
		</div>

		<div class="dg-section">Options</div>
		<div class="space-y-1 px-3">
			{#each TOGGLE_KEYS as t (t.key)}
				<label class="dg-toggle-row" title={t.hint}>
					<span class="dg-num-label">{t.label}</span>
					<input
						type="checkbox"
						class="dg-checkbox"
						checked={toggleValues[t.key]}
						onchange={(e) => setToggle(t.key, (e.currentTarget as HTMLInputElement).checked)}
					/>
				</label>
				{#if t.hint}
					<p class="dg-help">{t.hint}</p>
				{/if}
			{/each}
		</div>

		<div class="mt-4 px-3 pb-6">
			<button type="button" class="btn-danger dg-reset-btn" onclick={resetDefaults}>
				<Icon name="trash" size={12} />
				Reset every setting
			</button>
			<p class="dg-help" style="margin-top: 0.4rem; text-align: center;">
				Clears theme, direction, palette overrides and layout tweaks.
			</p>
		</div>
	</aside>
{/if}

<ConfirmDialog
	bind:open={confirmResetOpen}
	title="Reset every setting?"
	message="Clears theme, direction and layout tweaks for this Dicegram. Node content is untouched."
	confirmLabel="Reset settings"
	tone="danger"
	onConfirm={applyResetDefaults}
/>

<style>
	.dg-settings {
		position: fixed;
		top: var(--header-h);
		right: 0;
		bottom: 0;
		z-index: 40;
		width: 340px;
		overflow-y: auto;
		background: var(--app-surface);
		border-left: 1px solid var(--app-border);
		font-size: 0.75rem;
		color: var(--app-text);
	}
	.dg-settings-head {
		position: sticky;
		top: 0;
		z-index: 10;
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.5rem 0.85rem;
		background: var(--app-surface);
		border-bottom: 1px solid var(--app-border);
	}
	.dg-settings-title {
		display: inline-flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.78rem;
		font-weight: 500;
		color: var(--app-text);
	}

	.dg-section {
		margin: 0.85rem 0 0.35rem;
		padding: 0 0.85rem;
		font-size: 0.62rem;
		font-weight: 600;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		color: var(--app-text-dim);
	}
	.dg-section-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}
	.dg-section-trigger {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		background: transparent;
		border: 0;
		padding: 0;
		font: inherit;
		color: inherit;
		text-transform: inherit;
		letter-spacing: inherit;
		cursor: pointer;
	}
	.dg-section-trigger:hover { color: var(--app-text); }

	.dg-pal-section {
		margin: 0.55rem 0 0.3rem;
		font-size: 0.6rem;
		font-weight: 600;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		color: var(--app-text-muted);
	}
	.dg-pal-label {
		flex-shrink: 0;
		width: 6rem;
		font-size: 0.7rem;
		color: var(--app-text-muted);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.dg-set-input {
		flex: 1;
		min-width: 0;
		height: 28px;
		padding: 0.15rem 0.5rem;
		font-size: 0.75rem;
		color: var(--app-text);
		background: var(--app-surface-2);
		border: 1px solid var(--app-border);
		border-radius: var(--app-radius-sm);
	}
	.dg-set-input:focus {
		outline: 2px solid var(--app-ring);
		outline-offset: 0;
		border-color: transparent;
	}
	.dg-set-input::placeholder { color: var(--app-text-dim); }
	.dg-set-input-mono {
		font-family: var(--app-mono-font);
		font-size: 0.7rem;
	}

	.dg-set-color {
		height: 28px;
		width: 32px;
		flex-shrink: 0;
		padding: 0;
		background: var(--app-surface-2);
		border: 1px solid var(--app-border);
		border-radius: var(--app-radius-sm);
		cursor: pointer;
	}

	.dg-set-mini {
		padding: 0.15rem 0.5rem;
		font-size: 0.65rem;
		font-weight: 500;
		text-transform: none;
		letter-spacing: 0;
		color: var(--app-text-muted);
		background: transparent;
		border: 1px solid var(--app-border);
		border-radius: var(--app-radius-sm);
		cursor: pointer;
		transition: color var(--app-dur-fast) var(--app-ease);
	}
	.dg-set-mini:hover { color: var(--app-text); }

	.dg-set-mini-x {
		padding: 0.15rem 0.3rem;
		color: var(--app-text-dim);
		background: transparent;
		border: 1px solid var(--app-border);
		border-radius: var(--app-radius-sm);
		cursor: pointer;
		transition: color var(--app-dur-fast) var(--app-ease);
	}
	.dg-set-mini-x:hover:not(:disabled) { color: var(--app-text); }
	.dg-set-mini-x:disabled { opacity: 0.3; cursor: not-allowed; }

	.dg-set-segment {
		display: flex;
		overflow: hidden;
		border: 1px solid var(--app-border);
		border-radius: var(--app-radius-sm);
	}
	.dg-set-seg-btn {
		flex: 1;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		height: 30px;
		color: var(--app-text-muted);
		background: transparent;
		border: 0;
		border-right: 1px solid var(--app-border);
		cursor: pointer;
		transition:
			background-color var(--app-dur-fast) var(--app-ease),
			color var(--app-dur-fast) var(--app-ease);
	}
	.dg-set-seg-btn:last-child { border-right: 0; }
	.dg-set-seg-btn:hover { background: var(--app-hover); color: var(--app-text); }
	.dg-set-seg-on { background: var(--app-accent-soft); color: var(--app-accent); }

	.dg-num-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.5rem;
	}
	.dg-num-label {
		font-size: 0.72rem;
		color: var(--app-text);
	}
	/* Number-with-px-suffix wrap: the suffix sits inside the bordered
	   input row so the user knows the unit (UAT bug #39 — previously the
	   number had no visible unit). */
	.dg-num-input-wrap {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		padding: 0 0.5rem 0 0;
		background: var(--app-surface-2);
		border: 1px solid var(--app-border);
		border-radius: var(--app-radius-sm);
	}
	.dg-num-input-wrap:focus-within {
		outline: 2px solid var(--app-ring);
		outline-offset: 0;
		border-color: transparent;
	}
	.dg-num-input {
		width: 4.5rem;
		height: 28px;
		padding: 0.15rem 0 0.15rem 0.55rem;
		background: transparent;
		color: var(--app-text);
		border: 0;
		font-size: 0.78rem;
		text-align: right;
	}
	.dg-num-input:focus { outline: none; }
	.dg-num-suffix {
		font-family: var(--app-mono-font);
		font-size: 0.65rem;
		color: var(--app-text-dim);
	}

	.dg-toggle-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.5rem;
		cursor: pointer;
	}
	.dg-checkbox {
		width: 14px;
		height: 14px;
		accent-color: var(--app-accent);
		background: var(--app-surface-2);
		border: 1px solid var(--app-border);
		border-radius: 3px;
	}

	.dg-help {
		margin: 0.4rem 0 0;
		font-size: 0.65rem;
		line-height: 1.4;
		color: var(--app-text-dim);
	}

	.dg-reset-btn {
		display: inline-flex;
		align-items: center;
		gap: 0.4rem;
		width: 100%;
		justify-content: center;
		font-size: 0.72rem;
	}
</style>
