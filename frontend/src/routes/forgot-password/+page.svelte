<script lang="ts">
	import { ApiError, api } from '$lib/api';

	let email = $state('');
	let submitting = $state(false);
	let submitted = $state(false);
	let error = $state<string | null>(null);

	async function submit(e: Event) {
		e.preventDefault();
		if (submitting) return;
		submitting = true;
		error = null;
		try {
			await api.post('/auth/request-reset', { email });
			submitted = true;
		} catch (err) {
			// Backend always returns 204 to avoid enumeration, so errors
			// here are network-ish — still show a generic success.
			if (err instanceof ApiError && err.status < 500) {
				submitted = true;
			} else {
				error = err instanceof Error ? err.message : 'Something went wrong.';
			}
		} finally {
			submitting = false;
		}
	}
</script>

<svelte:head><title>Forgot password · Dicegram</title></svelte:head>

<section class="mx-auto w-full max-w-md px-4 py-12">
	<h1 class="mb-2 text-xl font-semibold text-app">Reset your password</h1>
	<p class="mb-6 text-sm text-muted">
		Enter the email address on your account. If it matches, we'll email you
		a reset link (valid for 1 hour).
	</p>

	{#if submitted}
		<div role="status" class="toast toast-ok p-4 text-sm">
			If an account exists for <strong>{email}</strong>, we just sent a reset link.
			Check your inbox (and your spam folder).
		</div>
		<div class="mt-4 text-xs">
			<a href="/login" class="link">Back to log in</a>
		</div>
	{:else}
		<form onsubmit={submit} class="space-y-3">
			<label class="block">
				<span class="field-label">Email</span>
				<input
					type="email"
					required
					autocomplete="email"
					bind:value={email}
					class="input-themed mt-1 block w-full text-sm"
				/>
			</label>
			{#if error}
				<p role="alert" class="text-xs text-danger">{error}</p>
			{/if}
			<button type="submit" disabled={submitting || !email} class="btn-primary w-full">
				{submitting ? 'Sending…' : 'Send reset link'}
			</button>
			<div class="text-xs">
				<a href="/login" class="link">Back to log in</a>
			</div>
		</form>
	{/if}
</section>
