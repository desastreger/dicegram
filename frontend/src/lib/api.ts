const BASE = '/api';

export class ApiError extends Error {
	constructor(
		public status: number,
		message: string,
		/** Parsed `detail` from the error body. FastAPI allows a dict there,
		 *  and the login 401 uses it to return the account's password hint
		 *  alongside the message. */
		public detail?: unknown
	) {
		super(message);
	}
}

async function handle<T>(res: Response): Promise<T> {
	if (!res.ok) {
		const body = await res.json().catch(() => ({ detail: res.statusText }));
		const detail = body.detail;
		// `detail` is a string for ordinary errors and an object when a route
		// needs to return structured data with the failure.
		const message =
			typeof detail === 'string'
				? detail
				: ((detail as { detail?: string } | undefined)?.detail ?? 'request failed');
		throw new ApiError(res.status, message, detail);
	}
	if (res.status === 204) return undefined as T;
	// A non-204 response can still have an empty body (some endpoints, or
	// a proxy that strips it) — `res.json()` throws a raw SyntaxError on
	// empty input, which callers only expect to catch as an `ApiError`.
	// Read as text first so an empty body resolves to `undefined` instead
	// of an unhandled parse exception, and wrap any genuine malformed-JSON
	// error the same way.
	const text = await res.text();
	if (text.length === 0) return undefined as T;
	try {
		return JSON.parse(text) as T;
	} catch {
		throw new ApiError(res.status, 'invalid response from server');
	}
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
