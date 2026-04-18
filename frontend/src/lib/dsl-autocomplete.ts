import {
	autocompletion,
	type Completion,
	type CompletionContext,
	type CompletionResult
} from '@codemirror/autocomplete';

const KEYWORDS = ['direction', 'setting', 'swimlane', 'box', 'group', 'note'];
const DIRECTIONS = [
	'top-to-bottom',
	'left-to-right',
	'bottom-to-top',
	'right-to-left'
];
const SETTINGS = [
	'color_scheme',
	'snap_grid',
	'node_width',
	'node_height',
	'h_gap',
	'v_gap',
	'swimlane_gap',
	'container_padding',
	'auto_capitalize',
	'show_step_bands'
];
const COLOR_SCHEMES = [
	'default-dark',
	'light',
	'solarized-dark',
	'solarized-light',
	'dracula',
	'gruvbox',
	'high-contrast'
];
const SHAPES = [
	'rect',
	'rounded',
	'diamond',
	'circle',
	'parallelogram',
	'hexagon',
	'cylinder',
	'stadium'
];
const TYPES = [
	'process',
	'decision',
	'input',
	'output',
	'datastore',
	'start',
	'end',
	'manual',
	'automated',
	'approval',
	'external'
];
const STATUSES = ['draft', 'active', 'blocked', 'deprecated', 'complete'];
const PRIORITIES = ['low', 'medium', 'high', 'critical'];
const ATTR_KEYS = [
	'step',
	'type',
	'owner',
	'status',
	'priority',
	'tags',
	'width',
	'height',
	'id',
	'condition',
	'weight'
];

function asCompletion(list: string[], type: string): Completion[] {
	return list.map((label) => ({ label, type }));
}

function collectDeclared(src: string): string[] {
	const set = new Set<string>();
	const re = /^\s*\[(?:rect|rounded|diamond|circle|parallelogram|hexagon|cylinder|stadium)\]\s+(\w+)\s+"/gm;
	let m: RegExpExecArray | null;
	while ((m = re.exec(src)) !== null) set.add(m[1]);
	return [...set];
}

function inString(text: string): boolean {
	// Count un-escaped quotes in `text`; odd count = we're inside a string.
	let count = 0;
	for (let i = 0; i < text.length; i++) {
		const c = text[i];
		if (c === '\\' && i + 1 < text.length) {
			i++;
			continue;
		}
		if (c === '"') count++;
	}
	return count % 2 === 1;
}

function dslCompletion(ctx: CompletionContext): CompletionResult | null {
	const before = ctx.matchBefore(/[\w-]*/);
	if (!before || (before.from === before.to && !ctx.explicit)) return null;

	const line = ctx.state.doc.lineAt(ctx.pos);
	const textBefore = line.text.slice(0, ctx.pos - line.from);

	// Never suggest inside a quoted string (label text) or a line comment.
	if (inString(textBefore) || textBefore.includes('//')) return null;

	// attribute-value completion: `type:pro|` or `status:ac|`
	const attrMatch = /(\w+):([\w-]*)$/.exec(textBefore);
	if (attrMatch) {
		const key = attrMatch[1];
		const valueStart = ctx.pos - attrMatch[2].length;
		if (key === 'type') return { from: valueStart, options: asCompletion(TYPES, 'enum') };
		if (key === 'status') return { from: valueStart, options: asCompletion(STATUSES, 'enum') };
		if (key === 'priority')
			return { from: valueStart, options: asCompletion(PRIORITIES, 'enum') };
	}

	// direction values
	const dirMatch = /^\s*direction\s+([\w-]*)$/.exec(textBefore);
	if (dirMatch) {
		return {
			from: ctx.pos - dirMatch[1].length,
			options: asCompletion(DIRECTIONS, 'enum')
		};
	}

	// setting keys
	const setMatch = /^\s*setting\s+([\w-]*)$/.exec(textBefore);
	if (setMatch) {
		return {
			from: ctx.pos - setMatch[1].length,
			options: asCompletion(SETTINGS, 'property')
		};
	}

	// setting color_scheme values
	const schemeMatch = /^\s*setting\s+color_scheme\s+([\w-]*)$/.exec(textBefore);
	if (schemeMatch) {
		return {
			from: ctx.pos - schemeMatch[1].length,
			options: asCompletion(COLOR_SCHEMES, 'enum')
		};
	}

	// shape brackets
	const shapeMatch = /\[(\w*)$/.exec(textBefore);
	if (shapeMatch) {
		return {
			from: ctx.pos - shapeMatch[1].length,
			options: asCompletion(SHAPES, 'class')
		};
	}

	// identifier-position: top-of-line, no shape bracket yet
	if (/^\s*$/.test(line.text.slice(0, before.from - line.from))) {
		return {
			from: before.from,
			options: asCompletion(KEYWORDS, 'keyword')
		};
	}

	// general: node names (for edges) + attr keys + keywords
	const declared = collectDeclared(ctx.state.doc.toString());
	const opts: Completion[] = [
		...asCompletion(declared, 'variable'),
		...ATTR_KEYS.map((k) => ({ label: `${k}:`, type: 'property' }))
	];
	return { from: before.from, options: opts };
}

export function dslAutocomplete() {
	return autocompletion({ override: [dslCompletion], activateOnTyping: true });
}
