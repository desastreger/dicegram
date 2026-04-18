import { ApiError, api } from './api';

export type User = { id: number; email: string };

function createAuth() {
	let user = $state<User | null>(null);
	let loading = $state(true);

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
			} catch (err) {
				if (err instanceof ApiError && err.status === 401) user = null;
				else throw err;
			} finally {
				loading = false;
			}
		},

		async signup(email: string, password: string) {
			user = await api.post<User>('/auth/signup', { email, password });
		},

		async login(email: string, password: string) {
			user = await api.post<User>('/auth/login', { email, password });
		},

		async logout() {
			await api.post('/auth/logout');
			user = null;
		}
	};
}

export const auth = createAuth();
