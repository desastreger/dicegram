// Theme store — mirrors document.documentElement[data-theme] and
// persists to localStorage. Default detection happens in app.html so the
// initial paint matches.

export type Theme = 'light' | 'dark';

const KEY = 'dicegram:theme';

function readCurrent(): Theme {
	if (typeof document === 'undefined') return 'dark';
	const attr = document.documentElement.getAttribute('data-theme');
	return attr === 'light' ? 'light' : 'dark';
}

class ThemeStore {
	current: Theme = $state(readCurrent());

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
		this.set(this.current === 'dark' ? 'light' : 'dark');
	}

	/** Sync the in-memory store back to whatever the DOM currently has.
	 * Used after SSR hydration / page transitions. */
	rehydrate() {
		this.current = readCurrent();
	}
}

export const theme = new ThemeStore();
