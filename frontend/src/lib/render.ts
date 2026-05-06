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
	parent_id: string;
	attrs: Record<string, string>;
	style: Record<string, string>;
};

export type RenderEdge = {
	id: string;
	source: string;
	target: string;
	kind: 'solid' | 'dashed' | 'thick' | 'solid_line' | 'dotted_line' | 'bidirectional';
	label: string;
	attrs: Record<string, string>;
	source_port: string | null;
	target_port: string | null;
	// Deterministic geometry from the backend route planner. The frontend
	// renders these directly — no further routing decisions.
	source_x: number | null;
	source_y: number | null;
	target_x: number | null;
	target_y: number | null;
	waypoints: { x: number; y: number }[];
	label_x: number | null;
	label_y: number | null;
	label_axis: 'horizontal' | 'vertical';
	corner_radius: number;
};

export type RenderLane = {
	id: string;
	name: string;
	x: number;
	y: number;
	width: number;
	height: number;
};

export type RenderBox = {
	id: string;
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

export type Notice = { severity: 'fix' | 'info'; message: string; line: number | null };

export type TreeEntry = {
	id: string;
	kind: 'root' | 'swimlane' | 'box' | 'shape' | 'group' | 'note' | 'edge';
	label: string;
	parent: string | null;
	children: string[];
	shape?: string | null;
};

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
	notices: Notice[];
	tree: TreeEntry[];
	normalized_source: string;
	source_changed: boolean;
};

export function renderDsl(source: string, normalize = true): Promise<RenderResult> {
	return api.post<RenderResult>('/render', { source, normalize_source: normalize });
}
