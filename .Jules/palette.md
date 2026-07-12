## 2024-05-24 - Accessible Custom File Inputs
**Learning:** Using `display: none` or the Tailwind `hidden` class on `<input type="file">` elements removes them from the accessibility tree, making keyboard navigation and screen reader usage impossible for custom-styled upload buttons.
**Action:** Use the `sr-only peer` pattern. Keep the `<input>` element before the `<label>` in the DOM. Apply `sr-only peer` to the `<input>`, and then apply `peer-focus-visible:ring-x` to the `<label>`. This hides the native input visually while maintaining keyboard focus, and applies visible focus styles to the custom label component.

## 2024-06-21 - Replace native alert with accessible inline alert
**Learning:** Native `alert()` dialogs used for form validation disrupt the user experience and can break the flow for screen reader users by removing focus context. They are also not visually consistent with the app's design system.
**Action:** Replace native `alert()` calls with inline text elements styled appropriately (e.g., using Tailwind classes for error states) and possessing the `role="alert"` attribute. Show and hide these elements by toggling CSS classes like `hidden` to ensure a smooth, accessible experience.
## 2026-06-20 - Inline Accessible Form Validation
**Learning:** Using `alert()` for form validation interrupts the user experience, changes focus unexpectedly, and often isn't read cleanly by screen readers in the context of the form.
**Action:** Use inline text elements with `role="alert"` (ARIA live regions) and clear visual styling (e.g., text-red-600) near the relevant input to provide immediate, contextual, and accessible feedback without breaking flow.
## 2026-06-19 - Replace Browser Alerts with ARIA Inline Errors
**Learning:** Native browser `alert()` popups are a jarring and often inaccessible UX pattern that interrupt the user journey.
**Action:** Use inline form error elements with `role="alert"` and `aria-live="assertive"` to provide immediate, contextually relevant feedback without blocking the user interface.

## 2024-06-25 - Grouping File Inputs for Screen Readers
**Learning:** Using an orphan `<label>` tag without a `for` attribute to describe a group of file inputs (like camera vs gallery buttons) fails to provide programmatic context for screen readers.
**Action:** Use a `<span id="groupId">` for the descriptive text, and wrap the related inputs in a container with `role="group"` and `aria-labelledby="groupId"`. This ensures screen reader users understand the purpose of the grouped inputs.

## 2024-06-25 - Accessible Placeholder Contrast in Lotus Theme
**Learning:** The light `pink-300` color used for placeholders in the app's Lotus theme fails WCAG color contrast requirements against white backgrounds, making it hard for visually impaired users to read hints.
**Action:** Use darker shades like `gray-500` for input placeholders to maintain a clean aesthetic while ensuring accessibility.

## 2024-08-01 - Visual Feedback for Drag and Drop on Custom File Inputs
**Learning:** Adding drag and drop to custom file upload labels improves UX, but without visual feedback (like changing border color or background on `dragenter` and `dragover`), users don't know the drop zone is active or where exactly they can drop the file.
**Action:** Always add visual cues (e.g., changing border styles, background colors, or applying a slight scale transform) on `dragenter` and `dragover` events for drop zones, and remove them on `dragleave` and `drop` to clearly indicate when an element is ready to receive a file.

## 2026-06-25 - Allow File Selection Clearing and Restore Focus
**Learning:** Users often select the wrong file by mistake. Without a way to clear the selection, they are forced to refresh the page or upload a dummy file to replace it, which is poor UX. Furthermore, when an action like clearing a file removes the current context (the preview), screen reader and keyboard users can lose their place in the document if focus isn't managed.
**Action:** Always provide a clear, accessible way to cancel or clear a file selection. When the selection is cleared and the preview is hidden, explicitly move keyboard focus back to a logical starting point (like the file upload input) to maintain a seamless keyboard navigation experience.

## 2026-06-27 - Preserve Accessibility and Interactive States During Merge Conflicts
**Learning:** When resolving merge conflicts between an accessibility/error-handling PR and a UI-redesign PR, blindly accepting one branch can result in the loss of critical UX features (like loading state indication) or accessibility fixes (like `aria-live` regions or focus rings).
**Action:** Carefully combine the changes. Ensure that interactive features (such as caching `innerHTML` for loading states) and accessibility improvements (such as `focus-visible` utility classes and ARIA attributes) are both maintained in the merged element.

<<<<<<< HEAD
<<<<<<< HEAD
## 2024-05-27 - Inline Input Hints
**Learning:** Using placeholder text (`placeholder="..."`) for crucial input hints (like expected format) is poor UX. Placeholders disappear as soon as the user starts typing, making them forget the expected format. Furthermore, light placeholder colors often fail contrast guidelines.
**Action:** Extract placeholder text into a dedicated description element (`<p>`) placed near the input. Link the description to the input using `aria-describedby` to ensure screen readers announce the hint when the input is focused. This keeps the hint visible while typing and improves accessibility.
=======
## 2026-06-29 - Accessible Placeholder hints
**Learning:** Using placeholder text for input hints means the hint disappears upon typing and often fails color contrast guidelines. Users might forget what format is expected.
**Action:** Use a dedicated, always-visible description element (e.g., `<p>`) for hints and link it to the input via `aria-describedby` to provide persistent context for sighted users and robust semantic meaning for screen readers.
>>>>>>> palette-ux-weight-hint-15959018386035856729
=======
## 2026-06-30 - Visible Input Hints
**Learning:** Using placeholders for input hints (like expected format or examples) is problematic for accessibility and UX. The text often disappears once the user starts typing, forcing them to clear the input to read it again. It also frequently fails color contrast requirements.
**Action:** Use a dedicated, visible description element (like a `<p>`) placed before the input, and link it to the input using the `aria-describedby` attribute. This ensures the hint remains visible and is properly announced by screen readers.
>>>>>>> palette/visible-input-hint-869195354420355491
