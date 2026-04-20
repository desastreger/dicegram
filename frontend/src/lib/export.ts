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

function buildLlmPrompt(source: string): string {
	const lockRule = palette.locked
		? '3. BRAND LOCK IS ON: do not emit any style dict ({fill:#…}, {stroke:#…}, {text:#…}). Colour must come from the palette via the `type:` / `status:` / `priority:` attributes only. An inline style override will be visually ignored — the Inspector hides those fields.'
		: '3. Prefer the `type:` attribute over inline `{fill:#…}` dicts — it lets the user re-brand the diagram just by changing their palette. Emit explicit colours only when the DSL really needs a one-off exception.';
	return `You are an expert author of Dicegram DSL. Your output will be pasted
directly into the Dicegram editor, so emit ONLY the DSL block — no prose,
no Markdown fences, no commentary.

==============================
GRAMMAR (authoritative)
==============================

// Lines starting with // are comments. Blank lines are ignored.

direction <top-to-bottom | left-to-right | bottom-to-top | right-to-left>
    Sets flow axis. Default top-to-bottom. Shorthand TB / LR / BT / RL accepted.

setting <key> <value>
    Runtime defaults. Useful keys:
      node_width, node_height, h_gap, v_gap, swimlane_gap, snap_grid.

swimlane "Display Name" { <objects + boxes> }
    Groups objects into a lane. In TB/BT lanes are vertical columns;
    in LR/RL lanes are horizontal rows. Objects outside any swimlane sit
    in the "free" area.

box "Label" { <objects> }
box "Label" {fill:#hex, stroke:#hex} { <objects> }
    A tinted sub-container. Lives INSIDE a swimlane block. The style dict
    is OPTIONAL and comes BEFORE the body block.

group "Name" { obj1 obj2 obj3 }
    Dashed visual overlay around referenced objects. Can span swimlanes.
    Does not own layout — it just draws a dashed border.

note "Sticky text" [target_object]
    A sticky note attached to an existing object by name.

[shape] unique_name "Display Label" step:N [attrs] [{style}] [@(x,y)]
    The ONLY way to declare an object. Every field after the label is
    optional except step:.

    shape (required, one of, in brackets):
        [rect]           rectangle               (process / task)
        [rounded]        rounded rectangle       (sub-process)
        [diamond]        diamond                 (decision / gateway)
        [circle]         circle / ellipse        (start or end event)
        [parallelogram]  slanted rectangle       (data input / output)
        [hexagon]        hexagon                 (preparation)
        [cylinder]       cylinder                (datastore)
        [stadium]        pill / capsule          (terminal / boundary)

    unique_name: lowercase identifier, no spaces. Used as the ID in
    connections. Must be unique across the whole document.

    "Display Label": quoted string shown on the node. For multi-line
    labels, use the \`[linebreak]\` token between quoted segments:
        [rect] api "First part" [linebreak] "Second part" step:0
    Never emit raw \\n inside a string — that's a programmer-ism. The
    \`[linebreak]\` token is the authoritative way to split a label.

    step:N (required for layout): integer ordering along the flow axis.
    Same step = parallel placement. Start at step:0.

    attrs (all optional, space-separated):
        type:<process|decision|input|output|datastore|start|end|manual|automated|approval|external>
        owner:"Name"            responsibility assignment
        status:<draft|active|blocked|deprecated|complete>
            draft=dashed, blocked=red stroke, complete=green stroke,
            deprecated=strikethrough.
        priority:<low|medium|high|critical>
            critical/high thicken + colour the stroke.
        tags:"alpha, beta"      comma-separated free labels.
        id:N                    external reference number.

    style dict (optional, in braces, comma-separated, each is key:value):
        fill:#hex, stroke:#hex, text:#hex, rx:<px>,
        font_size:<px>, font_family:<name>, opacity:<0..1>, stroke_width:<px>

    @(x,y) (optional): pins the node to an absolute position, overriding
    auto-layout. Omit unless you really need a fixed pin.

Connections (outside swimlane blocks):
    A -> B                    solid arrow             (sequence)
    A --> B                   dashed arrow            (message / conditional)
    A ==> B                   thick arrow             (critical path)
    A --- B                   solid line, no arrow    (association)
    A -.- B                   dotted line, no arrow   (dependency)
    A -> B : "label text"
    A -> B : "label" [above|below|center]
    A -> B condition:"expr" weight:5
    A -> A : "retry"          self-loops are allowed

    Explicit ports (optional — override the geometry-based auto-picker):
        A@r -> B@l            source exits right, target enters left
        A@top -> B@bottom     source exits top, target enters bottom
        A@b -> B             only pin source side; target port auto
        A -> B@t             only pin target side; source port auto
        Accepted port values: t/top/n/north, b/bottom/s/south,
                              l/left/w/west,  r/right/e/east.

    Connector end decorations (optional — default is an arrow at the
    target end for ->, -->, ==> and nothing for ---, -.-):
        A -> B : "x" end:arrow       (default for -> )
        A -> B end:circle             dot at target
        A -> B end:diamond            filled diamond
        A -> B end:open_arrow         outlined arrow
        A -> B end:tee                perpendicular stop bar
        A -> B end:square             square cap
        A -> B end:none               no decoration at target
        A -> B start:circle end:arrow dot at source, arrow at target
        A -> B start:arrow            arrow at source too (bidirectional)
        Opacity: \`opacity:0.5\` attr on the edge (0..1).

    Verbose block form — spell every detail explicitly. Use this when
    an edge carries more than 2-3 attrs, or when clarity matters more
    than brevity. Everything supported inline is also supported here:

        edge meet_love -> trust {
            label:        "yes"
            kind:         solid          (solid | dashed | thick | solid_line | dotted_line)
            from_anchor:  right          (top, bottom, left, right — the anchor side)
            to_anchor:    left
            back:         none           (tip at the source end; same values as tip:)
            tip:          arrow
            opacity:      0.5
            color:        #ff5500
            condition:    "user agrees"
            weight:       5
        }

    The \`edge\` keyword before the source name is optional; \`A -> B { … }\`
    parses identically. Ports on the header line (\`A@r -> B@l { … }\`)
    compose with any \`from_anchor:\` / \`to_anchor:\` inside the block — the
    block wins when both are given.

    Object-style bracket form — the preferred form when you want a
    connector to surface in the inspector and be clicked as a single
    unit. One line, named fields, no trailing colon tail:

        [connector] c1 from:decide@r to:issue@l kind:dashed tip:arrow back:none label:"yes"

    Bracket-form keys (all optional unless marked):
        from:           source node — REQUIRED. \`from:A@right\` splits
                        into node "A" + anchor "right". \`from:A\` alone
                        lets the picker choose the anchor.
        to:             target node — REQUIRED. Same grammar as \`from:\`.
        from_anchor:    explicit source anchor (top/bottom/left/right).
                        Separated from \`from:\` for the self-healer: a
                        visible anchor field means the compiler can fix
                        bad routing without guessing user intent.
        to_anchor:      explicit target anchor.
        kind:           line style (default solid).
        tip:            terminator at the target end (default arrow for
                        solid/dashed/thick; none for solid_line/dotted_line).
                        Values: arrow, open_arrow, circle, diamond, tee,
                        square, none.
        back:           terminator at the source end. Same values as tip.
        label:          quoted label. Multi-line: use \`[linebreak]\`
                        between quoted segments.
        opacity:        0..1.
        color:          #rrggbb edge colour override.
        condition / weight / <custom>: pass through unchanged.

    Prefer inline \`A -> B\` for terse sequence diagrams; use \`[connector]\`
    when you want the edge to behave like a first-class object (named,
    inspector-editable, autocomplete-friendly) or when the connector
    carries a bundle of attrs.

==============================
${settingsBlock()}

${paletteBlock()}
==============================

RULES — follow these exactly:
1. Emit the whole document. Do not truncate or add "(...)".
2. Keep shape identifiers (\`unique_name\`) snake_case and terse.
${lockRule}
4. Include swimlanes when there's more than one actor/responsibility.
5. Every node needs a step: value. Parallel siblings share a step.
6. Connections live OUTSIDE swimlane blocks and reference nodes by
   \`unique_name\`.
7. Only use the shape brackets and attr values listed above — invented
   shapes or types will silently fall back to \`[rect]\`.

==============================
WORKED EXAMPLE
==============================

direction top-to-bottom

swimlane "Frontend" {
  [circle] req     "Login clicked" step:0 type:start
  [rect]   form    "Submit form"   step:1 type:process
  [circle] done    "Home page"     step:4 type:end
}

swimlane "Backend" {
  [diamond]  verify  "Credentials valid?" step:2 type:decision
  [cylinder] db      "Users DB"           step:2 type:datastore
  [rect]     issue   "Issue session"      step:3 type:process
  [rect]     reject  "401 response"       step:3 type:process status:blocked
}

req -> form
form -> verify
verify --> db : "lookup"
verify -> issue : "yes"
verify -> reject : "no" [below]
issue -> done
reject --> done : "retry"

==============================
CURRENT DIEGRAM (modify this)
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
