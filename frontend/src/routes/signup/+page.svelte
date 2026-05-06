<script lang="ts">
	import { goto } from '$app/navigation';
	import { ApiError } from '$lib/api';
	import { auth } from '$lib/auth.svelte';
	import favicon from '$lib/assets/favicon.svg';

	let username = $state('');
	let email = $state('');
	let password = $state('');
	let passwordHint = $state('');
	let error = $state<string | null>(null);
	let submitting = $state(false);

	$effect(() => {
		if (!auth.loading && auth.user) goto('/editor');
	});

	const ready = $derived(
		username.trim().length > 0 &&
			email.trim().length > 0 &&
			password.length >= 8 &&
			passwordHint.trim().length > 0
	);

	async function submit(e: Event) {
		e.preventDefault();
		if (!ready) return;
		error = null;
		submitting = true;
		try {
			await auth.signup({
				username: username.trim(),
				email: email.trim(),
				password,
				password_hint: passwordHint.trim()
			});
			await goto('/editor');
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'signup failed';
		} finally {
			submitting = false;
		}
	}
</script>

<svelte:head><title>Sign up · Dicegram</title></svelte:head>

<section class="auth-shell">
	<div class="auth-card">
		<div class="auth-eyebrow eyebrow">
			<img src={favicon} alt="" class="auth-mark" aria-hidden="true" />
			<span>Make your first dicegram</span>
		</div>
		<h1 class="auth-title">Create your account</h1>
		<p class="auth-lede">
			Free, no card. Save and version diegrams in your browser, exportable to SVG / PNG / PDF.
		</p>

		<!-- Heads-up: while SMTP recovery is offline, the user has no
		     "forgot password" path. The hint they choose below is the only
		     bridge — call it out clearly so they don't sleepwalk past. -->
		<div class="auth-warn" role="note">
			<span class="auth-warn-dot" aria-hidden="true"></span>
			<span>
				<strong>Save your password somewhere safe.</strong>
				Email-based recovery is temporarily disabled — the hint below is the only
				way back into your account.
			</span>
		</div>

		<form onsubmit={submit} class="flex w-full flex-col gap-4">
			<label class="flex flex-col gap-1">
				<span class="field-label">Username</span>
				<input
					type="text"
					required
					maxlength="60"
					autocomplete="nickname"
					bind:value={username}
					class="input-themed"
				/>
				<span class="text-xs text-dim">Shown next to your work. Pick anything; you can change it later.</span>
			</label>
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
			<label class="flex flex-col gap-1">
				<span class="field-label">Password reminder</span>
				<input
					type="text"
					required
					maxlength="140"
					placeholder="e.g. my dog's birthday + favourite city"
					bind:value={passwordHint}
					aria-describedby="signup-hint-help"
					class="input-themed"
				/>
				<span id="signup-hint-help" class="text-xs text-dim">
					A nudge to <em>you</em>, not the password itself. Anyone with your email can see this — keep it personal but not literal.
				</span>
			</label>
			{#if error}
				<p role="alert" class="text-sm text-danger">{error}</p>
			{/if}
			<button type="submit" disabled={submitting || !ready} class="btn-primary">
				{submitting ? 'Creating…' : 'Create account'}
			</button>
		</form>
		<hr class="auth-divider" />
		<p class="auth-foot center">
			Already have one? <a href="/login" class="link">Log in</a>
		</p>
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
</style>
