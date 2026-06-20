## 2024-05-24 - Accessible Custom File Inputs
**Learning:** Using `display: none` or the Tailwind `hidden` class on `<input type="file">` elements removes them from the accessibility tree, making keyboard navigation and screen reader usage impossible for custom-styled upload buttons.
**Action:** Use the `sr-only peer` pattern. Keep the `<input>` element before the `<label>` in the DOM. Apply `sr-only peer` to the `<input>`, and then apply `peer-focus-visible:ring-x` to the `<label>`. This hides the native input visually while maintaining keyboard focus, and applies visible focus styles to the custom label component.

## 2026-06-20 - Inline Accessible Form Validation
**Learning:** Using `alert()` for form validation interrupts the user experience, changes focus unexpectedly, and often isn't read cleanly by screen readers in the context of the form.
**Action:** Use inline text elements with `role="alert"` (ARIA live regions) and clear visual styling (e.g., text-red-600) near the relevant input to provide immediate, contextual, and accessible feedback without breaking flow.
