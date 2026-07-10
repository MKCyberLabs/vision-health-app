## 2024-06-18 - Replacing Native Alerts & Grouping Form Inputs

**Learning:** When multiple file inputs (e.g., 'Upload File' and 'Take Photo') share a conceptual purpose, using a single `<label>` is semantically invalid. Screen readers require a `<fieldset>` with a `<legend>` to properly associate the inputs. Additionally, using `alert()` for form validation blocks the main thread and provides poor UX.

**Action:** Use `<fieldset>` and `<legend>` to group related inputs semantically instead of an isolated label. Replace native `alert()` dialogs with inline, accessible error messages containing `role="alert"` for non-blocking and screen reader-friendly validation feedback.

## 2026-07-01 - Accessible Input Hints
**Learning:** When providing input hints to convey expected formats, relying solely on the `placeholder` attribute is a poor UX practice because it disappears upon typing and often fails contrast guidelines, leaving users without context once they start filling the field.
**Action:** Use a dedicated, visible description element (e.g., `<p>`) for hints and explicitly link it to the input field using `aria-describedby` to ensure context remains visible and screen readers announce it properly.

## 2024-07-10 - Accessible Dynamically Appearing Status Banners
**Learning:** For dynamically appearing status banners (like offline connection notifications), relying only on visual CSS transforms is insufficient for screen readers. The banners need `role="alert"` and `aria-live="assertive"` so their presence is announced. Additionally, the `aria-hidden` attribute must be dynamically toggled via JavaScript ('false' when visible, 'true' when hidden) to accurately reflect their visibility state to assistive technologies.
**Action:** Always include `role="alert"` and `aria-live="assertive"` on critical status banners. In the JavaScript that manages the banner's visibility, explicitly update the `aria-hidden` attribute to ensure state changes are immediately announced to users relying on assistive technologies.
