# UAT Visual Walkthrough — 3 May 2026

Walked every reachable surface (landing, auth, editor, dicegrams list, settings, shared view), in **both light and dark modes**, at desktop (1440×900), tablet (768×1024) and mobile (375×812). Screenshots in `uat/{light,dark,mobile,tablet}/`.

---

## 🐛 Real bugs (fixed during the walk)

| # | Symptom | Cause | Fix |
|---|---------|-------|-----|
| **1** | Login / signup / verify / password-reset returned **HTTP 500** under slowapi 0.1.9. Whole auth flow was unreachable. | slowapi requires routes that return non-`Response` bodies to declare a `response: Response` parameter; four endpoints did not. | Added `response: Response` to `signup`, `login`, `verify_email`, `reset_password` in `backend/app/routers/auth.py`. |
| **2** | `setting color_scheme solarized_light` (and `solarized_dark`, `warm_dark`, `default_dark`, `high_contrast`, `gruvbox_dark`) silently fell back to `auto`. Theme registry IDs are hyphenated (`solarized-light`), users naturally write underscores. | `getTheme()` did a single direct lookup with no normalisation. | Lookup now tries the literal id, then the underscore→hyphen variant, then hyphen→underscore, before falling back. `frontend/src/lib/themes.ts`. |
| **3** | Visiting `/` propagated the iframe editor's `setting color_scheme warm` directive into the parent page's chrome via `localStorage`, silently flipping a user's saved dark preference to light on next reload. | Editor's chrome-sync `$effect` ran inside the landing iframe and wrote to shared `localStorage`. | Effect now early-returns when `mode === 'landing' \|\| mode === 'embed'`. `frontend/src/routes/editor/+page.svelte`. |

## 🐛 Real bugs (found, NOT fixed — left for follow-up)

| # | Symptom | Repro |
|---|---------|-------|
| **4** | A DSL using `[stadium]`, `[round]`, `[parallelogram]`, `[hexagon]` shapes renders the editor **completely blank** — no canvas, no error, no toast. Code editor disappears too. | `uat/shapes-01-comprehensive.png` |
| **5** | Visiting `/editor?id=NONEXISTENT` silently auto-creates a new "Untitled dicegram" and redirects, hiding the missing-resource error. Each visit accumulates a row. After this UAT alone, ids 5–10 were created and most were `Untitled`. | Repeated `/editor?id=5` requests after delete. |
| **6** | `DELETE /api/dicegrams/{id}` returns **HTTP 500** when the dicegram has an active share. No cascade-delete; the share row blocks the foreign-key cleanup. | Create dicegram → share → delete → 500. |
| **7** | Navigating to `/editor?id=N` via SvelteKit SPA routing (not full reload) sometimes paints the default-template editor instead of the saved DSL — title says `Untitled dicegram` while URL has the real id. Hard reload fixes it. | First SPA navigation after login. |
| **8** | The "Loading diegrams…" state on `/dicegrams` sometimes never resolves on a SPA navigation while the user is logged in. Background fetch returns 200 but the component stays in the loading branch. | Reproducible by navigating settings → dicegrams. |

---

## ✨ Polish items

| # | Where | Issue |
|---|-------|-------|
| 1 | Landing page | Iframe demo shows the **"1 auto-fix applied: rewrote 5 inline connectors…"** toast on first paint — internal refactor noise on the marketing surface. Auto-fix should be silent in `mode=landing`. |
| 2 | Landing page | Live-editor iframe is a **blank cream rectangle** until the JS bundle arrives (no skeleton/spinner). |
| 3 | Editor → LLM dialog | Hard-codes third-party brand names — Claude, ChatGPT, Gemini, Copilot, Perplexity, Mistral. Memory rule says no third-party brand references. |
| 4 | Export menu | "**Visio CSV**" labels the .csv export with a third-party trademark. Rename to e.g. "Spreadsheet (CSV)". |
| 5 | Settings palette swatches | Default colours (`#064e3b` start / `#3f1d1d` end / `#3a2f0b` decision / `#0c3a5c` datastore / `#1f2937` node fill / `#e5e7eb` node text) are **dark-mode-only**. On light/cream canvases they read as muddy near-black; `node_text=#e5e7eb` is unreadable on cream. Either ship light + dark default sets, or pick neutral hues that survive both. |
| 6 | All error messages | **Lowercase**: "invalid credentials", "verification link invalid or expired", "not found", etc. Inconsistent with sentence-cased UI strings. |
| 7 | `/forgot-password` | Reachable for already-logged-in users; the form asks for an email and treats the user as anonymous. Should redirect to `/settings#change-password`. |
| 8 | `/d/<bad-slug>` 404 page | "Create your own" CTA points to `/signup`; for already-logged-in users it should say "Open editor" and link to `/editor`. |
| 9 | Editor | Opening any saved dicegram triggers the auto-fix toast on **initial load** (the user changed nothing) — should fire only after a user edit. |
| 10 | Editor settings pane | Layout numbers (Node width, Horizontal gap, Snap grid, etc.) have **no unit suffix**. Users have to guess px. |
| 11 | Editor toolbar dropdowns | "New" / "Export" / "Share" buttons have `aria-expanded` but no `aria-haspopup`. Polish, not a blocker. |
| 12 | All routes | SPA navigation in dev briefly paints a **flash of blank** (HMR/hydration timing). May be Vite-only; verify on a built bundle. |
| 13 | Verify-email banner | Position is fine, but a **resend** click that hits the 3/min rate limit silently re-shows the same idle banner with no toast. |
| 14 | Edge labels in dark themes | "yes" / "no" connector labels in `warm_dark`, `default_dark`, `dracula`, `gruvbox_dark`, `high_contrast` use a light cream fill with dark text — readable, but visually loud against very dark canvases. Inverted (dark fill, light text) would track the rest of the palette. |
| 15 | Mobile editor | Toolbar wraps onto multiple rows; insert palette also wraps. Functional but cramped. The split between code and canvas is barely usable below ~600 px wide. Consider a stacked code-above-canvas layout under `sm`. |
| 16 | Dicegrams list cards | Thumbnails are a small flowchart inside a large cream card with lots of empty margin around it. The card aspect ratio could fit the SVG more tightly. |

---

## What I confirmed works

- Skip link is the first tab stop and shows on focus (both themes).
- Dark/light theme toggle — chrome and canvas stay in sync.
- Login form: empty → filled → 401 error toast → success redirect.
- Logout via header icon, session clears.
- Dicegrams list: rename (inline), duplicate (lands in rename), delete (two-click confirm), share (slug copies), empty state.
- Editor toolbar: tree, settings pane, inspector, direction toggle (TB/LR/BT/RL), Save, Open, New (template picker).
- Theme cycle: **warm**, **warm-dark**, **default-dark**, **light**, **solarized-light** (after fix #2), **solarized-dark**, **dracula**, **gruvbox**, **high-contrast** all render.
- Direction LR/RL/BT — layout flips correctly.
- Share popup → public viewer at `/d/<slug>` → "Could not load shared dicegram" page on bad slug.
- Verify-email banner appears for unverified users at the bottom of every page.
- Settings: palette toggle (Enforce brand palette), preset save (badge becomes ACTIVE), preset switch.
- Reduced-motion media-query honoured (CSS rule present).
- Color contrast: btn-primary/btn-secondary/links/muted text all pass WCAG AA in both themes (post-a11y-pass).

---

## Console error sweep

Across every route visited:
- `GET /api/auth/me 401` — expected on logged-out routes (auth refresh probe).
- `GET /favicon.ico 404` — every page (the `<link rel="icon">` is set but the browser's automatic /favicon.ico request 404s; trivial fix is to also serve a static favicon).

No JS exceptions, no Svelte hydration warnings beyond the `a11y_click_events_have_key_events` whitelist already in source.

---

## Suggested next sprint

1. **Backend health**: cascade-delete shares with their dicegram (bug #6); show a real error UI instead of auto-creating on missing dicegram (bug #5); harden the SPA navigation race (bug #7, #8).
2. **DSL robustness**: a list of accepted shape ids should be canonical in code AND in `dsl-autocomplete.ts` AND in the LLM prompt. Today they drift, and unknown shapes produce a blank canvas (bug #4).
3. **Branding rule pass**: remove "Visio CSV", "Anthropic theme" (commit a4f94cd), `downloadVisioCsv` symbol, and the LLM-provider name list — per the no-third-party-brand memory rule. The audit dict can include all of these.
4. **Default palette**: ship a per-mode default (light + dark) so `/settings` swatches don't show a near-black `End` shape on a cream canvas.
5. **Copy polish**: sentence-case every error / toast string. Tiny but lifts the felt quality.
6. **Mobile editor**: stack code-above-canvas under 640 px; reduce toolbar to a hamburger.
