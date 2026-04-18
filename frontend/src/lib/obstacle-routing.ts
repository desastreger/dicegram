export type Point = { x: number; y: number };
export type Rect = { x: number; y: number; w: number; h: number };

function gridKey(c: Point): string {
	return `${c.x},${c.y}`;
}

function manhattan(a: Point, b: Point): number {
	return Math.abs(a.x - b.x) + Math.abs(a.y - b.y);
}

function simplify(path: Point[]): Point[] {
	if (path.length <= 2) return path;
	const out: Point[] = [path[0]];
	for (let i = 1; i < path.length - 1; i++) {
		const a = path[i - 1];
		const b = path[i];
		const c = path[i + 1];
		const dx1 = b.x - a.x;
		const dy1 = b.y - a.y;
		const dx2 = c.x - b.x;
		const dy2 = c.y - b.y;
		if (Math.sign(dx1) === Math.sign(dx2) && Math.sign(dy1) === Math.sign(dy2)) continue;
		out.push(b);
	}
	out.push(path[path.length - 1]);
	return out;
}

function rectContains(r: Rect, p: Point, margin = 0): boolean {
	return (
		p.x >= r.x - margin &&
		p.x <= r.x + r.w + margin &&
		p.y >= r.y - margin &&
		p.y <= r.y + r.h + margin
	);
}

function segmentCrossesRect(a: Point, b: Point, r: Rect): boolean {
	// AABB segment test. Treat segment as axis-aligned (which our routing is).
	if (a.x === b.x) {
		const x = a.x;
		if (x < r.x || x > r.x + r.w) return false;
		const y0 = Math.min(a.y, b.y);
		const y1 = Math.max(a.y, b.y);
		return y1 > r.y && y0 < r.y + r.h;
	}
	if (a.y === b.y) {
		const y = a.y;
		if (y < r.y || y > r.y + r.h) return false;
		const x0 = Math.min(a.x, b.x);
		const x1 = Math.max(a.x, b.x);
		return x1 > r.x && x0 < r.x + r.w;
	}
	return false;
}

/**
 * Compute an orthogonal polyline from start → end that avoids rectangular
 * obstacles, using A* on a coarse grid. Returns world coords; empty array
 * means no improvement over a straight line.
 */
export function routeAround(
	start: Point,
	end: Point,
	obstacles: Rect[],
	cellSize = 20,
	padding = 8
): Point[] {
	if (obstacles.length === 0) return [start, end];

	// Bounding box of everything + margin.
	const xs: number[] = [start.x, end.x];
	const ys: number[] = [start.y, end.y];
	for (const o of obstacles) {
		xs.push(o.x - padding, o.x + o.w + padding);
		ys.push(o.y - padding, o.y + o.h + padding);
	}
	const minX = Math.min(...xs) - 2 * cellSize;
	const minY = Math.min(...ys) - 2 * cellSize;
	const maxX = Math.max(...xs) + 2 * cellSize;
	const maxY = Math.max(...ys) + 2 * cellSize;
	const cols = Math.ceil((maxX - minX) / cellSize) + 1;
	const rows = Math.ceil((maxY - minY) / cellSize) + 1;

	if (cols * rows > 40000) {
		// Grid too large; fall back to straight line.
		return [start, end];
	}

	const toGrid = (p: Point): Point => ({
		x: Math.round((p.x - minX) / cellSize),
		y: Math.round((p.y - minY) / cellSize)
	});
	const toWorld = (c: Point): Point => ({
		x: minX + c.x * cellSize,
		y: minY + c.y * cellSize
	});

	const blocked = new Set<string>();
	for (const o of obstacles) {
		const c0 = Math.floor((o.x - padding - minX) / cellSize);
		const c1 = Math.ceil((o.x + o.w + padding - minX) / cellSize);
		const r0 = Math.floor((o.y - padding - minY) / cellSize);
		const r1 = Math.ceil((o.y + o.h + padding - minY) / cellSize);
		for (let c = c0; c <= c1; c++) {
			for (let r = r0; r <= r1; r++) {
				blocked.add(`${c},${r}`);
			}
		}
	}

	const s = toGrid(start);
	const t = toGrid(end);
	blocked.delete(gridKey(s));
	blocked.delete(gridKey(t));

	// Direct straight shot first.
	const straight: Point[] = [start, end];
	let clear = true;
	for (const o of obstacles) {
		if (segmentCrossesRect(straight[0], straight[1], o)) {
			clear = false;
			break;
		}
	}
	if (clear) return straight;

	// A* (Manhattan).
	type Open = { c: Point; f: number; g: number };
	const open: Open[] = [{ c: s, f: manhattan(s, t), g: 0 }];
	const cameFrom = new Map<string, Point>();
	const gScore = new Map<string, number>();
	gScore.set(gridKey(s), 0);

	const neighbors: Point[] = [
		{ x: 1, y: 0 },
		{ x: -1, y: 0 },
		{ x: 0, y: 1 },
		{ x: 0, y: -1 }
	];

	const maxIter = 4000;
	let iter = 0;
	while (open.length && iter++ < maxIter) {
		open.sort((a, b) => a.f - b.f);
		const { c: cur, g } = open.shift()!;
		if (cur.x === t.x && cur.y === t.y) {
			const path: Point[] = [];
			let k: Point | undefined = cur;
			while (k) {
				path.unshift(k);
				k = cameFrom.get(gridKey(k));
			}
			const simplified = simplify(path);
			const worldPath = simplified.map(toWorld);
			// Anchor endpoints back to exact start/end.
			if (worldPath.length > 0) {
				worldPath[0] = start;
				worldPath[worldPath.length - 1] = end;
			}
			return worldPath;
		}
		for (const d of neighbors) {
			const n = { x: cur.x + d.x, y: cur.y + d.y };
			if (n.x < 0 || n.x >= cols || n.y < 0 || n.y >= rows) continue;
			if (blocked.has(gridKey(n))) continue;
			const tentative = g + 1;
			if (tentative < (gScore.get(gridKey(n)) ?? Infinity)) {
				gScore.set(gridKey(n), tentative);
				cameFrom.set(gridKey(n), cur);
				open.push({ c: n, f: tentative + manhattan(n, t), g: tentative });
			}
		}
	}
	return [start, end];
}

/** Render an orthogonal polyline as an SVG path with rounded corners. */
export function polylineToPath(points: Point[], radius = 8): string {
	if (points.length < 2) return '';
	if (points.length === 2) {
		return `M ${points[0].x} ${points[0].y} L ${points[1].x} ${points[1].y}`;
	}
	const out: string[] = [`M ${points[0].x} ${points[0].y}`];
	for (let i = 1; i < points.length - 1; i++) {
		const prev = points[i - 1];
		const cur = points[i];
		const next = points[i + 1];
		const dx1 = cur.x - prev.x;
		const dy1 = cur.y - prev.y;
		const len1 = Math.abs(dx1) + Math.abs(dy1);
		const dx2 = next.x - cur.x;
		const dy2 = next.y - cur.y;
		const len2 = Math.abs(dx2) + Math.abs(dy2);
		const r = Math.min(radius, len1 / 2, len2 / 2);
		const ax = cur.x - Math.sign(dx1) * r;
		const ay = cur.y - Math.sign(dy1) * r;
		const bx = cur.x + Math.sign(dx2) * r;
		const by = cur.y + Math.sign(dy2) * r;
		out.push(`L ${ax} ${ay}`);
		out.push(`Q ${cur.x} ${cur.y} ${bx} ${by}`);
	}
	const last = points[points.length - 1];
	out.push(`L ${last.x} ${last.y}`);
	return out.join(' ');
}
