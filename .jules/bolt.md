## 2024-05-24 - [Avoid FileReader for synchronous image preview generation]
**Learning:** `FileReader.readAsDataURL()` reads the entire image into memory and converts it into a base64 string. Doing this on large photos blocks the main thread, causing significant UI jank.
**Action:** Use `URL.createObjectURL(file)` instead. It’s an O(1) operation that avoids base64 encoding and doesn't block the UI thread. Remember to clean up old URLs with `URL.revokeObjectURL()` to prevent memory leaks.

## 2024-06-20 - [Avoid synchronous file deletion in Node.js request handlers]
**Learning:** Using `fs.unlinkSync()` blocks the Node.js event loop while the file is being deleted. Under high concurrent request load, this synchronous operation significantly degrades server throughput and increases response times for all users.
**Action:** Always use the asynchronous `fs.unlink()` method (or `fs.promises.unlink()`) inside request handlers to allow the event loop to continue processing other requests during the disk I/O operation.
