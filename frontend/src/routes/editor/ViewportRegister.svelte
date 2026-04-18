<script lang="ts">
	import { onMount } from 'svelte';
	import { useSvelteFlow } from '@xyflow/svelte';
	import { setViewportCenterGetter } from '$lib/viewport-state';

	const flow = useSvelteFlow();

	onMount(() => {
		setViewportCenterGetter(() => {
			try {
				const el = document.querySelector<HTMLElement>('.svelte-flow');
				if (!el) return null;
				const rect = el.getBoundingClientRect();
				return flow.screenToFlowPosition({
					x: rect.left + rect.width / 2,
					y: rect.top + rect.height / 2
				});
			} catch {
				return null;
			}
		});
		return () => setViewportCenterGetter(null);
	});
</script>
