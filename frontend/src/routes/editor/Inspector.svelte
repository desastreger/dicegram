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
  import type { RenderNode, RenderResult } from '$lib/render';

  let {
    source = $bindable(''),
    selected,
    result,
    open = $bindable(false),
    onClose,
    onSelectionChange,
    onReparent,
    onSiblingMove,
  }: {
    source: string;
    selected: RenderNode | null;
    result: RenderResult | null;
    open: boolean;
    onClose: () => void;
    onSelectionChange: (newId: string | null) => void;
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
  const currentFill = $derived(selected?.style?.fill ?? '#1f2937');
  const currentStroke = $derived(selected?.style?.stroke ?? '#4b5563');
  const currentText = $derived(selected?.style?.text ?? '#e5e7eb');
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

  function commitFontFamily() {
    if (!selected) return;
    const v = fontFamilyDraft.trim();
    if (!v) {
      source = removeNodeStyle(source, selected.id, 'font_family');
    } else {
      source = setNodeStyle(source, selected.id, 'font_family', v);
    }
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
    class="fixed top-[var(--header-h)] right-0 bottom-0 z-40 w-[340px] overflow-y-auto border-l border-neutral-800 bg-neutral-950 text-xs text-neutral-100"
  >
    <header
      class="sticky top-0 z-10 flex items-center justify-between border-b border-neutral-800 bg-neutral-950 px-3 py-2"
    >
      <div class="flex items-baseline gap-1.5">
        <h2 class="flex items-center gap-1.5 text-xs font-medium text-neutral-200">
          <Icon name="panel-right" size={13} /> Inspector
        </h2>
        {#if selected}
          <span class="font-mono text-[10px] text-neutral-500">&lt;{currentId}&gt;</span>
        {/if}
      </div>
      <button
        type="button"
        onclick={onClose}
        class="rounded p-1 text-neutral-400 hover:bg-neutral-800 hover:text-neutral-100"
        aria-label="Close inspector"
      >
        <Icon name="x" size={14} />
      </button>
    </header>

    {#if !selected}
      <div class="p-5 text-center text-[11px] text-neutral-500">
        Select a node to edit its properties.
      </div>
    {:else}
      <ShapePreview node={selected} />
      <div class="mt-3 mb-1 flex items-center justify-between px-3 text-[10px] uppercase tracking-wide text-neutral-500">
        <span>Hierarchy</span>
        <div class="flex items-center gap-0.5">
          <button
            type="button"
            title="Move up among siblings"
            class="rounded border border-neutral-800 p-0.5 text-neutral-400 hover:text-neutral-100"
            onclick={() => selected && onSiblingMove?.(selected.id, -1)}
          >
            <Icon name="move-up" size={11} />
          </button>
          <button
            type="button"
            title="Move down among siblings"
            class="rounded border border-neutral-800 p-0.5 text-neutral-400 hover:text-neutral-100"
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
        />
      </div>

      <div class="mt-3 mb-1 px-3 text-[10px] uppercase tracking-wide text-neutral-500">Identity</div>
      <div class="space-y-1 px-3">
        <div class="flex items-center gap-2">
          <label class="w-14 text-[11px] text-neutral-400">Name</label>
          <input
            type="text"
            class="h-6 flex-1 rounded border border-neutral-800 bg-neutral-900 px-1.5 text-xs text-neutral-100"
            bind:value={nameDraft}
            onblur={commitName}
            onkeydown={(e) => onTextKey(e, commitName)}
          />
        </div>
        <div class="flex items-center gap-2">
          <label class="w-14 text-[11px] text-neutral-400">Shape</label>
          <div class="flex-1">
            <Dropdown value={currentShape} options={shapeOptions} onchange={commitShape} />
          </div>
        </div>
        <div class="flex items-start gap-2">
          <label class="w-14 pt-1 text-[11px] text-neutral-400">Label</label>
          <textarea
            rows="3"
            class="flex-1 resize-y rounded border border-neutral-800 bg-neutral-900 px-1.5 py-1 text-xs text-neutral-100"
            bind:value={labelDraft}
            onblur={commitLabel}
          ></textarea>
        </div>
      </div>

      <div
        class="mt-3 mb-1 flex items-center justify-between px-3 text-[10px] uppercase tracking-wide text-neutral-500"
      >
        <span>Position &amp; Size</span>
        <button
          type="button"
          class="rounded border border-neutral-800 px-1.5 py-0.5 text-[10px] normal-case tracking-normal text-neutral-400 hover:text-neutral-100"
          title="Revert to auto-layout position"
          onclick={autoPosition}
        >
          Auto
        </button>
      </div>
      <div class="grid grid-cols-2 gap-1 px-3">
        <label class="flex items-center gap-1">
          <span class="w-4 text-[11px] text-neutral-400">X</span>
          <input
            type="number"
            class="h-6 w-full rounded border border-neutral-800 bg-neutral-900 px-1.5 text-xs text-neutral-100"
            bind:value={xDraft}
            onchange={commitPosition}
          />
        </label>
        <label class="flex items-center gap-1">
          <span class="w-4 text-[11px] text-neutral-400">Y</span>
          <input
            type="number"
            class="h-6 w-full rounded border border-neutral-800 bg-neutral-900 px-1.5 text-xs text-neutral-100"
            bind:value={yDraft}
            onchange={commitPosition}
          />
        </label>
        <label class="flex items-center gap-1">
          <span class="w-4 text-[11px] text-neutral-400">W</span>
          <input
            type="number"
            class="h-6 w-full rounded border border-neutral-800 bg-neutral-900 px-1.5 text-xs text-neutral-100"
            bind:value={widthDraft}
            onchange={commitWidth}
          />
        </label>
        <label class="flex items-center gap-1">
          <span class="w-4 text-[11px] text-neutral-400">H</span>
          <input
            type="number"
            class="h-6 w-full rounded border border-neutral-800 bg-neutral-900 px-1.5 text-xs text-neutral-100"
            bind:value={heightDraft}
            onchange={commitHeight}
          />
        </label>
        <label class="col-span-2 flex items-center gap-2">
          <span class="w-14 text-[11px] text-neutral-400">Step</span>
          <input
            type="text"
            class="h-6 flex-1 rounded border border-neutral-800 bg-neutral-900 px-1.5 text-xs text-neutral-100"
            bind:value={stepDraft}
            onblur={commitStep}
            onkeydown={(e) => onTextKey(e, commitStep)}
          />
        </label>
      </div>

      <div class="mt-3 mb-1 px-3 text-[10px] uppercase tracking-wide text-neutral-500">Semantics</div>
      <div class="space-y-1 px-3">
        <div class="flex items-center gap-2">
          <label class="w-14 text-[11px] text-neutral-400">Type</label>
          <div class="flex-1">
            <Dropdown value={currentType} options={typeOptions} onchange={commitSelectAttr('type')} />
          </div>
        </div>
        <div class="flex items-center gap-2">
          <label class="w-14 text-[11px] text-neutral-400">Owner</label>
          <input
            type="text"
            class="h-6 flex-1 rounded border border-neutral-800 bg-neutral-900 px-1.5 text-xs text-neutral-100"
            bind:value={ownerDraft}
            onblur={commitOwner}
            onkeydown={(e) => onTextKey(e, commitOwner)}
          />
        </div>
        <div class="flex items-center gap-2">
          <label class="w-14 text-[11px] text-neutral-400">Status</label>
          <div class="flex-1">
            <Dropdown value={currentStatus} options={statusOptions} onchange={commitSelectAttr('status')} />
          </div>
        </div>
        <div class="flex items-center gap-2">
          <label class="w-14 text-[11px] text-neutral-400">Priority</label>
          <div class="flex-1">
            <Dropdown value={currentPriority} options={priorityOptions} onchange={commitSelectAttr('priority')} />
          </div>
        </div>
        <div class="flex items-center gap-2">
          <label class="w-14 text-[11px] text-neutral-400">Tags</label>
          <input
            type="text"
            placeholder="a, b, c"
            class="h-6 flex-1 rounded border border-neutral-800 bg-neutral-900 px-1.5 text-xs text-neutral-100"
            bind:value={tagsDraft}
            onblur={commitTags}
            onkeydown={(e) => onTextKey(e, commitTags)}
          />
        </div>
      </div>

      <div class="mt-3 mb-1 px-3 text-[10px] uppercase tracking-wide text-neutral-500">Style</div>
      <div class="space-y-1 px-3">
        <div class="flex items-center gap-2">
          <label class="w-14 text-[11px] text-neutral-400">Fill</label>
          <input
            type="color"
            class="h-6 w-8 cursor-pointer rounded border border-neutral-800 bg-neutral-900"
            value={currentFill}
            onchange={(e) => commitStyle('fill', (e.target as HTMLInputElement).value)}
          />
          <button
            type="button"
            class="rounded border border-neutral-800 px-1.5 py-0.5 text-[10px] text-neutral-400 hover:text-neutral-100"
            onclick={() => clearStyle('fill')}
          >
            Clear
          </button>
        </div>
        <div class="flex items-center gap-2">
          <label class="w-14 text-[11px] text-neutral-400">Stroke</label>
          <input
            type="color"
            class="h-6 w-8 cursor-pointer rounded border border-neutral-800 bg-neutral-900"
            value={currentStroke}
            onchange={(e) => commitStyle('stroke', (e.target as HTMLInputElement).value)}
          />
          <button
            type="button"
            class="rounded border border-neutral-800 px-1.5 py-0.5 text-[10px] text-neutral-400 hover:text-neutral-100"
            onclick={() => clearStyle('stroke')}
          >
            Clear
          </button>
        </div>
        <div class="flex items-center gap-2">
          <label class="w-14 text-[11px] text-neutral-400">Text</label>
          <input
            type="color"
            class="h-6 w-8 cursor-pointer rounded border border-neutral-800 bg-neutral-900"
            value={currentText}
            onchange={(e) => commitStyle('text', (e.target as HTMLInputElement).value)}
          />
          <button
            type="button"
            class="rounded border border-neutral-800 px-1.5 py-0.5 text-[10px] text-neutral-400 hover:text-neutral-100"
            onclick={() => clearStyle('text')}
          >
            Clear
          </button>
        </div>
      </div>

      <div class="mt-3 mb-1 px-3 text-[10px] uppercase tracking-wide text-neutral-500">
        Typography &amp; shape
      </div>
      <div class="grid grid-cols-2 gap-1 px-3">
        <label class="flex items-center gap-1">
          <span class="w-14 text-[11px] text-neutral-400">Font</span>
          <input
            type="number"
            placeholder="13"
            min="6"
            class="h-6 w-full rounded border border-neutral-800 bg-neutral-900 px-1.5 text-xs text-neutral-100"
            bind:value={fontSizeDraft}
            onblur={() => commitStyleNum('font_size', fontSizeDraft)}
            onkeydown={(e) => onTextKey(e, () => commitStyleNum('font_size', fontSizeDraft))}
          />
        </label>
        <label class="flex items-center gap-1">
          <span class="w-14 text-[11px] text-neutral-400">Radius</span>
          <input
            type="number"
            placeholder="auto"
            min="0"
            class="h-6 w-full rounded border border-neutral-800 bg-neutral-900 px-1.5 text-xs text-neutral-100"
            bind:value={rxDraft}
            onblur={() => commitStyleNum('rx', rxDraft)}
            onkeydown={(e) => onTextKey(e, () => commitStyleNum('rx', rxDraft))}
          />
        </label>
        <label class="flex items-center gap-1">
          <span class="w-14 text-[11px] text-neutral-400">Stroke</span>
          <input
            type="number"
            placeholder="auto"
            min="0"
            step="0.25"
            class="h-6 w-full rounded border border-neutral-800 bg-neutral-900 px-1.5 text-xs text-neutral-100"
            bind:value={strokeWidthDraft}
            onblur={() => commitStyleNum('stroke_width', strokeWidthDraft)}
            onkeydown={(e) =>
              onTextKey(e, () => commitStyleNum('stroke_width', strokeWidthDraft))}
          />
        </label>
        <label class="flex items-center gap-1">
          <span class="w-14 text-[11px] text-neutral-400">Opacity</span>
          <input
            type="number"
            placeholder="1"
            min="0"
            max="1"
            step="0.05"
            class="h-6 w-full rounded border border-neutral-800 bg-neutral-900 px-1.5 text-xs text-neutral-100"
            bind:value={opacityDraft}
            onblur={() => commitStyleNum('opacity', opacityDraft)}
            onkeydown={(e) => onTextKey(e, () => commitStyleNum('opacity', opacityDraft))}
          />
        </label>
        <label class="col-span-2 flex items-center gap-2">
          <span class="w-14 text-[11px] text-neutral-400">Font family</span>
          <input
            type="text"
            placeholder="inherit"
            class="h-6 flex-1 rounded border border-neutral-800 bg-neutral-900 px-1.5 text-xs text-neutral-100"
            bind:value={fontFamilyDraft}
            onblur={commitFontFamily}
            onkeydown={(e) => onTextKey(e, commitFontFamily)}
          />
        </label>
      </div>

      <button
        type="button"
        class="mt-4 mx-3 mb-4 flex w-[calc(100%-1.5rem)] items-center justify-center gap-1.5 rounded border border-red-900 bg-red-950 px-2 py-1.5 text-xs text-red-300 hover:bg-red-900"
        onclick={handleDelete}
      >
        <Icon name="trash" size={13} />
        {confirmDelete ? 'Click again to confirm' : 'Delete node'}
      </button>
    {/if}
  </aside>
{/if}
