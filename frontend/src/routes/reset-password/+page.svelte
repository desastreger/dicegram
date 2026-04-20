<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { ApiError, api } from '$lib/api';
	import { auth } from '$lib/auth.svelte';

	let token = $state<string>('');
	let password = $state('');
	let confirm = $state('');
	let submitting = $state(false);
	let error = $state<string | null>(null);
	let done = $state(false);

	onMount(() => {
		token = page.url.searchParams.get('token') ?? '';
		if (!token) {
			error = 'This link is missing its reset token.';
		}
	});

	async function submit(e: Event) {
		e.preventDefault();
		if (submitting) return;
		if (password !== confirm) {
			error = "Passwords don't match.";
			return;
		}
		if (password.length < 8) {
			error = 'Password must be at least 8 characters.';
			return;
		}
		submitting = true;
		error = null;
		try {
			await api.post('/auth/reset', { token, password });
			await auth.refresh();
			done = true;
			setTimeout(() => goto('/editor'), 1200);
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Reset failed.';
		} finally {
			submitting = false;
		}
	}
</script>

<svelte:head><title>Reset password · Dicegram</title></svelte:head>

<section class="mx-auto max-w-md px-4 py-12">
	<h1 class="mb-2 text-xl font-semibold">Set a new password</h1>

	{#if done}
		<div class="rounded border border-emerald-900 bg-emerald-950/50 p-4 text-sm text-emerald-200">
			Password updated. Redirecting to the editor…
		</div>
	{:else}
		<form onsubmit={submit} class="space-y-3">
			<label class="block">
				<span class="text-sm font-medium text-neutral-300">New password</span>
				<input
					type="password"
					required
					minlength="8"
					autocomplete="new-password"
					bind:value={password}
					class="mt-1 block w-full rounded border border-neutral-800 bg-neutral-950 px-3 py-2 text-sm focus:border-neutral-600 focus:outline-none"
				/>
			</label>
			<label class="block">
				<span class="text-sm font-medium text-neutral-300">Confirm new password</span>
				<input
					type="password"
					required
					minlength="8"
					autocomplete="new-password"
					bind:value={confirm}
					class="mt-1 block w-full rounded border border-neutral-800 bg-neutral-950 px-3 py-2 text-sm focus:border-neutral-600 focus:outline-none"
				/>
			</label>
			{#if error}
				<p class="text-xs text-red-400">{error}</p>
			{/if}
			<button
				type="submit"
				disabled={submitting || !token || !password || !confirm}
				class="w-full rounded bg-blue-600 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
			>
				{submitting ? 'Updating…' : 'Update password'}
			</button>
		</form>
	{/if}
</section>
