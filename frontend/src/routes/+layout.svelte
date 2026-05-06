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
	// and the /embed/{slug} share-link viewers render the editor inside
	// an <iframe>, so the app header / footer would duplicate against
	// the parent page. Any page can opt out by adding `?mode=landing` or
	// `?mode=embed` to its URL; the `/embed/` route also gets it for
	// free via the path check.
	const chromeless = $derived(
		page.url.searchParams.get('mode') === 'landing' ||
			page.url.searchParams.get('mode') === 'embed' ||
			page.url.pathname.startsWith('/embed/')
	);

	onMount(() => {
		auth.refresh();
		theme.rehydrate();
	});

	async function handleLogout() {
		await auth.logout();
		await goto('/');
	}
</script>

<svelte:head>
	<link rel="icon" href={favicon} type="image/svg+xml" />
	<link rel="alternate icon" href="/favicon.ico" type="image/x-icon" />
</svelte:head>

<a href="#main-content" class="skip-link">Skip to main content</a>

<div class="flex h-screen flex-col overflow-hidden">
	{#if !chromeless}
		<header
			role="banner"
			class="sticky top-0 z-40 shrink-0 border-b backdrop-blur"
			style="background: color-mix(in oklab, var(--app-bg) 86%, transparent); border-color: var(--app-border);"
		>
			<nav aria-label="Primary" class="app-nav">
				<a href="/" class="brand">
					<img src={favicon} alt="" class="brand-icon" aria-hidden="true" />
					<span class="brand-word">Dicegram</span>
				</a>
				<div class="nav-actions">
					{#if auth.user}
						<a
							href="/dicegrams"
							class="nav-link"
							aria-label="My diegrams"
						>
							<Icon name="folder" size={15} />
							<span class="nav-label">Diegrams</span>
						</a>
						<a
							href="/editor"
							class="nav-link"
							aria-label="Open editor"
						>
							<Icon name="file-text" size={15} />
							<span class="nav-label">Editor</span>
						</a>
						<a
							href="/settings"
							class="nav-link"
							aria-label="Settings — branding palette"
						>
							<Icon name="settings" size={15} />
							<span class="nav-label">Settings</span>
						</a>
						<span class="nav-email" title={auth.user.email}>{auth.user.username || auth.user.email}</span>
						<button
							type="button"
							onclick={() => theme.toggle()}
							title={theme.current === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
							aria-label={theme.current === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
							class="nav-icon"
						>
							<Icon name={theme.current === 'dark' ? 'sun' : 'moon'} size={15} />
						</button>
						<button
							type="button"
							onclick={handleLogout}
							title="Log out"
							aria-label="Log out"
							class="nav-icon"
						>
							<Icon name="log-out" size={15} />
						</button>
					{:else}
						<button
							type="button"
							onclick={() => theme.toggle()}
							title={theme.current === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
							aria-label={theme.current === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
							class="nav-icon"
						>
							<Icon name={theme.current === 'dark' ? 'sun' : 'moon'} size={15} />
						</button>
						<a href="/login" class="nav-link">Log in</a>
						<a href="/signup" class="nav-cta">Sign up</a>
					{/if}
				</div>
			</nav>
		</header>
	{/if}

	<main id="main-content" role="main" class="flex min-h-0 flex-1 flex-col overflow-auto">
		{@render children()}
	</main>

	{#if !chromeless}
		<footer role="contentinfo" class="app-footer">
			<div class="footer-row">
				<p>
					Built and maintained by
					<a
						href="https://desastregerstudio.com"
						class="themed-link"
						target="_blank"
						rel="noopener noreferrer"
					>Nacho De Saeger</a>
					· © Nacho De Saeger · Licensed under
					<a
						href="https://www.gnu.org/licenses/agpl-3.0.en.html"
						class="themed-link"
						target="_blank"
						rel="noopener noreferrer"
					>AGPL-3.0</a>
					· Commercial licences available on request.
				</p>
				<a
					href="mailto:dicegram_feedback@desastregerstudio.com?subject=Dicegram%20feedback"
					class="footer-cta"
					aria-label="Send feedback via email"
				>
					Send feedback
				</a>
			</div>
		</footer>
	{/if}
</div>

<style>
	/* App-level header. Generous tap targets (44px square) on touch
	   widths so we clear the WCAG / Apple HIG minimum (UAT bug #34). */
	:global(.app-nav) {
		display: flex;
		width: 100%;
		align-items: center;
		justify-content: space-between;
		padding: 0.4rem 0.85rem;
		gap: 0.6rem;
	}

	:global(.brand) {
		display: inline-flex;
		align-items: center;
		gap: 0.55rem;
		color: var(--app-text);
		font-family: var(--app-display-font);
		font-weight: 500;
		font-size: 1.05rem;
		letter-spacing: -0.01em;
		padding: 0.35rem 0.5rem;
		border-radius: var(--app-radius-sm);
		transition: background-color var(--app-dur-fast) var(--app-ease);
	}
	:global(.brand:hover) { background-color: var(--app-hover); }
	:global(.brand-icon) {
		width: 22px;
		height: 22px;
		display: block;
		filter: drop-shadow(0 1px 0 rgba(0, 0, 0, 0.04));
	}
	:global(.brand-word) {
		display: inline-block;
		font-feature-settings: 'liga' 1, 'kern' 1;
	}

	:global(.nav-actions) {
		display: flex;
		align-items: center;
		gap: 0.15rem;
	}

	:global(.nav-link) {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		min-height: 36px;
		min-width: 36px;
		padding: 0.35rem 0.65rem;
		font-size: 0.82rem;
		font-weight: 500;
		color: var(--app-text-muted);
		border-radius: var(--app-radius-sm);
		transition: background-color var(--app-dur-fast) var(--app-ease),
			color var(--app-dur-fast) var(--app-ease);
	}
	:global(.nav-link:hover) {
		background-color: var(--app-hover);
		color: var(--app-text);
	}

	:global(.nav-icon) {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-height: 36px;
		min-width: 36px;
		padding: 0.4rem;
		color: var(--app-text-muted);
		background: transparent;
		border: 0;
		border-radius: var(--app-radius-sm);
		cursor: pointer;
		transition: background-color var(--app-dur-fast) var(--app-ease),
			color var(--app-dur-fast) var(--app-ease);
	}
	:global(.nav-icon:hover) {
		background-color: var(--app-hover);
		color: var(--app-text);
	}

	:global(.nav-email) {
		display: none;
		max-width: 18ch;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		margin: 0 0.4rem;
		font-size: 0.7rem;
		color: var(--app-text-dim);
	}

	:global(.nav-cta) {
		min-height: 36px;
		display: inline-flex;
		align-items: center;
		padding: 0.4rem 0.95rem;
		font-size: 0.82rem;
		font-weight: 500;
		background: var(--app-accent);
		color: var(--app-accent-text);
		border-radius: var(--app-radius-sm);
		transition: background-color var(--app-dur-fast) var(--app-ease),
			transform var(--app-dur-fast) var(--app-ease);
	}
	:global(.nav-cta:hover) {
		background-color: color-mix(in srgb, var(--app-accent) 88%, var(--app-text) 12%);
	}
	:global(.nav-cta:active) { transform: translateY(1px); }

	:global(.nav-label) {
		display: none;
	}

	@media (min-width: 640px) {
		:global(.nav-label) { display: inline; }
	}
	@media (min-width: 768px) {
		:global(.nav-email) { display: inline; }
	}

	/* Mobile: bump tap targets and breathe out the row. */
	@media (max-width: 480px) {
		:global(.app-nav) {
			padding: 0.45rem 0.65rem;
			gap: 0.4rem;
		}
		:global(.nav-link),
		:global(.nav-icon) {
			min-height: 44px;
			min-width: 44px;
		}
		:global(.nav-cta) {
			min-height: 44px;
		}
		:global(.brand) {
			padding: 0.5rem 0.55rem;
		}
	}

	/* Footer */
	:global(.app-footer) {
		position: sticky;
		bottom: 0;
		z-index: 40;
		flex-shrink: 0;
		padding: 0.55rem 1rem;
		background: var(--app-surface);
		border-top: 1px solid var(--app-rule);
		font-size: 0.72rem;
		color: var(--app-text-muted);
	}
	:global(.footer-row) {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		text-align: center;
	}
	@media (min-width: 640px) {
		:global(.footer-row) {
			flex-direction: row;
			justify-content: space-between;
			text-align: left;
		}
	}
	:global(.footer-cta) {
		padding: 0.3rem 0.65rem;
		border: 1px solid var(--app-border);
		border-radius: var(--app-radius-sm);
		color: var(--app-text);
		transition: background-color var(--app-dur-fast) var(--app-ease),
			border-color var(--app-dur-fast) var(--app-ease);
	}
	:global(.footer-cta:hover) {
		background-color: var(--app-hover);
		border-color: var(--app-border-strong);
	}

	:global(.themed-link) {
		color: var(--app-text);
		text-decoration: underline;
		text-decoration-color: transparent;
		text-underline-offset: 0.2em;
		transition: text-decoration-color 0.15s;
	}
	:global(.themed-link:hover) {
		text-decoration-color: var(--app-text);
	}
</style>
