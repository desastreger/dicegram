// Branding palette — Dicegram-tunable default colours. Layer order from
// lowest precedence to highest: theme baseline → user brand overrides
// (stored on the user row) → per-Dicegram overrides (in the DSL header) →
// inline DSL `style:` keys on a single node. Inline styles always win;
// the palette fills in the rest. Backend is the source of truth — see
// backend/app/palette.py.

const DEFAULT_DARK_PALETTE: Record<string, string> = {
	type_start: '#064e3b',
	type_end: '#3f1d1d',
	type_decision: '#3a2f0b',
	type_datastore: '#0c3a5c',
	type_process: '',
	type_input: '',
	type_output: '',
	type_manual: '',
	type_automated: '',
	type_approval: '',
	type_external: '',
	node_fill: '#1f2937',
	node_stroke: '#64748b',
	node_text: '#e5e7eb',
	priority_critical: '#ef4444',
	priority_high: '#f59e0b',
	status_blocked: '#ef4444',
	status_complete: '#10b981',
	status_deprecated_text: '#71717a',
	edge: '#94a3b8',
	edge_label: '#e5e7eb'
};

const ANTHROPIC_PALETTE: Record<string, string> = {
	type_start: '#fce4d6',
	type_end: '#fce4d6',
	type_decision: '#e6e3f7',
	type_datastore: '#dde6f0',
	type_process: '#dceadb',
	type_input: '#fce4d6',
	type_output: '#fce4d6',
	type_manual: '#dceadb',
	type_automated: '#dceadb',
	type_approval: '#e6e3f7',
	type_external: '#fce4d6',
	node_fill: '#dceadb',
	node_stroke: '#a8c2a3',
	node_text: '#3d5c3a',
	priority_critical: '#c44536',
	priority_high: '#d4863b',
	status_blocked: '#c44536',
	status_complete: '#5b8060',
	status_deprecated_text: '#8a8780',
	edge: '#8a8a82',
	edge_label: '#3d3d35'
};

const LIGHT_PALETTE: Record<string, string> = {
	type_start: '#bbf7d0',
	type_end: '#fecaca',
	type_decision: '#fde68a',
	type_datastore: '#bfdbfe',
	type_process: '',
	type_input: '',
	type_output: '',
	type_manual: '',
	type_automated: '',
	type_approval: '',
	type_external: '',
	node_fill: '#f8fafc',
	node_stroke: '#475569',
	node_text: '#0f172a',
	priority_critical: '#dc2626',
	priority_high: '#d97706',
	status_blocked: '#dc2626',
	status_complete: '#059669',
	status_deprecated_text: '#9ca3af',
	edge: '#475569',
	edge_label: '#0f172a'
};

const THEME_PRESETS: Record<string, Record<string, string>> = {
	anthropic: ANTHROPIC_PALETTE,
	'default-dark': DEFAULT_DARK_PALETTE,
	light: LIGHT_PALETTE
};

const DEFAULT_THEME_ID = 'default-dark';

// Back-compat: callers that referenced PALETTE_DEFAULTS directly get the
// historical default-dark palette so behaviour matches the pre-theme code.
export const PALETTE_DEFAULTS = DEFAULT_DARK_PALETTE;
export const PALETTE_THEME_IDS = Object.keys(THEME_PRESETS);

export function themePalette(themeId: string | null | undefined): Record<string, string> {
	const id = (themeId ?? '').trim().toLowerCase();
	return { ...(THEME_PRESETS[id] ?? DEFAULT_DARK_PALETTE) };
}

// Human-readable order and grouping for the settings UI.
export const PALETTE_SECTIONS: {
	title: string;
	keys: { key: string; label: string; hint?: string }[];
}[] = [
	{
		title: 'Element types',
		keys: [
			{ key: 'type_start', label: 'Start', hint: 'type:start' },
			{ key: 'type_end', label: 'End', hint: 'type:end' },
			{ key: 'type_decision', label: 'Decision', hint: 'type:decision' },
			{ key: 'type_datastore', label: 'Datastore', hint: 'type:datastore' },
			{ key: 'type_process', label: 'Process', hint: 'type:process' },
			{ key: 'type_input', label: 'Input', hint: 'type:input' },
			{ key: 'type_output', label: 'Output', hint: 'type:output' },
			{ key: 'type_manual', label: 'Manual', hint: 'type:manual' },
			{ key: 'type_automated', label: 'Automated', hint: 'type:automated' },
			{ key: 'type_approval', label: 'Approval', hint: 'type:approval' },
			{ key: 'type_external', label: 'External', hint: 'type:external' }
		]
	},
	{
		title: 'Node defaults',
		keys: [
			{ key: 'node_fill', label: 'Default fill' },
			{ key: 'node_stroke', label: 'Default stroke' },
			{ key: 'node_text', label: 'Default text' }
		]
	},
	{
		title: 'Priority accents',
		keys: [
			{ key: 'priority_critical', label: 'Critical stroke' },
			{ key: 'priority_high', label: 'High stroke' }
		]
	},
	{
		title: 'Status accents',
		keys: [
			{ key: 'status_blocked', label: 'Blocked stroke' },
			{ key: 'status_complete', label: 'Complete stroke' },
			{ key: 'status_deprecated_text', label: 'Deprecated text' }
		]
	},
	{
		title: 'Edges',
		keys: [
			{ key: 'edge', label: 'Edge colour' },
			{ key: 'edge_label', label: 'Edge label colour' }
		]
	}
];

const ALLOWED_KEYS = new Set(Object.keys(DEFAULT_DARK_PALETTE));

function sanitize(raw: Record<string, unknown>): Record<string, string> {
	const out: Record<string, string> = {};
	for (const [k, v] of Object.entries(raw)) {
		if (!ALLOWED_KEYS.has(k)) continue;
		if (typeof v !== 'string') continue;
		const s = v.trim();
		if (s === '') continue;
		if (!/^(#|rgb|hsl)/.test(s)) continue;
		out[k] = s;
	}
	return out;
}

function applyOverrides(
	base: Record<string, string>,
	overrides: Record<string, string>
): Record<string, string> {
	const out = { ...base };
	for (const [k, v] of Object.entries(overrides)) {
		if (!ALLOWED_KEYS.has(k)) continue;
		if (typeof v !== 'string' || v === '') continue;
		out[k] = v;
	}
	return out;
}

export type Preset = {
	name: string;
	overrides: Record<string, string>;
	active: boolean;
};

class PaletteStore {
	// What the API gave us — the user's saved brand palette overrides
	// (sanitized, sparse map: only keys the user actually overrode).
	userOverrides: Record<string, string> = $state({});
	// Per-Dicegram overrides scraped from `setting palette_<key> <color>`
	// in the DSL. Cleared when the user opens a different Dicegram.
	dicegramOverrides: Record<string, string> = $state({});
	// Active theme id, picked by the Dicegram via `setting color_scheme`.
	activeThemeId: string = $state(DEFAULT_THEME_ID);
	presets: Preset[] = $state([]);
	locked = $state(false);
	loaded = $state(false);
	saving = $state(false);

	// `current` is the resolved palette every consumer reads. Layered:
	// theme baseline → user brand overrides → per-Dicegram overrides.
	get current(): Record<string, string> {
		return applyOverrides(
			applyOverrides(themePalette(this.activeThemeId), this.userOverrides),
			this.dicegramOverrides
		);
	}

	setActiveTheme(themeId: string | null | undefined) {
		const id = (themeId ?? '').trim().toLowerCase() || DEFAULT_THEME_ID;
		if (id !== this.activeThemeId) this.activeThemeId = id;
	}

	setDicegramOverrides(overrides: Record<string, string>) {
		this.dicegramOverrides = sanitize(overrides as Record<string, unknown>);
	}

	async load(): Promise<void> {
		try {
			const res = await fetch('/api/auth/me/palette', { credentials: 'include' });
			if (res.ok) {
				const j = await res.json();
				// The API returns the merged palette — convert it back into a
				// sparse user-overrides map by diffing against the dark default.
				const merged = sanitize(j.palette ?? {});
				const sparse: Record<string, string> = {};
				for (const [k, v] of Object.entries(merged)) {
					if (DEFAULT_DARK_PALETTE[k] !== v) sparse[k] = v;
				}
				this.userOverrides = sparse;
				this.locked = Boolean(j.locked);
			}
			await this.loadPresets();
		} catch {
			// Offline or anon — keep defaults.
		} finally {
			this.loaded = true;
		}
	}

	async loadPresets(): Promise<void> {
		try {
			const res = await fetch('/api/auth/me/palettes', { credentials: 'include' });
			if (res.ok) {
				const j = await res.json();
				this.presets = Array.isArray(j.presets) ? j.presets : [];
			}
		} catch {
			this.presets = [];
		}
	}

	async save(overrides: Record<string, string>, locked?: boolean): Promise<void> {
		// Strip values equal to the dark default; backend stores overrides only.
		const payload: Record<string, string> = {};
		for (const [k, v] of Object.entries(overrides)) {
			if (!ALLOWED_KEYS.has(k)) continue;
			const s = (v ?? '').trim();
			if (s === '' || s === DEFAULT_DARK_PALETTE[k]) continue;
			payload[k] = s;
		}
		this.saving = true;
		try {
			const body: Record<string, unknown> = { palette: payload };
			if (typeof locked === 'boolean') body.locked = locked;
			const res = await fetch('/api/auth/me/palette', {
				method: 'PUT',
				credentials: 'include',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(body)
			});
			if (res.ok) {
				const j = await res.json();
				const merged = sanitize(j.palette ?? {});
				const sparse: Record<string, string> = {};
				for (const [k, v] of Object.entries(merged)) {
					if (DEFAULT_DARK_PALETTE[k] !== v) sparse[k] = v;
				}
				this.userOverrides = sparse;
				this.locked = Boolean(j.locked);
			}
		} finally {
			this.saving = false;
			await this.loadPresets();
		}
	}

	async setLocked(locked: boolean): Promise<void> {
		await this.save(this.userOverrides, locked);
	}

	async reset(): Promise<void> {
		await this.save({});
	}

	async savePreset(name: string): Promise<void> {
		const res = await fetch('/api/auth/me/palettes', {
			method: 'POST',
			credentials: 'include',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ name })
		});
		if (res.ok) {
			const j = await res.json();
			this.presets = Array.isArray(j.presets) ? j.presets : [];
		}
	}

	async activatePreset(name: string): Promise<void> {
		const res = await fetch(
			`/api/auth/me/palettes/${encodeURIComponent(name)}/activate`,
			{ method: 'PATCH', credentials: 'include' }
		);
		if (res.ok) {
			const j = await res.json();
			const merged = sanitize(j.palette ?? {});
			const sparse: Record<string, string> = {};
			for (const [k, v] of Object.entries(merged)) {
				if (DEFAULT_DARK_PALETTE[k] !== v) sparse[k] = v;
			}
			this.userOverrides = sparse;
			await this.loadPresets();
		}
	}

	async deletePreset(name: string): Promise<void> {
		const res = await fetch(
			`/api/auth/me/palettes/${encodeURIComponent(name)}`,
			{ method: 'DELETE', credentials: 'include' }
		);
		if (res.ok || res.status === 204) {
			this.presets = this.presets.filter((p) => p.name !== name);
			await this.loadPresets();
		}
	}

	typeFill(type: string | undefined): string {
		const cur = this.current;
		if (!type) return cur.node_fill;
		const v = cur[`type_${type}`];
		return v && v.length ? v : cur.node_fill;
	}
}

export const palette = new PaletteStore();
