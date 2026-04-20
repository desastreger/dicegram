<script lang="ts">
	import { page } from '$app/state';
	import { ApiError } from '$lib/api';
	import { renderDsl, type RenderResult } from '$lib/render';
	import { getTheme } from '$lib/themes';
	import Canvas from '../../editor/Canvas.svelte';
	import CodeEditor from '../../editor/CodeEditor.svelte';
	import EdgeMarkers from '../../editor/EdgeMarkers.svelte';

	type PublicDicegram = { name: string; source: string; updated_at: string };

	const slug = $derived(page.params.slug);
	const showCode = $derived(page.url.searchParams.get('code') !== '0');
	let data = $state<PublicDicegram | null>(null);
	let error = $state<string | null>(null);
	let loading = $state(true);
	let source = $state('');
	let result = $state<RenderResult | null>(null);
	const theme = getTheme('default-dark');
	let debounceTimer: ReturnType<typeof setTimeout> | undefined;

	$effect(() => {
		const s = slug;
		loading = true;
		error = null;
		fetch(`/api/shares/${s}`)
			.then(async (r) => {
				if (!r.ok) {
					const body = await r.json().catch(() => ({ detail: r.statusText }));
					throw new ApiError(r.status, body.detail ?? 'not found');
				}
				return r.json() as Promise<PublicDicegram>;
			})
			.then((d) => {
				data = d;
				source = d.source;
				loading = false;
			})
			.catch((err) => {
				error = err instanceof ApiError ? err.message : 'could not load shared dicegram';
				loading = false;
			});
	});

	$effect(() => {
		const src = source;
		if (!src) return;
		clearTimeout(debounceTimer);
		debounceTimer = setTimeout(() => {
			renderDsl(src, false)
				.then((r) => (result = r))
				.catch(() => {
					/* keep previous */
				});
		}, 100);
	});
</script>

<svelte:head>
	<title>{data?.name ?? 'Shared dicegram'} — Dicegram</title>
</svelte:head>

<div class="flex h-screen w-screen flex-col" style:background={theme.canvas}>
	<EdgeMarkers />
	{#if loading}
		<div class="flex flex-1 items-center justify-center text-xs text-neutral-500">
			Loading…
		</div>
	{:else if error}
		<div class="flex flex-1 items-center justify-center p-6 text-center text-xs text-red-400">
			<div>
				<p class="font-medium">Could not load shared dicegram</p>
				<p class="mt-1">{error}</p>
			</div>
		</div>
	{:else}
		<div
			class="grid flex-1 overflow-hidden"
			style:grid-template-columns={showCode ? 'minmax(280px, 1fr) minmax(0, 2fr)' : '1fr'}
		>
			{#if showCode}
				<section
					class="relative flex flex-col border-r"
					style:background-color={theme.codeBg}
					style:border-color={theme.panelBorder}
				>
					<CodeEditor bind:value={source} {theme} readOnly />
				</section>
			{/if}
			<section class="relative flex min-w-0 flex-col" style:background-color={theme.canvas}>
				<Canvas {result} {theme} />
			</section>
		</div>
	{/if}
</div>
