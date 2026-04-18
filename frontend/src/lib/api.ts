const BASE = '/api';

export class ApiError extends Error {
	constructor(
		public status: number,
		message: string
	) {
		super(message);
	}
}

async function handle<T>(res: Response): Promise<T> {
	if (!res.ok) {
		const body = await res.json().catch(() => ({ detail: res.statusText }));
		throw new ApiError(res.status, body.detail ?? 'request failed');
	}
	if (res.status === 204) return undefined as T;
	return res.json() as Promise<T>;
}

export const api = {
	get<T>(path: string) {
		return fetch(`${BASE}${path}`, { credentials: 'include' }).then(handle<T>);
	},
	post<T>(path: string, body?: unknown) {
		return fetch(`${BASE}${path}`, {
			method: 'POST',
			credentials: 'include',
			headers: body ? { 'Content-Type': 'application/json' } : undefined,
			body: body ? JSON.stringify(body) : undefined
		}).then(handle<T>);
	},
	put<T>(path: string, body: unknown) {
		return fetch(`${BASE}${path}`, {
			method: 'PUT',
			credentials: 'include',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(body)
		}).then(handle<T>);
	},
	del<T>(path: string) {
		return fetch(`${BASE}${path}`, { method: 'DELETE', credentials: 'include' }).then(
			handle<T>
		);
	}
};
