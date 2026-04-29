export type Theme = {
	id: string;
	label: string;
	bg: string;
	panel: string;
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
	codeBg: string;
	codeText: string;
	codeGutter: string;
	codeActiveLine: string;
};

export const THEMES: Record<string, Theme> = {
	anthropic: {
		id: 'anthropic',
		label: 'Anthropic',
		bg: '#fbf7f2',
		panel: '#fbf7f2',
		panelBorder: '#e3d9cf',
		text: '#3d3530',
		muted: '#8a7a6a',
		accent: '#d97757',
		canvas: '#fbf7f2',
		gridDot: '#e3d9cf',
		nodeFill: '#dceadb',
		nodeStroke: '#a8c2a3',
		nodeText: '#3d5c3a',
		edge: '#8a8a82',
		codeBg: '#fbf7f2',
		codeText: '#3d3530',
		codeGutter: '#a8a39a',
		codeActiveLine: '#f1ece4'
	},
	'default-dark': {
		id: 'default-dark',
		label: 'Default Dark',
		bg: '#0a0a0a',
		panel: '#0a0a0a',
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
		codeBg: '#0a0a0a',
		codeText: '#e5e7eb',
		codeGutter: '#52525b',
		codeActiveLine: '#18181b'
	},
	light: {
		id: 'light',
		label: 'Light',
		bg: '#ffffff',
		panel: '#f8fafc',
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
		codeBg: '#ffffff',
		codeText: '#0f172a',
		codeGutter: '#94a3b8',
		codeActiveLine: '#f1f5f9'
	},
	'solarized-dark': {
		id: 'solarized-dark',
		label: 'Solarized Dark',
		bg: '#002b36',
		panel: '#073642',
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
		codeBg: '#002b36',
		codeText: '#eee8d5',
		codeGutter: '#586e75',
		codeActiveLine: '#073642'
	},
	'solarized-light': {
		id: 'solarized-light',
		label: 'Solarized Light',
		bg: '#fdf6e3',
		panel: '#eee8d5',
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
		codeBg: '#fdf6e3',
		codeText: '#073642',
		codeGutter: '#93a1a1',
		codeActiveLine: '#eee8d5'
	},
	dracula: {
		id: 'dracula',
		label: 'Dracula',
		bg: '#282a36',
		panel: '#21222c',
		panelBorder: '#44475a',
		text: '#f8f8f2',
		muted: '#6272a4',
		accent: '#bd93f9',
		canvas: '#282a36',
		gridDot: '#44475a',
		nodeFill: '#44475a',
		nodeStroke: '#6272a4',
		nodeText: '#f8f8f2',
		edge: '#bd93f9',
		codeBg: '#282a36',
		codeText: '#f8f8f2',
		codeGutter: '#6272a4',
		codeActiveLine: '#44475a'
	},
	gruvbox: {
		id: 'gruvbox',
		label: 'Gruvbox Dark',
		bg: '#282828',
		panel: '#1d2021',
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
		codeBg: '#282828',
		codeText: '#ebdbb2',
		codeGutter: '#928374',
		codeActiveLine: '#3c3836'
	},
	'high-contrast': {
		id: 'high-contrast',
		label: 'High Contrast',
		bg: '#000000',
		panel: '#000000',
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
		codeBg: '#000000',
		codeText: '#ffffff',
		codeGutter: '#888888',
		codeActiveLine: '#222222'
	}
};

export const THEME_IDS = Object.keys(THEMES);
export const DEFAULT_THEME_ID = 'default-dark';

export function getTheme(id: string | null | undefined): Theme {
	return THEMES[id ?? DEFAULT_THEME_ID] ?? THEMES[DEFAULT_THEME_ID];
}
