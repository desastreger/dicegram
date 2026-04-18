<script lang="ts">
	import { useSvelteFlow } from '@xyflow/svelte';

	let { focusId = null, trigger = 0 }: { focusId?: string | null; trigger?: number } = $props();

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
</script>
