<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { auth } from '$lib/auth.svelte';
	import { dicegrams, type Dicegram } from '$lib/dicegrams';
	import { api } from '$lib/api';
	import Icon from '$lib/Icon.svelte';

	let items = $state<Dicegram[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let renamingId = $state<number | null>(null);
	let renameValue = $state('');
	let toast = $state<string | null>(null);
	let toastTimer: ReturnType<typeof setTimeout> | null = null;

	$effect(() => {
		if (!auth.loading && !auth.user) {
			const here = page.url.pathname + page.url.search;
			goto(`/login?next=${encodeURIComponent(here)}`);
		}
	});

	$effect(() => {
		if (!auth.loading && auth.user) load();
	});

	async function load() {
		loading = true;
		error = null;
		try {
			items = await dicegrams.list();
		} catch (err) {
			error = err instanceof Error ? err.message : 'failed to load diegrams';
		} finally {
			loading = false;
		}
	}

	function showToast(msg: string) {
		toast = msg;
		if (toastTimer) clearTimeout(toastTimer);
		toastTimer = setTimeout(() => {
			toast = null;
		}, 2000);
	}

	function open(d: Dicegram) {
		goto('/editor?id=' + d.id);
	}

	function startRename(d: Dicegram) {
		renamingId = d.id;
		renameValue = d.name;
	}

	function cancelRename() {
		renamingId = null;
		renameValue = '';
	}

	async function commitRename(d: Dicegram) {
		const newName = renameValue.trim();
		if (!newName || newName === d.name) {
			cancelRename();
			return;
		}
		try {
			await dicegrams.update(d.id, { name: newName, source: d.source });
			cancelRename();
			await load();
		} catch (err) {
			showToast(err instanceof Error ? err.message : 'rename failed');
		}
	}

	function onRenameKey(e: KeyboardEvent, d: Dicegram) {
		if (e.key === 'Enter') {
			e.preventDefault();
			commitRename(d);
		} else if (e.key === 'Escape') {
			e.preventDefault();
			cancelRename();
		}
	}

	async function duplicate(d: Dicegram) {
		const name = `${d.name} (copy)`;
		try {
			const created = await dicegrams.create({ name, source: d.source });
			await load();
			startRename(created);
		} catch (err) {
			showToast(err instanceof Error ? err.message : 'duplicate failed');
		}
	}

	let confirmDeleteId = $state<number | null>(null);
	let confirmTimer: ReturnType<typeof setTimeout> | null = null;

	function armDelete(d: Dicegram) {
		confirmDeleteId = d.id;
		if (confirmTimer) clearTimeout(confirmTimer);
		confirmTimer = setTimeout(() => {
			confirmDeleteId = null;
		}, 3000);
	}

	async function remove(d: Dicegram) {
		if (confirmDeleteId !== d.id) {
			armDelete(d);
			return;
		}
		if (confirmTimer) clearTimeout(confirmTimer);
		confirmDeleteId = null;
		try {
			await dicegrams.remove(d.id);
			await load();
		} catch (err) {
			showToast(err instanceof Error ? err.message : 'delete failed');
		}
	}

	async function share(d: Dicegram) {
		try {
			const res = await api.post<{ slug: string }>(`/dicegrams/${d.id}/share`);
			const url = `${location.origin}/d/${res.slug}`;
			await navigator.clipboard.writeText(url);
			showToast('Share link copied');
		} catch (err) {
			showToast(err instanceof Error ? err.message : 'share failed');
		}
	}

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
</script>

<svelte:head><title>My diegrams · Dicegram</title></svelte:head>

<section class="mx-auto max-w-6xl px-4 py-6 text-app">
	<div class="mb-4 flex items-center justify-between">
		<h1 class="flex items-baseline gap-2 text-lg font-semibold">
			My diegrams
			<span class="text-xs text-dim">{items.length}</span>
		</h1>
		<button
			type="button"
			onclick={() => goto('/editor')}
			class="btn-primary flex items-center gap-1 text-xs"
		>
			<Icon name="plus" size={14} />
			New dicegram
		</button>
	</div>

	{#if loading}
		<p role="status" aria-live="polite" class="text-xs text-muted">Loading diegrams…</p>
	{:else if error}
		<div role="alert" class="toast toast-error p-3 text-xs">
			<p class="font-medium text-app">Could not load diegrams</p>
			<p class="mt-1 text-danger">{error}</p>
			<button type="button" onclick={load} class="btn-danger mt-2 text-[11px]">
				Try again
			</button>
		</div>
	{:else if items.length === 0}
		<div class="panel p-10 text-center" style="border-style: dashed;">
			<p class="text-sm text-app">You don't have any diegrams yet.</p>
			<p class="mt-1 text-xs text-dim">
				Start with a blank canvas and your work will show up here.
			</p>
			<button
				type="button"
				onclick={() => goto('/editor')}
				class="btn-primary mt-4 inline-flex items-center gap-1 text-xs"
			>
				<Icon name="plus" size={14} />
				Create your first dicegram
			</button>
		</div>
	{:else}
		<div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
			{#each items as d (d.id)}
				<article class="panel overflow-hidden transition hover:border-strong">
					<button
						type="button"
						onclick={() => open(d)}
						class="flex aspect-video w-full items-center justify-center overflow-hidden border-b border-app bg-surface-2"
						aria-label={`Open ${d.name}`}
					>
						<img
							src={`/api/dicegrams/${d.id}/svg`}
							alt={`Thumbnail for ${d.name}`}
							class="max-h-full max-w-full object-contain"
							loading="lazy"
						/>
					</button>
					<div class="p-2.5">
						{#if renamingId === d.id}
							<input
								type="text"
								bind:value={renameValue}
								onkeydown={(e) => onRenameKey(e, d)}
								onblur={() => commitRename(d)}
								aria-label={`Rename ${d.name}`}
								class="input-themed w-full text-sm font-medium"
							/>
						{:else}
							<button
								type="button"
								onclick={() => open(d)}
								class="block w-full truncate text-left text-sm font-medium text-app hover:text-accent"
							>
								{d.name}
							</button>
						{/if}
						<p class="mt-0.5 text-[10px] text-dim">
							Updated {formatDate(d.updated_at)}
						</p>
						<div class="mt-2 flex items-center gap-0.5">
							<button
								type="button"
								onclick={() => startRename(d)}
								title="Rename"
								aria-label={`Rename ${d.name}`}
								class="btn-icon"
							>
								<Icon name="pencil" size={13} />
							</button>
							<button
								type="button"
								onclick={() => duplicate(d)}
								title="Duplicate"
								aria-label={`Duplicate ${d.name}`}
								class="btn-icon"
							>
								<Icon name="duplicate" size={13} />
							</button>
							<button
								type="button"
								onclick={() => share(d)}
								title="Copy share link"
								aria-label={`Copy share link for ${d.name}`}
								class="btn-icon"
							>
								<Icon name="share" size={13} />
							</button>
							<span class="flex-1"></span>
							<button
								type="button"
								onclick={() => remove(d)}
								title={confirmDeleteId === d.id ? 'Click again to confirm' : 'Delete'}
								aria-label={confirmDeleteId === d.id
									? `Confirm delete ${d.name}`
									: `Delete ${d.name}`}
								class="btn-icon flex items-center gap-1 {confirmDeleteId === d.id
									? 'btn-icon-active text-danger'
									: 'hover:text-danger'}"
							>
								<Icon name="trash" size={13} />
								{#if confirmDeleteId === d.id}<span class="text-[10px]">Confirm?</span>{/if}
							</button>
						</div>
					</div>
				</article>
			{/each}
		</div>
	{/if}

	{#if toast}
		<div
			role="status"
			aria-live="polite"
			class="toast fixed right-4 bottom-4 flex items-center gap-1.5"
		>
			<Icon name="check" size={13} />
			{toast}
		</div>
	{/if}
</section>
