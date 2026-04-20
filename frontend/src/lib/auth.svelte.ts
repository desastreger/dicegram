import { ApiError, api } from './api';
import { palette } from './palette.svelte';

export type User = { id: number; email: string };

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

		async signup(email: string, password: string) {
			user = await api.post<User>('/auth/signup', { email, password });
			await hydratePalette();
		},

		async login(email: string, password: string) {
			user = await api.post<User>('/auth/login', { email, password });
			await hydratePalette();
		},

		async logout() {
			await api.post('/auth/logout');
			user = null;
		}
	};
}

export const auth = createAuth();
