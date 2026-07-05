## 2024-06-18 - Replacing Native Alerts & Grouping Form Inputs

**Learning:** When multiple file inputs (e.g., 'Upload File' and 'Take Photo') share a conceptual purpose, using a single `<label>` is semantically invalid. Screen readers require a `<fieldset>` with a `<legend>` to properly associate the inputs. Additionally, using `alert()` for form validation blocks the main thread and provides poor UX.

**Action:** Use `<fieldset>` and `<legend>` to group related inputs semantically instead of an isolated label. Replace native `alert()` dialogs with inline, accessible error messages containing `role="alert"` for non-blocking and screen reader-friendly validation feedback.

## 2026-07-01 - Accessible Input Hints
**Learning:** When providing input hints to convey expected formats, relying solely on the `placeholder` attribute is a poor UX practice because it disappears upon typing and often fails contrast guidelines, leaving users without context once they start filling the field.
**Action:** Use a dedicated, visible description element (e.g., `<p>`) for hints and explicitly link it to the input field using `aria-describedby` to ensure context remains visible and screen readers announce it properly.

## 2024-07-25 - Dynamically Appearing Status Banner Accessibility
**Learning:** Ensure dynamically appearing status banners (like offline connection notifications) include `role="alert"` and `aria-live="assertive"` attributes, and dynamically toggle `aria-hidden` via JavaScript ('false' when visible, 'true' when hidden) so that their presence and state changes are immediately announced to users relying on assistive technologies.
**Action:** Always add ARIA live regions and dynamically manage `aria-hidden` attributes for notification or alert banners that appear without a page reload or direct user interaction.
