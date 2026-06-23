## 2024-05-24 - [Avoid FileReader for synchronous image preview generation]
**Learning:** `FileReader.readAsDataURL()` reads the entire image into memory and converts it into a base64 string. Doing this on large photos blocks the main thread, causing significant UI jank.
**Action:** Use `URL.createObjectURL(file)` instead. It’s an O(1) operation that avoids base64 encoding and doesn't block the UI thread. Remember to clean up old URLs with `URL.revokeObjectURL()` to prevent memory leaks.

## 2026-06-21 - [Replace synchronous file operations with asynchronous]
**Learning:** Using synchronous filesystem methods like `fs.existsSync` and `fs.unlinkSync` in Node.js request handlers blocks the event loop, degrading server throughput, especially under concurrent load.
**Action:** Always use asynchronous filesystem methods (e.g., `fs.unlink`) in request handlers to avoid blocking the main thread and ensure non-blocking I/O. Use distinct variable names for error handling to avoid variable shadowing in nested scopes (e.g., `unlinkErr`).
