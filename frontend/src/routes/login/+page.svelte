<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { ApiError } from '$lib/api';
	import { auth } from '$lib/auth.svelte';
	import favicon from '$lib/assets/favicon.svg';

	let identifier = $state('');
	// Hint surfaced by the 401 when the username exists but the password is
	// wrong. Replaces the old /forgot-password page, which asked any visitor
	// for an email and handed back that account's hint.
	let hint = $state('');
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
			await auth.login(identifier.trim(), password);
			await goto(nextTarget());
		} catch (err) {
			// The 401 body carries {detail, password_hint}; show the reminder
			// right here rather than sending the user to a lookup page.
			const detail = err instanceof ApiError ? (err.detail as { password_hint?: string } | undefined) : undefined;
			hint = detail?.password_hint?.trim() ?? '';
			error = err instanceof ApiError ? 'Wrong username or password.' : 'login failed';
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
		<p class="auth-lede">Pick up where you left off — your dicegrams autosave to your account.</p>
		<form onsubmit={submit} class="flex w-full flex-col gap-4">
			<label class="flex flex-col gap-1">
				<span class="field-label">Username</span>
				<input
					type="text"
					required
					autocomplete="username"
					bind:value={identifier}
					aria-describedby="login-id-help"
					class="input-themed"
				/>
				<span id="login-id-help" class="text-xs text-dim">
					If you signed up before usernames, your email still works.
				</span>
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
			{#if hint}
				<p class="text-sm text-muted">
					<span class="font-semibold">Your reminder:</span> {hint}
				</p>
			{/if}
			<button type="submit" disabled={submitting || !identifier || !password} class="btn-primary">
				{submitting ? 'Signing in…' : 'Log in'}
			</button>
		</form>
		<hr class="auth-divider" />
		<div class="auth-foot">
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
