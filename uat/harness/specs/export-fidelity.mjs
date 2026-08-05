// What you export must match what you saw, and must not silently lose parts
// of the drawing. Three defects found on 2026-08-05:
//
//  1. The SVG viewBox was computed from node/lane/box/note extents only and
//     ignored edge routes entirely. Orthogonal detours regularly leave the
//     node bounding box, so edge segments and whole edge labels were sliced
//     off the exported file. Measured on a branching flow: the viewBox spanned
//     x 100..520 while real content spanned 80..555 — losing ~20px on the left
//     and 15px on the right, the latter slicing an edge-label chip in half.
//
//  2. Note text is never wrapped. layout.py sizes notes at `note_width`
//     (80px) with the comment "encourages wrap", but no renderer implemented
//     wrapping. The canvas gets away with it via CSS white-space:pre-wrap;
//     SVG <text> has no such behaviour, so note text renders as one long
//     unwrapped line straddling and escaping its own box.
//
//  3. The export theme defaulted to `default-dark` (palette.py) whenever the
//     document carried no `setting color_scheme`, and export.ts never sent
//     the on-screen theme — so a user working in light mode exported a black
//     diagram.
//
// Run: node specs/export-fidelity.mjs
import { runSpec, openEditor, exportSvg, svgMetrics, shotSvg } from '../lib/harness.mjs';

// Branching flow: the "no" branch forces a route outside the node bounds.
const BRANCHY = `direction top-to-bottom

[circle] rec "Alert received" type:start
[rect] tri "Triage severity"
[diamond] sev "Sev 1?" type:decision
[rect] page "Page on-call"
[rect] ticket "File ticket"
[rect] fix "Mitigate"
[circle] done "Resolved" type:end

rec -> tri
tri -> sev
sev -> page : "yes"
sev -> ticket : "no"
page -> fix
ticket -> fix
fix -> done
`;

const WITH_NOTE = `direction top-to-bottom

[rect] a "Authorise card" step:0
[rect] b "Capture funds" step:1

a -> b
[note] n1 "3-D Secure step happens here" target:a
`;

/** True drawn extent of every element, measured in a real browser. */
async function measure(page, svg) {
  return page.evaluate((s) => {
    const host = document.createElement('div');
    host.style.cssText = 'position:absolute;left:0;top:0';
    host.innerHTML = s;
    document.body.appendChild(host);
    const el = host.querySelector('svg');
    const vb = el.getAttribute('viewBox').split(/\s+/).map(Number);
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const n of el.querySelectorAll('path,rect,ellipse,polygon,text,line')) {
      // <defs> marker templates report bbox in their own coordinate space
      // (0..10) and are never drawn there — counting them fakes a clip.
      if (n.closest('defs')) continue;
      let bb;
      try { bb = n.getBBox(); } catch { continue; }
      if (!isFinite(bb.x) || (bb.width === 0 && bb.height === 0)) continue;
      x0 = Math.min(x0, bb.x); y0 = Math.min(y0, bb.y);
      x1 = Math.max(x1, bb.x + bb.width); y1 = Math.max(y1, bb.y + bb.height);
    }
    // Does note text stay inside a box? Identified by CONTENT, not by fill —
    // keying off the note colour made this spec theme-dependent and it broke
    // the moment the default palette changed.
    const NOTE_WORDS = ['3-D', 'Secure', 'step', 'happens', 'here'];
    const noteTexts = [...el.querySelectorAll('text')].filter((t) =>
      NOTE_WORDS.includes(t.textContent.trim()),
    );
    const rects = [...el.querySelectorAll('rect')].map((r) => r.getBBox());
    const escapes = [];
    for (const t of noteTexts) {
      const tb = t.getBBox();
      const contained = rects.some(
        (rb) =>
          tb.x >= rb.x - 1 &&
          tb.x + tb.width <= rb.x + rb.width + 1 &&
          tb.y >= rb.y - 1 &&
          tb.y + tb.height <= rb.y + rb.height + 1,
      );
      if (!contained) {
        escapes.push(
          `"${t.textContent.trim()}" x=${tb.x.toFixed(0)}..${(tb.x + tb.width).toFixed(0)} is inside no box`,
        );
      }
    }
    host.remove();
    return { viewBox: vb, content: [x0, y0, x1, y1], noteRects: noteTexts.length, escapes };
  }, svg);
}

const r = await runSpec('export-fidelity', async (page, t) => {
  await openEditor(page);

  // ─── 1. Nothing may fall outside the viewBox ───
  const res = await exportSvg(page, BRANCHY);
  t.check('export endpoint returns an SVG', res.ok, `status ${res.status}`);
  if (!res.ok) return;
  await shotSvg(page, res.svg, 'fidelity-01-branchy');

  const m = await measure(page, res.svg);
  const [vx, vy, vw, vh] = m.viewBox;
  const [cx0, cy0, cx1, cy1] = m.content;
  t.check(
    'viewBox contains all drawn content on the left',
    cx0 >= vx - 0.5,
    `content starts at x=${cx0.toFixed(1)}, viewBox at x=${vx}`,
  );
  t.check(
    'viewBox contains all drawn content on the right',
    cx1 <= vx + vw + 0.5,
    `content ends at x=${cx1.toFixed(1)}, viewBox ends at ${vx + vw}`,
  );
  t.check(
    'viewBox contains all drawn content vertically',
    cy0 >= vy - 0.5 && cy1 <= vy + vh + 0.5,
    `content y ${cy0.toFixed(1)}..${cy1.toFixed(1)}, viewBox ${vy}..${vy + vh}`,
  );

  const geo = svgMetrics(res.svg);
  t.check(
    'export has sane dimensions',
    geo.width > 0 && geo.height > 0 && isFinite(geo.width) && isFinite(geo.height),
    JSON.stringify(geo),
  );

  // ─── 2. Note text stays inside its note ───
  const noteRes = await exportSvg(page, WITH_NOTE);
  await shotSvg(page, noteRes.svg, 'fidelity-02-note');
  const nm = await measure(page, noteRes.svg);
  t.check('the note text was rendered', nm.noteRects > 0, `${nm.noteRects} note text lines found`);
  t.check(
    'note text does not escape its own box',
    nm.escapes.length === 0,
    nm.escapes.join(' | '),
  );

  // ─── 3. Theme must not silently flip to dark ───
  // A document with no `setting color_scheme` is the common case — the
  // landing-page example and anything an LLM writes both omit it.
  const plain = await exportSvg(page, '[rect] a "Only node"\n');
  const isDark = /#0b0b0d|#111827|#1f2937/i.test(plain.svg.slice(0, 1200));
  await shotSvg(page, plain.svg, 'fidelity-03-default-theme');
  t.check(
    'a document with no color_scheme does not export as dark',
    !isDark,
    'export fell back to default-dark while the editor renders light',
  );
});

process.exit(r.failed ? 1 : 0);
