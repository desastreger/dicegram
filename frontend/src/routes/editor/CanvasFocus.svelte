<script lang="ts">
	import { useSvelteFlow } from '@xyflow/svelte';

	let {
		focusId = null,
		trigger = 0,
		fitAllTrigger = 0
	}: { focusId?: string | null; trigger?: number; fitAllTrigger?: number } = $props();

	const flow = useSvelteFlow();

	let lastTrigger = -1;
	$effect(() => {
		if (trigger === lastTrigger) return;
		lastTrigger = trigger;
		if (!focusId) return;
		try {
			flow.fitView({ nodes: [{ id: focusId }], duration: 280, padding: 0.35 });
		} catch {
			/* node not present yet */
		}
	});

	let lastFitAll = -1;
	$effect(() => {
		if (fitAllTrigger === lastFitAll) return;
		lastFitAll = fitAllTrigger;
		if (fitAllTrigger === 0) return;
		try {
			flow.fitView({ duration: 320, padding: 0.2 });
		} catch {
			/* flow not ready yet */
		}
	});
</script>
