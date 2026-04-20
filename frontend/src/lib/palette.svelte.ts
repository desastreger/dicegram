// Branding palette — user-tunable default colours. DSL-inline styles always
// win; the palette fills in defaults the DSL didn't specify. Backend is the
// source of truth (see backend/app/palette.py); this store mirrors it.

const DEFAULTS: Record<string, string> = {
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

function sanitize(raw: Record<string, unknown>): Record<string, string> {
	const out: Record<string, string> = { ...DEFAULTS };
	for (const [k, v] of Object.entries(raw)) {
		if (!(k in DEFAULTS)) continue;
		if (typeof v !== 'string') continue;
		const s = v.trim();
		if (s === '') continue;
		if (!/^(#|rgb|hsl)/.test(s)) continue;
		out[k] = s;
	}
	return out;
}

export type Preset = {
	name: string;
	overrides: Record<string, string>;
	active: boolean;
};

class PaletteStore {
	current: Record<string, string> = $state({ ...DEFAULTS });
	presets: Preset[] = $state([]);
	locked = $state(false);
	loaded = $state(false);
	saving = $state(false);

	async load(): Promise<void> {
		try {
			const res = await fetch('/api/auth/me/palette', { credentials: 'include' });
			if (res.ok) {
				const j = await res.json();
				this.current = sanitize(j.palette ?? {});
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
		// Strip values equal to the default; backend stores overrides only.
		const payload: Record<string, string> = {};
		for (const [k, v] of Object.entries(overrides)) {
			if (!(k in DEFAULTS)) continue;
			const s = (v ?? '').trim();
			if (s === '' || s === DEFAULTS[k]) continue;
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
				this.current = sanitize(j.palette ?? {});
				this.locked = Boolean(j.locked);
			}
		} finally {
			this.saving = false;
			// Recompute active preset after overrides changed.
			await this.loadPresets();
		}
	}

	async setLocked(locked: boolean): Promise<void> {
		// Keep current overrides; just flip the lock.
		const current: Record<string, string> = {};
		for (const [k, v] of Object.entries(this.current)) {
			if (v !== DEFAULTS[k]) current[k] = v;
		}
		await this.save(current, locked);
	}

	async reset(): Promise<void> {
		await this.save({});
	}

	async savePreset(name: string): Promise<void> {
		// Save the current active overrides under this name (backend will
		// read branding_palette when `overrides` is omitted).
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
			this.current = sanitize(j.palette ?? {});
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
		if (!type) return this.current.node_fill;
		const v = this.current[`type_${type}`];
		return v && v.length ? v : this.current.node_fill;
	}
}

export const palette = new PaletteStore();
export { DEFAULTS as PALETTE_DEFAULTS };
