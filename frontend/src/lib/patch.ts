// Surgical DSL string patching. All functions take a source string + change params,
// return a new source string with minimal disruption (preserves formatting where possible).

const NODE_LINE_RE = /^(\s*)\[(\w+)\]\s+(\w+)\s+"((?:[^"\\]|\\.)*)"(.*)$/;
const ATTR_FIND_RE = /(\w+):((?:"[^"]*"|\S+))/g;
const STYLE_BLOCK_RE = /\{([^{}]*)\}/;
const POSITION_RE = /@\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)/;

export function escapeRegex(s: string): string {
	return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

export type NodeLineParts = {
	indent: string;
	shape: string;
	name: string;
	label: string;
	attrs: Record<string, string>;
	style: Record<string, string>;
	position: { x: number; y: number } | null;
};

function parseRest(rest: string): {
	attrs: Record<string, string>;
	style: Record<string, string>;
	position: { x: number; y: number } | null;
} {
	const style: Record<string, string> = {};
	const attrs: Record<string, string> = {};
	let position: { x: number; y: number } | null = null;
	let working = rest;

	const sm = STYLE_BLOCK_RE.exec(working);
	if (sm) {
		for (const pair of sm[1].split(',')) {
			const colonIdx = pair.indexOf(':');
			if (colonIdx > -1) {
				const k = pair.slice(0, colonIdx).trim();
				const v = pair.slice(colonIdx + 1).trim();
				if (k) style[k] = v;
			}
		}
		working = working.slice(0, sm.index) + working.slice(sm.index + sm[0].length);
	}

	const pm = POSITION_RE.exec(working);
	if (pm) {
		position = { x: parseFloat(pm[1]), y: parseFloat(pm[2]) };
		working = working.slice(0, pm.index) + working.slice(pm.index + pm[0].length);
	}

	let am: RegExpExecArray | null;
	ATTR_FIND_RE.lastIndex = 0;
	while ((am = ATTR_FIND_RE.exec(working)) !== null) {
		let v = am[2];
		if (v.startsWith('"') && v.endsWith('"')) v = v.slice(1, -1);
		attrs[am[1]] = v;
	}

	return { style, attrs, position };
}

export function findNodeLineIndex(source: string, id: string): number {
	const lines = source.split('\n');
	for (let i = 0; i < lines.length; i++) {
		const m = lines[i].match(NODE_LINE_RE);
		if (m && m[3] === id) return i;
	}
	return -1;
}

export function parseNodeLine(line: string): NodeLineParts | null {
	const m = line.match(NODE_LINE_RE);
	if (!m) return null;
	const [, indent, shape, name, rawLabel, rest] = m;
	const label = rawLabel.replace(/\\n/g, '\n');
	const { style, attrs, position } = parseRest(rest);
	return { indent, shape, name, label, style, attrs, position };
}

const ATTR_ORDER = [
	'step',
	'type',
	'owner',
	'status',
	'priority',
	'tags',
	'condition',
	'weight',
	'id',
	'width',
	'height'
];

export function serializeNodeLine(parts: NodeLineParts): string {
	const escapedLabel = parts.label.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n');
	const segments: string[] = [
		`${parts.indent}[${parts.shape}] ${parts.name} "${escapedLabel}"`
	];

	const remaining = new Set(Object.keys(parts.attrs));
	for (const key of ATTR_ORDER) {
		if (remaining.has(key)) {
			const v = parts.attrs[key];
			segments.push(`${key}:${needsQuote(v) ? `"${v}"` : v}`);
			remaining.delete(key);
		}
	}
	for (const key of [...remaining].sort()) {
		const v = parts.attrs[key];
		segments.push(`${key}:${needsQuote(v) ? `"${v}"` : v}`);
	}

	const styleEntries = Object.entries(parts.style);
	if (styleEntries.length) {
		segments.push(`{${styleEntries.map(([k, v]) => `${k}: ${v}`).join(', ')}}`);
	}

	if (parts.position) {
		segments.push(`@(${Math.round(parts.position.x)}, ${Math.round(parts.position.y)})`);
	}

	return segments.join(' ');
}

function needsQuote(v: string): boolean {
	return v === '' || /\s/.test(v) || /[#@]/.test(v);
}

function modifyNodeLine(
	source: string,
	id: string,
	modify: (parts: NodeLineParts) => NodeLineParts | null
): string {
	const lines = source.split('\n');
	for (let i = 0; i < lines.length; i++) {
		const parts = parseNodeLine(lines[i]);
		if (parts && parts.name === id) {
			const updated = modify(parts);
			if (updated === null) lines.splice(i, 1);
			else lines[i] = serializeNodeLine(updated);
			return lines.join('\n');
		}
	}
	return source;
}

export function setNodePosition(source: string, id: string, x: number, y: number): string {
	return modifyNodeLine(source, id, (p) => ({ ...p, position: { x, y } }));
}

export function clearNodePosition(source: string, id: string): string {
	return modifyNodeLine(source, id, (p) => ({ ...p, position: null }));
}

export function setNodeLabel(source: string, id: string, label: string): string {
	return modifyNodeLine(source, id, (p) => ({ ...p, label }));
}

export function setNodeShape(source: string, id: string, shape: string): string {
	return modifyNodeLine(source, id, (p) => ({ ...p, shape }));
}

export function setNodeName(source: string, id: string, newName: string): string {
	return modifyNodeLine(source, id, (p) => ({ ...p, name: newName }));
}

export function setNodeAttr(source: string, id: string, key: string, value: string): string {
	if (value === '' || value == null) return removeNodeAttr(source, id, key);
	return modifyNodeLine(source, id, (p) => ({ ...p, attrs: { ...p.attrs, [key]: value } }));
}

export function removeNodeAttr(source: string, id: string, key: string): string {
	return modifyNodeLine(source, id, (p) => {
		const attrs = { ...p.attrs };
		delete attrs[key];
		return { ...p, attrs };
	});
}

export function setNodeStyle(source: string, id: string, key: string, value: string): string {
	if (value === '' || value == null) return removeNodeStyle(source, id, key);
	return modifyNodeLine(source, id, (p) => ({ ...p, style: { ...p.style, [key]: value } }));
}

export function removeNodeStyle(source: string, id: string, key: string): string {
	return modifyNodeLine(source, id, (p) => {
		const style = { ...p.style };
		delete style[key];
		return { ...p, style };
	});
}

export function removeNode(source: string, id: string): string {
	const lines = source.split('\n');
	const result: string[] = [];
	const idRe = new RegExp(`(?:^|\\s)${escapeRegex(id)}(?:$|\\s|:)`);
	for (const line of lines) {
		const parts = parseNodeLine(line);
		if (parts && parts.name === id) continue;
		if (/->|-->|==>|---|-\.-/.test(line) && idRe.test(line)) continue;
		const noteM = line.match(/^\s*note\s+"[^"]*"\s+\[(\w+)\]\s*$/);
		if (noteM && noteM[1] === id) continue;
		result.push(line);
	}
	return result.join('\n');
}

export function setDirection(source: string, dir: string): string {
	const lines = source.split('\n');
	const idx = lines.findIndex((l) => /^\s*direction\s+\S+\s*$/.test(l));
	if (idx >= 0) lines[idx] = `direction ${dir}`;
	else lines.unshift(`direction ${dir}`, '');
	return lines.join('\n');
}

export function setSetting(source: string, key: string, value: string | number): string {
	const lines = source.split('\n');
	const re = new RegExp(`^\\s*setting\\s+${escapeRegex(key)}(\\s+|$)`);
	const idx = lines.findIndex((l) => re.test(l));
	const newLine = `setting ${key} ${value}`;
	if (idx >= 0) {
		lines[idx] = newLine;
	} else {
		let last = -1;
		for (let i = 0; i < lines.length; i++) {
			if (/^\s*(direction|setting)\b/.test(lines[i])) last = i;
		}
		lines.splice(last + 1, 0, newLine);
	}
	return lines.join('\n');
}

export function removeSetting(source: string, key: string): string {
	const lines = source.split('\n');
	const re = new RegExp(`^\\s*setting\\s+${escapeRegex(key)}(\\s+|$)`);
	return lines.filter((l) => !re.test(l)).join('\n');
}

export function getSetting(source: string, key: string): string | null {
	const lines = source.split('\n');
	const re = new RegExp(`^\\s*setting\\s+${escapeRegex(key)}\\s+(.+)$`);
	for (const l of lines) {
		const m = l.match(re);
		if (m) return m[1].trim();
	}
	return null;
}

export function getDirection(source: string): string {
	const lines = source.split('\n');
	const m = lines.find((l) => /^\s*direction\s+\S+\s*$/.test(l));
	return m ? m.trim().split(/\s+/)[1] : 'top-to-bottom';
}

export function addNode(
	source: string,
	opts: {
		name: string;
		shape: string;
		label?: string;
		step?: number;
		swimlane?: string | null;
		attrs?: Record<string, string>;
	}
): string {
	const label = opts.label ?? opts.name.charAt(0).toUpperCase() + opts.name.slice(1);
	const attrs: Record<string, string> = { ...(opts.attrs ?? {}) };
	if (opts.step != null) attrs.step = String(opts.step);

	const parts: NodeLineParts = {
		indent: opts.swimlane ? '\t' : '',
		shape: opts.shape,
		name: opts.name,
		label,
		attrs,
		style: {},
		position: null
	};
	const newLine = serializeNodeLine(parts);

	if (opts.swimlane) {
		const lines = source.split('\n');
		const slRe = new RegExp(`^\\s*swimlane\\s+"${escapeRegex(opts.swimlane)}"\\s*\\{\\s*$`);
		let depth = 0;
		let insertAt = -1;
		let inLane = false;
		for (let i = 0; i < lines.length; i++) {
			if (!inLane && slRe.test(lines[i])) {
				inLane = true;
				depth = 1;
				continue;
			}
			if (inLane) {
				const trimmed = lines[i].trim();
				if (trimmed === '}') {
					depth--;
					if (depth === 0) {
						insertAt = i;
						break;
					}
				} else if (trimmed.endsWith('{')) {
					depth++;
				}
			}
		}
		if (insertAt >= 0) {
			lines.splice(insertAt, 0, newLine);
			return lines.join('\n');
		}
	}

	return source.trimEnd() + '\n' + newLine + '\n';
}

export function addEdge(
	source: string,
	opts: {
		src: string;
		dst: string;
		kind?: 'solid' | 'dashed' | 'thick' | 'solid_line' | 'dotted_line';
		label?: string;
	}
): string {
	const sym = {
		solid: '->',
		dashed: '-->',
		thick: '==>',
		solid_line: '---',
		dotted_line: '-.-'
	}[opts.kind ?? 'solid'];
	let line = `${opts.src} ${sym} ${opts.dst}`;
	if (opts.label) line += ` : "${opts.label}"`;
	return source.trimEnd() + '\n' + line + '\n';
}

export function addSwimlane(source: string, name: string): string {
	const block = `\nswimlane "${name}" {\n}\n`;
	return source.trimEnd() + block;
}

export type ParentTarget =
	| { kind: 'root' }
	| { kind: 'swimlane'; name: string }
	| { kind: 'box'; label: string; swimlane: string | null };

function findBlockOpen(
	lines: string[],
	kind: 'swimlane' | 'box',
	name: string,
	range?: { start: number; end: number }
): number | null {
	const from = range?.start ?? 0;
	const to = range?.end ?? lines.length;
	const re =
		kind === 'swimlane'
			? new RegExp(`^\\s*swimlane\\s+"${escapeRegex(name)}"\\s*\\{\\s*$`)
			: new RegExp(
					`^\\s*box\\s+"${escapeRegex(name)}"\\s*(?:\\{[^{}]*\\})?\\s*\\{\\s*$`
				);
	for (let i = from; i < to; i++) {
		if (re.test(lines[i])) return i;
	}
	return null;
}

function findMatchingClose(lines: string[], openLine: number): number | null {
	let depth = 1;
	for (let i = openLine + 1; i < lines.length; i++) {
		const t = lines[i].trim();
		if (t === '}') {
			depth--;
			if (depth === 0) return i;
		} else if (/\{\s*$/.test(t)) {
			depth++;
		}
	}
	return null;
}

function extractNodeLine(lines: string[], id: string): { line: string; index: number } | null {
	for (let i = 0; i < lines.length; i++) {
		const parts = parseNodeLine(lines[i]);
		if (parts && parts.name === id) return { line: lines[i], index: i };
	}
	return null;
}

function indentFor(target: ParentTarget): string {
	if (target.kind === 'root') return '';
	if (target.kind === 'swimlane') return '\t';
	return '\t\t';
}

function reindent(line: string, newIndent: string): string {
	const parts = parseNodeLine(line);
	if (!parts) return newIndent + line.trimStart();
	return serializeNodeLine({ ...parts, indent: newIndent });
}

export function reparentNode(source: string, id: string, target: ParentTarget): string {
	const lines = source.split('\n');
	const found = extractNodeLine(lines, id);
	if (!found) return source;

	lines.splice(found.index, 1);

	if (target.kind === 'root') {
		const reindented = reindent(found.line, indentFor(target));
		return (lines.join('\n').trimEnd() + '\n' + reindented + '\n').replace(/\n{3,}/g, '\n\n');
	}

	if (target.kind === 'swimlane') {
		const openIdx = findBlockOpen(lines, 'swimlane', target.name);
		if (openIdx == null) return source;
		const closeIdx = findMatchingClose(lines, openIdx);
		if (closeIdx == null) return source;
		const reindented = reindent(found.line, indentFor(target));
		lines.splice(closeIdx, 0, reindented);
		return lines.join('\n');
	}

	// box target: must find the swimlane first (if any) to scope the search
	let searchRange: { start: number; end: number } | undefined;
	if (target.swimlane) {
		const swOpen = findBlockOpen(lines, 'swimlane', target.swimlane);
		if (swOpen == null) return source;
		const swClose = findMatchingClose(lines, swOpen);
		if (swClose == null) return source;
		searchRange = { start: swOpen + 1, end: swClose };
	}
	const boxOpen = findBlockOpen(lines, 'box', target.label, searchRange);
	if (boxOpen == null) return source;
	const boxClose = findMatchingClose(lines, boxOpen);
	if (boxClose == null) return source;
	const reindented = reindent(found.line, indentFor(target));
	lines.splice(boxClose, 0, reindented);
	return lines.join('\n');
}

export function moveNodeAmongSiblings(source: string, id: string, direction: -1 | 1): string {
	const lines = source.split('\n');
	const found = extractNodeLine(lines, id);
	if (!found) return source;

	let i = found.index + direction;
	while (i >= 0 && i < lines.length) {
		const parts = parseNodeLine(lines[i]);
		if (parts) {
			const mineIndent = found.line.match(/^\s*/)![0];
			const theirIndent = lines[i].match(/^\s*/)![0];
			if (mineIndent === theirIndent) {
				const [a, b] = [lines[found.index], lines[i]];
				lines[i] = a;
				lines[found.index] = b;
				return lines.join('\n');
			}
			break;
		}
		if (lines[i].trim() === '}' || /\{\s*$/.test(lines[i].trim())) break;
		i += direction;
	}
	return source;
}
