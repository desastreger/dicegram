// A form-field "draft" that mirrors an external (render) value — e.g. a
// value that can also change out from under the field via a canvas drag,
// a raw code edit, or another panel — EXCEPT while the field itself has
// focus, so live typing is never clobbered mid-keystroke. Replaces the
// old "seed once when the selected id changes" pattern, which left a
// draft stale after any edit that didn't come through that one field —
// a later blur then silently wrote the stale value back over the user's
// real change.
export function draftField<T>(getValue: () => T) {
	let focused = $state(false);
	let value = $state(getValue());

	$effect(() => {
		// `focused` is always read first so it's tracked on every run even
		// when we bail out early — that's what makes the effect re-fire
		// (and re-seed) the moment focus is lost.
		if (focused) return;
		value = getValue();
	});

	return {
		get value() {
			return value;
		},
		set value(v: T) {
			value = v;
		},
		onfocus() {
			focused = true;
		},
		onblur() {
			focused = false;
		}
	};
}
