// Surgical DSL string patching. All functions take a source string + change params,
// return a new source string with minimal disruption (preserves formatting where possible).

// A label is one quoted string OR a sequence joined by `[linebreak]` — e.g.
// `"First" [linebreak] "Second"`. The sequence form is preferred for multi-
// line labels so users never have to type `\n` themselves (a programmer
// habit that doesn't translate to end users).
const LABEL_SEQ_SRC =
	'"(?:[^"\\\\]|\\\\.)*"(?:\\s*\\[linebreak\\]\\s*"(?:[^"\\\\]|\\\\.)*")*';
const LABEL_PART_RE = /("(?:[^"\\]|\\.)*"|\[linebreak\])/g;
const NODE_LINE_RE = new RegExp(
	'^(\\s*)\\[(\\w+)\\]\\s+(\\w+)\\s+(' + LABEL_SEQ_SRC + ')(.*)$'
);
const ATTR_FIND_RE = /(\w+):((?:"[^"]*"|\S+))/g;
const STYLE_BLOCK_RE = /\{([^{}]*)\}/;
const POSITION_RE = /@\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)/;

export function joinLabelParts(raw: string): string {
	const out: string[] = [];
	LABEL_PART_RE.lastIndex = 0;
	let m: RegExpExecArray | null;
	while ((m = LABEL_PART_RE.exec(raw)) !== null) {
		const tok = m[1];
		if (tok === '[linebreak]') {
			out.push('\n');
		} else {
			out.push(tok.slice(1, -1).replace(/\\"/g, '"').replace(/\\\\/g, '\\').replace(/\\n/g, '\n'));
		}
	}
	return out.join('');
}

export function formatLabel(label: string): string {
	if (label.includes('\n')) {
		return label
			.split('\n')
			.map((seg) => `"${seg.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`)
			.join(' [linebreak] ');
	}
	return `"${label.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`;
}

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
	const label = joinLabelParts(rawLabel);
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
	const segments: string[] = [
		`${parts.indent}[${parts.shape}] ${parts.name} ${formatLabel(parts.label)}`
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
		// `[connector]` form carries refs in `from:` / `to:` attrs.
		if (CONNECTOR_LINE_RE.test(line)) {
			const conn = parseConnectorLineEdge(line);
			if (conn && (conn.src === id || conn.dst === id)) continue;
		}
		const noteM = line.match(/^\s*note\s+"[^"]*"\s+\[(\w+)\]\s*$/);
		if (noteM && noteM[1] === id) continue;
		result.push(line);
	}
	return result.join('\n');
}

export function setDirection(source: string, dir: string): string {
	const lines = source.split('\n');
	const idx = lines.findIndex((l) => /^\s*direction\s+\S+\s*$/.test(l));
	const current = idx >= 0 ? lines[idx].trim().split(/\s+/)[1] : 'top-to-bottom';
	if (current === dir) return source;
	if (idx >= 0) lines[idx] = `direction ${dir}`;
	else lines.unshift(`direction ${dir}`, '');
	// Pins are absolute coordinates placed for the old orientation; swapping
	// direction makes them nonsensical, so strip them and let auto-layout
	// reflow everything in the new direction.
	const POS_RE = /\s*@\(\s*-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?\s*\)/g;
	return lines.map((l) => l.replace(POS_RE, '')).join('\n');
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
		position?: { x: number; y: number } | null;
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
		position: opts.position
			? { x: Math.round(opts.position.x), y: Math.round(opts.position.y) }
			: null
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
		attrs?: Record<string, string>;
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
	const tail: string[] = [];
	if (opts.label) {
		tail.push(formatLabel(opts.label));
	}
	for (const [k, v] of Object.entries(opts.attrs ?? {})) {
		if (v == null || v === '') continue;
		const needsQuote = /\s|,/.test(v);
		tail.push(`${k}:${needsQuote ? `"${v}"` : v}`);
	}
	if (tail.length) line += ` : ${tail.join(' ')}`;
	return source.trimEnd() + '\n' + line + '\n';
}

export function addSwimlane(source: string, name: string): string {
	const block = `\nswimlane "${name}" {\n}\n`;
	return source.trimEnd() + block;
}

export function addBox(
	source: string,
	opts: { label: string; swimlane?: string | null; fill?: string }
): string {
	const style = opts.fill ? ` {fill: ${opts.fill}}` : '';
	const block = `\n\tbox "${opts.label}"${style} {\n\t}\n`;
	if (opts.swimlane) {
		// Place inside the named swimlane.
		const lines = source.split('\n');
		const slRe = new RegExp(`^\\s*swimlane\\s+"${escapeRegex(opts.swimlane)}"\\s*\\{\\s*$`);
		let depth = 0;
		let inLane = false;
		let insertAt = -1;
		for (let i = 0; i < lines.length; i++) {
			if (!inLane && slRe.test(lines[i])) {
				inLane = true;
				depth = 1;
				continue;
			}
			if (inLane) {
				const t = lines[i].trim();
				if (t === '}') {
					depth--;
					if (depth === 0) {
						insertAt = i;
						break;
					}
				} else if (t.endsWith('{')) depth++;
			}
		}
		if (insertAt >= 0) {
			lines.splice(insertAt, 0, `\tbox "${opts.label}"${style} {`, '\t}');
			return lines.join('\n');
		}
	}
	return source.trimEnd() + block;
}

export function addGroup(source: string, name: string, members: string[] = []): string {
	const block = `\ngroup "${name}" { ${members.join(' ')} }\n`;
	return source.trimEnd() + block;
}

export function addNote(source: string, text: string, target: string): string {
	return source.trimEnd() + `\nnote ${formatLabel(text)} [${target}]\n`;
}

/** Produce a node name that isn't already used in `source`. */
export function nextNodeName(source: string, prefix = 'node'): string {
	const used = new Set<string>();
	const re = /^\s*\[\w+\]\s+(\w+)\s+"/gm;
	for (const m of source.matchAll(re)) used.add(m[1]);
	let i = 1;
	while (used.has(`${prefix}${i}`)) i++;
	return `${prefix}${i}`;
}

/** Produce a unique swimlane/box label. */
export function nextLabel(source: string, kind: 'swimlane' | 'box' | 'group', base: string): string {
	const re = new RegExp(`^\\s*${kind}\\s+"([^"]+)"`, 'gm');
	const used = new Set<string>();
	for (const m of source.matchAll(re)) used.add(m[1]);
	if (!used.has(base)) return base;
	let i = 2;
	while (used.has(`${base} ${i}`)) i++;
	return `${base} ${i}`;
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

function moveRelative(source: string, moveId: string, anchorId: string, after: boolean): string {
	if (moveId === anchorId) return source;
	const lines = source.split('\n');
	const moveIdx = findNodeLineIndex(source, moveId);
	const anchorIdx = findNodeLineIndex(source, anchorId);
	if (moveIdx < 0 || anchorIdx < 0 || moveIdx === anchorIdx) return source;

	const moveParts = parseNodeLine(lines[moveIdx]);
	if (!moveParts) return source;
	const anchorIndent = lines[anchorIdx].match(/^\s*/)![0];
	const reindented = serializeNodeLine({ ...moveParts, indent: anchorIndent });

	lines.splice(moveIdx, 1);
	const adjusted = anchorIdx > moveIdx ? anchorIdx - 1 : anchorIdx;
	lines.splice(after ? adjusted + 1 : adjusted, 0, reindented);
	return lines.join('\n');
}

export function moveNodeBefore(source: string, moveId: string, anchorId: string): string {
	return moveRelative(source, moveId, anchorId, false);
}

export function moveNodeAfter(source: string, moveId: string, anchorId: string): string {
	return moveRelative(source, moveId, anchorId, true);
}

// --- edge editing ------------------------------------------------------------

// Edge lines now carry optional `@port` suffixes and attr pairs after the
// label:  `A@r -> B@l : "yes" end:circle weight:5`.
// Capture: 1=indent  2=src  3=src-port  4=sym  5=dst  6=dst-port  7=tail
const EDGE_LINE_RE =
	/^(\s*)(\w+)(?:@(\w+))?\s+(->|-->|==>|---|-\.-)\s+(\w+)(?:@(\w+))?(\s*:\s*.*)?\s*$/;

// Verbose block-form header:  `edge A@r -> B@l {` or `A -> B {`. Counted
// as an edge for ordinal purposes so the Inspector stays in sync, but
// the inline modifier helpers refuse to rewrite them (a block spans
// multiple lines; surgical in-place editing would silently drop the
// body). Users wanting to edit block-form edges edit the DSL directly.
const EDGE_BLOCK_HEADER_RE =
	/^(\s*)(?:edge\s+)?(\w+)(?:@\w+)?\s*(->|-->|==>|---|-\.-)\s*(\w+)(?:@\w+)?\s*\{/;

// Object-style connector: `[connector] name? from:A@r to:B@l kind:dashed
// tip:arrow back:none label:"x"`. Also the kind-keyword form
// `[arrow] …` / `[dashed_arrow] …` / `[thick_arrow] …` / `[line] …` /
// `[dotted_line] …` where the bracket names the line style. All parse
// through the same helper and round-trip with the original bracket
// keyword preserved.
const CONNECTOR_KEYWORDS = [
	'connector',
	'arrow',
	'solid_arrow',
	'dashed_arrow',
	'thick_arrow',
	'line',
	'solid_line',
	'dotted_line'
] as const;
type ConnectorKeyword = (typeof CONNECTOR_KEYWORDS)[number];
const CONNECTOR_LINE_RE = new RegExp(
	'^(\\s*)\\[(' + CONNECTOR_KEYWORDS.join('|') + ')\\]\\s+(?:(\\w+)\\s+)?(.*)$'
);
const CONNECTOR_KEYWORD_PRESETS: Record<ConnectorKeyword, { kind: string; tip: string }> = {
	connector: { kind: 'solid', tip: 'arrow' },
	arrow: { kind: 'solid', tip: 'arrow' },
	solid_arrow: { kind: 'solid', tip: 'arrow' },
	dashed_arrow: { kind: 'dashed', tip: 'arrow' },
	thick_arrow: { kind: 'thick', tip: 'arrow' },
	line: { kind: 'solid_line', tip: 'none' },
	solid_line: { kind: 'solid_line', tip: 'none' },
	dotted_line: { kind: 'dotted_line', tip: 'none' }
};
// Map a kind name back to the canonical bracket keyword for
// round-trip emission.
const KIND_TO_KEYWORD: Record<string, ConnectorKeyword> = {
	solid: 'arrow',
	dashed: 'dashed_arrow',
	thick: 'thick_arrow',
	solid_line: 'line',
	dotted_line: 'dotted_line'
};

function isEdgeLine(line: string): boolean {
	return (
		EDGE_LINE_RE.test(line) ||
		EDGE_BLOCK_HEADER_RE.test(line) ||
		CONNECTOR_LINE_RE.test(line)
	);
}

const EDGE_LABEL_RE = new RegExp(LABEL_SEQ_SRC);
// Value production for bracket-form attrs: label sequences OR bare tokens.
const EDGE_CONNECTOR_ATTR_RE = new RegExp(
	'(\\w+)\\s*:\\s*(' + LABEL_SEQ_SRC + '|\\S+)',
	'g'
);
const EDGE_ATTR_RE = /(\w+):((?:"[^"]*"|\S+))/g;

export const EDGE_KIND_SYM: Record<string, string> = {
	solid: '->',
	dashed: '-->',
	thick: '==>',
	solid_line: '---',
	dotted_line: '-.-'
};
export const EDGE_SYM_KIND: Record<string, string> = {
	'->': 'solid',
	'-->': 'dashed',
	'==>': 'thick',
	'---': 'solid_line',
	'-.-': 'dotted_line'
};

const PORT_ALIASES: Record<string, 't' | 'b' | 'l' | 'r'> = {
	t: 't', top: 't', n: 't', north: 't',
	b: 'b', bottom: 'b', s: 'b', south: 'b',
	l: 'l', left: 'l', w: 'l', west: 'l',
	r: 'r', right: 'r', e: 'r', east: 'r'
};
function canonPort(p: string | null | undefined): 't' | 'b' | 'l' | 'r' | null {
	if (!p) return null;
	return PORT_ALIASES[p.trim().toLowerCase()] ?? null;
}

type EdgeParts = {
	indent: string;
	src: string;
	srcPort: string | null;
	sym: string;
	dst: string;
	dstPort: string | null;
	label: string | null;
	attrs: Record<string, string>;
	// `inline` = `A -> B : "x"`; `connector` = `[connector] name from:A to:B`.
	form: 'inline' | 'connector';
	connectorName?: string;
};

function parseInlineEdgeLine(line: string): EdgeParts | null {
	const m = line.match(EDGE_LINE_RE);
	if (!m) return null;
	const tail = m[7] ?? '';
	let label: string | null = null;
	let rest = tail.replace(/^\s*:\s*/, '');
	const lm = rest.match(EDGE_LABEL_RE);
	if (lm && rest.startsWith(lm[0])) {
		label = joinLabelParts(lm[0]);
		rest = rest.slice(lm[0].length);
	}
	const attrs: Record<string, string> = {};
	for (const am of rest.matchAll(EDGE_ATTR_RE)) {
		let v = am[2];
		if (v.startsWith('"') && v.endsWith('"')) v = v.slice(1, -1);
		attrs[am[1]] = v;
	}
	return {
		indent: m[1],
		src: m[2],
		srcPort: canonPort(m[3]),
		sym: m[4],
		dst: m[5],
		dstPort: canonPort(m[6]),
		label,
		attrs,
		form: 'inline'
	};
}

function parseConnectorLineEdge(line: string): EdgeParts | null {
	const m = line.match(CONNECTOR_LINE_RE);
	if (!m) return null;
	const indent = m[1];
	const keyword = m[2] as ConnectorKeyword;
	const connectorName = m[3] ?? undefined;
	const body = m[4] ?? '';

	const preset = CONNECTOR_KEYWORD_PRESETS[keyword];
	let src = '';
	let srcPort: string | null = null;
	let dst = '';
	let dstPort: string | null = null;
	let label: string | null = null;
	let kindName = preset.kind;
	const attrs: Record<string, string> = { end: preset.tip };

	EDGE_CONNECTOR_ATTR_RE.lastIndex = 0;
	let am: RegExpExecArray | null;
	while ((am = EDGE_CONNECTOR_ATTR_RE.exec(body)) !== null) {
		const key = am[1].toLowerCase();
		const rawV = am[2];
		const v = rawV.startsWith('"') ? joinLabelParts(rawV) : rawV;
		if (key === 'from' || key === 'source' || key === 'origin') {
			const vLow = v.toLowerCase();
			// Bare port word only if source is already set (block-form
			// legacy). In bracket form src starts empty, so every `from:`
			// is treated as a node ref.
			if (!v.includes('@') && PORT_ALIASES[vLow] && src) {
				srcPort = PORT_ALIASES[vLow];
			} else {
				const atIdx = v.indexOf('@');
				const name = atIdx < 0 ? v : v.slice(0, atIdx);
				const port = atIdx < 0 ? '' : v.slice(atIdx + 1);
				if (name) src = name;
				if (port) srcPort = canonPort(port);
			}
		} else if (key === 'to' || key === 'target' || key === 'destination') {
			const vLow = v.toLowerCase();
			if (!v.includes('@') && PORT_ALIASES[vLow] && dst) {
				dstPort = PORT_ALIASES[vLow];
			} else {
				const atIdx = v.indexOf('@');
				const name = atIdx < 0 ? v : v.slice(0, atIdx);
				const port = atIdx < 0 ? '' : v.slice(atIdx + 1);
				if (name) dst = name;
				if (port) dstPort = canonPort(port);
			}
		} else if (
			key === 'from_anchor' ||
			key === 'from_port' ||
			key === 'source_anchor' ||
			key === 'source_port' ||
			key === 'origin_anchor'
		) {
			srcPort = canonPort(v);
		} else if (
			key === 'to_anchor' ||
			key === 'to_port' ||
			key === 'target_anchor' ||
			key === 'target_port' ||
			key === 'destination_anchor'
		) {
			dstPort = canonPort(v);
		} else if (key === 'label') {
			label = v;
		} else if (key === 'kind') {
			if (EDGE_KIND_SYM[v.toLowerCase()]) kindName = v.toLowerCase();
		} else if (key === 'tip') {
			attrs.end = v.toLowerCase();
		} else if (key === 'back') {
			attrs.start = v.toLowerCase();
		} else {
			attrs[key] = v;
		}
	}

	if (!src || !dst) return null;

	return {
		indent,
		src,
		srcPort,
		sym: EDGE_KIND_SYM[kindName] ?? '->',
		dst,
		dstPort,
		label,
		attrs,
		form: 'connector',
		connectorName
	};
}

function parseEdgeLine(line: string): EdgeParts | null {
	return parseInlineEdgeLine(line) ?? parseConnectorLineEdge(line);
}

function rebuildConnectorLine(p: EdgeParts): string {
	const kindName = EDGE_SYM_KIND[p.sym] ?? 'solid';
	// Prefer the kind-keyword bracket form (`[arrow]`, `[dashed_arrow]`,
	// `[line]`, `[dotted_line]`) — the keyword itself names the line
	// style, which reads more naturally than a redundant `kind:` field.
	const keyword = KIND_TO_KEYWORD[kindName] ?? 'connector';
	const bits: string[] = [`[${keyword}]`];
	if (p.connectorName) bits.push(p.connectorName);
	bits.push(`from:${p.src}`);
	bits.push(`from_anchor:${ANCHOR_LONG[p.srcPort ?? ''] ?? 'bottom'}`);
	bits.push(`to:${p.dst}`);
	bits.push(`to_anchor:${ANCHOR_LONG[p.dstPort ?? ''] ?? 'top'}`);
	bits.push(`tip:${p.attrs.end || 'none'}`);
	bits.push(`back:${p.attrs.start || 'none'}`);
	for (const [k, v] of Object.entries(p.attrs)) {
		if (k === 'end' || k === 'start' || k === 'name') continue;
		if (v === '' || v == null) continue;
		const needsQuote = /\s|,/.test(v) || v === '';
		bits.push(`${k}:${needsQuote ? `"${v}"` : v}`);
	}
	if (p.label && p.label.length > 0) bits.push(`label:${formatLabel(p.label)}`);
	return `${p.indent}${bits.join(' ')}`;
}

// Short port name → long anchor word used in the verbose bracket form.
const ANCHOR_LONG: Record<string, string> = {
	t: 'top', b: 'bottom', l: 'left', r: 'right'
};

function rebuildEdgeLine(p: EdgeParts): string {
	if (p.form === 'connector') return rebuildConnectorLine(p);
	const srcPart = p.srcPort ? `${p.src}@${p.srcPort}` : p.src;
	const dstPart = p.dstPort ? `${p.dst}@${p.dstPort}` : p.dst;
	let line = `${p.indent}${srcPart} ${p.sym} ${dstPart}`;
	const tailBits: string[] = [];
	if (p.label && p.label.length > 0) tailBits.push(formatLabel(p.label));
	for (const [k, v] of Object.entries(p.attrs)) {
		if (v === '' || v == null) continue;
		const needsQuote = /\s|,/.test(v) || v === '';
		tailBits.push(`${k}:${needsQuote ? `"${v}"` : v}`);
	}
	if (tailBits.length) line += ` : ${tailBits.join(' ')}`;
	return line;
}

function findEdgeLineIndexByOrdinal(source: string, ordinal: number): number {
	const lines = source.split('\n');
	let seen = 0;
	for (let i = 0; i < lines.length; i++) {
		if (isEdgeLine(lines[i])) {
			if (seen === ordinal) return i;
			seen += 1;
		}
	}
	return -1;
}

function modifyEdgeLine(
	source: string,
	ordinal: number,
	modify: (parts: EdgeParts) => EdgeParts | null
): string {
	const idx = findEdgeLineIndexByOrdinal(source, ordinal);
	if (idx < 0) return source;
	const lines = source.split('\n');
	// Refuse to touch block-form edges — the body spans multiple lines
	// and rewriting only the header would silently drop the body's attrs.
	// Authors editing block-form edges do it directly in the DSL.
	if (EDGE_BLOCK_HEADER_RE.test(lines[idx]) && !EDGE_LINE_RE.test(lines[idx])) {
		return source;
	}
	const parts = parseEdgeLine(lines[idx]);
	if (!parts) return source;
	const out = modify(parts);
	if (out === null) {
		lines.splice(idx, 1);
	} else {
		lines[idx] = rebuildEdgeLine(out);
	}
	return lines.join('\n');
}

export function setEdgeLabel(source: string, ordinal: number, label: string): string {
	return modifyEdgeLine(source, ordinal, (p) => ({ ...p, label: label || null }));
}

export function setEdgeKind(source: string, ordinal: number, kind: string): string {
	const sym = EDGE_KIND_SYM[kind];
	if (!sym) return source;
	return modifyEdgeLine(source, ordinal, (p) => ({ ...p, sym }));
}

export function setEdgePort(
	source: string,
	ordinal: number,
	which: 'source' | 'target',
	port: string | null
): string {
	const clean = canonPort(port);
	return modifyEdgeLine(source, ordinal, (p) =>
		which === 'source'
			? { ...p, srcPort: clean }
			: { ...p, dstPort: clean }
	);
}

export function setEdgeAttr(
	source: string,
	ordinal: number,
	key: string,
	value: string | null
): string {
	return modifyEdgeLine(source, ordinal, (p) => {
		const attrs = { ...p.attrs };
		if (value == null || value === '') delete attrs[key];
		else attrs[key] = value;
		return { ...p, attrs };
	});
}

export function removeEdge(source: string, ordinal: number): string {
	return modifyEdgeLine(source, ordinal, () => null);
}

// --- swimlane / box / group / note editing ----------------------------------

const SWIMLANE_OPEN_RE = /^(\s*)swimlane\s+"([^"]+)"\s*\{\s*$/;
// Captures: 1=indent 2=label 3=optional-style-block-contents (inside {})
const BOX_OPEN_RE = /^(\s*)box\s+"([^"]+)"\s*(?:\{([^{}]*)\})?\s*\{\s*$/;
const GROUP_LINE_RE = /^(\s*)group\s+"([^"]+)"\s*\{(.*)\}\s*$/;
const NOTE_LINE_RE = new RegExp(
	'^(\\s*)note\\s+(' + LABEL_SEQ_SRC + ')\\s+\\[(\\w+)\\]\\s*$'
);

function findSwimlaneHeaderIndex(source: string, name: string): number {
	const lines = source.split('\n');
	for (let i = 0; i < lines.length; i++) {
		const m = lines[i].match(SWIMLANE_OPEN_RE);
		if (m && m[2] === name) return i;
	}
	return -1;
}

function findMatchingCloseAt(lines: string[], openIdx: number): number {
	let depth = 1;
	for (let i = openIdx + 1; i < lines.length; i++) {
		const t = lines[i].trim();
		if (t === '}') {
			depth -= 1;
			if (depth === 0) return i;
		} else if (t.endsWith('{')) {
			depth += 1;
		}
	}
	return -1;
}

export function setSwimlaneName(source: string, oldName: string, newName: string): string {
	const trimmed = newName.trim();
	if (!trimmed || trimmed === oldName) return source;
	const lines = source.split('\n');
	const idx = findSwimlaneHeaderIndex(source, oldName);
	if (idx < 0) return source;
	const m = lines[idx].match(SWIMLANE_OPEN_RE);
	if (!m) return source;
	lines[idx] = `${m[1]}swimlane "${trimmed}" {`;
	return lines.join('\n');
}

export function removeSwimlane(source: string, name: string): string {
	const lines = source.split('\n');
	const open = findSwimlaneHeaderIndex(source, name);
	if (open < 0) return source;
	const close = findMatchingCloseAt(lines, open);
	if (close < 0) return source;
	lines.splice(open, close - open + 1);
	return lines.join('\n');
}

function findBoxHeaderIndex(source: string, label: string, swimlane: string | null): number {
	const lines = source.split('\n');
	if (swimlane === null) {
		for (let i = 0; i < lines.length; i++) {
			const m = lines[i].match(BOX_OPEN_RE);
			if (m && m[2] === label) return i;
		}
		return -1;
	}
	const sl = findSwimlaneHeaderIndex(source, swimlane);
	if (sl < 0) return -1;
	const slClose = findMatchingCloseAt(lines, sl);
	for (let i = sl + 1; i < (slClose < 0 ? lines.length : slClose); i++) {
		const m = lines[i].match(BOX_OPEN_RE);
		if (m && m[2] === label) return i;
	}
	return -1;
}

export function setBoxLabel(
	source: string,
	oldLabel: string,
	newLabel: string,
	swimlane: string | null
): string {
	const trimmed = newLabel.trim();
	if (!trimmed || trimmed === oldLabel) return source;
	const lines = source.split('\n');
	const idx = findBoxHeaderIndex(source, oldLabel, swimlane);
	if (idx < 0) return source;
	const m = lines[idx].match(BOX_OPEN_RE);
	if (!m) return source;
	const styleBlock = m[3] ? ` {${m[3]}}` : '';
	lines[idx] = `${m[1]}box "${trimmed}"${styleBlock} {`;
	return lines.join('\n');
}

export function setBoxStyle(
	source: string,
	label: string,
	swimlane: string | null,
	key: 'fill' | 'stroke' | 'text',
	value: string
): string {
	const lines = source.split('\n');
	const idx = findBoxHeaderIndex(source, label, swimlane);
	if (idx < 0) return source;
	const m = lines[idx].match(BOX_OPEN_RE);
	if (!m) return source;
	const style: Record<string, string> = {};
	if (m[3]) {
		for (const pair of m[3].split(',')) {
			const eq = pair.indexOf(':');
			if (eq < 0) continue;
			const k = pair.slice(0, eq).trim();
			const v = pair.slice(eq + 1).trim();
			if (k) style[k] = v;
		}
	}
	if (value.trim() === '') delete style[key];
	else style[key] = value;
	const keys = Object.keys(style);
	const styleBlock = keys.length > 0 ? ` {${keys.map((k) => `${k}: ${style[k]}`).join(', ')}}` : '';
	lines[idx] = `${m[1]}box "${m[2]}"${styleBlock} {`;
	return lines.join('\n');
}

export function removeBox(source: string, label: string, swimlane: string | null): string {
	const lines = source.split('\n');
	const open = findBoxHeaderIndex(source, label, swimlane);
	if (open < 0) return source;
	const close = findMatchingCloseAt(lines, open);
	if (close < 0) return source;
	lines.splice(open, close - open + 1);
	return lines.join('\n');
}

function findGroupLineIndex(source: string, name: string): number {
	const lines = source.split('\n');
	for (let i = 0; i < lines.length; i++) {
		const m = lines[i].match(GROUP_LINE_RE);
		if (m && m[2] === name) return i;
	}
	return -1;
}

export function setGroupName(source: string, oldName: string, newName: string): string {
	const trimmed = newName.trim();
	if (!trimmed || trimmed === oldName) return source;
	const lines = source.split('\n');
	const idx = findGroupLineIndex(source, oldName);
	if (idx < 0) return source;
	const m = lines[idx].match(GROUP_LINE_RE);
	if (!m) return source;
	lines[idx] = `${m[1]}group "${trimmed}" {${m[3]}}`;
	return lines.join('\n');
}

export function removeGroup(source: string, name: string): string {
	const lines = source.split('\n');
	const idx = findGroupLineIndex(source, name);
	if (idx < 0) return source;
	lines.splice(idx, 1);
	return lines.join('\n');
}

function findNoteLineIndexByOrdinal(source: string, ordinal: number): number {
	const lines = source.split('\n');
	let seen = 0;
	for (let i = 0; i < lines.length; i++) {
		if (NOTE_LINE_RE.test(lines[i])) {
			if (seen === ordinal) return i;
			seen += 1;
		}
	}
	return -1;
}

function escapeDslString(s: string): string {
	return s.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n');
}

export function setNoteText(source: string, ordinal: number, text: string): string {
	const lines = source.split('\n');
	const idx = findNoteLineIndexByOrdinal(source, ordinal);
	if (idx < 0) return source;
	const m = lines[idx].match(NOTE_LINE_RE);
	if (!m) return source;
	lines[idx] = `${m[1]}note ${formatLabel(text)} [${m[3]}]`;
	return lines.join('\n');
}

export function setNoteTarget(source: string, ordinal: number, target: string): string {
	const t = target.trim();
	if (!/^\w+$/.test(t)) return source;
	const lines = source.split('\n');
	const idx = findNoteLineIndexByOrdinal(source, ordinal);
	if (idx < 0) return source;
	const m = lines[idx].match(NOTE_LINE_RE);
	if (!m) return source;
	lines[idx] = `${m[1]}note ${m[2]} [${t}]`;
	return lines.join('\n');
}

export function removeNote(source: string, ordinal: number): string {
	const idx = findNoteLineIndexByOrdinal(source, ordinal);
	if (idx < 0) return source;
	const lines = source.split('\n');
	lines.splice(idx, 1);
	return lines.join('\n');
}
