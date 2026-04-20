<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import favicon from '$lib/assets/favicon.svg';
	import { auth } from '$lib/auth.svelte';
	import Icon from '$lib/Icon.svelte';
	import './layout.css';

	let { children } = $props();

	onMount(() => {
		auth.refresh();
	});

	async function handleLogout() {
		await auth.logout();
		await goto('/');
	}
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

<header class="border-b border-neutral-800 bg-neutral-950/80 backdrop-blur">
	<nav class="mx-auto flex max-w-6xl items-center justify-between px-4 py-1.5">
		<a href="/" class="flex items-center gap-1.5 text-sm font-semibold tracking-tight text-neutral-100">
			<img src={favicon} alt="" class="h-4 w-4" />
			Dicegram
		</a>
		<div class="flex items-center gap-1 text-xs">
			{#if auth.user}
				<a
					href="/dicegrams"
					title="My diegrams"
					class="flex items-center gap-1 rounded px-2 py-1 text-neutral-300 hover:bg-neutral-900 hover:text-white"
				>
					<Icon name="folder" size={14} />
					<span class="hidden sm:inline">Diegrams</span>
				</a>
				<a
					href="/editor"
					title="Editor"
					class="flex items-center gap-1 rounded px-2 py-1 text-neutral-300 hover:bg-neutral-900 hover:text-white"
				>
					<Icon name="file-text" size={14} />
					<span class="hidden sm:inline">Editor</span>
				</a>
				<a
					href="/settings"
					title="Settings · branding palette"
					class="flex items-center gap-1 rounded px-2 py-1 text-neutral-300 hover:bg-neutral-900 hover:text-white"
				>
					<Icon name="settings" size={14} />
					<span class="hidden sm:inline">Settings</span>
				</a>
				<span class="mx-2 hidden text-[11px] text-neutral-500 md:inline">{auth.user.email}</span>
				<button
					onclick={handleLogout}
					title="Log out"
					class="flex items-center gap-1 rounded px-2 py-1 text-neutral-300 hover:bg-neutral-900 hover:text-white"
				>
					<Icon name="log-out" size={14} />
				</button>
			{:else}
				<a href="/login" class="rounded px-2 py-1 text-neutral-300 hover:text-white">Log in</a>
				<a
					href="/signup"
					class="rounded-md bg-blue-600 px-3 py-1 font-medium text-white hover:bg-blue-500"
				>
					Sign up
				</a>
			{/if}
		</div>
	</nav>
</header>

<main class="text-neutral-100">
	{@render children()}
</main>

{#if auth.user && !auth.user.email_verified}
	<div
		class="pointer-events-none fixed inset-x-0 bottom-0 z-40 flex justify-center px-3 pb-3"
	>
		<div
			class="pointer-events-auto rounded-md border border-amber-800/60 bg-amber-950/80 px-3 py-2 text-xs text-amber-100 shadow-lg backdrop-blur"
		>
			Please verify your email —
			<button
				type="button"
				onclick={async () => {
					try {
						await (await import('$lib/api')).api.post('/auth/request-verify');
						alert('Verification email re-sent.');
					} catch {
						alert('Could not resend the email — check SMTP settings or the server logs.');
					}
				}}
				class="ml-1 underline hover:text-white"
			>
				resend link
			</button>
		</div>
	</div>
{/if}

<footer
	class="mt-12 border-t border-neutral-900 bg-neutral-950/50 px-4 py-4 text-[11px] text-neutral-500"
>
	<div class="mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 sm:flex-row">
		<p>
			Built and maintained by
			<a
				href="https://desastregerstudio.com"
				class="text-neutral-300 hover:text-white"
				rel="noreferrer"
			>Nacho De Saeger</a>
			·
			Copyright © Nacho De Saeger ·
			Licensed under
			<a
				href="https://www.gnu.org/licenses/agpl-3.0.en.html"
				class="text-neutral-300 hover:text-white"
				rel="noreferrer"
			>AGPL-3.0</a>
			· Commercial licences available on request.
		</p>
		<a
			href="mailto:dicegram_feedback@desastregerstudio.com?subject=Dicegram%20feedback"
			class="rounded border border-neutral-800 px-2 py-1 text-neutral-300 hover:bg-neutral-900 hover:text-white"
		>
			Send feedback
		</a>
	</div>
</footer>
