import { Decoration, EditorView, ViewPlugin } from '@codemirror/view';
import type { DecorationSet, ViewUpdate } from '@codemirror/view';

export type NodeRange = { from: number; to: number; id: string };

const SHAPE_SET = new Set([
	'rect',
	'rounded',
	'diamond',
	'circle',
	'parallelogram',
	'hexagon',
	'cylinder',
	'stadium'
]);

const KEYWORD_RE = /^(direction|setting|swimlane|box|group|note)\b/;
const SHAPE_RE = /\[(\w+)\]/g;
const ARROW_RE = /(==>|-->|-\.-|---|->)/g;
const POS_RE = /@\(\s*-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?\s*\)/g;
const ATTR_RE = /\b(\w+):(?=("[^"]*"|\S+))/g;
const STRING_RE = /"(?:[^"\\]|\\.)*"/g;
const IDENT_RE = /\b(\w+)\b/g;
const NODE_DEF_RE = /^(\s*)\[(\w+)\]\s+(\w+)\b/;

function indexOfCommentStart(line: string): number {
	let inStr = false;
	for (let i = 0; i < line.length; i++) {
		const c = line[i];
		if (c === '\\' && i + 1 < line.length) {
			i++;
			continue;
		}
		if (c === '"') {
			inStr = !inStr;
		} else if (!inStr && c === '/' && line[i + 1] === '/') {
			return i;
		}
	}
	return -1;
}

function collectDeclaredNodes(src: string): Set<string> {
	const out = new Set<string>();
	for (const line of src.split('\n')) {
		const m = NODE_DEF_RE.exec(line);
		if (m && SHAPE_SET.has(m[2])) out.add(m[3]);
	}
	return out;
}

type DecoEntry = { from: number; to: number; cls: string };

export function scanSource(src: string): {
	decorations: DecorationSet;
	ranges: NodeRange[];
} {
	const decos: DecoEntry[] = [];
	const ranges: NodeRange[] = [];
	const declared = collectDeclaredNodes(src);
	const lines = src.split('\n');
	let offset = 0;

	for (const line of lines) {
		const lineStart = offset;
		const commentStart = indexOfCommentStart(line);
		const effLine = commentStart >= 0 ? line.slice(0, commentStart) : line;

		if (commentStart >= 0) {
			decos.push({
				from: lineStart + commentStart,
				to: lineStart + line.length,
				cls: 'tok-comment'
			});
		}

		const strSpans: Array<[number, number]> = [];
		let sm: RegExpExecArray | null;
		STRING_RE.lastIndex = 0;
		while ((sm = STRING_RE.exec(effLine)) !== null) {
			strSpans.push([sm.index, sm.index + sm[0].length]);
			decos.push({
				from: lineStart + sm.index,
				to: lineStart + sm.index + sm[0].length,
				cls: 'tok-string'
			});
		}
		const inString = (i: number) => strSpans.some(([a, b]) => i >= a && i < b);

		const leadingWs = effLine.match(/^\s*/)![0].length;
		const stripped = effLine.slice(leadingWs);
		const kwm = KEYWORD_RE.exec(stripped);
		if (kwm) {
			decos.push({
				from: lineStart + leadingWs,
				to: lineStart + leadingWs + kwm[0].length,
				cls: 'tok-keyword'
			});
		}

		SHAPE_RE.lastIndex = 0;
		let shm: RegExpExecArray | null;
		while ((shm = SHAPE_RE.exec(effLine)) !== null) {
			if (!SHAPE_SET.has(shm[1])) continue;
			decos.push({
				from: lineStart + shm.index,
				to: lineStart + shm.index + shm[0].length,
				cls: 'tok-shape'
			});
		}

		const defM = NODE_DEF_RE.exec(effLine);
		let defNameStart = -1;
		if (defM && SHAPE_SET.has(defM[2])) {
			const after = defM[1].length + defM[2].length + 2;
			defNameStart = effLine.indexOf(defM[3], after);
			if (defNameStart >= 0) {
				const from = lineStart + defNameStart;
				const to = from + defM[3].length;
				decos.push({ from, to, cls: 'tok-ident tok-def' });
				ranges.push({ from, to, id: defM[3] });
			}
		}

		IDENT_RE.lastIndex = 0;
		let im: RegExpExecArray | null;
		while ((im = IDENT_RE.exec(effLine)) !== null) {
			const word = im[1];
			const idx = im.index;
			if (!declared.has(word)) continue;
			if (inString(idx)) continue;
			if (idx > 0 && effLine[idx - 1] === ':') continue;
			if (idx === defNameStart) continue;
			const from = lineStart + idx;
			const to = from + word.length;
			decos.push({ from, to, cls: 'tok-ident tok-ref' });
			ranges.push({ from, to, id: word });
		}

		ARROW_RE.lastIndex = 0;
		let am: RegExpExecArray | null;
		while ((am = ARROW_RE.exec(effLine)) !== null) {
			if (inString(am.index)) continue;
			decos.push({
				from: lineStart + am.index,
				to: lineStart + am.index + am[0].length,
				cls: 'tok-arrow'
			});
		}

		POS_RE.lastIndex = 0;
		let pm: RegExpExecArray | null;
		while ((pm = POS_RE.exec(effLine)) !== null) {
			if (inString(pm.index)) continue;
			decos.push({
				from: lineStart + pm.index,
				to: lineStart + pm.index + pm[0].length,
				cls: 'tok-pos'
			});
		}

		ATTR_RE.lastIndex = 0;
		let amm: RegExpExecArray | null;
		while ((amm = ATTR_RE.exec(effLine)) !== null) {
			if (inString(amm.index)) continue;
			decos.push({
				from: lineStart + amm.index,
				to: lineStart + amm.index + amm[1].length + 1,
				cls: 'tok-attr'
			});
		}

		offset += line.length + 1;
	}

	decos.sort((a, b) => a.from - b.from || a.to - b.to);
	const rendered = decos
		.filter((d) => d.to > d.from)
		.map((d) => Decoration.mark({ class: d.cls }).range(d.from, d.to));

	return {
		decorations: Decoration.set(rendered, true),
		ranges
	};
}

export function dslSyntaxExtension(onNodeClick: (id: string) => void) {
	return ViewPlugin.fromClass(
		class {
			decorations: DecorationSet;
			ranges: NodeRange[];

			constructor(view: EditorView) {
				const r = scanSource(view.state.doc.toString());
				this.decorations = r.decorations;
				this.ranges = r.ranges;
			}

			update(u: ViewUpdate) {
				if (u.docChanged) {
					const r = scanSource(u.state.doc.toString());
					this.decorations = r.decorations;
					this.ranges = r.ranges;
				}
			}
		},
		{
			decorations: (v) => v.decorations,
			eventHandlers: {
				click(e, view) {
					const pos = view.posAtCoords({ x: e.clientX, y: e.clientY });
					if (pos == null) return false;
					for (const r of this.ranges) {
						if (pos >= r.from && pos <= r.to) {
							onNodeClick(r.id);
							return false;
						}
					}
					return false;
				}
			}
		}
	);
}
