## 2024-05-24 - [Avoid FileReader for synchronous image preview generation]
**Learning:** `FileReader.readAsDataURL()` reads the entire image into memory and converts it into a base64 string. Doing this on large photos blocks the main thread, causing significant UI jank.
**Action:** Use `URL.createObjectURL(file)` instead. It’s an O(1) operation that avoids base64 encoding and doesn't block the UI thread. Remember to clean up old URLs with `URL.revokeObjectURL()` to prevent memory leaks.

## 2024-05-24 - [Avoid synchronous fs methods in request handlers]
**Learning:** Using synchronous filesystem methods like `fs.existsSync` or `fs.unlinkSync` blocks the Node.js event loop thread entirely. In a web server, doing this during a request lifecycle degrades throughput and causes latency spikes across all concurrent requests.
**Action:** Always use the asynchronous variants (like `fs.unlink(path, callback)`) to ensure the main thread remains free to handle other requests while waiting for I/O operations to complete.
