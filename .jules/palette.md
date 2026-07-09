## 2024-06-18 - Replacing Native Alerts & Grouping Form Inputs

**Learning:** When multiple file inputs (e.g., 'Upload File' and 'Take Photo') share a conceptual purpose, using a single `<label>` is semantically invalid. Screen readers require a `<fieldset>` with a `<legend>` to properly associate the inputs. Additionally, using `alert()` for form validation blocks the main thread and provides poor UX.

**Action:** Use `<fieldset>` and `<legend>` to group related inputs semantically instead of an isolated label. Replace native `alert()` dialogs with inline, accessible error messages containing `role="alert"` for non-blocking and screen reader-friendly validation feedback.

## 2026-07-01 - Accessible Input Hints
**Learning:** When providing input hints to convey expected formats, relying solely on the `placeholder` attribute is a poor UX practice because it disappears upon typing and often fails contrast guidelines, leaving users without context once they start filling the field.
**Action:** Use a dedicated, visible description element (e.g., `<p>`) for hints and explicitly link it to the input field using `aria-describedby` to ensure context remains visible and screen readers announce it properly.
## 2024-07-09 - Ensure dynamically appearing status banners correctly use aria-hidden
**Learning:** Dynamically appearing status banners (like offline connection notifications) that are hidden by default and animate in when active, need dynamic `aria-hidden` management to prevent screen readers from reading them incorrectly.
**Action:** Include `role="alert"`, `aria-live="assertive"`, and `aria-hidden="true"` on the HTML element. Dynamically toggle `aria-hidden` via JavaScript ('false' when visible, 'true' when hidden) so their presence and state changes are immediately announced to assistive technologies.
