<script lang="ts">
	// In-page replacement for window.confirm() / native beforeunload.
	// All app prompts go through this so they: (a) inherit the current
	// theme, (b) don't block Playwright UAT runs, (c) read as part of the
	// product instead of OS chrome.
	import { onMount } from 'svelte';

	type Tone = 'default' | 'danger';
	let {
		open = $bindable(false),
		title = 'Are you sure?',
		message = '',
		confirmLabel = 'Confirm',
		cancelLabel = 'Cancel',
		tone = 'default' as Tone,
		onConfirm,
		onCancel
	}: {
		open?: boolean;
		title?: string;
		message?: string;
		confirmLabel?: string;
		cancelLabel?: string;
		tone?: Tone;
		onConfirm?: () => void;
		onCancel?: () => void;
	} = $props();

	let confirmBtn: HTMLButtonElement | undefined = $state();

	$effect(() => {
		if (open && confirmBtn) {
			queueMicrotask(() => confirmBtn?.focus());
		}
	});

	function close(confirmed: boolean) {
		open = false;
		if (confirmed) onConfirm?.();
		else onCancel?.();
	}

	function onBackdropKey(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			e.stopPropagation();
			close(false);
		}
	}
</script>

{#if open}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="modal-backdrop"
		onclick={() => close(false)}
		onkeydown={onBackdropKey}
	>
		<div
			class="modal-panel dg-confirm"
			role="dialog"
			aria-modal="true"
			aria-labelledby="dg-confirm-title"
			tabindex="-1"
			onclick={(e) => e.stopPropagation()}
			onkeydown={(e) => {
				if (e.key === 'Escape') {
					e.stopPropagation();
					close(false);
				}
			}}
		>
			<h2 id="dg-confirm-title" class="dg-confirm-title">{title}</h2>
			{#if message}
				<p class="dg-confirm-msg">{message}</p>
			{/if}
			<div class="dg-confirm-actions">
				<button type="button" class="btn-secondary" onclick={() => close(false)}>
					{cancelLabel}
				</button>
				<button
					bind:this={confirmBtn}
					type="button"
					class={tone === 'danger' ? 'btn-danger' : 'btn-primary'}
					onclick={() => close(true)}
				>
					{confirmLabel}
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	.dg-confirm {
		width: min(28rem, calc(100vw - 2rem));
		padding: 1.25rem 1.35rem 1.1rem;
		display: flex;
		flex-direction: column;
		gap: 0.65rem;
	}
	.dg-confirm-title {
		font-family: var(--app-display-font);
		font-weight: 500;
		font-size: 1.15rem;
		line-height: 1.25;
		letter-spacing: -0.01em;
		color: var(--app-text);
	}
	.dg-confirm-msg {
		font-size: 0.875rem;
		line-height: 1.5;
		color: var(--app-text-muted);
		margin: 0;
	}
	.dg-confirm-actions {
		display: flex;
		justify-content: flex-end;
		gap: 0.5rem;
		margin-top: 0.4rem;
	}
</style>
