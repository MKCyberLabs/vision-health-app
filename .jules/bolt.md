## 2024-05-24 - [Avoid FileReader for synchronous image preview generation]
**Learning:** `FileReader.readAsDataURL()` reads the entire image into memory and converts it into a base64 string. Doing this on large photos blocks the main thread, causing significant UI jank.
**Action:** Use `URL.createObjectURL(file)` instead. It’s an O(1) operation that avoids base64 encoding and doesn't block the UI thread. Remember to clean up old URLs with `URL.revokeObjectURL()` to prevent memory leaks.

## 2026-06-19 - [Avoid synchronous filesystem calls to unblock the Node.js event loop]
**Learning:** Using synchronous methods like `fs.unlinkSync` inside Express route handlers blocks the Node.js main thread. This prevents the server from handling other concurrent requests while the disk operation completes, severely bottlenecking throughput under load.
**Action:** Always use asynchronous filesystem methods like `fs.unlink` (with a callback) or `fs.promises.unlink` when running within request handlers to keep the event loop free to serve other clients.
