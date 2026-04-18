<script lang="ts">
	import * as patch from '$lib/patch';
	import Icon from '$lib/Icon.svelte';
	import Dropdown from '$lib/Dropdown.svelte';
	import { THEMES, THEME_IDS, DEFAULT_THEME_ID } from '$lib/themes';
	import type { RenderResult } from '$lib/render';

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

	const ALL_SETTING_KEYS = [
		'color_scheme',
		...NUMBER_KEYS.map((n) => n.key),
		...TOGGLE_KEYS.map((t) => t.key)
	];

	const themeId = $derived(patch.getSetting(source, 'color_scheme') ?? DEFAULT_THEME_ID);
	const direction = $derived(patch.getDirection(source));
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

	function setDir(id: string) {
		source = patch.setDirection(source, id);
	}

	function setToggle(key: string, checked: boolean) {
		source = patch.setSetting(source, key, checked ? 1 : 0);
	}

	function resetDefaults() {
		if (!window.confirm('Reset every setting to defaults? This clears theme, direction and layout tweaks.')) return;
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
	<aside
		class="fixed top-[var(--header-h)] right-0 bottom-0 z-40 w-[340px] overflow-y-auto border-l border-neutral-800 bg-neutral-950 text-xs"
	>
		<div
			class="sticky top-0 z-10 flex items-center justify-between border-b border-neutral-800 bg-neutral-950 px-3 py-2"
		>
			<h2 class="flex items-center gap-1.5 text-xs font-medium text-neutral-100">
				<Icon name="settings" size={13} /> Settings
			</h2>
			<button
				type="button"
				class="rounded p-1 text-neutral-400 hover:bg-neutral-800 hover:text-neutral-100"
				aria-label="Close settings"
				onclick={handleClose}
			>
				<Icon name="x" size={14} />
			</button>
		</div>

		<div class="mt-3 mb-1 px-3 text-[10px] uppercase tracking-wide text-neutral-500">Theme</div>
		<div class="px-3">
			<Dropdown
				value={themeId}
				options={THEME_IDS.map((id) => ({ value: id, label: THEMES[id].label }))}
				onchange={setTheme}
			/>
		</div>

		<div class="mt-3 mb-1 px-3 text-[10px] uppercase tracking-wide text-neutral-500">Direction</div>
		<div class="px-3">
			<div class="flex overflow-hidden rounded border border-neutral-800">
				{#each DIRECTIONS as d (d.id)}
					<button
						type="button"
						title={d.label}
						class="flex h-7 flex-1 items-center justify-center border-r border-neutral-800 last:border-r-0 hover:bg-neutral-800 {direction === d.id ? 'bg-blue-700 text-white' : 'text-neutral-300'}"
						onclick={() => setDir(d.id)}
					>
						<Icon name={d.icon} size={13} />
					</button>
				{/each}
			</div>
		</div>

		<div class="mt-3 mb-1 px-3 text-[10px] uppercase tracking-wide text-neutral-500">Layout</div>
		<div class="space-y-1 px-3">
			{#each NUMBER_KEYS as n (n.key)}
				<label class="flex items-center justify-between gap-2">
					<span class="text-[11px] text-neutral-300">{n.label}</span>
					<input
						type="number"
						class="h-6 w-20 rounded border border-neutral-800 bg-neutral-900 px-1.5 text-xs text-neutral-100"
						value={numberValues[n.key]}
						oninput={(e) => {
							const v = Number((e.currentTarget as HTMLInputElement).value);
							if (Number.isFinite(v)) scheduleNumberWrite(n.key, v);
						}}
					/>
				</label>
			{/each}
		</div>

		<div class="mt-3 mb-1 px-3 text-[10px] uppercase tracking-wide text-neutral-500">Options</div>
		<div class="space-y-1 px-3">
			{#each TOGGLE_KEYS as t (t.key)}
				<label
					class="flex cursor-pointer items-center justify-between gap-2"
					title={t.hint}
				>
					<span class="text-[11px] text-neutral-300">{t.label}</span>
					<input
						type="checkbox"
						class="h-3.5 w-3.5 rounded border-neutral-800 bg-neutral-900 accent-blue-600"
						checked={toggleValues[t.key]}
						onchange={(e) => setToggle(t.key, (e.currentTarget as HTMLInputElement).checked)}
					/>
				</label>
				{#if t.hint}
					<p class="pl-0 text-[10px] leading-snug text-neutral-500">{t.hint}</p>
				{/if}
			{/each}
		</div>

		<div class="mt-4 px-3 pb-6">
			<button
				type="button"
				class="text-[11px] text-red-400 hover:text-red-300"
				onclick={resetDefaults}
			>
				Reset to defaults
			</button>
		</div>
	</aside>
{/if}
