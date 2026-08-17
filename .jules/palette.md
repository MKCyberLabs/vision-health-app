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

## 2024-08-13 - Discoverable Hidden Interactions
**Learning:** Hidden interaction patterns like drag-and-drop or clipboard pasting are convenient but completely invisible to many users, including those using screen readers.
**Action:** When implementing hidden interaction patterns (like drag-and-drop or pasting from the clipboard), always add visible, accessible helper text (e.g., using `aria-describedby` or `aria-labelledby`) so the features are discoverable to all users.

## 2024-07-25 - Discoverable Hidden Interactions & File Validation
**Learning:** When implementing hidden interaction patterns (like drag-and-drop or pasting from the clipboard), always add visible, accessible helper text (e.g., using aria-describedby or aria-labelledby) so the features are discoverable to all users. Additionally, handling custom drag-and-drop or paste events requires strict frontend file type validation to prevent UI breakage from unsupported file types.
**Action:** Always pair drag-and-drop/paste functionalities with visible hint text linked via ARIA attributes. Enforce file type validation (e.g., `file.type.startsWith('image/')`) in custom event handlers to maintain a robust experience.

## 2024-07-22 - Hidden Interaction Patterns & Global Paste
**Learning:** When implementing hidden interaction patterns (like drag-and-drop or pasting from the clipboard), they are not easily discoverable. Also, global paste handlers can break standard text entry if not careful.
**Action:** Always add visible, accessible helper text (e.g., using `aria-describedby` or `aria-labelledby`) so the features are discoverable. When adding a global `paste` event listener for file uploads, explicitly check the event target (e.g., `e.target.tagName !== 'INPUT'`) to avoid breaking standard text entry workflows. Implement strict frontend file type validation when handling drag-and-drop or paste events.

## 2024-07-22 - Global Paste Support & Hidden Interactions
**Learning:** When implementing hidden interaction patterns (like drag-and-drop or pasting from the clipboard), users may not discover the features if there is no visual indicator. Additionally, when handling custom drag-and-drop or paste events, passing unchecked files directly to the upload handler can break the UI if the file type is not supported.
**Action:** Always add visible, accessible helper text (e.g., using `aria-describedby`) for hidden interactions so they are discoverable. When handling global paste events, ensure the handler ignores paste events inside text inputs (`e.target.tagName !== 'INPUT'`) and implement strict frontend file type validation (e.g., `file.type.startsWith('image/')`) to prevent unsupported files from breaking the application.

## 2026-08-02 - Discoverability of Hidden Interactions
**Learning:** When implementing hidden interaction patterns (like drag-and-drop or pasting from the clipboard), users may not realize the features exist. Additionally, frontend file handling needs strict validation to avoid UI breakage when unsupported file types are pasted or dropped.
**Action:** Always add visible, accessible helper text (e.g., using `aria-describedby`) so the features are discoverable to all users. Additionally, always implement strict frontend file type validation (e.g., `file.type.startsWith('image/')`) to prevent UI breakage from unsupported file types.

## 2024-07-26 - Dynamic Result Focus and Scrolling
**Learning:** When dynamically displaying asynchronous results (like a generated summary or a new component appended to the DOM), users on mobile devices or using screen magnification may not realize content has appeared off-screen. Additionally, keyboard and screen reader users lose their place in the document context.
**Action:** Automatically scroll the new content into view (e.g., using `scrollIntoView({ behavior: 'smooth' })`) and explicitly move focus to the new container (using `.focus()` and ensuring it has `tabindex="-1"`) to guarantee visibility and maintain logical navigation flow.

## 2026-06-31 - Focus and Scroll Management for Dynamic Content
**Learning:** When dynamically displaying asynchronous results (like appending a result container), users might not realize new content has appeared, especially on mobile devices or for users using screen readers or keyboard navigation.
**Action:** Always automatically scroll the new content into view (e.g., using `scrollIntoView({ behavior: 'smooth' })`) and explicitly move focus to it (using `.focus()` with `tabindex="-1"` if it's not natively focusable) to ensure visibility for all users and maintain context.

## 2026-07-02 - Semantic Styling for Async Error Results
**Learning:** Displaying backend error messages inside an element styled for success (e.g., with green borders and backgrounds) confuses users and fails to semantically communicate the error state. Screen readers may also incorrectly announce an error as a polite status update if the ARIA role is not dynamically adjusted.
**Action:** When dynamically displaying async results, ensure the visual styling (colors) and ARIA attributes (`role`, `aria-live`) of the result container dynamically change to match the state (success, warning, error). Use `role="alert"` and red styling for errors, and `role="status"` with green styling for success.

## 2024-07-26 - Dynamic Result Scrolling and Focus
**Learning:** When dynamically displaying asynchronous results (e.g., appending a result container), simply making the container visible is often insufficient, especially on smaller screens where the new content might appear below the fold. Furthermore, keyboard and screen reader users need their focus explicitly moved to the new content to maintain context.
**Action:** Automatically scroll the new content into view (using `scrollIntoView({ behavior: 'smooth' })`) and explicitly move focus to it (using `.focus()` with `tabindex="-1"`) to ensure visibility for mobile users and maintain context for accessibility users.

## 2024-07-21 - Dynamic Styling and ARIA for Async Results
**Learning:** When dynamically displaying asynchronous results or backend errors in UI containers, simply changing the text content is insufficient. If the visual styling and ARIA attributes (like `role` and `aria-live`) do not reflect the state (e.g., green for success, red for error), it can confuse both sighted users and those using screen readers.
**Action:** Ensure that visual styling (e.g., color classes) and ARIA attributes (`role`, `aria-live`) are dynamically updated to accurately reflect the state (e.g., `role="alert"` and red styling for errors, `role="status"` and green styling for success) when updating dynamic containers.

## 2026-07-23 - Scrolling and Focusing Asynchronous Results
**Learning:** When displaying asynchronous results (like appending a result container), users, especially those on mobile devices or using screen readers, might miss the newly added content if it appears off-screen or without focus.
**Action:** When dynamically displaying asynchronous results, automatically scroll the new content into view (e.g., using `scrollIntoView({ behavior: 'smooth' })`) and explicitly move focus to it (using `.focus()` with `tabindex="-1"`) to ensure visibility for mobile users and maintain context for keyboard/screen reader users.

## 2024-07-25 - Discoverable Paste Support
**Learning:** Hidden interaction patterns (drag-and-drop, pasting) require visible helper text to be discoverable. Global paste handlers must explicitly ignore text inputs, and custom upload handlers must validate file types since they bypass HTML accept attributes.
**Action:** Add visible helper text (e.g. aria-describedby) to make hidden features discoverable. Scope global paste events to ignore text inputs, and apply strict frontend file type validation.

## 2024-08-10 - Focus Management for Dynamic Asynchronous Results
**Learning:** When dynamically displaying asynchronous results (e.g., appending a result container), users might not realize the new content has appeared, especially on mobile devices where it might render off-screen, or for screen reader users who remain focused on the submit button.
**Action:** Automatically scroll the new content into view (e.g., using `scrollIntoView({ behavior: 'smooth' })`) and explicitly move focus to it (using `.focus()` with `tabindex="-1"`) to ensure visibility for all users and maintain context for keyboard/screen reader users.

## 2024-07-25 - Discoverability of Hidden Interactions and Frontend Validation
**Learning:** Hidden interactions, such as drag-and-drop or pasting files directly from the clipboard, remain entirely invisible to most users (including screen reader users) unless explicitly communicated. Furthermore, intercepting clipboard paste events globally on the `window` object risks breaking standard text entry workflows in `input` and `textarea` fields, while lack of strict client-side validation on dropped/pasted items leads to unpredictable errors in processing.
**Action:** Always provide explicit, visually accessible helper text (linked via `aria-describedby` or `aria-labelledby`) to expose hidden features like drag-and-drop or copy-paste. Ensure global event listeners correctly ignore native text fields (`e.target.tagName !== 'INPUT'`), and enforce strict file type validation (e.g., `file.type.startsWith('image/')`) at the frontend layer to gracefully display validation feedback.

## 2024-07-22 - Discoverability of Hidden Interactions and Paste UX
**Learning:** Hidden interaction patterns like drag-and-drop or pasting from the clipboard are powerful UX tools, but they are completely invisible to users unless explicitly stated. Additionally, global paste listeners can inadvertently break text entry workflows if they intercept paste events inside inputs or textareas.
**Action:** When implementing hidden interaction patterns, always add visible, accessible helper text (e.g., using `aria-describedby`) to make the features discoverable. Furthermore, when adding global paste event listeners, explicitly check the event target (e.target.tagName !== 'INPUT' and e.target.tagName !== 'TEXTAREA') to ignore events meant for standard text entry.
