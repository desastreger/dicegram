<script lang="ts">
	// Admin-only instance stats.
	//
	// The funnel is rendered by Dicegram itself: the backend hands back a DSL
	// document and we post it to /api/export/svg, the same endpoint a user's
	// export goes through. So this page is a dicegram, and any rendering bug
	// visible here is one a user would hit too — which is rather the point.
	import { onMount } from 'svelte';
	import { ApiError, api } from '$lib/api';

	type Stats = {
		accounts: number;
		dicegrams: number;
		shares: number;
		accounts_7d: number;
		dicegrams_7d: number;
		requests_7d: number | null;
		renders_7d: number | null;
		exports_7d: number | null;
		errors_7d: number | null;
		renders_by_day: [string, number][];
		top_paths: [string, number][];
		log_available: boolean;
		dsl: string;
	};

	let stats = $state<Stats | null>(null);
	let svg = $state('');
	let error = $state<string | null>(null);
	let loading = $state(true);

	onMount(async () => {
		try {
			stats = await api.get<Stats>('/admin/stats');
			const res = await fetch('/api/export/svg', {
				method: 'POST',
				credentials: 'include',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ source: stats.dsl })
			});
			if (res.ok) {
				// Rendered via an <img> data URI rather than {@html}. An SVG
				// loaded as an image cannot execute script, so this keeps the
				// codebase's "no {@html}, no innerHTML" invariant intact — worth
				// more than the marginal convenience of inlining it, even for an
				// admin-only page. CSP already permits img-src 'self' data:.
				const raw = await res.text();
				svg = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(raw)));
			}
		} catch (err) {
			// current_admin returns 404 rather than 403, so a signed-in
			// non-admin cannot tell this surface exists. Mirror that here.
			error =
				err instanceof ApiError && (err.status === 404 || err.status === 401)
					? 'Not found.'
					: 'Could not load stats.';
		} finally {
			loading = false;
		}
	});

	const maxDay = $derived(Math.max(1, ...(stats?.renders_by_day ?? []).map(([, n]) => n)));
</script>

<svelte:head><title>Stats · Dicegram</title></svelte:head>

<section class="mx-auto flex w-full max-w-4xl flex-col gap-6 p-6">
	<h1 class="text-2xl font-semibold text-app">Instance stats</h1>

	{#if loading}
		<p class="text-muted">Loading…</p>
	{:else if error}
		<p role="alert" class="text-danger">{error}</p>
	{:else if stats}
		{#if svg}
			<div class="rounded-lg border border-app bg-surface p-4">
				<img src={svg} alt="Instance activity funnel" class="mx-auto max-w-full" />
			</div>
		{/if}

		<div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
			{#each [['Accounts', stats.accounts], ['Dicegrams', stats.dicegrams], ['Shares', stats.shares], ['New accounts (7d)', stats.accounts_7d]] as [label, value]}
				<div class="rounded-lg border border-app bg-surface p-3">
					<div class="text-2xl font-semibold text-app">{value}</div>
					<div class="text-xs text-muted">{label}</div>
				</div>
			{/each}
		</div>

		{#if stats.log_available}
			<div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
				{#each [['Requests (7d)', stats.requests_7d], ['Edits (7d)', stats.renders_7d], ['Exports (7d)', stats.exports_7d], ['5xx (7d)', stats.errors_7d]] as [label, value]}
					<div class="rounded-lg border border-app bg-surface p-3">
						<div class="text-2xl font-semibold text-app">{value}</div>
						<div class="text-xs text-muted">{label}</div>
					</div>
				{/each}
			</div>

			<div>
				<h2 class="mb-2 text-sm font-semibold text-app">Edits per day</h2>
				<div class="flex flex-col gap-1">
					{#each stats.renders_by_day as [day, n]}
						<div class="flex items-center gap-2 text-xs">
							<span class="w-24 shrink-0 text-muted">{day}</span>
							<span class="h-3 rounded bg-accent" style:width="{(n / maxDay) * 100}%"></span>
							<span class="text-muted">{n}</span>
						</div>
					{/each}
				</div>
			</div>

			<div>
				<h2 class="mb-2 text-sm font-semibold text-app">Top paths</h2>
				<table class="w-full text-left text-xs">
					<tbody>
						{#each stats.top_paths as [path, n]}
							<tr class="border-b border-app">
								<td class="py-1 font-mono text-muted">{path}</td>
								<td class="py-1 text-right text-app">{n}</td>
							</tr>
						{/each}
					</tbody>
				</table>
				<p class="mt-2 text-xs text-dim">
					Requests, not people — the access log stores no IP, user-agent or
					referrer, so there is no visitor count and no crawler filtering. Bot
					traffic is included here. <strong>Edits</strong> is the honest usage
					number: crawlers never POST to the render endpoint.
				</p>
			</div>
		{:else}
			<p class="text-sm text-dim">
				No access log mounted, so traffic figures are unavailable. Database
				totals above are unaffected.
			</p>
		{/if}
	{/if}
</section>
