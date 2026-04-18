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

<section class="mx-auto max-w-sm px-6 py-16 text-neutral-100">
	<h1 class="mb-6 text-2xl font-semibold">Log in</h1>
	<form onsubmit={submit} class="flex flex-col gap-4">
		<label class="flex flex-col gap-1">
			<span class="text-sm font-medium text-neutral-300">Email</span>
			<input
				type="email"
				required
				bind:value={email}
				class="rounded-md border border-neutral-800 bg-neutral-900 px-3 py-2 text-neutral-100 focus:border-neutral-600 focus:outline-none"
			/>
		</label>
		<label class="flex flex-col gap-1">
			<span class="text-sm font-medium text-neutral-300">Password</span>
			<input
				type="password"
				required
				bind:value={password}
				class="rounded-md border border-neutral-800 bg-neutral-900 px-3 py-2 text-neutral-100 focus:border-neutral-600 focus:outline-none"
			/>
		</label>
		{#if error}
			<p class="text-sm text-red-400">{error}</p>
		{/if}
		<button
			type="submit"
			disabled={submitting}
			class="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-500 disabled:opacity-50"
		>
			{submitting ? 'Signing in…' : 'Log in'}
		</button>
		<p class="text-center text-sm text-neutral-400">
			New here? <a href="/signup" class="text-blue-400 hover:underline">Create an account</a>
		</p>
	</form>
</section>
