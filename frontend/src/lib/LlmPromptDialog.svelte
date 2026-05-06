<script lang="ts">
	import Icon from '$lib/Icon.svelte';

	let {
		open = $bindable(false),
		promptText
	}: {
		open: boolean;
		promptText: string;
	} = $props();

	let copied = $state(false);

	async function copyPrompt() {
		try {
			await navigator.clipboard.writeText(promptText);
			copied = true;
			setTimeout(() => (copied = false), 1500);
		} catch {
			/* noop — clipboard unavailable in some embedded browsers */
		}
	}

	function closeOnBackdrop(e: KeyboardEvent | MouseEvent) {
		if ('key' in e && e.key !== 'Escape') return;
		open = false;
	}

	let panel: HTMLDivElement | undefined = $state();
	$effect(() => {
		if (open && panel) {
			// Move focus into the dialog so keyboard users land inside it.
			queueMicrotask(() => panel?.focus());
		}
	});
</script>

{#if open}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="modal-backdrop p-4"
		onclick={closeOnBackdrop}
		onkeydown={closeOnBackdrop}
		role="dialog"
		aria-modal="true"
		aria-label="Use Dicegram with an LLM"
	>
		<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
		<div
			bind:this={panel}
			class="modal-panel flex max-h-[90vh] w-full max-w-2xl flex-col overflow-hidden text-left focus:outline-none"
			tabindex="-1"
			onclick={(e) => e.stopPropagation()}
		>
			<header class="flex items-center justify-between border-b border-app px-4 py-3">
				<div class="flex items-center gap-2">
					<Icon name="sparkles" size={14} />
					<h2 class="text-sm font-semibold text-app">Use Dicegram with an LLM</h2>
				</div>
				<button
					type="button"
					onclick={() => (open = false)}
					class="btn-icon"
					aria-label="Close"
				>
					<Icon name="x" size={14} />
				</button>
			</header>
			<div class="min-h-0 flex-1 overflow-auto p-4">
				<p class="mb-3 text-xs text-muted">
					Copy this prompt, paste it into any chat model. The embedded DSL is
					your current dicegram — the model will return a full DSL block you
					can paste back into the editor.
				</p>
				<pre
					class="max-h-[40vh] overflow-auto rounded border border-app bg-surface-2 p-3 font-mono text-[11px] whitespace-pre-wrap text-app">{promptText}</pre>
				<div class="mt-3 flex flex-wrap items-center gap-2">
					<button
						type="button"
						onclick={copyPrompt}
						class="btn-secondary flex items-center gap-1.5 text-xs"
					>
						<Icon name={copied ? 'check' : 'copy'} size={13} />
						{copied ? 'Copied to clipboard' : 'Copy prompt'}
					</button>
				</div>
				<div class="mt-5 border-t border-app pt-4">
					<p class="eyebrow mb-2" style="font-size: 0.6rem;">Next step</p>
					<p class="text-xs text-muted">
						Paste the prompt into your chat model of choice — the model
						returns a full DSL block that drops back into the editor.
					</p>
				</div>
			</div>
		</div>
	</div>
{/if}

<svelte:window onkeydown={(e) => open && e.key === 'Escape' && (open = false)} />
