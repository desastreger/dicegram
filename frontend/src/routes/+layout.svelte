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
