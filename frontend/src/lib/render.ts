import { api } from './api';

export type RenderNode = {
	id: string;
	shape: string;
	label: string;
	x: number;
	y: number;
	width: number;
	height: number;
	swimlane: string | null;
	box: string | null;
	attrs: Record<string, string>;
	style: Record<string, string>;
};

export type RenderEdge = {
	id: string;
	source: string;
	target: string;
	kind: 'solid' | 'dashed' | 'thick' | 'solid_line' | 'dotted_line';
	label: string;
	attrs: Record<string, string>;
};

export type RenderLane = {
	name: string;
	x: number;
	y: number;
	width: number;
	height: number;
};

export type RenderBox = {
	label: string;
	swimlane: string | null;
	style: Record<string, string>;
	members: string[];
	x: number | null;
	y: number | null;
	width: number | null;
	height: number | null;
};

export type RenderGroup = {
	name: string;
	members: string[];
	x: number | null;
	y: number | null;
	width: number | null;
	height: number | null;
};

export type RenderNote = {
	text: string;
	target: string;
	x: number;
	y: number;
	width: number;
	height: number;
};

export type RenderError = { line: number; column: number; message: string };

export type RenderResult = {
	direction: string;
	settings: Record<string, number | string>;
	nodes: RenderNode[];
	edges: RenderEdge[];
	lanes: RenderLane[];
	boxes: RenderBox[];
	groups: RenderGroup[];
	notes: RenderNote[];
	errors: RenderError[];
};

export function renderDsl(source: string): Promise<RenderResult> {
	return api.post<RenderResult>('/render', { source });
}
