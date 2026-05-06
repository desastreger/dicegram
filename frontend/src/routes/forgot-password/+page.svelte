<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { ApiError, api } from '$lib/api';
	import { auth } from '$lib/auth.svelte';
	import favicon from '$lib/assets/favicon.svg';

	let email = $state('');
	let submitting = $state(false);
	let result = $state<{ ok: true; hint: string } | { ok: false } | null>(null);
	let error = $state<string | null>(null);

	// Logged-in users don't need recovery — bounce them to the editor.
	onMount(() => {
		if (!auth.loading && auth.user) goto('/editor');
	});
	$effect(() => {
		if (!auth.loading && auth.user) goto('/editor');
	});

	async function submit(e: Event) {
		e.preventDefault();
		if (submitting || !email.trim()) return;
		submitting = true;
		error = null;
		result = null;
		try {
			const res = await api.post<{ password_hint: string }>('/auth/hint-lookup', {
				email: email.trim()
			});
			if (res.password_hint) {
				result = { ok: true, hint: res.password_hint };
			} else {
				result = { ok: false };
			}
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Lookup failed.';
		} finally {
			submitting = false;
		}
	}

	function tryAgain() {
		result = null;
		error = null;
	}
</script>

<svelte:head><title>Forgot password · Dicegram</title></svelte:head>

<section class="auth-shell">
	<div class="auth-card">
		<div class="auth-eyebrow eyebrow">
			<img src={favicon} alt="" class="auth-mark" aria-hidden="true" />
			<span>Account recovery</span>
		</div>
		<h1 class="auth-title">Look up your password hint</h1>
		<p class="auth-lede">
			Email-based recovery is paused while we get our mail server sorted. In the meantime, you can
			look up the hint you wrote at signup.
		</p>

		<div class="auth-warn" role="note">
			<span class="auth-warn-dot" aria-hidden="true"></span>
			<span>
				The hint is what <em>you</em> typed when you signed up — it isn't your password. If you
				didn't set one, you'll need to <a href="/signup" class="link">create a new account</a>.
			</span>
		</div>

		{#if result && result.ok}
			<div class="hint-box">
				<div class="hint-eyebrow">Your hint</div>
				<p class="hint-text">{result.hint}</p>
			</div>
			<hr class="auth-divider" />
			<div class="auth-foot">
				<button type="button" onclick={tryAgain} class="link">Look up another</button>
				<a href="/login" class="btn-primary text-sm">Try logging in</a>
			</div>
		{:else if result && !result.ok}
			<div class="hint-box hint-empty">
				<p>
					No hint on file for <strong>{email}</strong> — either the address isn't registered, or
					the account was created before hints existed.
				</p>
			</div>
			<hr class="auth-divider" />
			<div class="auth-foot">
				<button type="button" onclick={tryAgain} class="link">Try a different email</button>
				<a href="/signup" class="btn-primary text-sm">Sign up</a>
			</div>
		{:else}
			<form onsubmit={submit} class="flex w-full flex-col gap-4">
				<label class="flex flex-col gap-1">
					<span class="field-label">Email</span>
					<input
						type="email"
						required
						autocomplete="email"
						bind:value={email}
						class="input-themed"
					/>
				</label>
				{#if error}
					<p role="alert" class="text-sm text-danger">{error}</p>
				{/if}
				<button type="submit" disabled={submitting || !email.trim()} class="btn-primary">
					{submitting ? 'Looking up…' : 'Show my hint'}
				</button>
			</form>
			<hr class="auth-divider" />
			<div class="auth-foot center">
				<a href="/login" class="link">Back to log in</a>
			</div>
		{/if}
	</div>
</section>

<style>
	.auth-mark {
		width: 18px;
		height: 18px;
		display: block;
	}
	.auth-warn {
		display: flex;
		align-items: flex-start;
		gap: 0.55rem;
		padding: 0.7rem 0.85rem;
		margin-bottom: 1.25rem;
		font-size: 0.78rem;
		line-height: 1.5;
		color: var(--app-text);
		background: color-mix(in srgb, var(--app-warn) 14%, var(--app-bg));
		border: 1px solid color-mix(in srgb, var(--app-warn) 50%, var(--app-border) 50%);
		border-radius: var(--app-radius);
	}
	.auth-warn-dot {
		flex-shrink: 0;
		width: 8px;
		height: 8px;
		margin-top: 0.45rem;
		border-radius: 9999px;
		background: var(--app-warn);
		box-shadow: 0 0 0 3px color-mix(in srgb, var(--app-warn) 18%, transparent);
	}
	.auth-warn em {
		font-style: italic;
		color: var(--app-text);
	}
	.hint-box {
		padding: 1rem 1.1rem;
		background: var(--app-accent-soft);
		border: 1px solid color-mix(in srgb, var(--app-accent) 45%, var(--app-border) 55%);
		border-radius: var(--app-radius);
	}
	.hint-empty {
		background: var(--app-surface-2);
		border-color: var(--app-border);
		color: var(--app-text-muted);
		font-size: 0.85rem;
		line-height: 1.5;
	}
	.hint-eyebrow {
		font-size: 0.7rem;
		font-weight: 600;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		color: var(--app-text-dim);
		margin-bottom: 0.4rem;
	}
	.hint-text {
		margin: 0;
		font-family: var(--app-display-font);
		font-size: 1.1rem;
		line-height: 1.35;
		color: var(--app-text);
	}
</style>
