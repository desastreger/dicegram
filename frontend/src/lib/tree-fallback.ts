import type { RenderResult, TreeEntry } from './render';

/**
 * Build a client-side scene tree when the backend render response lacks
 * `tree` (e.g. older backend version). The shape is identical to what
 * `backend/app/dsl/tree.py` produces.
 */
export function buildTreeFallback(result: RenderResult): TreeEntry[] {
	const out: TreeEntry[] = [];
	const byId = new Map<string, TreeEntry>();
	const root: TreeEntry = {
		id: '__root__',
		kind: 'root',
		label: '(root)',
		parent: null,
		children: []
	};
	out.push(root);
	byId.set(root.id, root);

	for (const l of result.lanes ?? []) {
		const id = `swimlane:${l.name}`;
		const entry: TreeEntry = {
			id,
			kind: 'swimlane',
			label: l.name,
			parent: root.id,
			children: []
		};
		out.push(entry);
		byId.set(id, entry);
		root.children.push(id);
	}

	for (const b of result.boxes ?? []) {
		const parentId = b.swimlane ? `swimlane:${b.swimlane}` : root.id;
		const id = `box:${b.swimlane ?? ''}::${b.label}`;
		const entry: TreeEntry = {
			id,
			kind: 'box',
			label: b.label,
			parent: parentId,
			children: []
		};
		out.push(entry);
		byId.set(id, entry);
		byId.get(parentId)?.children.push(id);
	}

	for (const n of result.nodes ?? []) {
		let parentId = root.id;
		if (n.box) {
			const candidate = `box:${n.swimlane ?? ''}::${n.box}`;
			if (byId.has(candidate)) parentId = candidate;
			else if (n.swimlane && byId.has(`swimlane:${n.swimlane}`))
				parentId = `swimlane:${n.swimlane}`;
		} else if (n.swimlane && byId.has(`swimlane:${n.swimlane}`)) {
			parentId = `swimlane:${n.swimlane}`;
		}
		const entry: TreeEntry = {
			id: n.id,
			kind: 'shape',
			label: n.id,
			parent: parentId,
			children: [],
			shape: n.shape
		};
		out.push(entry);
		byId.set(n.id, entry);
		byId.get(parentId)?.children.push(n.id);
	}

	for (const g of result.groups ?? []) {
		const id = `group:${g.name}`;
		const entry: TreeEntry = {
			id,
			kind: 'group',
			label: g.name,
			parent: root.id,
			children: []
		};
		out.push(entry);
		byId.set(id, entry);
		root.children.push(id);
	}

	for (let i = 0; i < (result.notes ?? []).length; i++) {
		const note = result.notes[i];
		const id = `note:${i}`;
		const entry: TreeEntry = {
			id,
			kind: 'note',
			label: note.text.split('\n')[0].slice(0, 40) || '(note)',
			parent: root.id,
			children: []
		};
		out.push(entry);
		byId.set(id, entry);
		root.children.push(id);
	}

	for (let i = 0; i < (result.edges ?? []).length; i++) {
		const e = result.edges[i];
		const id = `edge:${i}`;
		const entry: TreeEntry = {
			id,
			kind: 'edge',
			label: `${e.source} → ${e.target}`,
			parent: root.id,
			children: []
		};
		out.push(entry);
		byId.set(id, entry);
		root.children.push(id);
	}

	return out;
}
