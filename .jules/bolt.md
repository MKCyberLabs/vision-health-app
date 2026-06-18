## 2024-05-24 - [Avoid FileReader for synchronous image preview generation]
**Learning:** `FileReader.readAsDataURL()` reads the entire image into memory and converts it into a base64 string. Doing this on large photos blocks the main thread, causing significant UI jank.
**Action:** Use `URL.createObjectURL(file)` instead. It’s an O(1) operation that avoids base64 encoding and doesn't block the UI thread. Remember to clean up old URLs with `URL.revokeObjectURL()` to prevent memory leaks.
