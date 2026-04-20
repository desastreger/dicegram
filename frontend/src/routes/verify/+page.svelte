<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { ApiError, api } from '$lib/api';
	import { auth } from '$lib/auth.svelte';

	let status = $state<'idle' | 'verifying' | 'ok' | 'error'>('verifying');
	let message = $state<string>('Checking your verification link…');

	onMount(async () => {
		const token = page.url.searchParams.get('token');
		if (!token) {
			status = 'error';
			message = 'This link is missing its verification token.';
			return;
		}
		try {
			await api.get(`/auth/verify?token=${encodeURIComponent(token)}`);
			await auth.refresh();
			status = 'ok';
			message = 'Email verified. Welcome aboard.';
			setTimeout(() => goto('/editor'), 1200);
		} catch (err) {
			status = 'error';
			message =
				err instanceof ApiError
					? err.message
					: 'Verification failed — the link may be expired. Request a new one from Settings.';
		}
	});
</script>

<svelte:head><title>Verify · Dicegram</title></svelte:head>

<section class="mx-auto max-w-md px-4 py-16 text-center">
	<h1 class="mb-3 text-xl font-semibold">
		{#if status === 'ok'}
			You're in
		{:else if status === 'error'}
			Verification failed
		{:else}
			Verifying email…
		{/if}
	</h1>
	<p class="text-sm text-neutral-400">{message}</p>
	{#if status === 'error'}
		<div class="mt-6 flex justify-center gap-3 text-xs">
			<a
				href="/login"
				class="rounded border border-neutral-800 px-3 py-1 text-neutral-200 hover:bg-neutral-900"
			>
				Log in
			</a>
			<a
				href="/signup"
				class="rounded bg-blue-600 px-3 py-1 text-white hover:bg-blue-500"
			>
				Sign up again
			</a>
		</div>
	{/if}
</section>
