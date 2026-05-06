<script lang="ts">
  import {
    setNodeLabel,
    setNodeShape,
    setNodeName,
    setNodeAttr,
    removeNodeAttr,
    setNodeStyle,
    removeNodeStyle,
    setNodePosition,
    clearNodePosition,
    removeNode,
    type ParentTarget,
  } from '$lib/patch';
  import Icon from '$lib/Icon.svelte';
  import Dropdown from '$lib/Dropdown.svelte';
  import ShapePreview from './ShapePreview.svelte';
  import EdgePanel from './EdgePanel.svelte';
  import ObjectPanel, { type ObjectKind } from './ObjectPanel.svelte';
  import type { RenderNode, RenderResult } from '$lib/render';
  import { palette } from '$lib/palette.svelte';

  let {
    source = $bindable(''),
    selected,
    selectedEdgeId = null,
    selectedObjectKind = null,
    selectedObjectIndex = -1,
    result,
    open = $bindable(false),
    labelFocusTrigger = 0,
    onClose,
    onSelectionChange,
    onEdgeSelectionChange,
    onObjectSelectionChange,
    onReparent,
    onSiblingMove,
  }: {
    source: string;
    selected: RenderNode | null;
    selectedEdgeId?: string | null;
    selectedObjectKind?: ObjectKind | null;
    selectedObjectIndex?: number;
    result: RenderResult | null;
    open: boolean;
    labelFocusTrigger?: number;
    onClose: () => void;
    onSelectionChange: (newId: string | null) => void;
    onEdgeSelectionChange?: (id: string | null) => void;
    onObjectSelectionChange?: (kind: ObjectKind | null, index: number) => void;
    onReparent?: (id: string, target: ParentTarget) => void;
    onSiblingMove?: (id: string, direction: -1 | 1) => void;
  } = $props();

  const SHAPES = [
    'rect',
    'rounded',
    'diamond',
    'circle',
    'parallelogram',
    'hexagon',
    'cylinder',
    'stadium',
  ];

  const TYPES = [
    'process',
    'decision',
    'input',
    'output',
    'datastore',
    'start',
    'end',
    'manual',
    'automated',
    'approval',
    'external',
  ];

  const STATUSES = ['draft', 'active', 'blocked', 'deprecated', 'complete'];
  const PRIORITIES = ['low', 'medium', 'high', 'critical'];

  const currentId = $derived(selected?.id ?? '');
  const currentName = $derived(selected?.id ?? '');
  const currentShape = $derived(selected?.shape ?? 'rect');
  const currentLabel = $derived(selected?.label ?? '');
  const currentX = $derived(selected?.x ?? 0);
  const currentY = $derived(selected?.y ?? 0);
  const currentWidth = $derived(selected?.width ?? 0);
  const currentHeight = $derived(selected?.height ?? 0);
  const currentStep = $derived(selected?.attrs?.step ?? '');
  const currentType = $derived(selected?.attrs?.type ?? '');
  const currentOwner = $derived(selected?.attrs?.owner ?? '');
  const currentStatus = $derived(selected?.attrs?.status ?? '');
  const currentPriority = $derived(selected?.attrs?.priority ?? '');
  const currentTags = $derived(selected?.attrs?.tags ?? '');
  // When a colour has no inline DSL value, fall back to the palette-
  // resolved colour (type-fill + node defaults) so the inspector swatch
  // matches what the canvas actually renders.
  const typeAttrForPal = $derived(selected?.attrs?.type ?? '');
  const statusForPal = $derived(selected?.attrs?.status ?? '');
  const priorityForPal = $derived(selected?.attrs?.priority ?? '');
  const paletteFill = $derived(palette.typeFill(typeAttrForPal));
  const paletteStroke = $derived(
    priorityForPal === 'critical'
      ? palette.current.priority_critical
      : priorityForPal === 'high'
        ? palette.current.priority_high
        : statusForPal === 'blocked'
          ? palette.current.status_blocked
          : statusForPal === 'complete'
            ? palette.current.status_complete
            : palette.current.node_stroke
  );
  const paletteText = $derived(
    statusForPal === 'deprecated' ? palette.current.status_deprecated_text : palette.current.node_text
  );
  const fillFromPalette = $derived(!selected?.style?.fill);
  const strokeFromPalette = $derived(!selected?.style?.stroke);
  const textFromPalette = $derived(!selected?.style?.text);
  const currentFill = $derived(selected?.style?.fill ?? paletteFill);
  const currentStroke = $derived(selected?.style?.stroke ?? paletteStroke);
  const currentText = $derived(selected?.style?.text ?? paletteText);
  const currentRx = $derived(selected?.style?.rx ?? '');
  const currentFontSize = $derived(selected?.style?.font_size ?? '');
  const currentOpacity = $derived(selected?.style?.opacity ?? '');
  const currentStrokeWidth = $derived(selected?.style?.stroke_width ?? '');
  const currentFontFamily = $derived(selected?.style?.font_family ?? '');

  let nameDraft = $state('');
  let labelDraft = $state('');
  let ownerDraft = $state('');
  let tagsDraft = $state('');
  let xDraft = $state(0);
  let yDraft = $state(0);
  let widthDraft = $state(0);
  let heightDraft = $state(0);
  let stepDraft = $state('');
  let rxDraft = $state('');
  let fontSizeDraft = $state('');
  let opacityDraft = $state('');
  let strokeWidthDraft = $state('');
  let fontFamilyDraft = $state('');

  let labelTextarea: HTMLTextAreaElement | null = $state(null);
  let lastLabelFocusTrigger = -1;
  $effect(() => {
    if (labelFocusTrigger !== lastLabelFocusTrigger) {
      lastLabelFocusTrigger = labelFocusTrigger;
      if (labelFocusTrigger > 0) {
        queueMicrotask(() => {
          labelTextarea?.focus();
          labelTextarea?.select();
        });
      }
    }
  });

  let lastId = $state<string | null>(null);
  $effect(() => {
    if (selected && selected.id !== lastId) {
      lastId = selected.id;
      nameDraft = selected.id;
      labelDraft = selected.label ?? '';
      ownerDraft = selected.attrs?.owner ?? '';
      tagsDraft = selected.attrs?.tags ?? '';
      xDraft = selected.x ?? 0;
      yDraft = selected.y ?? 0;
      widthDraft = selected.width ?? 0;
      heightDraft = selected.height ?? 0;
      stepDraft = selected.attrs?.step ?? '';
      rxDraft = selected.style?.rx ?? '';
      fontSizeDraft = selected.style?.font_size ?? '';
      opacityDraft = selected.style?.opacity ?? '';
      strokeWidthDraft = selected.style?.stroke_width ?? '';
      fontFamilyDraft = selected.style?.font_family ?? '';
    } else if (!selected) {
      lastId = null;
    }
  });

  function commitStyleNum(key: 'rx' | 'font_size' | 'opacity' | 'stroke_width', value: string) {
    if (!selected) return;
    const trimmed = value.trim();
    if (!trimmed) {
      source = removeNodeStyle(source, selected.id, key);
    } else {
      source = setNodeStyle(source, selected.id, key, trimmed);
    }
  }

  function clearStyleNum(key: 'rx' | 'font_size' | 'opacity' | 'stroke_width') {
    if (!selected) return;
    source = removeNodeStyle(source, selected.id, key);
    if (key === 'rx') rxDraft = '';
    else if (key === 'font_size') fontSizeDraft = '';
    else if (key === 'opacity') opacityDraft = '';
    else if (key === 'stroke_width') strokeWidthDraft = '';
  }

  function commitFontFamily() {
    if (!selected) return;
    const v = fontFamilyDraft.trim();
    if (!v) {
      source = removeNodeStyle(source, selected.id, 'font_family');
    } else {
      source = setNodeStyle(source, selected.id, 'font_family', v);
    }
  }

  function clearFontFamily() {
    if (!selected) return;
    source = removeNodeStyle(source, selected.id, 'font_family');
    fontFamilyDraft = '';
  }

  // PowerPoint Slide Master + Godot "Make Unique" — a node tracks the
  // active theme by default. Make Unique snapshots every currently-
  // resolved color/typography token into inline `style:` keys so future
  // theme swaps don't touch this node. Snap to Master clears every inline
  // override and the node re-skins to the master theme on the next render.
  const isUnique = $derived(
    !!selected && selected.style && Object.keys(selected.style).length > 0
  );

  function makeUnique() {
    if (!selected || palette.locked) return;
    let next = source;
    const captures: Array<[string, string]> = [
      ['fill', currentFill],
      ['stroke', currentStroke],
      ['text', currentText],
    ];
    // Only capture typography that has a resolved value the master would
    // otherwise own. We don't capture font_size etc. because there's no
    // theme-level value for them today — they default at the renderer.
    for (const [k, v] of captures) {
      if (v) next = setNodeStyle(next, selected.id, k, v);
    }
    source = next;
  }

  function snapToMaster() {
    if (!selected) return;
    let next = source;
    for (const k of ['fill', 'stroke', 'text', 'rx', 'font_size', 'opacity', 'stroke_width', 'font_family']) {
      next = removeNodeStyle(next, selected.id, k);
    }
    source = next;
    rxDraft = '';
    fontSizeDraft = '';
    opacityDraft = '';
    strokeWidthDraft = '';
    fontFamilyDraft = '';
  }

  type ContainerOption = {
    key: string;
    label: string;
    target: ParentTarget;
  };

  const containerOptions = $derived.by<ContainerOption[]>(() => {
    const opts: ContainerOption[] = [{ key: 'root', label: '(root)', target: { kind: 'root' } }];
    if (!result) return opts;
    for (const lane of result.lanes) {
      opts.push({
        key: `s:${lane.name}`,
        label: `Lane: ${lane.name}`,
        target: { kind: 'swimlane', name: lane.name }
      });
    }
    for (const box of result.boxes) {
      const prefix = box.swimlane ? `${box.swimlane} > ` : '';
      opts.push({
        key: `b:${box.swimlane ?? ''}::${box.label}`,
        label: `Box: ${prefix}${box.label}`,
        target: { kind: 'box', label: box.label, swimlane: box.swimlane }
      });
    }
    return opts;
  });

  const currentParentKey = $derived.by<string>(() => {
    if (!selected) return 'root';
    if (selected.box) return `b:${selected.swimlane ?? ''}::${selected.box}`;
    if (selected.swimlane) return `s:${selected.swimlane}`;
    return 'root';
  });

  function commitParent(key: string) {
    if (!selected || !onReparent) return;
    const match = containerOptions.find((o) => o.key === key);
    if (!match) return;
    onReparent(selected.id, match.target);
  }

  const dropdownParentOptions = $derived(
    containerOptions.map((o) => ({ value: o.key, label: o.label }))
  );
  const shapeOptions = SHAPES.map((s) => ({ value: s, label: s }));
  const typeOptions = [{ value: '', label: '(none)' }, ...TYPES.map((t) => ({ value: t, label: t }))];
  const statusOptions = [
    { value: '', label: '(none)' },
    ...STATUSES.map((s) => ({ value: s, label: s }))
  ];
  const priorityOptions = [
    { value: '', label: '(none)' },
    ...PRIORITIES.map((p) => ({ value: p, label: p }))
  ];

  function commitName() {
    if (!selected) return;
    const next = nameDraft.trim();
    if (!next || next === selected.id) return;
    source = setNodeName(source, selected.id, next);
    onSelectionChange(next);
  }

  function commitLabel() {
    if (!selected) return;
    if (labelDraft === selected.label) return;
    source = setNodeLabel(source, selected.id, labelDraft);
  }

  function commitShape(v: string) {
    if (!selected) return;
    source = setNodeShape(source, selected.id, v);
  }

  function commitPosition() {
    if (!selected) return;
    source = setNodePosition(source, selected.id, xDraft, yDraft);
  }

  function commitWidth() {
    if (!selected) return;
    const v = Number(widthDraft);
    if (!Number.isFinite(v) || v <= 0) {
      source = removeNodeAttr(source, selected.id, 'width');
    } else {
      source = setNodeAttr(source, selected.id, 'width', String(v));
    }
  }

  function commitHeight() {
    if (!selected) return;
    const v = Number(heightDraft);
    if (!Number.isFinite(v) || v <= 0) {
      source = removeNodeAttr(source, selected.id, 'height');
    } else {
      source = setNodeAttr(source, selected.id, 'height', String(v));
    }
  }

  function commitStep() {
    if (!selected) return;
    const v = stepDraft.trim();
    if (!v) {
      source = removeNodeAttr(source, selected.id, 'step');
    } else {
      source = setNodeAttr(source, selected.id, 'step', v);
    }
  }

  function autoPosition() {
    if (!selected) return;
    source = clearNodePosition(source, selected.id);
  }

  function commitAttr(key: string, value: string) {
    if (!selected) return;
    if (!value) {
      source = removeNodeAttr(source, selected.id, key);
    } else {
      source = setNodeAttr(source, selected.id, key, value);
    }
  }

  function commitOwner() {
    commitAttr('owner', ownerDraft.trim());
  }

  function commitTags() {
    commitAttr('tags', tagsDraft.trim());
  }

  function commitSelectAttr(key: string) {
    return (v: string) => commitAttr(key, v);
  }

  function commitStyle(key: 'fill' | 'stroke' | 'text', value: string) {
    if (!selected) return;
    source = setNodeStyle(source, selected.id, key, value);
  }

  function clearStyle(key: 'fill' | 'stroke' | 'text') {
    if (!selected) return;
    source = removeNodeStyle(source, selected.id, key);
  }

  function commitHex(key: 'fill' | 'stroke' | 'text', value: string) {
    const v = value.trim();
    if (!v) return clearStyle(key);
    const m = /^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$/.exec(v);
    if (!m) return;
    commitStyle(key, v.startsWith('#') ? v : `#${v}`);
  }

  let confirmDelete = $state(false);
  let confirmDeleteTimer: ReturnType<typeof setTimeout> | null = null;

  function handleDelete() {
    if (!selected) return;
    if (!confirmDelete) {
      confirmDelete = true;
      if (confirmDeleteTimer) clearTimeout(confirmDeleteTimer);
      confirmDeleteTimer = setTimeout(() => {
        confirmDelete = false;
      }, 3000);
      return;
    }
    if (confirmDeleteTimer) clearTimeout(confirmDeleteTimer);
    confirmDelete = false;
    source = removeNode(source, selected.id);
    onSelectionChange(null);
  }

  function onTextKey(e: KeyboardEvent, commit: () => void) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      (e.currentTarget as HTMLElement).blur();
      commit();
    }
  }
</script>

{#if open}
  <aside
    class="flex h-full min-h-0 w-full flex-col border-l text-xs"
    style:background-color="var(--th-panel, var(--app-surface))"
    style:border-color="var(--th-panel-border, var(--app-border))"
    style:color="var(--th-text, var(--app-text))"
  >
    <header class="dg-inspector-head">
      <div class="flex items-baseline gap-1.5">
        <h2 class="dg-inspector-title">
          <Icon name="panel-right" size={13} /> Inspector
        </h2>
        {#if selected}
          <span class="dg-inspector-id numeric">&lt;{currentId}&gt;</span>
        {/if}
      </div>
      <button
        type="button"
        onclick={onClose}
        class="btn-icon"
        aria-label="Close inspector"
      >
        <Icon name="x" size={14} />
      </button>
    </header>

    {#if selectedObjectKind}
      <div class="min-h-0 flex-1 overflow-y-auto" data-editor-scroll>
        <ObjectPanel
          bind:source
          kind={selectedObjectKind}
          index={selectedObjectIndex}
          {result}
          onSelectionChange={(k, i) => onObjectSelectionChange?.(k, i)}
        />
      </div>
    {:else if selectedEdgeId}
      <div class="min-h-0 flex-1 overflow-y-auto" data-editor-scroll>
        <EdgePanel
          bind:source
          {selectedEdgeId}
          {result}
          onSelectionChange={(id) => onEdgeSelectionChange?.(id)}
        />
      </div>
    {:else if !selected}
      <div class="dg-inspector-empty">
        <div class="dg-inspector-empty-icon" aria-hidden="true">
          <Icon name="panel-right" size={20} />
        </div>
        <p>Select a shape, edge, or container on the canvas to edit its properties here.</p>
      </div>
    {:else}
      <!-- Preview sits pinned at the top of the shape branch and stays
           visible while the fields below scroll. -->
      <div class="dg-inspector-preview">
        <ShapePreview node={selected} />
      </div>
      <div class="min-h-0 flex-1 overflow-y-auto" data-editor-scroll>
      <!-- Shape selector is the primary "type" control for a node — it
           sits above everything else so the user can change what the
           thing *is* before tweaking details. -->
      <div class="dg-section-head">Shape</div>
      <div class="px-3">
        <Dropdown
          value={currentShape}
          options={shapeOptions}
          onchange={commitShape}
          ariaLabel="Shape"
        />
      </div>

      <div class="dg-section-head dg-section-head-row">
        <span>Hierarchy</span>
        <div class="flex items-center gap-0.5">
          <button
            type="button"
            title="Move up among siblings"
            aria-label="Move up among siblings"
            class="dg-mini-icon"
            onclick={() => selected && onSiblingMove?.(selected.id, -1)}
          >
            <Icon name="move-up" size={11} />
          </button>
          <button
            type="button"
            title="Move down among siblings"
            aria-label="Move down among siblings"
            class="dg-mini-icon"
            onclick={() => selected && onSiblingMove?.(selected.id, 1)}
          >
            <Icon name="move-down" size={11} />
          </button>
        </div>
      </div>
      <div class="px-3">
        <Dropdown
          value={currentParentKey}
          options={dropdownParentOptions}
          onchange={commitParent}
          ariaLabel="Parent container"
        />
      </div>

      <div class="dg-section-head">Identity</div>
      <div class="space-y-1 px-3">
        <label class="flex items-center gap-2">
          <span class="dg-field-label">Name</span>
          <input
            type="text"
            class="dg-input"
            bind:value={nameDraft}
            onblur={commitName}
            onkeydown={(e) => onTextKey(e, commitName)}
          />
        </label>
        <label class="flex items-start gap-2">
          <span class="dg-field-label" style="padding-top: 0.25rem;">Label</span>
          <textarea
            bind:this={labelTextarea}
            rows="3"
            class="dg-input dg-input-multi"
            bind:value={labelDraft}
            onblur={commitLabel}
          ></textarea>
        </label>
      </div>

      <div
        class="dg-section-head dg-section-head-row"
      >
        <span>Position &amp; Size</span>
        <button
          type="button"
          class="dg-mini"
          title="Revert to auto-layout position"
          aria-label="Revert to auto-layout position"
          onclick={autoPosition}
        >
          Auto
        </button>
      </div>
      <div class="grid grid-cols-2 gap-1 px-3">
        <label class="flex items-center gap-1">
          <span class="dg-field-label dg-field-label-tight" aria-hidden="true">X</span>
          <input
            type="number"
            aria-label="X position"
            class="dg-input"
            bind:value={xDraft}
            onchange={commitPosition}
          />
        </label>
        <label class="flex items-center gap-1">
          <span class="dg-field-label dg-field-label-tight" aria-hidden="true">Y</span>
          <input
            type="number"
            aria-label="Y position"
            class="dg-input"
            bind:value={yDraft}
            onchange={commitPosition}
          />
        </label>
        <label class="flex items-center gap-1">
          <span class="dg-field-label dg-field-label-tight" aria-hidden="true">W</span>
          <input
            type="number"
            aria-label="Width"
            class="dg-input"
            bind:value={widthDraft}
            onchange={commitWidth}
          />
        </label>
        <label class="flex items-center gap-1">
          <span class="dg-field-label dg-field-label-tight" aria-hidden="true">H</span>
          <input
            type="number"
            aria-label="Height"
            class="dg-input"
            bind:value={heightDraft}
            onchange={commitHeight}
          />
        </label>
        <label class="col-span-2 flex items-center gap-2">
          <span class="dg-field-label">Step</span>
          <input
            type="text"
            class="dg-input"
            bind:value={stepDraft}
            onblur={commitStep}
            onkeydown={(e) => onTextKey(e, commitStep)}
          />
        </label>
      </div>

      <div class="dg-section-head">Semantics</div>
      <div class="space-y-1 px-3">
        <div class="flex items-center gap-2">
          <span class="dg-field-label">Type</span>
          <div class="flex-1">
            <Dropdown
              value={currentType}
              options={typeOptions}
              onchange={commitSelectAttr('type')}
              ariaLabel="Type"
            />
          </div>
        </div>
        <label class="flex items-center gap-2">
          <span class="dg-field-label">Owner</span>
          <input
            type="text"
            class="dg-input"
            bind:value={ownerDraft}
            onblur={commitOwner}
            onkeydown={(e) => onTextKey(e, commitOwner)}
          />
        </label>
        <div class="flex items-center gap-2">
          <span class="dg-field-label">Status</span>
          <div class="flex-1">
            <Dropdown
              value={currentStatus}
              options={statusOptions}
              onchange={commitSelectAttr('status')}
              ariaLabel="Status"
            />
          </div>
        </div>
        <div class="flex items-center gap-2">
          <span class="dg-field-label">Priority</span>
          <div class="flex-1">
            <Dropdown
              value={currentPriority}
              options={priorityOptions}
              onchange={commitSelectAttr('priority')}
              ariaLabel="Priority"
            />
          </div>
        </div>
        <label class="flex items-center gap-2">
          <span class="dg-field-label">Tags</span>
          <input
            type="text"
            placeholder="a, b, c"
            class="dg-input"
            bind:value={tagsDraft}
            onblur={commitTags}
            onkeydown={(e) => onTextKey(e, commitTags)}
          />
        </label>
      </div>

      <div class="dg-section-head dg-section-head-row">
        <span class="flex items-center gap-1.5">
          Style
          {#if isUnique}
            <span
              class="dg-unique-pill"
              title="Detached from the master theme — overrides survive theme swaps"
            >
              <span class="dg-unique-dot"></span>
              Unique
            </span>
          {/if}
        </span>
        {#if palette.locked}
          <span title="Brand palette is locked in Settings" class="dg-locked">
            Palette locked
          </span>
        {/if}
      </div>

      <!-- Master / Unique toggle row. Make Unique captures the resolved
           colours so a later theme change won't repaint this node; Snap to
           Master clears every inline override so the node re-skins. -->
      {#if !palette.locked}
        <div class="dg-master-row">
          {#if isUnique}
            <button
              type="button"
              class="dg-master-btn"
              title="Drop every inline override and re-skin from the active theme"
              onclick={snapToMaster}
            >
              <Icon name="unlock" size={11} /> Snap to master
            </button>
          {:else}
            <button
              type="button"
              class="dg-master-btn"
              title="Pin the current resolved colours so future theme swaps don't touch this node"
              onclick={makeUnique}
            >
              <Icon name="lock" size={11} /> Make unique
            </button>
          {/if}
        </div>
      {/if}
      {#if palette.locked}
        <p class="dg-locked-note">
          Colour overrides are disabled. Edit the active palette in
          <a href="/settings" class="link">Settings</a> to change colours.
        </p>
      {:else}
      <div class="space-y-1 px-3">
        <div class="flex items-center gap-2">
          <span class="dg-field-label" aria-hidden="true">Fill</span>
          <input
            type="color"
            class="dg-color"
            value={currentFill}
            onchange={(e) => commitStyle('fill', (e.target as HTMLInputElement).value)}
            aria-label="Fill colour (overrides palette)"
          />
          <input
            type="text"
            placeholder="auto"
            class="dg-input dg-input-mono"
            value={selected.style?.fill ?? ''}
            onchange={(e) => commitHex('fill', (e.target as HTMLInputElement).value)}
            aria-label="Fill colour hex value"
          />
          <button
            type="button"
            class="dg-mini"
            onclick={() => clearStyle('fill')}
            aria-label="Reset fill colour to palette default"
            title="Revert to palette default"
          >
            Reset
          </button>
        </div>
        <div class="flex items-center gap-2">
          <span class="dg-field-label" aria-hidden="true">Stroke</span>
          <input
            type="color"
            class="dg-color"
            value={currentStroke}
            onchange={(e) => commitStyle('stroke', (e.target as HTMLInputElement).value)}
            aria-label="Stroke colour (overrides palette)"
          />
          <input
            type="text"
            placeholder="auto"
            class="dg-input dg-input-mono"
            value={selected.style?.stroke ?? ''}
            onchange={(e) => commitHex('stroke', (e.target as HTMLInputElement).value)}
            aria-label="Stroke colour hex value"
          />
          <button
            type="button"
            class="dg-mini"
            onclick={() => clearStyle('stroke')}
            aria-label="Reset stroke colour to palette default"
            title="Revert to palette default"
          >
            Reset
          </button>
        </div>
        <div class="flex items-center gap-2">
          <span class="dg-field-label" aria-hidden="true">Text</span>
          <input
            type="color"
            class="dg-color"
            value={currentText}
            onchange={(e) => commitStyle('text', (e.target as HTMLInputElement).value)}
            aria-label="Text colour (overrides palette)"
          />
          <input
            type="text"
            placeholder="auto"
            class="dg-input dg-input-mono"
            value={selected.style?.text ?? ''}
            onchange={(e) => commitHex('text', (e.target as HTMLInputElement).value)}
            aria-label="Text colour hex value"
          />
          <button
            type="button"
            class="dg-mini"
            onclick={() => clearStyle('text')}
            aria-label="Reset text colour to palette default"
            title="Revert to palette default"
          >
            Reset
          </button>
        </div>
      </div>
      {/if}

      <div class="dg-section-head">
        Typography &amp; shape
      </div>
      <div class="grid grid-cols-2 gap-1 px-3">
        <div class="flex items-center gap-1">
          <span class="dg-field-label" aria-hidden="true">Font</span>
          <input
            type="number"
            placeholder="13"
            min="6"
            aria-label="Font size"
            class="dg-input"
            bind:value={fontSizeDraft}
            onblur={() => commitStyleNum('font_size', fontSizeDraft)}
            onkeydown={(e) => onTextKey(e, () => commitStyleNum('font_size', fontSizeDraft))}
          />
          <button
            type="button"
            class="dg-mini-x"
            disabled={!selected?.style?.font_size}
            onclick={() => clearStyleNum('font_size')}
            aria-label="Clear font size override"
            title="Clear override (revert to master)"
          >
            <Icon name="x" size={9} />
          </button>
        </div>
        <div class="flex items-center gap-1">
          <span class="dg-field-label" aria-hidden="true">Radius</span>
          <input
            type="number"
            placeholder="auto"
            min="0"
            aria-label="Corner radius"
            class="dg-input"
            bind:value={rxDraft}
            onblur={() => commitStyleNum('rx', rxDraft)}
            onkeydown={(e) => onTextKey(e, () => commitStyleNum('rx', rxDraft))}
          />
          <button
            type="button"
            class="dg-mini-x"
            disabled={!selected?.style?.rx}
            onclick={() => clearStyleNum('rx')}
            aria-label="Clear corner radius override"
            title="Clear override (revert to master)"
          >
            <Icon name="x" size={9} />
          </button>
        </div>
        <div class="flex items-center gap-1">
          <span class="dg-field-label" aria-hidden="true">Stroke</span>
          <input
            type="number"
            placeholder="auto"
            min="0"
            step="0.25"
            aria-label="Stroke width"
            class="dg-input"
            bind:value={strokeWidthDraft}
            onblur={() => commitStyleNum('stroke_width', strokeWidthDraft)}
            onkeydown={(e) =>
              onTextKey(e, () => commitStyleNum('stroke_width', strokeWidthDraft))}
          />
          <button
            type="button"
            class="dg-mini-x"
            disabled={!selected?.style?.stroke_width}
            onclick={() => clearStyleNum('stroke_width')}
            aria-label="Clear stroke width override"
            title="Clear override (revert to master)"
          >
            <Icon name="x" size={9} />
          </button>
        </div>
        <div class="flex items-center gap-1">
          <span class="dg-field-label" aria-hidden="true">Opacity</span>
          <input
            type="number"
            placeholder="1"
            min="0"
            max="1"
            step="0.05"
            aria-label="Opacity"
            class="dg-input"
            bind:value={opacityDraft}
            onblur={() => commitStyleNum('opacity', opacityDraft)}
            onkeydown={(e) => onTextKey(e, () => commitStyleNum('opacity', opacityDraft))}
          />
          <button
            type="button"
            class="dg-mini-x"
            disabled={!selected?.style?.opacity}
            onclick={() => clearStyleNum('opacity')}
            aria-label="Clear opacity override"
            title="Clear override (revert to master)"
          >
            <Icon name="x" size={9} />
          </button>
        </div>
        <div class="col-span-2 flex items-center gap-2">
          <span class="dg-field-label" aria-hidden="true">Font family</span>
          <input
            type="text"
            placeholder="inherit"
            aria-label="Font family"
            class="dg-input"
            bind:value={fontFamilyDraft}
            onblur={commitFontFamily}
            onkeydown={(e) => onTextKey(e, commitFontFamily)}
          />
          <button
            type="button"
            class="dg-mini"
            disabled={!selected?.style?.font_family}
            onclick={clearFontFamily}
            aria-label="Reset font family override"
            title="Clear override (revert to master)"
          >
            Reset
          </button>
        </div>
      </div>

      <button
        type="button"
        class="dg-delete-btn"
        class:dg-delete-confirm={confirmDelete}
        onclick={handleDelete}
      >
        <Icon name="trash" size={13} />
        {confirmDelete ? 'Click again to confirm' : 'Delete node'}
      </button>
      </div>
    {/if}
  </aside>
{/if}

<style>
	.dg-inspector-head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		flex-shrink: 0;
		padding: 0.5rem 0.85rem;
		background: var(--app-surface);
		border-bottom: 1px solid var(--app-border);
	}
	.dg-inspector-title {
		display: inline-flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.78rem;
		font-weight: 500;
		color: var(--app-text);
	}
	.dg-inspector-id {
		font-family: var(--app-mono-font);
		font-size: 0.65rem;
		color: var(--app-text-dim);
	}
	.dg-inspector-empty {
		padding: 1.5rem 1.25rem;
		text-align: center;
		color: var(--app-text-dim);
		font-size: 0.75rem;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.6rem;
	}
	.dg-inspector-empty-icon {
		width: 36px;
		height: 36px;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		border-radius: 9999px;
		background: var(--app-surface-2);
		color: var(--app-accent);
	}
	.dg-inspector-preview {
		flex-shrink: 0;
		border-bottom: 1px solid var(--app-rule);
	}

	.dg-section-head {
		margin: 0.85rem 0 0.35rem;
		padding: 0 0.85rem;
		font-size: 0.62rem;
		font-weight: 600;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		color: var(--app-text-dim);
	}
	.dg-section-head-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.dg-field-label {
		flex-shrink: 0;
		width: 3.5rem;
		font-size: 0.7rem;
		color: var(--app-text-muted);
	}
	.dg-field-label-tight {
		width: 1rem;
	}

	.dg-input {
		flex: 1;
		min-width: 0;
		height: 28px;
		padding: 0.15rem 0.5rem;
		font-size: 0.75rem;
		font-family: var(--app-body-font);
		color: var(--app-text);
		background: var(--app-surface-2);
		border: 1px solid var(--app-border);
		border-radius: var(--app-radius-sm);
		transition:
			border-color var(--app-dur-fast) var(--app-ease),
			box-shadow var(--app-dur-fast) var(--app-ease);
	}
	.dg-input:focus {
		outline: 2px solid var(--app-ring);
		outline-offset: 0;
		border-color: transparent;
	}
	.dg-input::placeholder { color: var(--app-text-dim); }
	.dg-input-multi {
		height: auto;
		padding: 0.35rem 0.5rem;
		resize: vertical;
		font-family: var(--app-body-font);
	}
	.dg-input-mono {
		font-family: var(--app-mono-font);
		font-size: 0.7rem;
	}

	.dg-color {
		height: 28px;
		width: 32px;
		flex-shrink: 0;
		padding: 0;
		background: var(--app-surface-2);
		border: 1px solid var(--app-border);
		border-radius: var(--app-radius-sm);
		cursor: pointer;
	}

	.dg-mini {
		flex-shrink: 0;
		padding: 0.2rem 0.55rem;
		font-size: 0.65rem;
		font-weight: 500;
		font-family: var(--app-body-font);
		color: var(--app-text-muted);
		background: transparent;
		border: 1px solid var(--app-border);
		border-radius: var(--app-radius-sm);
		cursor: pointer;
		transition:
			color var(--app-dur-fast) var(--app-ease),
			background-color var(--app-dur-fast) var(--app-ease),
			border-color var(--app-dur-fast) var(--app-ease);
	}
	.dg-mini:hover:not(:disabled) {
		color: var(--app-text);
		background: var(--app-hover);
		border-color: var(--app-border-strong);
	}
	.dg-mini:disabled { opacity: 0.35; cursor: not-allowed; }

	.dg-mini-x {
		flex-shrink: 0;
		padding: 0.15rem 0.3rem;
		color: var(--app-text-dim);
		background: transparent;
		border: 1px solid var(--app-border);
		border-radius: var(--app-radius-sm);
		cursor: pointer;
		transition: color var(--app-dur-fast) var(--app-ease);
	}
	.dg-mini-x:hover:not(:disabled) { color: var(--app-text); }
	.dg-mini-x:disabled { opacity: 0.3; }

	.dg-mini-icon {
		padding: 0.15rem;
		color: var(--app-text-muted);
		background: transparent;
		border: 1px solid var(--app-border);
		border-radius: var(--app-radius-sm);
		cursor: pointer;
		transition: color var(--app-dur-fast) var(--app-ease),
			background-color var(--app-dur-fast) var(--app-ease);
	}
	.dg-mini-icon:hover { color: var(--app-text); background: var(--app-hover); }

	.dg-unique-pill {
		display: inline-flex;
		align-items: center;
		gap: 0.25rem;
		padding: 0.05rem 0.45rem;
		font-size: 0.6rem;
		font-weight: 500;
		letter-spacing: 0;
		text-transform: none;
		color: var(--app-warn);
		background: color-mix(in srgb, var(--app-warn) 14%, var(--app-bg) 86%);
		border: 1px solid color-mix(in srgb, var(--app-warn) 45%, var(--app-border) 55%);
		border-radius: 9999px;
	}
	.dg-unique-dot {
		width: 6px;
		height: 6px;
		border-radius: 9999px;
		background: var(--app-warn);
	}

	.dg-locked {
		font-size: 0.62rem;
		text-transform: none;
		letter-spacing: 0;
		color: var(--app-accent);
	}

	.dg-master-row {
		display: flex;
		gap: 0.25rem;
		padding: 0 0.85rem 0.55rem;
	}
	.dg-master-btn {
		flex: 1;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: 0.3rem;
		padding: 0.35rem 0.55rem;
		font-size: 0.7rem;
		color: var(--app-text);
		background: var(--app-surface-2);
		border: 1px solid var(--app-border);
		border-radius: var(--app-radius-sm);
		cursor: pointer;
		transition: background-color var(--app-dur-fast) var(--app-ease);
	}
	.dg-master-btn:hover { background: var(--app-surface-3, var(--app-surface-2)); }

	.dg-locked-note {
		margin: 0 0.85rem 0.55rem;
		padding: 0.35rem 0.6rem;
		font-size: 0.7rem;
		color: var(--app-text);
		background: var(--app-accent-soft);
		border: 1px solid color-mix(in srgb, var(--app-accent) 35%, var(--app-border) 65%);
		border-radius: var(--app-radius-sm);
	}

	.dg-delete-btn {
		display: flex;
		width: calc(100% - 1.7rem);
		margin: 1rem 0.85rem;
		padding: 0.45rem 0.6rem;
		align-items: center;
		justify-content: center;
		gap: 0.4rem;
		font-size: 0.75rem;
		color: var(--app-danger);
		background: color-mix(in srgb, var(--app-danger) 8%, var(--app-bg) 92%);
		border: 1px solid color-mix(in srgb, var(--app-danger) 35%, var(--app-border) 65%);
		border-radius: var(--app-radius-sm);
		cursor: pointer;
		transition: background-color var(--app-dur-fast) var(--app-ease),
			color var(--app-dur-fast) var(--app-ease);
	}
	.dg-delete-btn:hover {
		background: color-mix(in srgb, var(--app-danger) 16%, var(--app-bg) 84%);
	}
	.dg-delete-confirm {
		background: var(--app-danger);
		color: var(--app-accent-text);
		border-color: var(--app-danger);
	}
	.dg-delete-confirm:hover {
		background: color-mix(in srgb, var(--app-danger) 88%, var(--app-text) 12%);
	}
</style>
