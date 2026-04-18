let getterImpl: (() => { x: number; y: number } | null) | null = null;

export function setViewportCenterGetter(fn: (() => { x: number; y: number } | null) | null) {
	getterImpl = fn;
}

export function getViewportCenter(): { x: number; y: number } | null {
	return getterImpl ? getterImpl() : null;
}
