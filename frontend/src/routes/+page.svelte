<script lang="ts">
	import { auth } from '$lib/auth.svelte';
</script>

<svelte:head>
	<title>Dicegram</title>
</svelte:head>

<section
	class="mx-auto flex max-w-4xl flex-col items-center gap-8 px-6 py-24 text-center text-neutral-100"
>
	<h1
		class="bg-gradient-to-b from-neutral-50 to-neutral-400 bg-clip-text text-6xl font-bold tracking-tight text-transparent"
	>
		Dicegram
	</h1>
	<p class="max-w-xl text-lg text-neutral-400">
		Roll plain text into living Dicegrams. Write a step, get a shape. Share, save, version.
	</p>
	<div class="flex gap-3">
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
				href="/login"
				class="rounded-md border border-neutral-700 px-6 py-2.5 font-medium text-neutral-200 hover:bg-neutral-900"
			>
				Log in
			</a>
		{/if}
	</div>

	<div class="mt-12 grid w-full grid-cols-1 gap-4 text-left sm:grid-cols-3">
		<div class="rounded-lg border border-neutral-800 bg-neutral-950/60 p-5">
			<h3 class="mb-2 font-semibold text-neutral-100">Text-first</h3>
			<p class="text-sm text-neutral-400">
				Describe flows as steps. The layout engine does the boring positioning for you.
			</p>
		</div>
		<div class="rounded-lg border border-neutral-800 bg-neutral-950/60 p-5">
			<h3 class="mb-2 font-semibold text-neutral-100">Visio shapes</h3>
			<p class="text-sm text-neutral-400">
				Process, decision, data store, start/end — the shapes your stakeholders already read.
			</p>
		</div>
		<div class="rounded-lg border border-neutral-800 bg-neutral-950/60 p-5">
			<h3 class="mb-2 font-semibold text-neutral-100">Canonical source</h3>
			<p class="text-sm text-neutral-400">
				The DSL is the source of truth. Code, canvas and inspector are three windows into the
				same file.
			</p>
		</div>
	</div>
</section>
