// ─── The single theme store ───────────────────────────────────────────────
// THE CONTRACT — read this before adding any UI script:
//
// Every script (Svelte component, .ts module, build step) that needs to
// know which mode the chrome is in MUST read from this store and only
// this store. NEVER read `document.documentElement.dataset.theme` or
// `localStorage` directly — those are implementation details that may
// not reflect the truth during SSR, hydration, or override flows.
//
// Reads:
//   theme.current       'light' | 'dark' (reactive)
//   theme.isLight       boolean         (reactive)
//   theme.isDark        boolean         (reactive)
//
// Writes (only one place should write — the nav toggle):
//   theme.set('light')
//   theme.toggle()      honours the optional `override` hook
//
// CSS-only consumers should reach for `--app-*` tokens (the chrome's
// canonical surface palette) or one of the standard utility classes in
// layout.css. JS-only consumers — like the CodeMirror syntax palette
// in CodeEditor.svelte — read theme.isLight to pick a high-contrast
// token set at runtime.
//
// The Svelte 5 `$state` rune makes every property reactive; downstream
// `$derived` and `$effect` re-run automatically when chrome flips.

export type Theme = 'light' | 'dark';

const KEY = 'dicegram:theme';

function readCurrent(): Theme {
	if (typeof document === 'undefined') return 'dark';
	const attr = document.documentElement.getAttribute('data-theme');
	return attr === 'light' ? 'light' : 'dark';
}

class ThemeStore {
	current: Theme = $state(readCurrent());

	// Reactive booleans — components prefer these over `current === '…'`
	// comparisons because the intent reads more clearly.
	get isLight() {
		return this.current === 'light';
	}
	get isDark() {
		return this.current === 'dark';
	}

	// Resolved snapshot of the active --app-* tokens, read straight from
	// computed style. Use this when JS needs an actual colour string
	// (canvas-render-to-PNG, exported PDFs, CodeMirror palette, etc.).
	// Components that just need to *flip behaviour* on mode should read
	// `isLight` / `isDark` instead — those are reactive, this isn't.
	tokens(): Record<string, string> {
		if (typeof document === 'undefined') return {};
		const cs = getComputedStyle(document.documentElement);
		const keys = [
			'app-bg',
			'app-surface',
			'app-surface-2',
			'app-border',
			'app-border-strong',
			'app-text',
			'app-text-muted',
			'app-text-dim',
			'app-accent',
			'app-accent-2',
			'app-accent-text',
			'app-ring',
			'app-danger',
			'app-warn',
			'app-ok'
		];
		const out: Record<string, string> = {};
		for (const k of keys) out[k] = cs.getPropertyValue(`--${k}`).trim();
		return out;
	}

	// Optional override — pages where the theme is controlled by something
	// richer than a binary chrome flag (the editor, with its 8-theme
	// `setting color_scheme` directive) install a function here on mount
	// and clear it on unmount. When set, `toggle()` defers to it instead
	// of flipping data-theme directly. That way the nav-bar sun/moon
	// button keeps working consistently across the whole app: outside the
	// editor it toggles the chrome; inside the editor it swaps the
	// canvas's colour scheme between light/dark counterparts AND the
	// chrome follows automatically (via the editor's own effect).
	override: (() => void) | null = $state(null);

	set(next: Theme) {
		this.current = next;
		if (typeof document !== 'undefined') {
			document.documentElement.setAttribute('data-theme', next);
		}
		try {
			localStorage.setItem(KEY, next);
		} catch {
			/* ignore */
		}
	}

	toggle() {
		if (this.override) {
			this.override();
			return;
		}
		this.set(this.current === 'dark' ? 'light' : 'dark');
	}

	/** Sync the in-memory store back to whatever the DOM currently has.
	 * Used after SSR hydration / page transitions. */
	rehydrate() {
		this.current = readCurrent();
	}
}

export const theme = new ThemeStore();
