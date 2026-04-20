import type { RenderResult } from './render';

async function fetchSvg(source: string): Promise<string> {
	const res = await fetch('/api/export/svg', {
		method: 'POST',
		credentials: 'include',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ source })
	});
	if (!res.ok) throw new Error(`export failed: ${res.status}`);
	return res.text();
}

function triggerDownload(name: string, blob: Blob) {
	const url = URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = name;
	a.click();
	setTimeout(() => URL.revokeObjectURL(url), 1000);
}

type RasterResult = { blob: Blob; dataUrl: string; width: number; height: number };

function svgToRaster(svg: string, scale = 2): Promise<RasterResult> {
	return new Promise((resolve, reject) => {
		const img = new Image();
		const sourceBlob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' });
		const url = URL.createObjectURL(sourceBlob);
		img.onload = () => {
			const w = img.naturalWidth;
			const h = img.naturalHeight;
			const canvas = document.createElement('canvas');
			canvas.width = w * scale;
			canvas.height = h * scale;
			const ctx = canvas.getContext('2d');
			if (!ctx) {
				URL.revokeObjectURL(url);
				reject(new Error('canvas context unavailable'));
				return;
			}
			ctx.scale(scale, scale);
			ctx.drawImage(img, 0, 0);
			URL.revokeObjectURL(url);
			canvas.toBlob((b) => {
				if (!b) {
					reject(new Error('PNG encode failed'));
					return;
				}
				resolve({ blob: b, dataUrl: canvas.toDataURL('image/png'), width: w, height: h });
			}, 'image/png');
		};
		img.onerror = () => {
			URL.revokeObjectURL(url);
			reject(new Error('SVG image load failed'));
		};
		img.src = url;
	});
}

function svgToPngBlob(svg: string): Promise<Blob> {
	return svgToRaster(svg).then((r) => r.blob);
}

function safeName(name: string): string {
	return (name || 'dicegram').trim().replace(/[^\w.-]+/g, '_').replace(/^_+|_+$/g, '') || 'dicegram';
}

export async function downloadSvg(name: string, source: string) {
	const svg = await fetchSvg(source);
	triggerDownload(`${safeName(name)}.svg`, new Blob([svg], { type: 'image/svg+xml' }));
}

export async function downloadPng(name: string, source: string) {
	const svg = await fetchSvg(source);
	const blob = await svgToPngBlob(svg);
	triggerDownload(`${safeName(name)}.png`, blob);
}

export async function downloadPdf(name: string, source: string) {
	const svg = await fetchSvg(source);
	const raster = await svgToRaster(svg, 2);
	const { jsPDF } = await import('jspdf');
	const orientation = raster.width >= raster.height ? 'l' : 'p';
	const doc = new jsPDF({
		orientation,
		unit: 'pt',
		format: [raster.width, raster.height]
	});
	doc.addImage(raster.dataUrl, 'PNG', 0, 0, raster.width, raster.height);
	const blob = doc.output('blob');
	triggerDownload(`${safeName(name)}.pdf`, blob);
}

function escapeHtml(s: string): string {
	return s
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;')
		.replace(/'/g, '&#39;');
}

export async function downloadHtml(name: string, source: string) {
	const svg = await fetchSvg(source);
	const title = escapeHtml(name || 'dicegram');
	const now = new Date().toISOString().slice(0, 10);
	const dslEsc = escapeHtml(source);
	const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>${title}</title>
<style>
  body { margin: 0; font-family: -apple-system, Segoe UI, Roboto, sans-serif; color: #111; background: #fafafa; }
  header { padding: 20px 24px; border-bottom: 1px solid #e5e7eb; background: #fff; }
  header h1 { margin: 0 0 4px; font-size: 18px; font-weight: 600; }
  header .meta { font-size: 12px; color: #6b7280; }
  main { padding: 24px; display: flex; justify-content: center; }
  main svg { max-width: 100%; height: auto; background: #fff; border: 1px solid #e5e7eb; border-radius: 6px; }
  details { margin: 0 24px 24px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fff; }
  summary { padding: 10px 14px; cursor: pointer; font-size: 13px; color: #374151; }
  pre { margin: 0; padding: 12px 16px; border-top: 1px solid #e5e7eb; overflow: auto; font-size: 12px; color: #111; background: #f9fafb; }
</style>
</head>
<body>
  <header>
    <h1>${title}</h1>
    <div class="meta">Exported ${now} · Dicegram</div>
  </header>
  <main>${svg}</main>
  <details>
    <summary>Source (Dicegram DSL)</summary>
    <pre>${dslEsc}</pre>
  </details>
</body>
</html>`;
	triggerDownload(`${safeName(name)}.html`, new Blob([html], { type: 'text/html;charset=utf-8' }));
}

// Visio Data Visualizer CSV schema (Microsoft's documented column set).
// Next Step ID and Connector Label use `;` to delimit branches so a decision
// with Yes/No paths round-trips correctly.
const VISIO_COLUMNS = [
	'Process Step ID',
	'Process Step Description',
	'Shape Type',
	'Function Band',
	'Phase',
	'Next Step ID',
	'Connector Label'
];

function visioShapeFor(shape: string, type: string | undefined): string {
	if (type) {
		switch (type) {
			case 'process':
				return 'Process';
			case 'decision':
			case 'approval':
				return 'Decision';
			case 'input':
			case 'output':
				return 'Data';
			case 'datastore':
				return 'Database';
			case 'start':
			case 'end':
				return 'Start/End';
			case 'manual':
				return 'Manual Operation';
			case 'external':
				return 'External Data';
		}
	}
	switch (shape) {
		case 'diamond':
			return 'Decision';
		case 'circle':
		case 'stadium':
		case 'rounded':
			return 'Start/End';
		case 'parallelogram':
			return 'Data';
		case 'hexagon':
			return 'Preparation';
		case 'cylinder':
			return 'Database';
		default:
			return 'Process';
	}
}

function csvEscape(v: string): string {
	if (v == null) return '';
	if (/[",\n\r]/.test(v)) return `"${v.replace(/"/g, '""')}"`;
	return v;
}

export function buildVisioCsv(result: RenderResult): string {
	const outgoing = new Map<string, Array<{ target: string; label: string }>>();
	for (const e of result.edges) {
		const arr = outgoing.get(e.source) ?? [];
		arr.push({ target: e.target, label: e.label });
		outgoing.set(e.source, arr);
	}

	const rows: string[][] = [VISIO_COLUMNS];
	for (const n of result.nodes) {
		const outs = outgoing.get(n.id) ?? [];
		const nextIds = outs.map((o) => o.target).join(';');
		const labels = outs.map((o) => o.label).join(';');
		rows.push([
			n.id,
			n.label,
			visioShapeFor(n.shape, n.attrs.type),
			n.swimlane ?? '',
			n.attrs.step ?? '',
			nextIds,
			labels
		]);
	}
	return rows.map((r) => r.map(csvEscape).join(',')).join('\r\n') + '\r\n';
}

export function downloadVisioCsv(name: string, result: RenderResult) {
	const csv = buildVisioCsv(result);
	// BOM so Excel opens as UTF-8 rather than Windows-1252.
	const blob = new Blob(['\ufeff', csv], { type: 'text/csv;charset=utf-8' });
	triggerDownload(`${safeName(name)}.csv`, blob);
}

export async function copyDsl(source: string): Promise<void> {
	await navigator.clipboard.writeText(source);
}

export async function copySvg(source: string): Promise<void> {
	const svg = await fetchSvg(source);
	await navigator.clipboard.writeText(svg);
}

export const LLM_PROMPT_TEMPLATE = `You are an expert assistant for Dicegram, a step-based dicegram DSL.

GRAMMAR:
- direction <top-to-bottom|left-to-right|bottom-to-top|right-to-left>
- setting <key> <value>  (keys: node_width, node_height, h_gap, v_gap, swimlane_gap, color_scheme, snap_grid)
- swimlane "Name" { ... }                            // groups objects into a lane
- box "Label" {fill: #hex} { ... }                   // sub-container inside a swimlane
- group "Name" { obj1 obj2 obj3 }                    // visual overlay across lanes
- note "Sticky text" [target_object]
- [shape] name "Label" step:N type:T owner:"X" status:S priority:P tags:"a, b" {fill:#hex, stroke:#hex, text:#hex} @(x,y)
- shapes: rect, rounded, diamond, circle, parallelogram, hexagon, cylinder, stadium
- type: process, decision, input, output, datastore, start, end, manual, automated, approval, external
- status: draft, active, blocked, deprecated, complete
- priority: low, medium, high, critical
- connections:
    A -> B           solid arrow
    A --> B          dashed arrow
    A ==> B          thick arrow
    A --- B          line, no arrow
    A -.- B          dotted line, no arrow
    A -> B : "label"
- // line comments
- step:N controls vertical (or horizontal) ordering — same step = parallel placement.

CURRENT DICEGRAM:
\`\`\`
{SOURCE}
\`\`\`

Respond with the full updated DSL. Don't explain — just output the DSL block.`;

export async function copyLlmPrompt(source: string): Promise<void> {
	await navigator.clipboard.writeText(LLM_PROMPT_TEMPLATE.replace('{SOURCE}', source));
}
