<script lang="ts">
	import Icon from './Icon.svelte';

	type Option = { value: string; label: string };

	type Props = {
		value: string;
		options: Option[];
		placeholder?: string;
		title?: string;
		onchange: (next: string) => void;
		disabled?: boolean;
	};

	let {
		value,
		options,
		placeholder = '',
		title,
		onchange,
		disabled = false
	}: Props = $props();

	let open = $state(false);
	let root: HTMLDivElement | undefined = $state();

	const current = $derived(options.find((o) => o.value === value));

	$effect(() => {
		if (!open) return;
		const onDoc = (e: MouseEvent) => {
			if (root && !root.contains(e.target as Node)) open = false;
		};
		const onKey = (e: KeyboardEvent) => {
			if (e.key === 'Escape') open = false;
		};
		document.addEventListener('click', onDoc);
		document.addEventListener('keydown', onKey);
		return () => {
			document.removeEventListener('click', onDoc);
			document.removeEventListener('keydown', onKey);
		};
	});

	function pick(v: string) {
		open = false;
		if (v !== value) onchange(v);
	}
</script>

<div class="dd" bind:this={root}>
	<button
		type="button"
		{disabled}
		aria-haspopup="listbox"
		aria-expanded={open}
		title={title ?? current?.label ?? placeholder}
		class="dd-btn"
		onclick={() => (open = !open)}
	>
		<span class="dd-label" class:muted={!current}>
			{current?.label ?? placeholder}
		</span>
		<Icon name="chevron-down" size={12} />
	</button>
	{#if open}
		<ul class="dd-menu" role="listbox">
			{#each options as opt (opt.value)}
				{@const active = opt.value === value}
				<li>
					<button
						type="button"
						role="option"
						aria-selected={active}
						class="dd-item"
						class:active
						title={opt.label}
						onclick={() => pick(opt.value)}
					>
						{opt.label}
					</button>
				</li>
			{/each}
		</ul>
	{/if}
</div>

<style>
	.dd {
		position: relative;
		width: 100%;
	}
	.dd-btn {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 4px;
		width: 100%;
		height: 26px;
		padding: 0 8px;
		border: 1px solid var(--th-panel-border, #404040);
		border-radius: 4px;
		background: var(--th-panel, #171717);
		color: var(--th-text, #e5e7eb);
		font-size: 12px;
		line-height: 1;
		cursor: pointer;
		text-align: left;
	}
	.dd-btn:hover:not(:disabled) {
		background: color-mix(in srgb, var(--th-panel, #171717) 80%, white 20%);
	}
	.dd-btn:disabled {
		opacity: 0.5;
		cursor: default;
	}
	.dd-label {
		flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.dd-label.muted {
		color: var(--th-muted, #9ca3af);
	}
	.dd-menu {
		position: absolute;
		top: calc(100% + 2px);
		left: 0;
		right: 0;
		z-index: 100;
		margin: 0;
		padding: 2px 0;
		list-style: none;
		background: var(--th-panel, #0a0a0a);
		border: 1px solid var(--th-panel-border, #404040);
		border-radius: 4px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
		max-height: 260px;
		overflow: auto;
		min-width: 100%;
		width: max-content;
		max-width: 360px;
	}
	.dd-item {
		display: block;
		width: 100%;
		padding: 5px 10px;
		border: 0;
		background: transparent;
		color: var(--th-text, #e5e7eb);
		font-size: 12px;
		text-align: left;
		cursor: pointer;
		white-space: nowrap;
	}
	.dd-item:hover {
		background: color-mix(in srgb, var(--th-panel, #171717) 60%, white 40%);
	}
	.dd-item.active {
		background: var(--th-accent, #3b82f6);
		color: white;
	}
</style>
