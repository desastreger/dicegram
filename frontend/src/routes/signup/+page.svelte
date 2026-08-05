<script lang="ts">
	import { goto } from '$app/navigation';
	import { ApiError } from '$lib/api';
	import { auth } from '$lib/auth.svelte';
	import favicon from '$lib/assets/favicon.svg';

	let username = $state('');
	let password = $state('');
	let passwordHint = $state('');
	// Show/hide instead of a confirm-password field. With no reset of any
	// kind, a typo on signup locks the account permanently — but a second
	// field is friction, and letting people SEE what they typed solves the
	// same problem without one.
	let showPassword = $state(false);
	let error = $state<string | null>(null);
	let submitting = $state(false);

	$effect(() => {
		if (!auth.loading && auth.user) goto('/editor');
	});

	// Hint is optional now — it is a courtesy, not a credential.
	const ready = $derived(username.trim().length >= 2 && password.length >= 8);

	async function submit(e: Event) {
		e.preventDefault();
		if (!ready) return;
		error = null;
		submitting = true;
		try {
			await auth.signup({
				username: username.trim(),
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
			Free, no card, no email address. Save and version dicegrams, exportable to
			SVG / PNG / PDF.
		</p>

		<!-- There is genuinely no recovery path: no email subsystem exists, so
		     there is nothing to send a reset link to and no support channel
		     that can restore an account. Say so plainly rather than softening
		     it — a user who skims this and forgets their password loses their
		     work permanently. -->
		<div class="auth-warn" role="note">
			<span class="auth-warn-dot" aria-hidden="true"></span>
			<span>
				<strong>There is no password reset.</strong>
				Dicegram has no email system, so we can&rsquo;t send you a reset link and
				no one can recover your account for you. Your username and password are
				the only way in &mdash; <strong>write them down somewhere safe before you
				continue.</strong>
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
				<span class="text-xs text-dim">
					This is how you sign in, and it is shown next to your work. Letters,
					numbers, spaces, <code>_ . -</code>
				</span>
			</label>
			<label class="flex flex-col gap-1">
				<span class="field-label">Password</span>
				<div class="relative flex items-center">
					<input
						type={showPassword ? 'text' : 'password'}
						required
						minlength="8"
						autocomplete="new-password"
						bind:value={password}
						aria-describedby="signup-pw-hint"
						class="input-themed w-full pr-16"
					/>
					<button
						type="button"
						class="absolute right-2 text-xs text-muted underline"
						onclick={() => (showPassword = !showPassword)}
					>
						{showPassword ? 'Hide' : 'Show'}
					</button>
				</div>
				<span id="signup-pw-hint" class="text-xs text-dim">
					At least 8 characters. Use <em>Show</em> to check it before you commit &mdash;
					there is no way to reset it later.
				</span>
			</label>
			<label class="flex flex-col gap-1">
				<span class="field-label">Password reminder <span class="text-dim">(optional)</span></span>
				<input
					type="text"
					maxlength="140"
					placeholder="e.g. my dog's birthday + favourite city"
					bind:value={passwordHint}
					aria-describedby="signup-hint-help"
					class="input-themed"
				/>
				<span id="signup-hint-help" class="text-xs text-dim">
					Shown to you after a failed sign-in. A nudge to <em>you</em>, never the
					password itself &mdash; anyone who guesses your username and gets the
					password wrong will see it.
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
