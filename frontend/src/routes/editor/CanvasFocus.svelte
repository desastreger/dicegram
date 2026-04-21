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
		// Orientation flips happen in two steps: the DSL is rewritten
		// first, then the backend re-renders and new node positions land
		// here ~250 ms later. Fitting the view right now would frame the
		// OLD layout. Retry three times at widening intervals so we
		// always catch the post-render state, regardless of whether the
		// user's net latency is 10 ms or 600 ms.
		let attempts = 0;
		const tryFit = () => {
			try {
				flow.fitView({ duration: 320, padding: 0.2 });
			} catch {
				/* flow not ready yet */
			}
			attempts += 1;
			if (attempts < 3) setTimeout(tryFit, attempts === 1 ? 350 : 450);
		};
		setTimeout(tryFit, 0);
	});
</script>
