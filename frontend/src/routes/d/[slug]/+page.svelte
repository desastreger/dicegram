<script lang="ts">
	import { page } from '$app/state';
	import { ApiError } from '$lib/api';
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

<section class="mx-auto max-w-6xl px-4 py-6 text-neutral-100">
	{#if loading}
		<p class="text-xs text-neutral-500">Loading…</p>
	{:else if error}
		<div class="rounded border border-red-900 bg-red-950/50 p-4 text-xs text-red-300">
			<p class="font-medium">Could not load shared dicegram</p>
			<p class="mt-1 text-red-400">{error}</p>
			<p class="mt-2 text-neutral-400">
				The owner may have revoked the link, or the URL is wrong.
			</p>
			<div class="mt-3 flex gap-2">
				<a
					href="/"
					class="rounded border border-neutral-700 px-3 py-1 text-xs text-neutral-200 hover:bg-neutral-800"
				>
					Go to Dicegram home
				</a>
				<a
					href="/signup"
					class="rounded bg-blue-600 px-3 py-1 text-xs font-medium text-white hover:bg-blue-500"
				>
					Create your own
				</a>
			</div>
		</div>
	{:else if data}
		<div class="mb-3 flex flex-wrap items-center justify-between gap-2">
			<div class="min-w-0">
				<h1 class="flex items-center gap-2 truncate text-lg font-semibold">
					<Icon name="eye" size={16} />
					{data.name}
				</h1>
				<p class="mt-0.5 text-[11px] text-neutral-500">
					Shared dicegram — updated {formatDate(data.updated_at)}
				</p>
			</div>
			<div class="flex items-center gap-1">
				<button
					type="button"
					onclick={copyLink}
					title="Copy link"
					class="flex items-center gap-1 rounded border border-neutral-800 px-2 py-1 text-xs text-neutral-200 hover:bg-neutral-800"
				>
					<Icon name={copied ? 'check' : 'link'} size={13} />
					{copied ? 'Copied' : 'Copy link'}
				</button>
				<button
					type="button"
					onclick={copyDsl}
					title="Copy DSL source"
					class="flex items-center gap-1 rounded border border-neutral-800 px-2 py-1 text-xs text-neutral-200 hover:bg-neutral-800"
				>
					<Icon name={dslCopied ? 'check' : 'copy'} size={13} />
					{dslCopied ? 'Copied' : 'Copy DSL'}
				</button>
				<button
					type="button"
					onclick={download}
					title="Download SVG"
					class="flex items-center gap-1 rounded border border-neutral-800 px-2 py-1 text-xs text-neutral-200 hover:bg-neutral-800"
				>
					<Icon name="download" size={13} /> SVG
				</button>
			</div>
		</div>

		<div
			class="overflow-auto rounded-lg border border-neutral-800 bg-neutral-950 p-2"
			style="max-height: calc(100vh - var(--header-h) - 140px)"
		>
			<img
				src={`/api/shares/${slug}/svg`}
				alt={data.name}
				class="mx-auto block max-w-full"
			/>
		</div>

		<details class="mt-4 rounded border border-neutral-800 bg-neutral-950 p-3 text-xs">
			<summary class="cursor-pointer text-neutral-400 hover:text-neutral-200">
				View DSL source
			</summary>
			<pre
				class="mt-2 overflow-auto rounded bg-neutral-900 p-3 font-mono text-[11px] text-neutral-200">{data.source}</pre>
		</details>
	{/if}
</section>
