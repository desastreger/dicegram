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
	class="mx-auto flex w-full max-w-6xl flex-col items-center gap-6 px-4 py-10 text-center text-app sm:gap-8 sm:px-6 sm:py-16"
>
	<h1
		class="w-full bg-gradient-to-b from-neutral-50 to-neutral-400 bg-clip-text text-4xl font-bold leading-tight tracking-tight break-words text-transparent sm:text-5xl md:text-6xl"
	>
		Dicegram
	</h1>
	<p class="max-w-xl text-base break-words text-muted sm:text-lg">
		Roll plain text into living diegrams. Write a step, get a shape. Share, save, version.
	</p>
	<div class="flex flex-wrap justify-center gap-3">
		{#if auth.user}
			<a href="/editor" class="btn-primary px-6 py-2.5">
				Open editor
			</a>
		{:else}
			<a href="/signup" class="btn-primary px-6 py-2.5">
				Get started
			</a>
			<a href="/editor?demo=1" class="btn-secondary px-6 py-2.5">
				Try without an account
			</a>
			<a href="/login" class="btn-secondary px-6 py-2.5">
				Log in
			</a>
		{/if}
		<button
			type="button"
			onclick={() => (llmOpen = true)}
			class="btn-secondary flex items-center gap-2 px-6 py-2.5"
		>
			<Icon name="sparkles" size={14} />
			Use with an LLM
		</button>
	</div>

	<!-- Live editor iframe: the real /editor route in landing mode. Same
	     Canvas + CodeEditor + render pipeline as the full app, just with
	     toolbar / inspector / tree / autosave stripped. -->
	<div class="panel mini-editor w-full overflow-hidden text-left">
		<div class="flex items-center justify-between border-b border-app px-3 py-1.5">
			<span class="text-[10px] uppercase tracking-wide text-dim"
				>Try it — edit on the left</span
			>
			<a href="/editor?demo=1" class="link text-[11px]">
				Open full editor →
			</a>
		</div>
		<iframe
			src={editorSrc}
			title="Dicegram live editor"
			class="block w-full border-0"
			style="height: min(60vh, 460px); background: var(--app-bg)"
			loading="lazy"
		></iframe>
	</div>

	<div class="mt-4 grid w-full grid-cols-1 gap-4 text-left sm:grid-cols-2 lg:grid-cols-3">
		<div class="panel min-w-0 p-5">
			<h2 class="mb-2 font-semibold text-app">Text-first</h2>
			<p class="text-sm break-words text-muted">
				Describe flows as steps. The layout engine does the boring positioning for you.
			</p>
		</div>
		<div class="panel min-w-0 p-5">
			<h2 class="mb-2 font-semibold text-app">Familiar shapes</h2>
			<p class="text-sm break-words text-muted">
				Process, decision, data store, start/end — the shapes your stakeholders already read.
			</p>
		</div>
		<div class="panel min-w-0 p-5">
			<h2 class="mb-2 font-semibold text-app">Canonical source</h2>
			<p class="text-sm break-words text-muted">
				The DSL is the source of truth. Code, canvas and inspector are three windows into the
				same file.
			</p>
		</div>
	</div>
</section>

<LlmPromptDialog bind:open={llmOpen} promptText={LLM_PROMPT_FOR_COPY} />
