<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { ApiError } from '$lib/api';
	import { auth } from '$lib/auth.svelte';
	import favicon from '$lib/assets/favicon.svg';

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

<section class="auth-shell">
	<div class="auth-card">
		<div class="auth-eyebrow eyebrow">
			<img src={favicon} alt="" class="auth-mark" aria-hidden="true" />
			<span>Welcome back</span>
		</div>
		<h1 class="auth-title">Log in to Dicegram</h1>
		<p class="auth-lede">Pick up where you left off — your diegrams autosave to your account.</p>
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
			<button type="submit" disabled={submitting || !email || !password} class="btn-primary">
				{submitting ? 'Signing in…' : 'Log in'}
			</button>
		</form>
		<hr class="auth-divider" />
		<div class="auth-foot">
			<a href="/forgot-password" class="link" title="Look up the hint you set at signup">Forgot? Look up your hint</a>
			<a href="/signup" class="link">Create an account</a>
		</div>
	</div>
</section>

<style>
	.auth-mark {
		width: 18px;
		height: 18px;
		display: block;
	}
</style>
