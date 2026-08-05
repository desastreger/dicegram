import type { RenderResult } from './render';
import { palette } from './palette.svelte';

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

// Process-flow CSV — a widely supported column set for diagram-to-CSV
// pipelines (Process Step ID, shape type, lane, next-step IDs). Next Step
// ID and Connector Label use `;` to delimit branches so a decision with
// Yes/No paths round-trips correctly.
const PROCESS_FLOW_COLUMNS = [
	'Process Step ID',
	'Process Step Description',
	'Shape Type',
	'Function Band',
	'Phase',
	'Next Step ID',
	'Connector Label'
];

function processFlowShapeFor(shape: string, type: string | undefined): string {
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

export function buildProcessFlowCsv(result: RenderResult): string {
	const outgoing = new Map<string, Array<{ target: string; label: string }>>();
	for (const e of result.edges) {
		const arr = outgoing.get(e.source) ?? [];
		arr.push({ target: e.target, label: e.label });
		outgoing.set(e.source, arr);
	}

	const rows: string[][] = [PROCESS_FLOW_COLUMNS];
	for (const n of result.nodes) {
		const outs = outgoing.get(n.id) ?? [];
		const nextIds = outs.map((o) => o.target).join(';');
		const labels = outs.map((o) => o.label).join(';');
		rows.push([
			n.id,
			n.label,
			processFlowShapeFor(n.shape, n.attrs.type),
			n.swimlane ?? '',
			// `step` is a first-class field: the parser pops it out of attrs,
			// so reading attrs.step left this column empty on every row.
			n.step != null ? String(n.step) : (n.attrs.step ?? ''),
			nextIds,
			labels
		]);
	}
	return rows.map((r) => r.map(csvEscape).join(',')).join('\r\n') + '\r\n';
}

export function downloadProcessFlowCsv(name: string, result: RenderResult) {
	const csv = buildProcessFlowCsv(result);
	// BOM so spreadsheets open as UTF-8 rather than Windows-1252.
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

function paletteBlock(): string {
	const p = palette.current;
	const used = (k: string) => p[k] && p[k].length > 0;
	const line = (label: string, key: string) =>
		`  ${label.padEnd(24)} ${used(key) ? p[key] : '(inherit node_fill)'}`;
	const header = palette.locked
		? "BRANDING PALETTE (LOCKED — don't emit style dicts; use the type: attr and let the palette colour the node):"
		: 'BRANDING PALETTE (prefer the type: attr — inline style dicts only when the DSL needs an exception):';
	return [
		header,
		line('node_fill', 'node_fill'),
		line('node_stroke', 'node_stroke'),
		line('node_text', 'node_text'),
		line('type:start', 'type_start'),
		line('type:end', 'type_end'),
		line('type:decision', 'type_decision'),
		line('type:datastore', 'type_datastore'),
		line('type:process', 'type_process'),
		line('type:input', 'type_input'),
		line('type:output', 'type_output'),
		line('type:manual', 'type_manual'),
		line('type:automated', 'type_automated'),
		line('type:approval', 'type_approval'),
		line('type:external', 'type_external'),
		line('priority:critical', 'priority_critical'),
		line('priority:high', 'priority_high'),
		line('status:blocked', 'status_blocked'),
		line('status:complete', 'status_complete'),
		line('edge', 'edge')
	].join('\n');
}

function settingsBlock(): string {
	// Surfaces the app-level state that changes what valid DSL looks like
	// for this user right now. Keep in sync with anything that alters how
	// styles / attrs render.
	const locked = palette.locked;
	const activePreset = palette.presets.find((p) => p.active)?.name ?? '(unsaved)';
	return [
		'USER SETTINGS (current state — respect these when generating):',
		`  palette lock:   ${locked ? 'ON — do NOT emit {fill:#…} / {stroke:#…} / {text:#…} style dicts. All colours must come from the palette via type:/status:/priority:.' : 'OFF — inline {fill:#…} overrides are allowed when you truly need an exception.'}`,
		`  active preset:  ${activePreset}`
	].join('\n');
}

// The instruction block a user pastes into a chat model alongside their
// question. Every claim in here is checked against the backend ground
// truth — grammar in dsl/parser.py, auto-fix rules in dsl/compiler.py,
// rank derivation in dsl/layout.py, theme ids in palette.py — so when the
// DSL changes, this is the other place that must change. Example-first
// because models copy the example's habits far more reliably than they
// follow prose rules; the reference exists to stop invention, not to
// teach.
export function buildLlmPrompt(source: string): string {
	const lockRule = palette.locked
		? '3. BRAND LOCK IS ON: do not emit any style dict ({fill:#…}, {stroke:#…}, {text:#…}). Colour must come from the palette via the `type:` / `status:` / `priority:` attributes only. An inline style override will be visually ignored — the Inspector hides those fields.'
		: '3. Prefer the `type:` attribute over inline `{fill:#…}` dicts — it lets the user re-brand the diagram just by changing their palette. Emit explicit colours only when the DSL really needs a one-off exception.';
	return `You are an expert author of Dicegram DSL. Your output will be pasted
directly into the Dicegram editor, so emit ONLY the DSL block — no prose,
no Markdown fences, no commentary.

==============================
WORKED EXAMPLE (canonical style — copy its habits)
==============================

direction top-to-bottom

swimlane "Frontend" {
  [circle] req  "Login clicked" type:start
  [rect]   form "Submit form"   type:process
  [circle] done "Home page"     type:end
}

swimlane "Backend" {
  [diamond]  verify "Valid?"        type:decision
  [rect]     issue  "Issue session" type:process
  [rect]     reject "401 response"  type:process status:blocked
  [cylinder] db     "Users DB"      type:datastore
}

req -> form
form -> verify
verify --> db : "lookup"
verify -> issue : "yes"
verify -> reject : "no"
issue -> done
reject --> form : "retry"

[note] n1 "Sessions expire" [linebreak] "after 24h" target:issue

The habits that matter: no step: anywhere (rank derives from the
arrows, retry loop-backs included), a type: on every node, labels of
1-3 words, edges after the lane blocks.

==============================
REFERENCE (authoritative — do not invent beyond it)
==============================

// Full-line or trailing comment. Blank lines are ignored.

direction top-to-bottom | left-to-right | bottom-to-top | right-to-left
    Default top-to-bottom. Full names only — TB/LR shorthands are NOT
    understood by layout. TB/BT draws swimlanes as columns; LR/RL as rows.

setting <key> <value>    (all optional)
    color_scheme: warm | light | default-dark | dracula | gruvbox |
      high-contrast | solarized-light | solarized-dark. Omit for the
      default warm-light look.
    node_width, node_height, h_gap, v_gap, swimlane_gap, snap_grid,
    font_size: numeric px overrides — rarely needed.

swimlane "Name" { …nodes… }     One lane per actor / system / team.
box "Label" { …nodes… }         Tinted sub-container INSIDE a swimlane;
    optional style dict before the body: box "L" {fill:#hex} { … }.
There is no other grouping construct — never emit \`group\` blocks
(they parse for legacy files but are not rendered).

NODES — [shape] id "Label" attrs… {style}? @(x,y)?
    Shapes: rect rounded diamond circle parallelogram hexagon cylinder
    stadium. Anything else is a PARSE ERROR (no fallback).
    id: snake_case, unique across the document.
    "Label": 1-4 words — long labels stretch the node into a wide bar.
    Multi-line: "Line one" [linebreak] "Line two" (don't pad the token
    with spaces inside a quoted string; they are kept as text).

    attrs (all optional, space-separated):
      type:<start|end|process|decision|input|output|datastore|manual|
            automated|approval|external>
        Give EVERY node a type where one fits. The palette colours by
        type, and the compiler forces the matching shape (start/end→
        circle, decision→diamond, datastore→cylinder, input/output→
        parallelogram, approval→hexagon, manual→rounded) — type wins
        over the bracket.
      step:N — OPTIONAL and all-or-nothing. Omit it EVERYWHERE and rank
        derives from the arrows (longest path; loop-back arrows such as
        a retry are ignored for ranking). If ANY node has step:, the
        derivation switches off and unstepped nodes land at step 0 —
        except unstepped type:end nodes, placed after the last explicit
        step. Same step = side by side. Prefer omitting.
      status:<draft|active|blocked|complete|deprecated>
        draft=dashed, blocked=red stroke, complete=green stroke,
        deprecated=greyed + struck through.
      priority:<low|medium|high|critical>  high/critical thicken and
        colour the stroke.
      owner:"Name"  tags:"alpha, beta"  — shown as chips on the node.
    style dict: {fill:#hex, stroke:#hex, text:#hex, rx:<px>,
    font_size:<px>, font_family:<name>, opacity:<0..1>, stroke_width:<px>}
    @(x,y): absolute pin — avoid; the compiler strips pins inside lanes.

EDGES — write them after the lane blocks, referencing node ids:
    a -> b        solid arrow           a --> b   dashed arrow
    a ==> b       thick arrow           a <-> b   arrows at both ends
    a --- b       plain line, no tip    a -.- b   dotted line, no tip
    a -> b : "yes"                      label — keep it to 1-2 words
    a -> a : "retry"                    self-loops are allowed
    Ports (optional): a@r -> b@l — values t/b/l/r (top/bottom/left/
    right; n/s/w/e also accepted).
    Extra attrs need a label first (a -> b : "x" end:circle) or the
    block form — a bare \`a -> b end:circle\` silently DROPS the attr:
        a -> b {
          label: "yes"
          tip:  circle      // target-end terminator: arrow, open_arrow,
          back: none        //   circle, diamond, tee, square, none
          opacity: 0.5      // back: is the source-end terminator
        }
    The editor rewrites every inline edge to a canonical bracket line,
    so the CURRENT DICEGRAM below may contain connectors like:
        [solid_line] from:a from_anchor:bottom to:b to_anchor:top tip:arrow back:none label:"yes"
    Keywords: [solid_line] [dashed_line] [thick_line] [dotted_line]
    [bidirectional], or generic [connector] … kind:<solid|dashed|thick|
    solid_line|dotted_line|bidirectional>. Anchors: top, bottom, left,
    right. Author whichever form you like; both are valid input.

NOTES — [note] id "Sticky text" target:node_id
    Sticky annotation beside its target. Text word-wraps by itself;
    [linebreak] between quoted segments forces a break.

AUTO-FIXES the compiler applies to your output (don't fight them):
    - inline edges are rewritten to the bracket form above
    - any line referencing an undeclared id is COMMENTED OUT — declare
      every node you connect
    - duplicate ids are renamed (second occurrence becomes id_2)
    - the shape bracket is rewritten to match type:

==============================
${settingsBlock()}

${paletteBlock()}
==============================

RULES — follow these exactly:
1. Emit the whole document. Do not truncate or add "(...)".
2. Keep ids snake_case and terse; keep labels short.
${lockRule}
4. Use swimlanes when there is more than one actor/responsibility.
5. Omit step: and let the arrows carry the order. If you must pin
   ranks, pin EVERY node — never mix stepped and unstepped.
6. Give every node a type: where one applies.
7. Only use the shapes, attrs and values listed above — unknown shape
   brackets are parse errors; unknown attr values do nothing.

==============================
CURRENT DICEGRAM (modify this)
==============================

${source}

Respond with the full updated DSL, starting immediately with \`direction\`
(or a comment). Do not wrap the output in Markdown fences.`;
}

export async function copyLlmPrompt(source: string): Promise<void> {
	await navigator.clipboard.writeText(buildLlmPrompt(source));
}

// Back-compat re-export so external callers that used the constant still
// work — now returns the prompt for an empty source.
export const LLM_PROMPT_TEMPLATE = buildLlmPrompt('{SOURCE}');
