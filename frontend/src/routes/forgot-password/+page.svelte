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

<section class="mx-auto max-w-md px-4 py-12">
	<h1 class="mb-2 text-xl font-semibold">Reset your password</h1>
	<p class="mb-6 text-sm text-neutral-400">
		Enter the email address on your account. If it matches, we'll email you
		a reset link (valid for 1 hour).
	</p>

	{#if submitted}
		<div class="rounded border border-emerald-900 bg-emerald-950/50 p-4 text-sm text-emerald-200">
			If an account exists for <strong>{email}</strong>, we just sent a reset link.
			Check your inbox (and your spam folder).
		</div>
		<div class="mt-4 text-xs">
			<a href="/login" class="text-neutral-400 hover:text-white">Back to log in</a>
		</div>
	{:else}
		<form onsubmit={submit} class="space-y-3">
			<label class="block">
				<span class="text-sm font-medium text-neutral-300">Email</span>
				<input
					type="email"
					required
					bind:value={email}
					class="mt-1 block w-full rounded border border-neutral-800 bg-neutral-950 px-3 py-2 text-sm focus:border-neutral-600 focus:outline-none"
				/>
			</label>
			{#if error}
				<p class="text-xs text-red-400">{error}</p>
			{/if}
			<button
				type="submit"
				disabled={submitting || !email}
				class="w-full rounded bg-blue-600 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
			>
				{submitting ? 'Sending…' : 'Send reset link'}
			</button>
			<div class="text-xs">
				<a href="/login" class="text-neutral-400 hover:text-white">Back to log in</a>
			</div>
		</form>
	{/if}
</section>
