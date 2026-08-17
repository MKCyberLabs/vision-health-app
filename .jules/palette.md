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

## 2024-07-21 - Accessible Dynamic Asynchronous Statuses
**Learning:** When displaying dynamic asynchronous results or error messages in the same container, failing to dynamically update both visual styling (like warning/error color classes) and ARIA attributes (`role="alert"`, `aria-live="assertive"` for errors vs. `role="status"`, `aria-live="polite"` for success) can lead to a confusing experience for both sighted users and screen reader users.
**Action:** When dynamically rendering status elements based on varying asynchronous results or states (like success, warning, or error), explicitly programmatically switch both their visual styling and corresponding ARIA attributes (`role`, `aria-live`) to accurately communicate the state to all users.

## 2024-08-04 - Discoverable Hidden Interactions
**Learning:** Features like drag-and-drop or pasting from the clipboard are powerful but hidden interaction patterns. If they are not visually indicated, most users will never discover them, reducing the app's overall usability and delight.
**Action:** Always add visible, accessible helper text (e.g., `<p>` tag) explaining hidden features and link it to the relevant interaction zone using `aria-describedby` so the features are discoverable to both sighted and screen-reader users.

## 2024-08-01 - Revealing Hidden Interactions & Frontend File Validation
**Learning:** Some interaction patterns (like drag-and-drop or pasting from the clipboard) are incredibly useful but entirely invisible to users unless explicitly stated. Additionally, relying solely on backend file type validation or HTML input `accept` attributes is insufficient when dealing with custom drag/paste events, leading to broken UI states if non-image files are dropped.
**Action:** Always add an accessible helper text to make hidden interaction patterns (like dropping or pasting) visible and discoverable. Implement strict frontend file type validation (e.g., checking `file.type.startsWith('image/')`) on custom drop/paste events before updating the UI state, providing immediate inline error feedback when invalid files are used.

## 2024-07-24 - Focus Management and Auto-scrolling for Asynchronous Results
**Learning:** When dynamically displaying asynchronous results (like a result container or confirmation dialog), it's not enough to simply reveal the content. Mobile users may not see it if it appears below the fold, and keyboard/screen reader users may lose context if focus isn't managed.
**Action:** Automatically scroll the new content into view (e.g., using `scrollIntoView({ behavior: 'smooth' })`) and explicitly move focus to it (using `.focus()` with `tabindex="-1"`) to ensure visibility for mobile users and maintain context for keyboard/screen reader users.

## 2026-07-26 - Auto-scroll and Focus for Async Results
**Learning:** When dynamically displaying asynchronous results (e.g., appending a result container), users on mobile devices or using screen readers often miss the new content because it appears outside their viewport or without focus. Simply unhiding the container is not enough to maintain context.
**Action:** Always automatically scroll the new content into view (e.g., using `scrollIntoView({ behavior: 'smooth' })`) and explicitly move focus to it (using `.focus()` with `tabindex="-1"`) to ensure visibility for mobile users and maintain context for keyboard/screen reader users.

## 2024-07-27 - Dynamic Content Visibility and Focus Management
**Learning:** When dynamically displaying asynchronous results (like appending a result container), simply unhiding the element doesn't guarantee users will see it, especially on mobile devices where the new content might appear below the current viewport fold. Furthermore, screen readers might not correctly associate the new state.
**Action:** Automatically scroll the new content into view (using `scrollIntoView({ behavior: 'smooth' })`) and explicitly move focus to it (using `.focus()` with `tabindex="-1"`) or its primary interactive element to ensure visibility for mobile users and maintain context for keyboard and screen reader users.

## 2024-07-20 - Focus and Scroll Management for Asynchronous Results
**Learning:** When dynamically displaying asynchronous results (e.g., appending a result container), simply making the element visible is insufficient. Mobile users might not see the new content if it appears off-screen, and keyboard/screen reader users lose context if focus remains on the triggering element or is lost entirely.
**Action:** Automatically scroll the new content into view (e.g., using `scrollIntoView({ behavior: 'smooth' })`) and explicitly move focus to it (using `.focus()` with `tabindex="-1"`) to ensure visibility for mobile users and maintain context for keyboard/screen reader users.

## 2024-08-03 - Documenting Hidden Interactions and File Validations
**Learning:** Hidden interaction patterns (like drag-and-drop or pasting from the clipboard) can easily go unnoticed by users, and relying solely on HTML `accept` attributes for file inputs is insufficient to prevent UI state breakage when users submit invalid file types manually.
**Action:** When implementing hidden interactions like drag-and-drop or clipboard paste, always add visible, accessible helper text (e.g., using `aria-describedby`) to make the features discoverable. Additionally, enforce strict frontend file validation (e.g., `file.type.startsWith('image/')`) inside the file handling logic, showing a focus-managed error message if validation fails.
