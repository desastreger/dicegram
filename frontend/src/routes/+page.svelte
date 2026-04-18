<script lang="ts">
	import { auth } from '$lib/auth.svelte';
	import { getTheme } from '$lib/themes';
	import { renderDsl, type RenderResult } from '$lib/render';
	import { LLM_PROMPT_TEMPLATE } from '$lib/export';
	import Icon from '$lib/Icon.svelte';
	import Canvas from './editor/Canvas.svelte';
	import CodeEditor from './editor/CodeEditor.svelte';

	let llmOpen = $state(false);
	let llmCopied = $state(false);

	const LLM_PROMPT_FOR_COPY = LLM_PROMPT_TEMPLATE.replace(
		'{SOURCE}',
		'(paste your dicegram source here, or describe what you want and ask the LLM to write it)'
	);

	async function copyLlmPrompt() {
		try {
			await navigator.clipboard.writeText(LLM_PROMPT_FOR_COPY);
			llmCopied = true;
			setTimeout(() => (llmCopied = false), 1500);
		} catch {
			/* ignore */
		}
	}

	function closeLlm(e: KeyboardEvent | MouseEvent) {
		if ('key' in e && e.key !== 'Escape') return;
		llmOpen = false;
	}

	const STARTER_SOURCE = `direction left-to-right
swimlane "Author" {
	[circle] idea "Idea" type:start
	[rect] draft "Draft" step:1
}
swimlane "Review" {
	[diamond] ok "Ship?" step:2 type:decision
}
swimlane "Release" {
	[hexagon] ship "Ship" step:3 type:automated
	[circle] done "Done" type:end
}
idea -> draft
draft -> ok
ok -> ship : "yes"
ship -> done`;

	let source = $state(STARTER_SOURCE);
	let result = $state<RenderResult | null>(null);
	let theme = $state(getTheme('default-dark'));
	let debounceTimer: ReturnType<typeof setTimeout> | undefined;

	$effect(() => {
		const src = source;
		clearTimeout(debounceTimer);
		debounceTimer = setTimeout(() => {
			renderDsl(src, true)
				.then((r) => {
					result = r;
				})
				.catch(() => {
					/* keep previous result on transient errors */
				});
		}, 200);
	});
</script>

<svelte:head>
	<title>Dicegram</title>
</svelte:head>

<section
	class="mx-auto flex w-full max-w-6xl flex-col items-center gap-6 px-4 py-10 text-center text-neutral-100 sm:gap-8 sm:px-6 sm:py-16"
>
	<h1
		class="w-full bg-gradient-to-b from-neutral-50 to-neutral-400 bg-clip-text text-4xl font-bold leading-tight tracking-tight break-words text-transparent sm:text-5xl md:text-6xl"
	>
		Dicegram
	</h1>
	<p class="max-w-xl text-base break-words text-neutral-400 sm:text-lg">
		Roll plain text into living Dicegrams. Write a step, get a shape. Share, save, version.
	</p>
	<div class="flex flex-wrap justify-center gap-3">
		{#if auth.user}
			<a
				href="/editor"
				class="rounded-md bg-blue-600 px-6 py-2.5 font-medium text-white shadow-lg shadow-blue-900/40 hover:bg-blue-500"
			>
				Open editor
			</a>
		{:else}
			<a
				href="/signup"
				class="rounded-md bg-blue-600 px-6 py-2.5 font-medium text-white shadow-lg shadow-blue-900/40 hover:bg-blue-500"
			>
				Get started
			</a>
			<a
				href="/editor?demo=1"
				class="rounded-md border border-blue-700/70 bg-blue-900/20 px-6 py-2.5 font-medium text-blue-100 hover:bg-blue-900/40"
			>
				Try without an account
			</a>
			<a
				href="/login"
				class="rounded-md border border-neutral-700 px-6 py-2.5 font-medium text-neutral-200 hover:bg-neutral-900"
			>
				Log in
			</a>
		{/if}
		<button
			type="button"
			onclick={() => (llmOpen = true)}
			class="flex items-center gap-2 rounded-md border border-purple-700/70 bg-purple-900/20 px-6 py-2.5 font-medium text-purple-100 hover:bg-purple-900/40"
		>
			<Icon name="sparkles" size={14} />
			Use with an LLM
		</button>
	</div>

	<!-- Mini live editor: the real CodeEditor + Canvas components,
	     sized down and stripped of Toolbar / Inspector / Tree. -->
	<div
		class="mini-editor w-full overflow-hidden rounded-lg border border-neutral-800 bg-neutral-950 text-left shadow-xl"
	>
		<div class="flex items-center justify-between border-b border-neutral-800 px-3 py-1.5">
			<span class="text-[10px] uppercase tracking-wide text-neutral-500">Try it — edit on the left</span>
			<a
				href="/editor?demo=1"
				class="text-[11px] text-blue-400 hover:text-blue-300 hover:underline"
			>
				Open full editor →
			</a>
		</div>
		<div
			class="grid min-h-0 grid-cols-1 md:grid-cols-2"
			style="height: min(60vh, 460px)"
		>
			<div
				class="min-w-0 overflow-hidden border-b border-neutral-800 text-left md:border-r md:border-b-0"
			>
				<CodeEditor bind:value={source} {theme} />
			</div>
			<div class="min-w-0" style:background-color={theme.canvas}>
				<Canvas {result} {theme} />
			</div>
		</div>
	</div>

	<div class="mt-4 grid w-full grid-cols-1 gap-4 text-left sm:grid-cols-2 lg:grid-cols-3">
		<div class="min-w-0 rounded-lg border border-neutral-800 bg-neutral-950/60 p-5">
			<h3 class="mb-2 font-semibold text-neutral-100">Text-first</h3>
			<p class="text-sm break-words text-neutral-400">
				Describe flows as steps. The layout engine does the boring positioning for you.
			</p>
		</div>
		<div class="min-w-0 rounded-lg border border-neutral-800 bg-neutral-950/60 p-5">
			<h3 class="mb-2 font-semibold text-neutral-100">Visio shapes</h3>
			<p class="text-sm break-words text-neutral-400">
				Process, decision, data store, start/end — the shapes your stakeholders already read.
			</p>
		</div>
		<div class="min-w-0 rounded-lg border border-neutral-800 bg-neutral-950/60 p-5">
			<h3 class="mb-2 font-semibold text-neutral-100">Canonical source</h3>
			<p class="text-sm break-words text-neutral-400">
				The DSL is the source of truth. Code, canvas and inspector are three windows into the
				same file.
			</p>
		</div>
	</div>
</section>

{#if llmOpen}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
		onclick={closeLlm}
		onkeydown={closeLlm}
		role="dialog"
		aria-modal="true"
		aria-label="Use Dicegram with an LLM"
	>
		<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
		<div
			class="flex max-h-[90vh] w-full max-w-2xl flex-col overflow-hidden rounded-lg border border-neutral-800 bg-neutral-950 text-left text-neutral-100 shadow-2xl"
			onclick={(e) => e.stopPropagation()}
		>
			<header class="flex items-center justify-between border-b border-neutral-800 px-4 py-3">
				<div class="flex items-center gap-2">
					<Icon name="sparkles" size={14} />
					<h2 class="text-sm font-semibold">Use Dicegram with an LLM</h2>
				</div>
				<button
					type="button"
					onclick={() => (llmOpen = false)}
					class="rounded p-1 text-neutral-400 hover:bg-neutral-900 hover:text-neutral-100"
					aria-label="Close"
				>
					<Icon name="x" size={14} />
				</button>
			</header>
			<div class="min-h-0 flex-1 overflow-auto p-4">
				<p class="mb-3 text-xs text-neutral-400">
					Copy this prompt, paste it into any chat model. Put your current DSL
					(or a description of what you want) where it asks, and the model will
					return a full DSL block you can paste back into the editor.
				</p>
				<pre
					class="max-h-[40vh] overflow-auto rounded border border-neutral-800 bg-neutral-900 p-3 font-mono text-[11px] whitespace-pre-wrap text-neutral-200">{LLM_PROMPT_FOR_COPY}</pre>
				<div class="mt-3 flex flex-wrap items-center gap-2">
					<button
						type="button"
						onclick={copyLlmPrompt}
						class="flex items-center gap-1.5 rounded border border-neutral-700 bg-neutral-800 px-3 py-1.5 text-xs font-medium text-neutral-100 hover:bg-neutral-700"
					>
						<Icon name={llmCopied ? 'check' : 'copy'} size={13} />
						{llmCopied ? 'Copied to clipboard' : 'Copy prompt'}
					</button>
				</div>
				<div class="mt-5 border-t border-neutral-800 pt-4">
					<p class="mb-2 text-[10px] uppercase tracking-wide text-neutral-500">
						Open a chat
					</p>
					<div class="flex flex-wrap gap-2">
						<a
							href="https://claude.ai/new"
							target="_blank"
							rel="noopener noreferrer"
							class="flex items-center gap-1.5 rounded border border-neutral-800 bg-neutral-900 px-3 py-1.5 text-xs text-neutral-100 hover:bg-neutral-800"
						>
							Claude
							<Icon name="arrow-right" size={12} />
						</a>
						<a
							href="https://chatgpt.com/"
							target="_blank"
							rel="noopener noreferrer"
							class="flex items-center gap-1.5 rounded border border-neutral-800 bg-neutral-900 px-3 py-1.5 text-xs text-neutral-100 hover:bg-neutral-800"
						>
							ChatGPT
							<Icon name="arrow-right" size={12} />
						</a>
						<a
							href="https://gemini.google.com/app"
							target="_blank"
							rel="noopener noreferrer"
							class="flex items-center gap-1.5 rounded border border-neutral-800 bg-neutral-900 px-3 py-1.5 text-xs text-neutral-100 hover:bg-neutral-800"
						>
							Gemini
							<Icon name="arrow-right" size={12} />
						</a>
					</div>
				</div>
			</div>
		</div>
	</div>
{/if}

<svelte:window onkeydown={(e) => e.key === 'Escape' && llmOpen && (llmOpen = false)} />
