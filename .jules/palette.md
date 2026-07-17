## 2024-06-18 - Replacing Native Alerts & Grouping Form Inputs

**Learning:** When multiple file inputs (e.g., 'Upload File' and 'Take Photo') share a conceptual purpose, using a single `<label>` is semantically invalid. Screen readers require a `<fieldset>` with a `<legend>` to properly associate the inputs. Additionally, using `alert()` for form validation blocks the main thread and provides poor UX.

**Action:** Use `<fieldset>` and `<legend>` to group related inputs semantically instead of an isolated label. Replace native `alert()` dialogs with inline, accessible error messages containing `role="alert"` for non-blocking and screen reader-friendly validation feedback.

## 2026-07-01 - Accessible Input Hints
**Learning:** When providing input hints to convey expected formats, relying solely on the `placeholder` attribute is a poor UX practice because it disappears upon typing and often fails contrast guidelines, leaving users without context once they start filling the field.
**Action:** Use a dedicated, visible description element (e.g., `<p>`) for hints and explicitly link it to the input field using `aria-describedby` to ensure context remains visible and screen readers announce it properly.

## 2024-07-11 - Accessible Offline Banners
**Learning:** Dynamically appearing status banners like offline connection notifications need proper ARIA roles to be announced by screen readers when their state changes.
**Action:** Ensure dynamically appearing status banners include `role="alert"` and `aria-live="assertive"` attributes, and dynamically toggle `aria-hidden` via JavaScript ('false' when visible, 'true' when hidden) so that their presence and state changes are immediately announced to users relying on assistive technologies.

## 2024-07-15 - Focus Management and Icon-Only Button Tooltips
**Learning:** When displaying an inline form error that interrupts a user flow, simply unhiding the error element (even if it has `role="alert"`) may not be enough for keyboard users who then have to tab through the document to find what went wrong. Additionally, icon-only buttons with `aria-label` are accessible to screen readers, but sighted mouse users still need to understand what the button does.
**Action:** When a form validation fails and an error message is shown, explicitly move keyboard focus to the error message element (using `element.focus()` and ensuring the element has `tabindex="-1"`). For icon-only buttons, always include a `title` attribute matching the `aria-label` to provide a native hover tooltip for sighted users.

## 2024-07-16 - Global Drag and Drop Prevention
**Learning:** When implementing custom drag-and-drop zones, users often miss the target area. By default, browsers will open the dropped file, navigating away from the application and causing users to lose all their unsaved state.
**Action:** Always add global `dragover` and `drop` event listeners to the `window` to prevent default behavior, ensuring that dropping a file outside the designated zone safely does nothing instead of hijacking the session.

## 2024-07-20 - Focus Management and Scroll for Async Results
**Learning:** When displaying dynamic async results at the bottom of a page, users (especially on mobile) might not see the new content, and keyboard/screen reader users lose their context if focus is not explicitly managed.
**Action:** Automatically scroll the newly revealed result container into view and programmatically shift focus to it (using `tabindex="-1"`) to provide a seamless and accessible experience.
