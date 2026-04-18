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

function svgToPngBlob(svg: string): Promise<Blob> {
	return new Promise((resolve, reject) => {
		const img = new Image();
		const sourceBlob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' });
		const url = URL.createObjectURL(sourceBlob);
		img.onload = () => {
			const canvas = document.createElement('canvas');
			const scale = 2;
			canvas.width = img.naturalWidth * scale;
			canvas.height = img.naturalHeight * scale;
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
				if (b) resolve(b);
				else reject(new Error('PNG encode failed'));
			}, 'image/png');
		};
		img.onerror = () => {
			URL.revokeObjectURL(url);
			reject(new Error('SVG image load failed'));
		};
		img.src = url;
	});
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

export async function copyDsl(source: string): Promise<void> {
	await navigator.clipboard.writeText(source);
}

export async function copySvg(source: string): Promise<void> {
	const svg = await fetchSvg(source);
	await navigator.clipboard.writeText(svg);
}

const LLM_PROMPT_TEMPLATE = `You are an expert assistant for Dicegram, a step-based dicegram DSL.

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

CURRENT DIAGRAM:
\`\`\`
{SOURCE}
\`\`\`

Respond with the full updated DSL. Don't explain — just output the DSL block.`;

export async function copyLlmPrompt(source: string): Promise<void> {
	await navigator.clipboard.writeText(LLM_PROMPT_TEMPLATE.replace('{SOURCE}', source));
}
