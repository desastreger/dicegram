import { api } from './api';

export type Dicegram = {
	id: number;
	name: string;
	source: string;
	created_at: string;
	updated_at: string;
};

export const dicegrams = {
	list: () => api.get<Dicegram[]>('/dicegrams'),
	get: (id: number) => api.get<Dicegram>(`/dicegrams/${id}`),
	create: (data: { name: string; source: string }) => api.post<Dicegram>('/dicegrams', data),
	update: (id: number, data: { name: string; source: string }) =>
		api.put<Dicegram>(`/dicegrams/${id}`, data),
	remove: (id: number) => api.del<void>(`/dicegrams/${id}`)
};
