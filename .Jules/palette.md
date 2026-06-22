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
