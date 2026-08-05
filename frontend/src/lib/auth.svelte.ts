import { ApiError, api } from './api';
import { palette } from './palette.svelte';

export type User = {
	id: number;
	username: string;
	/** Legacy only — never collected at signup; present on pre-migration rows. */
	email?: string | null;
	password_hint?: string | null;
};

export type SignupPayload = {
	username: string;
	password: string;
	password_hint?: string;
};

function createAuth() {
	let user = $state<User | null>(null);
	let loading = $state(true);

	async function hydratePalette() {
		await palette.load();
	}

	return {
		get user() {
			return user;
		},
		get loading() {
			return loading;
		},

		async refresh() {
			loading = true;
			try {
				user = await api.get<User>('/auth/me');
				await hydratePalette();
			} catch (err) {
				if (err instanceof ApiError && err.status === 401) user = null;
				else throw err;
			} finally {
				loading = false;
			}
		},

		async signup(payload: SignupPayload) {
			user = await api.post<User>('/auth/signup', payload);
			await hydratePalette();
		},

		/**
		 * `identifier` is a username. Accounts created before the switch to
		 * username login may still pass their email — the backend accepts
		 * either while the legacy column exists.
		 */
		async login(identifier: string, password: string) {
			user = await api.post<User>('/auth/login', { identifier, password });
			await hydratePalette();
		},

		async logout() {
			await api.post('/auth/logout');
			user = null;
		},

		async updateHint(hint: string) {
			user = await api.put<User>('/auth/me/hint', { password_hint: hint });
		},

		async updateUsername(username: string) {
			user = await api.put<User>('/auth/me/username', { username });
		}
	};
}

export const auth = createAuth();
