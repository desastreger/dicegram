<script lang="ts">
	import { auth } from '$lib/auth.svelte';
	import { LLM_PROMPT_TEMPLATE } from '$lib/export';
	import Icon from '$lib/Icon.svelte';
	import LlmPromptDialog from '$lib/LlmPromptDialog.svelte';
	import { DEFAULT_TEMPLATE_ID } from '$lib/templates';

	let llmOpen = $state(false);

	const LLM_PROMPT_FOR_COPY = LLM_PROMPT_TEMPLATE.replace(
		'{SOURCE}',
		'(paste your dicegram source here, or describe what you want and ask the LLM to write it)'
	);

	// Mount the live editor as an iframe pointing at the same /editor
	// route the app uses, in `landing` mode. This means the homepage
	// always runs the current editor — new features (syntax, inspector,
	// line-style brackets, etc.) land here automatically and can never
	// drift behind the main app the way the old inline mini-editor did.
	const editorSrc = `/editor?mode=landing&template=${DEFAULT_TEMPLATE_ID}`;
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
		Roll plain text into living diegrams. Write a step, get a shape. Share, save, version.
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

	<!-- Live editor iframe: the real /editor route in landing mode. Same
	     Canvas + CodeEditor + render pipeline as the full app, just with
	     toolbar / inspector / tree / autosave stripped. -->
	<div
		class="mini-editor w-full overflow-hidden rounded-lg border border-neutral-800 bg-neutral-950 text-left shadow-xl"
	>
		<div class="flex items-center justify-between border-b border-neutral-800 px-3 py-1.5">
			<span class="text-[10px] uppercase tracking-wide text-neutral-500"
				>Try it — edit on the left</span
			>
			<a
				href="/editor?demo=1"
				class="text-[11px] text-blue-400 hover:text-blue-300 hover:underline"
			>
				Open full editor →
			</a>
		</div>
		<iframe
			src={editorSrc}
			title="Dicegram live editor"
			class="block w-full border-0"
			style="height: min(60vh, 460px); background: #0a0a0a"
			loading="lazy"
		></iframe>
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

<LlmPromptDialog bind:open={llmOpen} promptText={LLM_PROMPT_FOR_COPY} />
