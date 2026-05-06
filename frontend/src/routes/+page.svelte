<script lang="ts">
	import { auth } from '$lib/auth.svelte';
	import { LLM_PROMPT_TEMPLATE } from '$lib/export';
	import Icon from '$lib/Icon.svelte';
	import LlmPromptDialog from '$lib/LlmPromptDialog.svelte';

	let llmOpen = $state(false);

	const LLM_PROMPT_FOR_COPY = LLM_PROMPT_TEMPLATE.replace(
		'{SOURCE}',
		'(paste your dicegram source here, or describe what you want and ask the LLM to write it)'
	);
</script>

<svelte:head>
	<title>Dicegram — write a flow, get a diagram</title>
	<meta
		name="description"
		content="Dicegram turns plain-text steps into living diagrams. The DSL is the source of truth; canvas, code and inspector are three windows into the same file."
	/>
</svelte:head>

<section class="landing">
	<!-- Hero. One large, characterful headline. The italic display cut
	     does the heavy lifting; everything else stays calm. -->
	<div class="hero">
		<div class="hero-eyebrow eyebrow app-rise">
			<span class="step-glyph" aria-hidden="true"><i></i><i></i><i></i><i></i></span>
			<span>Plain text · into shapes</span>
		</div>
		<h1 class="display-1 app-rise app-rise-delay-1">
			Write a flow.<br />
			<span class="display-italic" style="color: var(--app-accent);">Get a diagram.</span>
		</h1>
		<p class="lede app-rise app-rise-delay-2">
			Dicegram is a tiny, friendly DSL for the kind of diegrams you sketch on a whiteboard
			at 2&nbsp;p.m. on a Tuesday — flowcharts, swimlanes, decision trees, system maps.
			Type a step, get a shape. Auto-layout does the boring positioning. Share, save, version
			your diegrams.
		</p>
		<div class="cta-row app-rise app-rise-delay-3">
			{#if auth.user}
				<a href="/editor" class="btn-primary cta-primary">
					<span>Open editor</span>
					<Icon name="arrow-right" size={14} />
				</a>
				<a href="/dicegrams" class="btn-secondary cta-secondary">
					<Icon name="folder" size={14} />
					<span>My diegrams</span>
				</a>
			{:else}
				<a href="/signup" class="btn-primary cta-primary">
					<span>Make your first dicegram</span>
					<Icon name="arrow-right" size={14} />
				</a>
				<a href="/editor?demo=1" class="btn-secondary cta-secondary">
					<Icon name="play" size={14} />
					<span>Try it without signing up</span>
				</a>
				<a href="/login" class="btn-ghost cta-ghost">Log in</a>
			{/if}
			<button
				type="button"
				onclick={() => (llmOpen = true)}
				class="btn-ghost cta-ghost"
			>
				<Icon name="sparkles" size={14} />
				<span>Use with an LLM</span>
			</button>
		</div>
	</div>

	<!-- Three pillars. Friendly copy, no marketing fluff. -->
	<div class="pillars app-rise app-rise-delay-4">
		<article class="pillar">
			<div class="pillar-mark" aria-hidden="true">01</div>
			<h2 class="pillar-title display-3">Text is the source of truth</h2>
			<p class="pillar-body body-sm">
				The DSL is canonical. Drag a node on the canvas — the text rewrites.
				Edit the text — the canvas redraws. No state lives in two places, so
				there's nothing to "save back".
			</p>
		</article>
		<article class="pillar">
			<div class="pillar-mark" aria-hidden="true">02</div>
			<h2 class="pillar-title display-3">Shapes your reader already knows</h2>
			<p class="pillar-body body-sm">
				Process, decision, datastore, start &amp; end, swimlanes — the same
				vocabulary your stakeholders skim past in a slide deck. No exotic
				geometry to teach the room.
			</p>
		</article>
		<article class="pillar">
			<div class="pillar-mark" aria-hidden="true">03</div>
			<h2 class="pillar-title display-3">Everything is one file</h2>
			<p class="pillar-body body-sm">
				Diff it, paste it into a chat, hand it to an LLM, drop it into a
				PR. The whole dicegram is a few lines of plain text — and exports
				to SVG, PNG, PDF, HTML when you need pixels.
			</p>
		</article>
	</div>

	<!-- Tiny code-vs-shape split that shows what the DSL actually feels
	     like. Calmer than another iframe, and reinforces "text is the
	     source of truth" without pretending the syntax is hard. -->
	<div class="snippet">
		<div class="snippet-text">
			<div class="eyebrow">A few lines of text</div>
			<pre class="snippet-code"><code>direction top-to-bottom

[circle]   start  "Login clicked"   step:0  type:start
[rect]     form   "Submit form"     step:1  type:process
[diamond]  ok?    "Valid?"          step:2  type:decision
[rect]     home   "Home page"       step:3  type:end

start -&gt; form -&gt; ok?
ok? -&gt; home : "yes"
ok? --&gt; form : "no"</code></pre>
		</div>
		<div class="snippet-shape">
			<div class="eyebrow">…becomes a dicegram</div>
			<svg viewBox="0 0 220 280" role="img" aria-label="Sample dicegram preview" class="snippet-preview">
				<defs>
					<marker id="dgArrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
						<path d="M0,0 L8,4 L0,8 z" fill="currentColor" />
					</marker>
				</defs>
				<g style="color: var(--app-text-muted);">
					<line x1="110" y1="46" x2="110" y2="76" stroke="currentColor" stroke-width="1.5" marker-end="url(#dgArrow)" />
					<line x1="110" y1="116" x2="110" y2="146" stroke="currentColor" stroke-width="1.5" marker-end="url(#dgArrow)" />
					<line x1="110" y1="200" x2="110" y2="230" stroke="currentColor" stroke-width="1.5" marker-end="url(#dgArrow)" />
					<path d="M 70 173 Q 30 173 30 110 Q 30 76 70 76" fill="none" stroke="currentColor" stroke-width="1.5" stroke-dasharray="4 3" marker-end="url(#dgArrow)" />
				</g>
				<!-- start: circle -->
				<circle cx="110" cy="26" r="22" fill="var(--app-surface-2)" stroke="var(--app-border-strong)" stroke-width="1.5" />
				<text x="110" y="30" text-anchor="middle" fill="var(--app-text)" font-size="10" font-family="var(--app-body-font)">Login</text>
				<!-- form: rect -->
				<rect x="74" y="80" width="72" height="34" rx="4" fill="var(--app-surface-2)" stroke="var(--app-border-strong)" stroke-width="1.5" />
				<text x="110" y="101" text-anchor="middle" fill="var(--app-text)" font-size="10" font-family="var(--app-body-font)">Submit form</text>
				<!-- ok?: diamond -->
				<polygon points="110,150 152,173 110,196 68,173" fill="var(--app-accent-soft)" stroke="var(--app-accent)" stroke-width="1.5" />
				<text x="110" y="177" text-anchor="middle" fill="var(--app-text)" font-size="10" font-family="var(--app-body-font)">Valid?</text>
				<!-- home: rect end -->
				<rect x="74" y="234" width="72" height="34" rx="4" fill="var(--app-surface-2)" stroke="var(--app-border-strong)" stroke-width="1.5" />
				<text x="110" y="255" text-anchor="middle" fill="var(--app-text)" font-size="10" font-family="var(--app-body-font)">Home page</text>
				<text x="118" y="218" font-size="9" fill="var(--app-text-muted)" font-family="var(--app-body-font)">yes</text>
				<text x="36" y="120" font-size="9" fill="var(--app-text-muted)" font-family="var(--app-body-font)">no</text>
			</svg>
		</div>
	</div>

	<!-- A short, helpful primer that says: this is a friendly tool. -->
	<aside class="primer">
		<div class="step-glyph" aria-hidden="true"><i></i><i></i><i></i><i></i></div>
		<div>
			<h2 class="display-3">New here?</h2>
			<p class="body-sm" style="color: var(--app-text-muted); margin-top: 0.4rem;">
				Open the editor, hit <kbd>?</kbd> for keyboard shortcuts, or grab the
				<button
					type="button"
					onclick={() => (llmOpen = true)}
					class="link"
					style="background: none; border: 0; padding: 0; cursor: pointer; font: inherit;"
				>LLM prompt</button>
				and ask any chat model to write a dicegram for you. The output drops
				straight into the editor.
			</p>
		</div>
	</aside>
</section>

<LlmPromptDialog bind:open={llmOpen} promptText={LLM_PROMPT_FOR_COPY} />

<style>
	.landing {
		max-width: 64rem;
		margin: 0 auto;
		padding: clamp(2.5rem, 6vw, 5rem) clamp(1rem, 4vw, 2rem) 4rem;
		display: flex;
		flex-direction: column;
		gap: clamp(2.5rem, 5vw, 4rem);
	}

	.hero {
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
		align-items: flex-start;
		text-align: left;
		max-width: 52rem;
	}

	.hero-eyebrow {
		display: inline-flex;
		align-items: center;
		gap: 0.55rem;
		color: var(--app-text-dim);
	}

	.lede {
		font-size: clamp(1rem, 1.4vw, 1.15rem);
		line-height: 1.55;
		color: var(--app-text-muted);
		max-width: 42rem;
	}

	.cta-row {
		display: flex;
		flex-wrap: wrap;
		gap: 0.6rem;
		align-items: center;
		margin-top: 0.4rem;
	}
	.cta-primary,
	.cta-secondary,
	.cta-ghost {
		display: inline-flex;
		align-items: center;
		gap: 0.55rem;
		padding: 0.6rem 1.1rem;
		font-size: 0.9rem;
	}
	.cta-ghost {
		padding: 0.6rem 0.85rem;
	}

	/* Three pillars */
	.pillars {
		display: grid;
		grid-template-columns: 1fr;
		gap: 1.25rem;
	}
	@media (min-width: 720px) {
		.pillars { grid-template-columns: repeat(3, 1fr); }
	}
	.pillar {
		display: flex;
		flex-direction: column;
		gap: 0.55rem;
		padding: 1.25rem 1.25rem 1.5rem;
		border: 1px solid var(--app-border);
		border-radius: var(--app-radius);
		background: var(--app-surface);
		transition: border-color var(--app-dur-base) var(--app-ease),
			transform var(--app-dur-base) var(--app-ease),
			box-shadow var(--app-dur-base) var(--app-ease);
	}
	.pillar:hover {
		border-color: var(--app-border-strong);
		transform: translateY(-2px);
		box-shadow: var(--app-shadow-md);
	}
	.pillar-mark {
		font-family: var(--app-mono-font);
		font-size: 0.72rem;
		letter-spacing: 0.08em;
		color: var(--app-accent);
		font-weight: 500;
	}
	.pillar-title {
		color: var(--app-text);
	}
	.pillar-body {
		color: var(--app-text-muted);
	}

	/* Snippet split */
	.snippet {
		display: grid;
		grid-template-columns: 1fr;
		gap: 1rem;
		padding: 1.5rem;
		border: 1px solid var(--app-border);
		border-radius: var(--app-radius-lg);
		background: var(--app-surface);
	}
	@media (min-width: 720px) {
		.snippet { grid-template-columns: 1.2fr 1fr; gap: 1.5rem; }
	}
	.snippet-text { display: flex; flex-direction: column; gap: 0.65rem; min-width: 0; }
	.snippet-code {
		margin: 0;
		padding: 0.9rem 1rem;
		background: var(--app-bg);
		border: 1px solid var(--app-border);
		border-radius: var(--app-radius);
		font-size: 0.78rem;
		line-height: 1.6;
		color: var(--app-text);
		overflow-x: auto;
		font-feature-settings: 'tnum' 1, 'lnum' 1;
	}
	.snippet-shape {
		display: flex;
		flex-direction: column;
		gap: 0.65rem;
		align-items: stretch;
	}
	.snippet-preview {
		width: 100%;
		max-height: 320px;
		background: var(--app-bg);
		border: 1px solid var(--app-border);
		border-radius: var(--app-radius);
		background-image: radial-gradient(circle at 1px 1px, var(--app-rule) 1px, transparent 0);
		background-size: 14px 14px;
	}

	/* Primer card */
	.primer {
		display: flex;
		gap: 1rem;
		align-items: flex-start;
		padding: 1.1rem 1.25rem;
		border: 1px dashed var(--app-border-strong);
		border-radius: var(--app-radius);
		background: color-mix(in srgb, var(--app-accent) 5%, var(--app-bg) 95%);
	}
	.primer .step-glyph {
		width: 1.4rem;
		height: 1.4rem;
		margin-top: 0.2rem;
		flex-shrink: 0;
	}

	kbd {
		display: inline-block;
		padding: 0 0.35rem;
		font-size: 0.78em;
		font-family: var(--app-mono-font);
		background: var(--app-surface);
		border: 1px solid var(--app-border);
		border-bottom-width: 2px;
		border-radius: 4px;
		color: var(--app-text);
	}
</style>
