// Theme — single source of truth for editor canvas + site chrome colours
// in a given visual mode. Every theme MUST define every token; missing
// tokens were the historical cause of "switch theme, app breaks" bugs.
//
// Token contract (consumers must use these — never hardcode):
//   mode             chrome flips to 'light' or 'dark' to match
//   bg / panel /     site + panel surfaces
//     panelMuted /
//     panelBorder
//   text / muted / accent      typography + accent colour
//   canvas / gridDot           editor canvas + dotted grid
//   nodeFill / nodeStroke /    default shape colours when no `type:` matches
//     nodeText
//   edge                       connector stroke
//   noteFill / noteBorder /    sticky-note rendering
//     noteText / noteLeader
//   tagAgent / tagHuman /      tagged-frame accent colours (one accent per
//     tagSystem / tagReview /  tag kind — bg/border/label derive from this
//     tagTodo                  via colour-mix or alpha)
//   groupBorder / groupLabel   group overlay + label
//   codeBg / codeText /        code editor surface
//     codeGutter / codeActiveLine
//   shadowSm / shadowMd        elevation (CSS box-shadow strings)
//   radiusSm / radiusMd /      corner radii (CSS length strings) — softer
//     radiusLg                 in light themes, tighter in dense dark ones
//   fontSans                   primary font-family stack

export type Theme = {
	id: string;
	label: string;
	mode: 'light' | 'dark';

	bg: string;
	panel: string;
	panelMuted: string;
	panelBorder: string;
	text: string;
	muted: string;
	accent: string;

	canvas: string;
	gridDot: string;

	nodeFill: string;
	nodeStroke: string;
	nodeText: string;
	edge: string;

	noteFill: string;
	noteBorder: string;
	noteText: string;
	noteLeader: string;

	tagAgent: string;
	tagHuman: string;
	tagSystem: string;
	tagReview: string;
	tagTodo: string;

	groupBorder: string;
	groupLabel: string;

	codeBg: string;
	codeText: string;
	codeGutter: string;
	codeActiveLine: string;

	shadowSm: string;
	shadowMd: string;

	radiusSm: string;
	radiusMd: string;
	radiusLg: string;

	fontSans: string;
};

// Soft sans stack — slightly rounded counters, gentle weights. Used by
// every light theme. Dark themes can opt into the same stack if they want
// the friendlier look.
const SOFT_SANS =
	'"Inter", "InterVariable", ui-sans-serif, -apple-system, BlinkMacSystemFont, ' +
	'"Segoe UI", Roboto, "Helvetica Neue", sans-serif';
const SYSTEM_SANS =
	'ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, ' +
	'"Helvetica Neue", sans-serif';

// Light/dark counterpart map. The chrome's sun/moon toggle uses this to
// flip a canvas between modes without losing the user's flavour
// (warm ↔ warm-dark, dracula ↔ solarized-light, etc.). Themes without an
// obvious counterpart fall back to the flagship pair (`warm` / `warm-dark`).
// `auto` is its own counterpart — it tracks chrome via `--app-*` so the
// chrome toggle already flips it; nothing to swap.
const COUNTERPARTS: Record<string, string> = {
	auto: 'auto',
	warm: 'warm-dark',
	'warm-dark': 'warm',
	'default-dark': 'light',
	light: 'default-dark',
	'solarized-dark': 'solarized-light',
	'solarized-light': 'solarized-dark',
	dracula: 'solarized-light',
	gruvbox: 'solarized-light',
	'high-contrast': 'light'
};

export function counterpartThemeId(id: string | null | undefined): string {
	const key = (id ?? '').trim().toLowerCase();
	return COUNTERPARTS[key] ?? (key && THEMES[key]?.mode === 'light' ? 'warm-dark' : 'warm');
}

export const THEMES: Record<string, Theme> = {
	// `auto` — the unified theme. Every token is a `var(--app-*)` reference
	// (or a color-mix derived from one), so the canvas, code editor,
	// inspector, tree, dropdowns — every editor surface — automatically
	// re-renders when the chrome's sun/moon toggle flips
	// `:root[data-theme]`. This is the default for new dicegrams. Users
	// who want a fixed canvas style (warm, dracula, solarized, …) opt in
	// via `setting color_scheme`; their pick wins for that dicegram.
	auto: {
		id: 'auto',
		label: 'Auto (follows chrome)',
		// `mode` is a hint used by `counterpartThemeId`; auto is its own
		// counterpart so the value here doesn't actually matter.
		mode: 'dark',
		bg: 'var(--app-bg)',
		panel: 'var(--app-surface)',
		panelMuted: 'var(--app-surface-2)',
		panelBorder: 'var(--app-border)',
		text: 'var(--app-text)',
		muted: 'var(--app-text-muted)',
		accent: 'var(--app-accent)',
		canvas: 'var(--app-bg)',
		// Grid dots — slightly stronger than 14% so they read on light
		// cream without feeling like a print-misregistration on dark.
		gridDot: 'color-mix(in srgb, var(--app-text) 22%, transparent)',
		// Node defaults: lift the fill OFF the canvas with a deeper mix so
		// boxes visibly separate in light mode. `--app-surface-2` is only
		// 6 brightness points darker than the bg in the warm cream chrome,
		// which is too tight for a canvas. Mixing 80% surface-2 with 20%
		// border-strong gives a clear ~10-point step in light, and reads
		// as elevated panel in dark.
		nodeFill:
			'color-mix(in srgb, var(--app-surface-2) 80%, var(--app-border-strong) 20%)',
		nodeStroke: 'var(--app-border-strong)',
		nodeText: 'var(--app-text)',
		// Edges: text-muted is gentle; on light cream that reads as fog.
		// Pull halfway toward border-strong so connectors trace clearly.
		edge: 'color-mix(in srgb, var(--app-text-muted) 60%, var(--app-border-strong) 40%)',
		// Notes — paper-yellow that's strong enough to register as a
		// sticky note on either chrome. 38% warn over bg gives a yellow
		// wash that's clearly not the canvas.
		noteFill: 'color-mix(in oklab, var(--app-warn) 38%, var(--app-bg))',
		noteBorder: 'var(--app-warn)',
		noteText: 'var(--app-text)',
		noteLeader: 'var(--app-warn)',
		tagAgent: 'var(--app-accent)',
		tagHuman: 'color-mix(in oklab, var(--app-danger) 80%, var(--app-text-muted))',
		tagSystem: 'color-mix(in oklab, var(--app-accent) 70%, var(--app-text))',
		tagReview: 'var(--app-warn)',
		tagTodo: 'var(--app-ok)',
		groupBorder: 'var(--app-warn)',
		groupLabel: 'var(--app-warn)',
		codeBg: 'var(--app-bg)',
		codeText: 'var(--app-text)',
		codeGutter: 'var(--app-text-dim)',
		codeActiveLine: 'var(--app-surface)',
		shadowSm: 'var(--app-shadow-sm)',
		shadowMd: 'var(--app-shadow-md)',
		radiusSm: 'var(--app-radius-sm)',
		radiusMd: 'var(--app-radius)',
		radiusLg: 'var(--app-radius-lg)',
		fontSans: SOFT_SANS
	},
	warm: {
		id: 'warm',
		label: 'Warm',
		mode: 'light',
		bg: '#fbf7f2',
		panel: '#f7f1e9',
		panelMuted: '#f1ebe1',
		panelBorder: '#e3d9cf',
		text: '#3d3530',
		// muted lifted from #8a7a6a (3.5:1 — sub-AA) to #6d5e50 (5.4:1) so
		// secondary text is legible on the warm cream bg.
		muted: '#6d5e50',
		accent: '#d97757',
		canvas: '#fbf7f2',
		gridDot: '#e3d9cf',
		nodeFill: '#dceadb',
		nodeStroke: '#a8c2a3',
		nodeText: '#3d5c3a',
		edge: '#8a8a82',
		noteFill: '#fef3c7',
		noteBorder: '#d4863b',
		noteText: '#5a3d0a',
		noteLeader: '#d4863b',
		tagAgent: '#d97757',
		tagHuman: '#c87a8a',
		tagSystem: '#7a8fc8',
		tagReview: '#b48ec8',
		tagTodo: '#9aa97a',
		groupBorder: '#b8a48f',
		// groupLabel was sharing the previous low-contrast muted; lifted in
		// step with `muted` above.
		groupLabel: '#6d5e50',
		codeBg: '#fbf7f2',
		codeText: '#3d3530',
		// codeGutter lifted from #a8a39a (2.4:1 — illegible) to #7a7368
		// (4.7:1) so line numbers are readable.
		codeGutter: '#7a7368',
		codeActiveLine: '#f1ece4',
		shadowSm: '0 1px 0 rgba(60, 50, 40, 0.04), 0 2px 6px -2px rgba(60, 50, 40, 0.08)',
		shadowMd: '0 1px 0 rgba(60, 50, 40, 0.05), 0 8px 24px -12px rgba(60, 50, 40, 0.10)',
		radiusSm: '6px',
		radiusMd: '10px',
		radiusLg: '14px',
		fontSans: SOFT_SANS
	},
	'warm-dark': {
		id: 'warm-dark',
		label: 'Warm Dark',
		mode: 'dark',
		bg: '#1a1614',
		panel: '#211c19',
		panelMuted: '#27211d',
		panelBorder: '#3a322c',
		text: '#ede4d8',
		muted: '#a89684',
		accent: '#e09376',
		canvas: '#1a1614',
		gridDot: '#3a322c',
		nodeFill: '#2c4234',
		nodeStroke: '#5b8060',
		nodeText: '#cce0c9',
		edge: '#8a8175',
		noteFill: '#3a2f1a',
		noteBorder: '#a87a3a',
		noteText: '#f0d99a',
		noteLeader: '#a87a3a',
		tagAgent: '#e09376',
		tagHuman: '#d49aa6',
		tagSystem: '#9aabd4',
		tagReview: '#c4a8d4',
		tagTodo: '#aebd92',
		groupBorder: '#7a6a58',
		groupLabel: '#a89684',
		codeBg: '#1a1614',
		codeText: '#ede4d8',
		// codeGutter lifted from #6b6259 (2.6:1 — illegible) to #8d8278 (4.6:1).
		codeGutter: '#8d8278',
		codeActiveLine: '#27211d',
		shadowSm: '0 1px 0 rgba(0, 0, 0, 0.20), 0 2px 6px -2px rgba(0, 0, 0, 0.30)',
		shadowMd: '0 1px 0 rgba(0, 0, 0, 0.25), 0 8px 24px -12px rgba(0, 0, 0, 0.40)',
		radiusSm: '6px',
		radiusMd: '10px',
		radiusLg: '14px',
		fontSans: SOFT_SANS
	},
	'default-dark': {
		id: 'default-dark',
		label: 'Default Dark',
		mode: 'dark',
		bg: '#0a0a0a',
		panel: '#141414',
		panelMuted: '#1a1a1a',
		panelBorder: '#262626',
		text: '#e5e7eb',
		muted: '#9ca3af',
		accent: '#3b82f6',
		canvas: '#0a0a0a',
		gridDot: '#1f2937',
		nodeFill: '#1f2937',
		nodeStroke: '#64748b',
		nodeText: '#e5e7eb',
		edge: '#94a3b8',
		noteFill: '#1f2937',
		noteBorder: '#475569',
		noteText: '#e5e7eb',
		noteLeader: '#64748b',
		tagAgent: '#60a5fa',
		tagHuman: '#f472b6',
		tagSystem: '#a78bfa',
		tagReview: '#facc15',
		tagTodo: '#34d399',
		groupBorder: '#f59e0b',
		groupLabel: '#f59e0b',
		codeBg: '#0a0a0a',
		codeText: '#e5e7eb',
		// codeGutter lifted from #52525b (2.6:1) to #6f6f78 (4.5:1).
		codeGutter: '#6f6f78',
		codeActiveLine: '#18181b',
		shadowSm: '0 1px 0 rgba(0, 0, 0, 0.30), 0 2px 6px -2px rgba(0, 0, 0, 0.45)',
		shadowMd: '0 1px 0 rgba(0, 0, 0, 0.35), 0 8px 24px -12px rgba(0, 0, 0, 0.55)',
		radiusSm: '4px',
		radiusMd: '6px',
		radiusLg: '10px',
		fontSans: SYSTEM_SANS
	},
	light: {
		id: 'light',
		label: 'Light',
		mode: 'light',
		bg: '#ffffff',
		panel: '#f8fafc',
		panelMuted: '#f1f5f9',
		panelBorder: '#e2e8f0',
		text: '#0f172a',
		muted: '#64748b',
		accent: '#2563eb',
		canvas: '#ffffff',
		gridDot: '#e2e8f0',
		nodeFill: '#f8fafc',
		nodeStroke: '#475569',
		nodeText: '#0f172a',
		edge: '#475569',
		noteFill: '#fef3c7',
		noteBorder: '#d97706',
		noteText: '#422006',
		noteLeader: '#d97706',
		tagAgent: '#2563eb',
		tagHuman: '#db2777',
		tagSystem: '#7c3aed',
		tagReview: '#ca8a04',
		tagTodo: '#16a34a',
		groupBorder: '#d97706',
		groupLabel: '#d97706',
		codeBg: '#ffffff',
		codeText: '#0f172a',
		// codeGutter lifted from #94a3b8 (2.8:1) to #64748b (4.6:1, reuses
		// the muted token's slate hue).
		codeGutter: '#64748b',
		codeActiveLine: '#f1f5f9',
		shadowSm: '0 1px 0 rgba(15, 23, 42, 0.04), 0 2px 6px -2px rgba(15, 23, 42, 0.08)',
		shadowMd: '0 1px 0 rgba(15, 23, 42, 0.05), 0 8px 24px -12px rgba(15, 23, 42, 0.10)',
		radiusSm: '6px',
		radiusMd: '10px',
		radiusLg: '14px',
		fontSans: SOFT_SANS
	},
	'solarized-dark': {
		id: 'solarized-dark',
		label: 'Solarized Dark',
		mode: 'dark',
		bg: '#002b36',
		panel: '#073642',
		panelMuted: '#0a3f4d',
		panelBorder: '#0e4651',
		text: '#eee8d5',
		muted: '#839496',
		accent: '#268bd2',
		canvas: '#002b36',
		gridDot: '#0e4651',
		nodeFill: '#073642',
		nodeStroke: '#586e75',
		nodeText: '#eee8d5',
		edge: '#93a1a1',
		noteFill: '#073642',
		noteBorder: '#b58900',
		noteText: '#eee8d5',
		noteLeader: '#b58900',
		tagAgent: '#268bd2',
		tagHuman: '#d33682',
		tagSystem: '#6c71c4',
		tagReview: '#b58900',
		tagTodo: '#859900',
		groupBorder: '#b58900',
		groupLabel: '#b58900',
		codeBg: '#002b36',
		codeText: '#eee8d5',
		// codeGutter lifted from canonical Solarized base01 #586e75 (3.1:1)
		// to #7a8f96 (4.7:1) — accessibility wins over palette purity.
		codeGutter: '#7a8f96',
		codeActiveLine: '#073642',
		shadowSm: '0 1px 0 rgba(0, 20, 28, 0.35), 0 2px 6px -2px rgba(0, 20, 28, 0.50)',
		shadowMd: '0 1px 0 rgba(0, 20, 28, 0.40), 0 8px 24px -12px rgba(0, 20, 28, 0.60)',
		radiusSm: '4px',
		radiusMd: '6px',
		radiusLg: '10px',
		fontSans: SYSTEM_SANS
	},
	'solarized-light': {
		id: 'solarized-light',
		label: 'Solarized Light',
		mode: 'light',
		bg: '#fdf6e3',
		panel: '#eee8d5',
		panelMuted: '#e6dfc6',
		panelBorder: '#d8d2bf',
		text: '#073642',
		muted: '#586e75',
		accent: '#268bd2',
		canvas: '#fdf6e3',
		gridDot: '#d8d2bf',
		nodeFill: '#eee8d5',
		nodeStroke: '#93a1a1',
		nodeText: '#073642',
		edge: '#586e75',
		noteFill: '#eee8d5',
		noteBorder: '#b58900',
		noteText: '#073642',
		noteLeader: '#b58900',
		tagAgent: '#268bd2',
		tagHuman: '#d33682',
		tagSystem: '#6c71c4',
		tagReview: '#b58900',
		tagTodo: '#859900',
		groupBorder: '#b58900',
		groupLabel: '#b58900',
		codeBg: '#fdf6e3',
		codeText: '#073642',
		// codeGutter lifted from #93a1a1 (2.3:1 — illegible) to #586e75
		// (6.4:1, reuses Solarized base01 / muted hue).
		codeGutter: '#586e75',
		codeActiveLine: '#eee8d5',
		shadowSm: '0 1px 0 rgba(7, 54, 66, 0.05), 0 2px 6px -2px rgba(7, 54, 66, 0.10)',
		shadowMd: '0 1px 0 rgba(7, 54, 66, 0.06), 0 8px 24px -12px rgba(7, 54, 66, 0.12)',
		radiusSm: '6px',
		radiusMd: '10px',
		radiusLg: '14px',
		fontSans: SOFT_SANS
	},
	dracula: {
		id: 'dracula',
		label: 'Dracula',
		mode: 'dark',
		bg: '#282a36',
		panel: '#21222c',
		panelMuted: '#2b2d3a',
		panelBorder: '#44475a',
		text: '#f8f8f2',
		// muted lifted from canonical Dracula `comment` #6272a4 (3.3:1)
		// to #8a98c8 (4.9:1) — keeps the Dracula hue, accessibility-safe.
		muted: '#8a98c8',
		accent: '#bd93f9',
		canvas: '#282a36',
		gridDot: '#44475a',
		nodeFill: '#44475a',
		nodeStroke: '#6272a4',
		nodeText: '#f8f8f2',
		edge: '#bd93f9',
		noteFill: '#44475a',
		noteBorder: '#ffb86c',
		noteText: '#f8f8f2',
		noteLeader: '#ffb86c',
		tagAgent: '#8be9fd',
		tagHuman: '#ff79c6',
		tagSystem: '#bd93f9',
		tagReview: '#f1fa8c',
		tagTodo: '#50fa7b',
		groupBorder: '#ffb86c',
		groupLabel: '#ffb86c',
		codeBg: '#282a36',
		codeText: '#f8f8f2',
		// codeGutter lifted in step with muted so line numbers stay legible.
		codeGutter: '#8a98c8',
		codeActiveLine: '#44475a',
		shadowSm: '0 1px 0 rgba(0, 0, 0, 0.30), 0 2px 6px -2px rgba(0, 0, 0, 0.45)',
		shadowMd: '0 1px 0 rgba(0, 0, 0, 0.35), 0 8px 24px -12px rgba(0, 0, 0, 0.55)',
		radiusSm: '4px',
		radiusMd: '6px',
		radiusLg: '10px',
		fontSans: SYSTEM_SANS
	},
	gruvbox: {
		id: 'gruvbox',
		label: 'Gruvbox Dark',
		mode: 'dark',
		bg: '#282828',
		panel: '#1d2021',
		panelMuted: '#262727',
		panelBorder: '#3c3836',
		text: '#ebdbb2',
		muted: '#928374',
		accent: '#fabd2f',
		canvas: '#282828',
		gridDot: '#3c3836',
		nodeFill: '#3c3836',
		nodeStroke: '#928374',
		nodeText: '#ebdbb2',
		edge: '#d5c4a1',
		noteFill: '#3c3836',
		noteBorder: '#fabd2f',
		noteText: '#ebdbb2',
		noteLeader: '#fabd2f',
		tagAgent: '#83a598',
		tagHuman: '#d3869b',
		tagSystem: '#b16286',
		tagReview: '#fabd2f',
		tagTodo: '#b8bb26',
		groupBorder: '#fabd2f',
		groupLabel: '#fabd2f',
		codeBg: '#282828',
		codeText: '#ebdbb2',
		codeGutter: '#928374',
		codeActiveLine: '#3c3836',
		shadowSm: '0 1px 0 rgba(0, 0, 0, 0.30), 0 2px 6px -2px rgba(0, 0, 0, 0.45)',
		shadowMd: '0 1px 0 rgba(0, 0, 0, 0.35), 0 8px 24px -12px rgba(0, 0, 0, 0.55)',
		radiusSm: '4px',
		radiusMd: '6px',
		radiusLg: '10px',
		fontSans: SYSTEM_SANS
	},
	'high-contrast': {
		id: 'high-contrast',
		label: 'High Contrast',
		mode: 'dark',
		bg: '#000000',
		panel: '#000000',
		panelMuted: '#0a0a0a',
		panelBorder: '#ffffff',
		text: '#ffffff',
		muted: '#cccccc',
		accent: '#ffff00',
		canvas: '#000000',
		gridDot: '#444444',
		nodeFill: '#000000',
		nodeStroke: '#ffffff',
		nodeText: '#ffffff',
		edge: '#ffffff',
		noteFill: '#000000',
		noteBorder: '#ffff00',
		noteText: '#ffffff',
		noteLeader: '#ffff00',
		tagAgent: '#00ffff',
		tagHuman: '#ff00ff',
		tagSystem: '#ffff00',
		tagReview: '#ffaa00',
		tagTodo: '#00ff00',
		groupBorder: '#ffff00',
		groupLabel: '#ffff00',
		codeBg: '#000000',
		codeText: '#ffffff',
		codeGutter: '#888888',
		codeActiveLine: '#222222',
		shadowSm: 'none',
		shadowMd: 'none',
		radiusSm: '0px',
		radiusMd: '2px',
		radiusLg: '4px',
		fontSans: SYSTEM_SANS
	}
};

export const THEME_IDS = Object.keys(THEMES);
// Default for new dicegrams: `auto`, which tracks chrome via `--app-*`.
// Users can opt into a fixed canvas style with `setting color_scheme`.
export const DEFAULT_THEME_ID = 'auto';

export function getTheme(id: string | null | undefined): Theme {
	if (!id) return THEMES[DEFAULT_THEME_ID];
	// Accept both hyphen and underscore forms (`solarized-light` and
	// `solarized_light`). The registry keys are hyphenated, but users (and
	// the LLM prompt) often write underscore-separated identifiers — both
	// should resolve to the same canvas theme.
	const direct = THEMES[id];
	if (direct) return direct;
	const normalised = id.replace(/_/g, '-');
	if (THEMES[normalised]) return THEMES[normalised];
	const underscored = id.replace(/-/g, '_');
	if (THEMES[underscored]) return THEMES[underscored];
	return THEMES[DEFAULT_THEME_ID];
}

// Build the CSS variable string a consumer can drop on a wrapper element so
// every descendant resolves theme tokens via `var(--th-*)`. The same name
// shape is used by the editor wrapper and any other surface that wants
// theme-token consistency. Keep keys in sync with `Theme` above.
export function themeCssVars(t: Theme): string {
	return [
		`--th-bg:${t.bg}`,
		`--th-panel:${t.panel}`,
		`--th-panel-muted:${t.panelMuted}`,
		`--th-panel-border:${t.panelBorder}`,
		`--th-text:${t.text}`,
		`--th-muted:${t.muted}`,
		`--th-accent:${t.accent}`,
		`--th-canvas:${t.canvas}`,
		`--th-grid-dot:${t.gridDot}`,
		`--th-node-fill:${t.nodeFill}`,
		`--th-node-stroke:${t.nodeStroke}`,
		`--th-node-text:${t.nodeText}`,
		`--th-edge:${t.edge}`,
		`--th-note-fill:${t.noteFill}`,
		`--th-note-border:${t.noteBorder}`,
		`--th-note-text:${t.noteText}`,
		`--th-note-leader:${t.noteLeader}`,
		`--th-tag-agent:${t.tagAgent}`,
		`--th-tag-human:${t.tagHuman}`,
		`--th-tag-system:${t.tagSystem}`,
		`--th-tag-review:${t.tagReview}`,
		`--th-tag-todo:${t.tagTodo}`,
		`--th-group-border:${t.groupBorder}`,
		`--th-group-label:${t.groupLabel}`,
		`--th-code-bg:${t.codeBg}`,
		`--th-code-text:${t.codeText}`,
		`--th-code-gutter:${t.codeGutter}`,
		`--th-code-active:${t.codeActiveLine}`,
		`--th-shadow-sm:${t.shadowSm}`,
		`--th-shadow-md:${t.shadowMd}`,
		`--th-radius-sm:${t.radiusSm}`,
		`--th-radius-md:${t.radiusMd}`,
		`--th-radius-lg:${t.radiusLg}`,
		`--th-font-sans:${t.fontSans}`
	].join(';');
}
