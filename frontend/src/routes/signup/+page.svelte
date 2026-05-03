<script lang="ts">
	import { goto } from '$app/navigation';
	import { ApiError } from '$lib/api';
	import { auth } from '$lib/auth.svelte';

	let email = $state('');
	let password = $state('');
	let error = $state<string | null>(null);
	let submitting = $state(false);

	$effect(() => {
		if (!auth.loading && auth.user) goto('/editor');
	});

	async function submit(e: Event) {
		e.preventDefault();
		error = null;
		submitting = true;
		try {
			await auth.signup(email, password);
			await goto('/editor');
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'signup failed';
		} finally {
			submitting = false;
		}
	}
</script>

<svelte:head><title>Sign up · Dicegram</title></svelte:head>

<section class="mx-auto w-full max-w-sm px-6 py-16 text-app">
	<h1 class="mb-6 text-2xl font-semibold">Create your account</h1>
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
				minlength="8"
				autocomplete="new-password"
				bind:value={password}
				aria-describedby="signup-pw-hint"
				class="input-themed"
			/>
			<span id="signup-pw-hint" class="text-xs text-dim">At least 8 characters.</span>
		</label>
		{#if error}
			<p role="alert" class="text-sm text-danger">{error}</p>
		{/if}
		<button type="submit" disabled={submitting} class="btn-primary">
			{submitting ? 'Creating…' : 'Create account'}
		</button>
		<p class="text-center text-sm text-muted">
			Already have one? <a href="/login" class="link">Log in</a>
		</p>
	</form>
</section>
