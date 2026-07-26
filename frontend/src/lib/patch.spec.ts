import { describe, it, expect } from 'vitest';
import {
	setNodeName,
	removeNode,
	setNodePosition,
	setNodeAttr,
	setDirection,
	setEdgeLabel,
	setEdgeKind,
	parseNodeLine,
	serializeNodeLine
} from './patch';

// --- Finding 1: bidirectional edge kind survives an inspector edit ---------

describe('bidirectional edge kind (finding 1)', () => {
	it('[bidirectional] bracket connector keeps its kind after an unrelated edit', () => {
		const src = '[bidirectional] from:a to:b';
		const out = setEdgeLabel(src, 0, 'hello');
		expect(out).toContain('[bidirectional]');
		expect(out).not.toMatch(/\[connector\]/);
		expect(out).toContain('label:"hello"');
	});

	it('[connector] kind:bidirectional survives round-tripping through a label edit', () => {
		const src = '[connector] from:a to:b kind:bidirectional';
		const out = setEdgeLabel(src, 0, 'x');
		// Either an explicit kind: field or the dedicated bracket keyword is
		// acceptable, as long as the kind itself is preserved (not dropped
		// to solid).
		expect(out).toMatch(/\[bidirectional\]|kind:bidirectional/);
		expect(out).not.toMatch(/\bkind:solid\b/);
	});

	it('inline `<->` symbol is recognized as an edge line and round-trips', () => {
		const src = 'a <-> b';
		const out = setEdgeLabel(src, 0, 'both ways');
		expect(out).toContain('<->');
		expect(out).toContain('"both ways"');
	});

	it('setEdgeKind can switch an edge TO bidirectional and it survives a second edit', () => {
		const src = 'a -> b';
		const bidi = setEdgeKind(src, 0, 'bidirectional');
		expect(bidi).toContain('<->');
		const relabeled = setEdgeLabel(bidi, 0, 'x');
		expect(relabeled).toContain('<->');
	});
});

// --- Finding 2: setNodeName rewrites every reference ------------------------

describe('setNodeName rewrites references (finding 2)', () => {
	it('rewrites the definition and an inline edge endpoint', () => {
		const src = '[rect] a "A"\n[rect] b "B"\na -> b';
		const out = setNodeName(src, 'a', 'z');
		expect(out).toContain('[rect] z "A"');
		expect(out).toContain('z -> b');
		expect(out).not.toMatch(/\ba\b/);
	});

	it('rewrites the destination side of an inline edge', () => {
		const src = '[rect] a "A"\n[rect] b "B"\nb -> a';
		const out = setNodeName(src, 'a', 'z');
		expect(out).toContain('b -> z');
	});

	it('does not touch a same-named token inside a quoted label', () => {
		const src = '[rect] a "A"\n[rect] x "X"\n[rect] y "Y"\nx -> y : "call a now"';
		const out = setNodeName(src, 'a', 'z');
		expect(out).toContain('[rect] z "A"');
		expect(out).toContain('x -> y : "call a now"');
	});

	it('rewrites a block-form edge header', () => {
		const src = '[rect] a "A"\n[rect] b "B"\nedge a -> b {\n\tlabel: "x"\n}\n';
		const out = setNodeName(src, 'a', 'z');
		expect(out).toContain('edge z -> b {');
		expect(out).toContain('label: "x"');
	});

	it('rewrites [connector] from:/to: fields', () => {
		const src = '[rect] a "A"\n[rect] b "B"\n[connector] from:a to:b';
		const out = setNodeName(src, 'a', 'z');
		expect(out).toContain('from:z');
		expect(out).toContain('to:b');
	});

	it('rewrites a note target (bracket form)', () => {
		const src = '[rect] a "A"\n[note] "reminder" target:a';
		const out = setNodeName(src, 'a', 'z');
		expect(out).toContain('target:z');
	});

	it('rewrites a note target (legacy form)', () => {
		const src = '[rect] a "A"\nnote "reminder" [a]';
		const out = setNodeName(src, 'a', 'z');
		expect(out).toContain('note "reminder" [z]');
	});
});

// --- Finding 3: removeNode drops whole blocks and avoids false positives ---

describe('removeNode (finding 3)', () => {
	it('removes an entire block-form edge (header + body + closing brace)', () => {
		const src = '[rect] a "A"\n[rect] b "B"\nedge a -> b {\n\tlabel: "x"\n}\n';
		const out = removeNode(src, 'a');
		expect(out).not.toContain('[rect] a "A"');
		expect(out).not.toContain('edge a -> b {');
		expect(out).not.toContain('label: "x"');
		// No dangling closing brace left behind.
		const closingBraces = (out.match(/^\s*}\s*$/gm) ?? []).length;
		expect(closingBraces).toBe(0);
		expect(out).toContain('[rect] b "B"');
	});

	it('does not delete an unrelated edge whose label merely contains the id as a word', () => {
		const src = '[rect] a "A"\n[rect] x "X"\n[rect] y "Y"\nx -> y : "call a now"';
		const out = removeNode(src, 'a');
		expect(out).not.toContain('[rect] a "A"');
		expect(out).toContain('x -> y : "call a now"');
	});

	it('still removes an inline edge that genuinely references the deleted node', () => {
		const src = '[rect] a "A"\n[rect] b "B"\na -> b';
		const out = removeNode(src, 'a');
		expect(out).not.toContain('a -> b');
		expect(out).toContain('[rect] b "B"');
	});

	it('removes a [connector] edge referencing the deleted node', () => {
		const src = '[rect] a "A"\n[rect] b "B"\n[connector] from:a to:b';
		const out = removeNode(src, 'a');
		expect(out).not.toMatch(/from:a\b/);
	});

	it('removes a note that targets the deleted node', () => {
		const src = '[rect] a "A"\n[note] "reminder" target:a';
		const out = removeNode(src, 'a');
		expect(out).not.toContain('target:a');
	});
});

// --- Finding 4: serializeNodeLine preserves comments & quoted braces -------

describe('serializeNodeLine losslessness (finding 4)', () => {
	it('keeps a trailing // comment across a position edit', () => {
		const src = '[rect] a "A" step:1 // note';
		const out = setNodePosition(src, 'a', 5, 6);
		expect(out).toContain('// note');
		expect(out).toContain('@(5, 6)');
		expect(out).toContain('step:1');
	});

	it('keeps a trailing // comment across a label-only round trip via parse/serialize', () => {
		const src = '[rect] a "A" // trailing comment';
		const parts = parseNodeLine(src);
		expect(parts?.trailing).toBe('// trailing comment');
		expect(serializeNodeLine(parts!)).toBe(src);
	});

	it('survives a position patch when an attr value contains braces inside quotes', () => {
		const src = '[rect] a "A" owner:"team {x}"';
		const out = setNodePosition(src, 'a', 1, 2);
		expect(out).toContain('owner:"team {x}"');
		expect(out).toContain('@(1, 2)');
		// Must not have been misparsed as a style block.
		const parts = parseNodeLine(src);
		expect(parts?.style).toEqual({});
		expect(parts?.attrs.owner).toBe('team {x}');
	});

	it('a real style block still parses and round-trips normally', () => {
		const src = '[rect] a "A" {fill: red, stroke: blue}';
		const out = setNodeAttr(src, 'a', 'step', '2');
		expect(out).toContain('{fill: red, stroke: blue}');
		expect(out).toContain('step:2');
	});
});

// --- Finding 12: isEdgeLine / edge-counting agrees with backend grammar ----

describe('edge ordinal counting agrees with backend grammar (finding 12)', () => {
	it('counts a no-space inline edge (a->b) as an edge', () => {
		const src = 'a->b';
		const out = setEdgeLabel(src, 0, 'x');
		expect(out).toContain('"x"');
	});

	it('addresses the correct edge among mixed spaced / unspaced / connector forms', () => {
		const src = ['a->b', 'b -> c', '[connector] from:c to:d'].join('\n');
		const out = setEdgeLabel(src, 2, 'third');
		const lines = out.split('\n');
		expect(lines[0]).toBe('a->b');
		expect(lines[1]).toBe('b -> c');
		expect(lines[2]).toContain('label:"third"');
	});

	it('does not count an incomplete [connector] line (no from:/to: yet) as an edge', () => {
		const src = ['[connector]', 'a -> b'].join('\n');
		const out = setEdgeLabel(src, 0, 'real edge');
		// Ordinal 0 must land on the real `a -> b` edge, not the incomplete
		// connector stub above it.
		expect(out.split('\n')[1]).toContain('"real edge"');
		expect(out.split('\n')[0]).toBe('[connector]');
	});
});

// --- Finding 13: misc small correctness fixes -------------------------------

describe('setDirection is string/comment aware (finding 13a)', () => {
	it('does not strip a literal @(x,y) inside a quoted label', () => {
		const src = 'direction top-to-bottom\n[rect] a "Meet @(3,4) later"';
		const out = setDirection(src, 'left-to-right');
		expect(out).toContain('"Meet @(3,4) later"');
	});

	it('does not rewrite from_anchor-looking text inside a comment', () => {
		const src =
			'direction top-to-bottom\n[rect] a "A"\n[rect] b "B"\na -> b // from_anchor:bottom looks nice';
		const out = setDirection(src, 'left-to-right');
		expect(out).toContain('// from_anchor:bottom looks nice');
	});

	it('still flips a real from_anchor/to_anchor pair on a connector', () => {
		const src =
			'direction top-to-bottom\n[rect] a "A"\n[rect] b "B"\n[connector] from:a from_anchor:bottom to:b to_anchor:top';
		const out = setDirection(src, 'left-to-right');
		expect(out).toContain('from_anchor:right');
		expect(out).toContain('to_anchor:left');
	});
});

describe('setEdgeKind clears a stale arrowhead on arrowless kinds (finding 13b)', () => {
	it('drops an inherited tip:arrow when switching to dotted_line (no arrow)', () => {
		const src = '[connector] from:a to:b kind:solid';
		const dotted = setEdgeKind(src, 0, 'dotted_line');
		expect(dotted).toContain('tip:none');
		expect(dotted).not.toContain('tip:arrow');
	});
});

describe('anchorless bracket connectors are not forced to gain anchors (finding 13c)', () => {
	it('an edit to a connector with no anchors does not inject from_anchor/to_anchor', () => {
		const src = '[connector] from:a to:b';
		const out = setEdgeLabel(src, 0, 'hi');
		expect(out).not.toContain('from_anchor');
		expect(out).not.toContain('to_anchor');
	});

	it('an explicit anchor is preserved across an edit', () => {
		const src = '[connector] from:a from_anchor:left to:b';
		const out = setEdgeLabel(src, 0, 'hi');
		expect(out).toContain('from_anchor:left');
		expect(out).not.toContain('to_anchor');
	});
});
