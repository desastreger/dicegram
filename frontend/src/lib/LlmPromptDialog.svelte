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
</script>

{#if open}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
		onclick={closeOnBackdrop}
		onkeydown={closeOnBackdrop}
		role="dialog"
		aria-modal="true"
		aria-label="Use Dicegram with an LLM"
	>
		<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
		<div
			class="flex max-h-[90vh] w-full max-w-2xl flex-col overflow-hidden rounded-lg border border-neutral-800 bg-neutral-950 text-left text-neutral-100 shadow-2xl"
			onclick={(e) => e.stopPropagation()}
		>
			<header class="flex items-center justify-between border-b border-neutral-800 px-4 py-3">
				<div class="flex items-center gap-2">
					<Icon name="sparkles" size={14} />
					<h2 class="text-sm font-semibold">Use Dicegram with an LLM</h2>
				</div>
				<button
					type="button"
					onclick={() => (open = false)}
					class="rounded p-1 text-neutral-400 hover:bg-neutral-900 hover:text-neutral-100"
					aria-label="Close"
				>
					<Icon name="x" size={14} />
				</button>
			</header>
			<div class="min-h-0 flex-1 overflow-auto p-4">
				<p class="mb-3 text-xs text-neutral-400">
					Copy this prompt, paste it into any chat model. The embedded DSL is
					your current dicegram — the model will return a full DSL block you
					can paste back into the editor.
				</p>
				<pre
					class="max-h-[40vh] overflow-auto rounded border border-neutral-800 bg-neutral-900 p-3 font-mono text-[11px] whitespace-pre-wrap text-neutral-200">{promptText}</pre>
				<div class="mt-3 flex flex-wrap items-center gap-2">
					<button
						type="button"
						onclick={copyPrompt}
						class="flex items-center gap-1.5 rounded border border-neutral-700 bg-neutral-800 px-3 py-1.5 text-xs font-medium text-neutral-100 hover:bg-neutral-700"
					>
						<Icon name={copied ? 'check' : 'copy'} size={13} />
						{copied ? 'Copied to clipboard' : 'Copy prompt'}
					</button>
				</div>
				<div class="mt-5 border-t border-neutral-800 pt-4">
					<p class="mb-2 text-[10px] uppercase tracking-wide text-neutral-500">
						Open a chat
					</p>
					<div class="flex flex-wrap gap-2">
						<a
							href="https://claude.ai/new"
							target="_blank"
							rel="noopener noreferrer"
							class="flex items-center gap-1.5 rounded border border-neutral-800 bg-neutral-900 px-3 py-1.5 text-xs text-neutral-100 hover:bg-neutral-800"
						>
							Claude
							<Icon name="arrow-right" size={12} />
						</a>
						<a
							href="https://chatgpt.com/"
							target="_blank"
							rel="noopener noreferrer"
							class="flex items-center gap-1.5 rounded border border-neutral-800 bg-neutral-900 px-3 py-1.5 text-xs text-neutral-100 hover:bg-neutral-800"
						>
							ChatGPT
							<Icon name="arrow-right" size={12} />
						</a>
						<a
							href="https://gemini.google.com/app"
							target="_blank"
							rel="noopener noreferrer"
							class="flex items-center gap-1.5 rounded border border-neutral-800 bg-neutral-900 px-3 py-1.5 text-xs text-neutral-100 hover:bg-neutral-800"
						>
							Gemini
							<Icon name="arrow-right" size={12} />
						</a>
						<a
							href="https://copilot.microsoft.com/"
							target="_blank"
							rel="noopener noreferrer"
							class="flex items-center gap-1.5 rounded border border-neutral-800 bg-neutral-900 px-3 py-1.5 text-xs text-neutral-100 hover:bg-neutral-800"
						>
							Copilot
							<Icon name="arrow-right" size={12} />
						</a>
						<a
							href="https://www.perplexity.ai/"
							target="_blank"
							rel="noopener noreferrer"
							class="flex items-center gap-1.5 rounded border border-neutral-800 bg-neutral-900 px-3 py-1.5 text-xs text-neutral-100 hover:bg-neutral-800"
						>
							Perplexity
							<Icon name="arrow-right" size={12} />
						</a>
						<a
							href="https://chat.mistral.ai/"
							target="_blank"
							rel="noopener noreferrer"
							class="flex items-center gap-1.5 rounded border border-neutral-800 bg-neutral-900 px-3 py-1.5 text-xs text-neutral-100 hover:bg-neutral-800"
						>
							Mistral
							<Icon name="arrow-right" size={12} />
						</a>
					</div>
				</div>
			</div>
		</div>
	</div>
{/if}

<svelte:window onkeydown={(e) => open && e.key === 'Escape' && (open = false)} />
