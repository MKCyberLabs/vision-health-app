## 2026-06-19 - Replace Browser Alerts with ARIA Inline Errors
**Learning:** Native browser `alert()` popups are a jarring and often inaccessible UX pattern that interrupt the user journey.
**Action:** Use inline form error elements with `role="alert"` and `aria-live="assertive"` to provide immediate, contextually relevant feedback without blocking the user interface.
