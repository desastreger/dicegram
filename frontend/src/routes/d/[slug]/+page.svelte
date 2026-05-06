<script lang="ts">
	import { page } from '$app/state';
	import { ApiError } from '$lib/api';
	import { auth } from '$lib/auth.svelte';
	import Icon from '$lib/Icon.svelte';

	type PublicDicegram = { name: string; source: string; updated_at: string };

	const slug = $derived(page.params.slug);
	let data = $state<PublicDicegram | null>(null);
	let error = $state<string | null>(null);
	let loading = $state(true);
	let copied = $state(false);
	let dslCopied = $state(false);

	$effect(() => {
		const s = slug;
		loading = true;
		error = null;
		data = null;
		fetch(`/api/shares/${s}`)
			.then(async (r) => {
				if (!r.ok) {
					const body = await r.json().catch(() => ({ detail: r.statusText }));
					throw new ApiError(r.status, body.detail ?? 'not found');
				}
				return r.json() as Promise<PublicDicegram>;
			})
			.then((d: PublicDicegram) => {
				data = d;
				loading = false;
			})
			.catch((err) => {
				error = err instanceof ApiError ? err.message : 'could not load shared dicegram';
				loading = false;
			});
	});

	function formatDate(s: string) {
		const d = new Date(s);
		if (isNaN(d.getTime())) return s;
		return d.toLocaleString(undefined, {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	async function copyLink() {
		try {
			await navigator.clipboard.writeText(location.href);
			copied = true;
			setTimeout(() => (copied = false), 1500);
		} catch {
			/* ignore */
		}
	}

	async function copyDsl() {
		if (!data) return;
		try {
			await navigator.clipboard.writeText(data.source);
			dslCopied = true;
			setTimeout(() => (dslCopied = false), 1500);
		} catch {
			/* ignore */
		}
	}

	function download() {
		const a = document.createElement('a');
		a.href = `/api/shares/${slug}/svg`;
		const base = (data?.name ?? 'dicegram').replace(/[^\w.-]+/g, '_');
		a.download = `${base || 'dicegram'}.svg`;
		a.click();
	}
</script>

<svelte:head>
	<title>{data?.name ? `${data.name} · Dicegram` : 'Shared dicegram · Dicegram'}</title>
</svelte:head>

<section class="mx-auto max-w-6xl px-4 py-6 text-app">
	{#if loading}
		<p role="status" aria-live="polite" class="text-xs text-dim">Loading…</p>
	{:else if error}
		<div role="alert" class="toast toast-error p-4 text-xs">
			<p class="font-medium text-app">Could not load shared dicegram</p>
			<p class="mt-1 text-danger">{error}</p>
			<p class="mt-2 text-muted">
				The owner may have revoked the link, or the URL is wrong.
			</p>
			<div class="mt-3 flex gap-2">
				<a href="/" class="btn-secondary text-xs">Go to Dicegram home</a>
				{#if auth.user}
					<a href="/editor" class="btn-primary text-xs">Open editor</a>
				{:else}
					<a href="/signup" class="btn-primary text-xs">Create your own</a>
				{/if}
			</div>
		</div>
	{:else if data}
		<div class="mb-3 flex flex-wrap items-center justify-between gap-2">
			<div class="min-w-0">
				<h1 class="flex items-center gap-2 truncate text-lg font-semibold">
					<Icon name="eye" size={16} />
					{data.name}
				</h1>
				<p class="mt-0.5 text-[11px] text-dim">
					Shared dicegram — updated {formatDate(data.updated_at)}
				</p>
			</div>
			<div class="flex items-center gap-1">
				<button
					type="button"
					onclick={copyLink}
					title="Copy link"
					class="btn-secondary flex items-center gap-1 text-xs"
				>
					<Icon name={copied ? 'check' : 'link'} size={13} />
					{copied ? 'Copied' : 'Copy link'}
				</button>
				<button
					type="button"
					onclick={copyDsl}
					title="Copy DSL source"
					class="btn-secondary flex items-center gap-1 text-xs"
				>
					<Icon name={dslCopied ? 'check' : 'copy'} size={13} />
					{dslCopied ? 'Copied' : 'Copy DSL'}
				</button>
				<button
					type="button"
					onclick={download}
					title="Download SVG"
					class="btn-secondary flex items-center gap-1 text-xs"
				>
					<Icon name="download" size={13} /> SVG
				</button>
			</div>
		</div>

		<div
			class="panel overflow-auto p-2"
			style="max-height: calc(100vh - var(--header-h) - 140px)"
		>
			<img
				src={`/api/shares/${slug}/svg`}
				alt={data.name}
				class="mx-auto block max-w-full"
			/>
		</div>

		<details class="panel mt-4 p-3 text-xs">
			<summary class="cursor-pointer text-muted hover:text-app">
				View DSL source
			</summary>
			<pre
				class="mt-2 overflow-auto rounded bg-surface-2 p-3 font-mono text-[11px] text-app">{data.source}</pre>
		</details>
	{/if}
</section>
