## 2024-06-17 - Argument Injection in pexpect.spawn
**Vulnerability:** Found an argument injection vulnerability where user-controlled input (`prompt_for_cli`) was being directly interpolated into a command string passed to `pexpect.spawn`. By injecting quotes, an attacker could add arbitrary arguments to the command being executed.
**Learning:** `pexpect.spawn` behaves like `subprocess.Popen(..., shell=False)` when given a list, but when given a string, it uses `shlex.split` under the hood. If user input containing quotes is placed inside a string command, `shlex.split` can interpret those quotes, allowing attackers to escape the intended argument and inject additional arguments.
**Prevention:** Always pass arguments to `pexpect.spawn` as a list rather than a single interpolated string, especially when handling user-controlled data.

## 2024-06-18 - Reflected DOM XSS via InnerHTML Interpolation
**Vulnerability:** Found a Reflected DOM XSS vulnerability in `public/index.html` where untrusted data from the backend (`data.message`) was being directly interpolated into an HTML string and assigned to `resultDiv.innerHTML`. This allowed arbitrary JavaScript execution if the backend returned malicious content (e.g. via prompt injection or unexpected responses).
**Learning:** Rendering dynamic data proxied from a backend CLI directly into the DOM using `innerHTML` is highly dangerous. Even if the data originates from a "trusted" internal service, it can contain untrusted user input or unexpected formatting that breaks out of HTML contexts.
**Prevention:** Always use `textContent` or proper DOM manipulation methods (like creating elements programmatically and setting their properties) to insert dynamic data into the DOM safely. Never interpolate untrusted data directly into an `innerHTML` string.
## 2024-06-12 - Prevent Reflected DOM XSS in UI Prompts
**Vulnerability:** User input or external system text (like backend prompts) was inserted into HTML views using string interpolation with `innerHTML`.
**Learning:** Bypassing standard DOM methods and injecting directly via `innerHTML` can execute arbitrary scripts embedded within the backend data, causing a Reflected DOM XSS.
**Prevention:** Always use safe DOM APIs like `textContent` when injecting dynamic data originating from external inputs or proxies, ensuring it is rendered strictly as text, not executable HTML.

## 2024-07-25 - Prevent DoS via Unlimited File Uploads
**Vulnerability:** The application was vulnerable to a Denial of Service (DoS) attack via disk exhaustion because the `multer` configuration lacked a `limits: { fileSize: ... }` property. Attackers could upload arbitrarily large files, filling the server's disk space and crashing the service.
**Learning:** Default Express and `multer` configurations do not enforce limits on incoming file sizes. Furthermore, when unhandled errors occur (such as a generic crash), Express can sometimes leak HTML stack traces or internal framework information (via the `x-powered-by` header), increasing the attack surface.
**Prevention:** Always explicitly define size limits for file uploads using middleware like `multer`. Additionally, disable framework fingerprints (`app.disable('x-powered-by')`), enforce basic security headers, and use a secure global error handler that returns sanitized JSON instead of stack traces.

## 2026-06-24 - Arbitrary File Upload Vulnerability
**Vulnerability:** The application used `multer` for file uploads without a `fileFilter` configuration, meaning it accepted any file type. This allowed attackers to upload potentially malicious files, like executable scripts, presenting an arbitrary file upload vulnerability.
**Learning:** Default `multer` configurations only check properties like `limits: { fileSize: ... }` if provided, but they do not automatically reject files with incorrect MIME types. Failing to check file extensions or MIME types expands the application's attack surface.
**Prevention:** Always implement a `fileFilter` in `multer` configurations to strictly validate the MIME type (e.g., checking `mimetype.startsWith('image/')`) alongside `fileSize` limits to prevent arbitrary file upload vulnerabilities. Use a secure global error handler to handle file filter errors and return a sanitized JSON message instead of a stack trace.
## 2024-07-26 - Temporary File Leak DoS
**Vulnerability:** File uploads were processed but temporary files were never removed from the 'temp' directory in the backend upon failure, leading to potential disk exhaustion.
**Learning:** Backend processes must clean up temporary files they handle, especially when they error out, as frontends often rely on the backend to manage the lifecycle of files it acts upon.
**Prevention:** Always ensure temporary files are securely deleted in error paths of the backend handlers. Do not delete them in success paths if the frontend relies on them being served.

## 2026-06-26 - Prevent Information Disclosure via Flask Error Responses
**Vulnerability:** The Flask backend was returning default HTML error pages containing stack traces or internal framework details for unhandled exceptions (e.g., when a request body was a JSON array rather than an object, causing an `AttributeError` during `data.get()`, or for malformed requests like `400 Bad Request`).
**Learning:** Default Flask error handling can expose sensitive application internals when unhandled errors occur. Also, assuming `request.json` is always a dictionary is unsafe as clients can send empty payloads, arrays, or invalid formats.
**Prevention:** Always implement global error handling (e.g., `@app.errorhandler(Exception)`) to securely catch unhandled exceptions, log them internally, and return generic, sanitized JSON messages to the client. Additionally, actively validate incoming JSON payloads (e.g., `isinstance(request.json, dict)`) before interacting with them.

## 2024-06-27 - Interactive CLI Injection in pexpect.spawn sendline
**Vulnerability:** The application was vulnerable to Interactive CLI Injection. The user-controlled `answer` parameter was passed directly to `child.sendline(answer)` in `pexpect` without validation. Attackers could send unescaped input, arbitrary commands, or multiple newline characters that the interactive CLI tool would interpret and execute under its active session context.
**Learning:** Even when `pexpect.spawn` is instantiated safely (e.g., using a list of arguments to avoid initial argument injection), dynamic interaction via `.sendline()` still poses a risk if the CLI prompt accepts multi-line input or command-like sequences. Untrusted user data should never be sent raw to a spawned terminal interface.
**Prevention:** Always apply strict allowlist validation to dynamic input before passing it to `child.sendline()` to ensure only expected inputs (e.g., `'y'`, `'n'`, `'yes'`, `'no'`) are sent to the spawned process.
