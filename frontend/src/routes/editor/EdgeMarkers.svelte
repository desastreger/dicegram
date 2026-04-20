<!--
  Hidden SVG that publishes our custom edge-terminator markers into the
  document. Referenced by xyflow's `markerEnd` / `markerStart` via
  `url(#dcg-…)`. Markers use `fill="context-stroke"` (and
  `stroke="context-stroke"` for outlined variants) so every terminator
  automatically inherits the edge's current stroke colour — no need to
  duplicate markers per theme or per custom edge colour.
-->
<svg
	aria-hidden="true"
	focusable="false"
	width="0"
	height="0"
	style="position:absolute;width:0;height:0;overflow:hidden"
>
	<defs>
		<!-- Filled triangle, pointed away from the node (used at the target end). -->
		<marker
			id="dcg-arrow"
			viewBox="0 0 10 10"
			refX="10"
			refY="5"
			markerWidth="10"
			markerHeight="10"
			orient="auto-start-reverse"
			markerUnits="userSpaceOnUse"
		>
			<path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke" />
		</marker>
		<!-- Reversed triangle for source-side arrows (point back at the node). -->
		<marker
			id="dcg-arrow-rev"
			viewBox="0 0 10 10"
			refX="0"
			refY="5"
			markerWidth="10"
			markerHeight="10"
			orient="auto"
			markerUnits="userSpaceOnUse"
		>
			<path d="M 10 0 L 0 5 L 10 10 z" fill="context-stroke" />
		</marker>
		<!-- Outlined arrow (UML "interface", "implements"). -->
		<marker
			id="dcg-open-arrow"
			viewBox="0 0 10 10"
			refX="10"
			refY="5"
			markerWidth="10"
			markerHeight="10"
			orient="auto-start-reverse"
			markerUnits="userSpaceOnUse"
		>
			<path d="M 0 0 L 10 5 L 0 10" fill="none" stroke="context-stroke" stroke-width="1.5" />
		</marker>
		<marker
			id="dcg-open-arrow-rev"
			viewBox="0 0 10 10"
			refX="0"
			refY="5"
			markerWidth="10"
			markerHeight="10"
			orient="auto"
			markerUnits="userSpaceOnUse"
		>
			<path d="M 10 0 L 0 5 L 10 10" fill="none" stroke="context-stroke" stroke-width="1.5" />
		</marker>
		<!-- Filled circle terminator. -->
		<marker
			id="dcg-circle"
			viewBox="0 0 10 10"
			refX="5"
			refY="5"
			markerWidth="8"
			markerHeight="8"
			orient="auto"
			markerUnits="userSpaceOnUse"
		>
			<circle cx="5" cy="5" r="3.5" fill="context-stroke" />
		</marker>
		<!-- Filled diamond (UML "composition-lite"). -->
		<marker
			id="dcg-diamond"
			viewBox="0 0 12 10"
			refX="11"
			refY="5"
			markerWidth="12"
			markerHeight="10"
			orient="auto-start-reverse"
			markerUnits="userSpaceOnUse"
		>
			<path d="M 0 5 L 6 0 L 12 5 L 6 10 z" fill="context-stroke" />
		</marker>
		<!-- Tee / stop bar — "must-not" or "blocked" semantic. -->
		<marker
			id="dcg-tee"
			viewBox="0 0 4 10"
			refX="2"
			refY="5"
			markerWidth="4"
			markerHeight="10"
			orient="auto"
			markerUnits="userSpaceOnUse"
		>
			<rect x="0" y="0" width="4" height="10" fill="context-stroke" />
		</marker>
		<!-- Square terminator. -->
		<marker
			id="dcg-square"
			viewBox="0 0 8 8"
			refX="4"
			refY="4"
			markerWidth="8"
			markerHeight="8"
			orient="auto"
			markerUnits="userSpaceOnUse"
		>
			<rect x="1" y="1" width="6" height="6" fill="context-stroke" />
		</marker>
	</defs>
</svg>
