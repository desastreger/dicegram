// Deterministic SVG-path generation for edges produced by the backend
// route planner. The planner hands us a polyline; this module renders it
// with soft corners — small arcs at every bend instead of sharp 90°
// joints, which reads as a more humane and intentional aesthetic.

export type Point = { x: number; y: number };

/**
 * Emit an SVG path string for `points`, rounding every interior corner
 * with a quarter-arc of `radius` px. Endpoints stay sharp because we
 * want the arrow tip flush with the target face. The arc is sized down
 * automatically when adjacent segments are too short to fit the full
 * radius (otherwise the arc would overshoot the next vertex).
 */
export function roundedPolylinePath(points: Point[], radius = 6): string {
	const cleaned = collapseRedundant(points);
	if (cleaned.length < 2) return '';
	if (cleaned.length === 2) {
		const [a, b] = cleaned;
		return `M ${a.x} ${a.y} L ${b.x} ${b.y}`;
	}
	const parts: string[] = [`M ${cleaned[0].x} ${cleaned[0].y}`];
	for (let i = 1; i < cleaned.length - 1; i++) {
		const prev = cleaned[i - 1];
		const cur = cleaned[i];
		const next = cleaned[i + 1];
		// Direction vectors entering and leaving this corner. Both are
		// axis-aligned because the planner only emits orthogonal
		// polylines, so each is purely horizontal or purely vertical.
		const inDx = Math.sign(cur.x - prev.x);
		const inDy = Math.sign(cur.y - prev.y);
		const outDx = Math.sign(next.x - cur.x);
		const outDy = Math.sign(next.y - cur.y);
		// Collinear (no corner) → straight line, no arc.
		if (inDx === outDx && inDy === outDy) {
			parts.push(`L ${cur.x} ${cur.y}`);
			continue;
		}
		// Clamp the radius so it never exceeds half of either adjacent
		// segment. Otherwise short segments produce overshoot arcs that
		// fold back on themselves.
		const inLen = Math.abs(cur.x - prev.x) + Math.abs(cur.y - prev.y);
		const outLen = Math.abs(next.x - cur.x) + Math.abs(next.y - cur.y);
		const r = Math.max(0, Math.min(radius, inLen / 2, outLen / 2));
		if (r < 0.5) {
			// Degenerate corner — fall back to a sharp joint.
			parts.push(`L ${cur.x} ${cur.y}`);
			continue;
		}
		// Arc start sits `r` back along the incoming segment from the
		// corner; arc end sits `r` forward along the outgoing segment.
		const ax = cur.x - inDx * r;
		const ay = cur.y - inDy * r;
		const bx = cur.x + outDx * r;
		const by = cur.y + outDy * r;
		// Sweep flag = 1 for clockwise turns, 0 for anti-clockwise.
		// Cross product of (in) × (out) tells us the turn direction.
		const cross = inDx * outDy - inDy * outDx;
		const sweep = cross > 0 ? 1 : 0;
		parts.push(`L ${ax} ${ay}`);
		parts.push(`A ${r} ${r} 0 0 ${sweep} ${bx} ${by}`);
	}
	const last = cleaned[cleaned.length - 1];
	parts.push(`L ${last.x} ${last.y}`);
	return parts.join(' ');
}

/**
 * Drop consecutive-duplicate points and any midpoint that lies on the
 * line between its neighbours. Two passes so a chain of redundancies
 * fully collapses (e.g., the planner sometimes emits an extra point at
 * the same coord as a neighbour for explicitness).
 */
function collapseRedundant(points: Point[]): Point[] {
	const dedup: Point[] = [];
	for (const p of points) {
		const last = dedup[dedup.length - 1];
		if (!last || Math.abs(p.x - last.x) > 0.5 || Math.abs(p.y - last.y) > 0.5) {
			dedup.push(p);
		}
	}
	if (dedup.length < 3) return dedup;
	let cur = dedup;
	for (let pass = 0; pass < 4; pass++) {
		const next: Point[] = [cur[0]];
		let changed = false;
		for (let i = 1; i < cur.length - 1; i++) {
			const a = next[next.length - 1];
			const b = cur[i];
			const c = cur[i + 1];
			const collinearV = Math.abs(a.x - b.x) < 0.5 && Math.abs(b.x - c.x) < 0.5;
			const collinearH = Math.abs(a.y - b.y) < 0.5 && Math.abs(b.y - c.y) < 0.5;
			if (collinearV || collinearH) {
				changed = true;
				continue;
			}
			next.push(b);
		}
		next.push(cur[cur.length - 1]);
		if (!changed) return next;
		cur = next;
	}
	return cur;
}
