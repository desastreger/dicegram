<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { ApiError } from '$lib/api';
	import { auth } from '$lib/auth.svelte';

	let email = $state('');
	let password = $state('');
	let error = $state<string | null>(null);
	let submitting = $state(false);

	function nextTarget(): string {
		const raw = page.url.searchParams.get('next');
		if (raw && raw.startsWith('/') && !raw.startsWith('//')) return raw;
		return '/editor';
	}

	$effect(() => {
		if (!auth.loading && auth.user) goto(nextTarget());
	});

	async function submit(e: Event) {
		e.preventDefault();
		error = null;
		submitting = true;
		try {
			await auth.login(email, password);
			await goto(nextTarget());
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'login failed';
		} finally {
			submitting = false;
		}
	}
</script>

<svelte:head><title>Log in · Dicegram</title></svelte:head>

<section class="mx-auto w-full max-w-sm px-6 py-16 text-app">
	<h1 class="mb-6 text-2xl font-semibold">Log in</h1>
	<form onsubmit={submit} class="flex w-full flex-col gap-4">
		<label class="flex flex-col gap-1">
			<span class="field-label">Email</span>
			<input
				type="email"
				required
				autocomplete="username"
				bind:value={email}
				class="input-themed"
			/>
		</label>
		<label class="flex flex-col gap-1">
			<span class="field-label">Password</span>
			<input
				type="password"
				required
				autocomplete="current-password"
				bind:value={password}
				class="input-themed"
			/>
		</label>
		{#if error}
			<p role="alert" class="text-sm text-danger">{error}</p>
		{/if}
		<button type="submit" disabled={submitting} class="btn-primary">
			{submitting ? 'Signing in…' : 'Log in'}
		</button>
		<div class="flex items-center justify-between text-sm">
			<a href="/forgot-password" class="link">Forgot password?</a>
			<a href="/signup" class="link">Create an account</a>
		</div>
	</form>
</section>
