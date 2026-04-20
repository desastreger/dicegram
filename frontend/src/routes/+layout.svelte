<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import favicon from '$lib/assets/favicon.svg';
	import { auth } from '$lib/auth.svelte';
	import { theme } from '$lib/theme.svelte';
	import Icon from '$lib/Icon.svelte';
	import './layout.css';

	let { children } = $props();

	// Chromeless mode for iframe embeds: the landing page's live editor
	// and future /embed/{slug} share-link viewers render the editor inside
	// an <iframe>, so the app header, footer and verify-email banner
	// would duplicate (or clip) against the parent page. Any page can
	// opt out by adding `?mode=landing` or `?mode=embed` to its URL; the
	// `/embed/` route also gets it for free via the path check.
	const chromeless = $derived(
		page.url.searchParams.get('mode') === 'landing' ||
			page.url.searchParams.get('mode') === 'embed' ||
			page.url.pathname.startsWith('/embed/')
	);

	let resendState = $state<'idle' | 'sending' | 'sent' | 'error'>('idle');
	let resendMsg = $state<string>('');
	let resendTimer: ReturnType<typeof setTimeout> | null = null;

	onMount(() => {
		auth.refresh();
		theme.rehydrate();
	});

	async function handleLogout() {
		await auth.logout();
		await goto('/');
	}

	async function resendVerification() {
		if (resendState === 'sending') return;
		resendState = 'sending';
		resendMsg = 'Sending…';
		try {
			await (await import('$lib/api')).api.post('/auth/request-verify');
			resendState = 'sent';
			resendMsg = 'Verification email sent — check your inbox. No email? SMTP may not be configured; the link is in the server logs.';
		} catch {
			resendState = 'error';
			resendMsg = 'Could not re-send. Check your connection or the server logs.';
		}
		if (resendTimer) clearTimeout(resendTimer);
		resendTimer = setTimeout(() => {
			resendState = 'idle';
			resendMsg = '';
		}, 6000);
	}
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

<a href="#main-content" class="skip-link">Skip to main content</a>

{#if !chromeless}
<header
	role="banner"
	class="border-b backdrop-blur"
	style="background:color-mix(in oklab, var(--app-bg) 85%, transparent); border-color: var(--app-border);"
>
	<nav
		aria-label="Primary"
		class="mx-auto flex max-w-6xl items-center justify-between px-4 py-1.5"
	>
		<a
			href="/"
			class="flex items-center gap-1.5 text-sm font-semibold tracking-tight"
			style="color: var(--app-text);"
		>
			<img src={favicon} alt="" class="h-4 w-4" aria-hidden="true" />
			<span>Dicegram</span>
		</a>
		<div class="flex items-center gap-1 text-xs">
			{#if auth.user}
				<a
					href="/dicegrams"
					class="nav-link flex items-center gap-1 rounded px-2 py-1"
					aria-label="My diegrams"
				>
					<Icon name="folder" size={14} />
					<span class="hidden sm:inline">Diegrams</span>
				</a>
				<a
					href="/editor"
					class="nav-link flex items-center gap-1 rounded px-2 py-1"
					aria-label="Editor"
				>
					<Icon name="file-text" size={14} />
					<span class="hidden sm:inline">Editor</span>
				</a>
				<a
					href="/settings"
					class="nav-link flex items-center gap-1 rounded px-2 py-1"
					aria-label="Settings — branding palette"
				>
					<Icon name="settings" size={14} />
					<span class="hidden sm:inline">Settings</span>
				</a>
				<span
					class="mx-2 hidden text-[11px] md:inline"
					style="color: var(--app-text-dim);"
				>{auth.user.email}</span>
				<button
					type="button"
					onclick={() => theme.toggle()}
					title={theme.current === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
					aria-label={theme.current === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
					class="nav-link flex items-center gap-1 rounded px-2 py-1"
				>
					<Icon name={theme.current === 'dark' ? 'sun' : 'moon'} size={14} />
				</button>
				<button
					type="button"
					onclick={handleLogout}
					title="Log out"
					aria-label="Log out"
					class="nav-link flex items-center gap-1 rounded px-2 py-1"
				>
					<Icon name="log-out" size={14} />
				</button>
			{:else}
				<button
					type="button"
					onclick={() => theme.toggle()}
					title={theme.current === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
					aria-label={theme.current === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
					class="nav-link flex items-center gap-1 rounded px-2 py-1"
				>
					<Icon name={theme.current === 'dark' ? 'sun' : 'moon'} size={14} />
				</button>
				<a href="/login" class="nav-link rounded px-2 py-1">Log in</a>
				<a
					href="/signup"
					class="rounded-md px-3 py-1 font-medium"
					style="background: var(--app-accent); color: var(--app-accent-text);"
				>
					Sign up
				</a>
			{/if}
		</div>
	</nav>
</header>
{/if}

<main id="main-content" role="main">
	{@render children()}
</main>

{#if !chromeless && auth.user && !auth.user.email_verified}
	<div
		class="pointer-events-none fixed inset-x-0 bottom-10 z-40 flex flex-col items-center gap-2 px-3"
		role="status"
		aria-live="polite"
	>
		<div
			class="pointer-events-auto rounded-md border px-3 py-2 text-xs shadow-lg backdrop-blur"
			style="border-color: var(--app-warn); background: color-mix(in oklab, var(--app-warn) 12%, var(--app-surface)); color: var(--app-text);"
		>
			Please verify your email —
			<button
				type="button"
				onclick={resendVerification}
				disabled={resendState === 'sending'}
				class="ml-1 underline disabled:opacity-60"
				style="color: var(--app-warn);"
			>
				{resendState === 'sending' ? 'sending…' : 'resend link'}
			</button>
		</div>
		{#if resendMsg}
			<div
				class="pointer-events-auto max-w-sm rounded-md border px-3 py-2 text-center text-[11px] shadow-lg backdrop-blur"
				style={resendState === 'error'
					? 'border-color: var(--app-danger); background: color-mix(in oklab, var(--app-danger) 10%, var(--app-surface)); color: var(--app-text);'
					: 'border-color: var(--app-ok); background: color-mix(in oklab, var(--app-ok) 10%, var(--app-surface)); color: var(--app-text);'}
			>
				{resendMsg}
			</div>
		{/if}
	</div>
{/if}

{#if !chromeless}
<footer
	role="contentinfo"
	class="mt-12 border-t px-4 py-4 text-[11px]"
	style="background: var(--app-surface); border-color: var(--app-border); color: var(--app-text-muted);"
>
	<div class="mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 sm:flex-row">
		<p>
			Built and maintained by
			<a
				href="https://desastregerstudio.com"
				class="themed-link"
				rel="noreferrer"
			>Nacho De Saeger</a>
			· Copyright © Nacho De Saeger · Licensed under
			<a
				href="https://www.gnu.org/licenses/agpl-3.0.en.html"
				class="themed-link"
				rel="noreferrer"
			>AGPL-3.0</a>
			· Commercial licences available on request.
		</p>
		<a
			href="mailto:dicegram_feedback@desastregerstudio.com?subject=Dicegram%20feedback"
			class="rounded border px-2 py-1"
			style="border-color: var(--app-border); color: var(--app-text);"
			aria-label="Send feedback via email"
		>
			Send feedback
		</a>
	</div>
</footer>
{/if}

<style>
	:global(.nav-link) {
		color: var(--app-text-muted);
	}
	:global(.nav-link:hover) {
		background: var(--app-surface-2);
		color: var(--app-text);
	}
	:global(.themed-link) {
		color: var(--app-text);
		text-decoration: underline;
		text-decoration-color: transparent;
		transition: text-decoration-color 0.15s;
	}
	:global(.themed-link:hover) {
		text-decoration-color: var(--app-text);
	}
</style>
