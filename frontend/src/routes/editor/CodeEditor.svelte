<script lang="ts">
	import { onMount } from 'svelte';
	import { Compartment, EditorState } from '@codemirror/state';
	import { EditorView, keymap, lineNumbers, highlightActiveLine } from '@codemirror/view';
	import {
		defaultKeymap,
		history,
		historyKeymap,
		indentWithTab
	} from '@codemirror/commands';
	import { foldGutter, foldKeymap, foldService } from '@codemirror/language';
	import { completionKeymap } from '@codemirror/autocomplete';
	import { dslSyntaxExtension } from '$lib/dsl-syntax';
	import { dslAutocomplete } from '$lib/dsl-autocomplete';
	import type { Theme } from '$lib/themes';

	let {
		value = $bindable(''),
		theme,
		revealLine = null,
		readOnly = false,
		onNodeClick,
		onEdgeClick
	}: {
		value: string;
		theme: Theme;
		revealLine?: number | null;
		readOnly?: boolean;
		onNodeClick?: (id: string) => void;
		onEdgeClick?: (ordinal: number) => void;
	} = $props();

	// `[connector]`, `[solid_line]`, `[dashed_line]`, `[thick_line]`,
	// `[dotted_line]` + legacy `[arrow]`/`[dashed_arrow]`/`[thick_arrow]`
	// /`[line]`/`[solid_arrow]`. Any line starting with one of these is
	// treated as a connector definition.
	const CONNECTOR_OPEN_RE =
		/^\s*\[(connector|solid_line|dashed_line|thick_line|dotted_line|arrow|solid_arrow|dashed_arrow|thick_arrow|line)\]\b/;
	// Old inline form: `A -> B`, `A@r -> B@l : "lbl"`, etc.
	const INLINE_EDGE_RE =
		/^\s*\w+(?:@\w+)?\s*(?:->|-->|==>|---|-\.-)\s*\w+(?:@\w+)?/;

	function edgeOrdinalForLine(docText: string, targetLine: number): number {
		const lines = docText.split('\n');
		let seen = 0;
		for (let i = 0; i < lines.length; i++) {
			if (CONNECTOR_OPEN_RE.test(lines[i]) || INLINE_EDGE_RE.test(lines[i])) {
				if (i + 1 === targetLine) return seen;
				seen += 1;
			}
		}
		return -1;
	}

	let container: HTMLDivElement;
	let view: EditorView | undefined;
	let syncing = false;
	const themeCompartment = new Compartment();

	function palette(t: Theme) {
		const isLight = t.bg === '#ffffff' || t.bg === '#fdf6e3';
		return isLight
			? {
					keyword: '#7e22ce',
					string: '#16a34a',
					shape: '#b45309',
					ident: '#1d4ed8',
					arrow: '#475569',
					attr: '#be185d',
					comment: '#6b7280',
					pos: '#6d28d9'
				}
			: {
					keyword: '#c084fc',
					string: '#86efac',
					shape: '#fbbf24',
					ident: '#60a5fa',
					arrow: '#94a3b8',
					attr: '#f472b6',
					comment: '#6b7280',
					pos: '#a78bfa'
				};
	}

	function buildTheme(t: Theme) {
		const p = palette(t);
		const isLight = t.bg === '#ffffff' || t.bg === '#fdf6e3';
		return EditorView.theme(
			{
				'&': {
					height: '100%',
					fontSize: '13px',
					color: t.codeText,
					backgroundColor: t.codeBg
				},
				'.cm-scroller': {
					fontFamily:
						'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace'
				},
				'.cm-content': { caretColor: t.accent },
				'.cm-gutters': {
					backgroundColor: t.codeBg,
					color: t.codeGutter,
					border: 'none',
					borderRight: `1px solid ${t.panelBorder}`
				},
				'.cm-activeLine': { backgroundColor: t.codeActiveLine },
				'.cm-activeLineGutter': { backgroundColor: t.codeActiveLine, color: t.text },
				'.cm-selectionBackground, ::selection': {
					backgroundColor: `${t.accent}33 !important`
				},
				'.cm-foldGutter': { color: t.codeGutter, paddingRight: '2px' },
				'.cm-foldGutter .cm-gutterElement': { cursor: 'pointer' },
				'.cm-foldPlaceholder': {
					backgroundColor: t.panelBorder,
					color: t.muted,
					border: 'none',
					borderRadius: '3px',
					padding: '0 6px',
					margin: '0 2px',
					fontSize: '11px'
				},
				'.tok-keyword': { color: p.keyword, fontWeight: '600' },
				'.tok-string': { color: p.string },
				'.tok-shape': { color: p.shape, fontWeight: '600' },
				'.tok-ident': { color: p.ident },
				'.tok-ident.tok-ref': {
					cursor: 'pointer',
					textDecoration: 'underline',
					textDecorationColor: 'transparent',
					textDecorationThickness: '1px',
					textUnderlineOffset: '2px'
				},
				'.tok-ident.tok-ref:hover': {
					textDecorationColor: p.ident
				},
				'.tok-ident.tok-def': { fontWeight: '600' },
				'.tok-arrow': { color: p.arrow, fontWeight: '600' },
				'.tok-attr': { color: p.attr },
				'.tok-comment': { color: p.comment, fontStyle: 'italic' },
				'.tok-pos': { color: p.pos, fontStyle: 'italic' }
			},
			{ dark: !isLight }
		);
	}

	const dslFolds = foldService.of((state, lineStart) => {
		const line = state.doc.lineAt(lineStart);
		const text = line.text;
		if (!/\{\s*$/.test(text)) return null;
		let depth = 1;
		for (let ln = line.number + 1; ln <= state.doc.lines; ln++) {
			const next = state.doc.line(ln);
			const t = next.text;
			let i = 0;
			while (i < t.length) {
				const c = t[i];
				if (c === '/' && t[i + 1] === '/') break;
				if (c === '"') {
					const end = t.indexOf('"', i + 1);
					i = end === -1 ? t.length : end + 1;
					continue;
				}
				if (c === '{') depth++;
				else if (c === '}') {
					depth--;
					if (depth === 0) {
						return { from: line.to, to: next.from + i };
					}
				}
				i++;
			}
		}
		return null;
	});

	onMount(() => {
		view = new EditorView({
			parent: container,
			state: EditorState.create({
				doc: value,
				extensions: [
					lineNumbers(),
					foldGutter(),
					dslFolds,
					highlightActiveLine(),
					history(),
					keymap.of([
						...defaultKeymap,
						...historyKeymap,
						...foldKeymap,
						...completionKeymap,
						indentWithTab
					]),
					themeCompartment.of(buildTheme(theme)),
					EditorState.readOnly.of(readOnly),
					EditorView.editable.of(!readOnly),
					dslSyntaxExtension((id) => onNodeClick?.(id)),
					dslAutocomplete(),
					EditorView.updateListener.of((u) => {
						if (u.docChanged) {
							syncing = true;
							value = u.state.doc.toString();
							syncing = false;
						}
						if (u.selectionSet && !u.docChanged) {
							const line = u.state.doc.lineAt(u.state.selection.main.head);
							const nodeM = /^\s*\[(\w+)\]\s+(\w+)\s+"/.exec(line.text);
							if (nodeM && !CONNECTOR_OPEN_RE.test(line.text)) {
								onNodeClick?.(nodeM[2]);
							} else if (
								CONNECTOR_OPEN_RE.test(line.text) ||
								INLINE_EDGE_RE.test(line.text)
							) {
								const ord = edgeOrdinalForLine(u.state.doc.toString(), line.number);
								if (ord >= 0) onEdgeClick?.(ord);
							}
						}
					})
				]
			})
		});

		return () => view?.destroy();
	});

	$effect(() => {
		const incoming = value;
		if (syncing || !view) return;
		const current = view.state.doc.toString();
		if (incoming === current) return;
		// Preserve cursor / selection across outside-driven rewrites (e.g. the
		// normalize-source round-trip fires a new `value` a second after the
		// user stops typing). Without this, the cursor snaps back to 0 and
		// typing feels punitive. Clamp to the new length in case normalize
		// shortened the document.
		const sel = view.state.selection.main;
		const newLen = incoming.length;
		const anchor = Math.min(sel.anchor, newLen);
		const head = Math.min(sel.head, newLen);
		view.dispatch({
			changes: { from: 0, to: current.length, insert: incoming },
			selection: { anchor, head }
		});
	});

	$effect(() => {
		const t = theme;
		if (!view) return;
		view.dispatch({ effects: themeCompartment.reconfigure(buildTheme(t)) });
	});

	$effect(() => {
		const target = revealLine;
		if (!view || target == null) return;
		if (target < 1 || target > view.state.doc.lines) return;
		const line = view.state.doc.line(target);
		view.dispatch({
			selection: { anchor: line.from, head: line.to },
			scrollIntoView: true
		});
		view.focus();
	});
</script>

<div bind:this={container} class="h-full flex-1 overflow-auto"></div>
