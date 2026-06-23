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

## 2025-02-27 - Insecure File Upload Handling
**Vulnerability:** The application was vulnerable to insecure file uploads because the `multer` configuration did not validate the MIME type of the uploaded file. An attacker could bypass frontend restrictions and upload non-image files (such as executable scripts, HTML files, or malware), which could be processed by the backend or accessed maliciously.
**Learning:** Checking the `fileSize` is not enough to secure file uploads. If a server expects only images but fails to enforce this at the backend level, it opens the door to arbitrary file uploads which can lead to Remote Code Execution (RCE), Stored XSS, or other forms of exploitation.
**Prevention:** Always implement a `fileFilter` in `multer` to rigorously validate the MIME type (e.g., verifying `mimetype.startsWith('image/')`) or the file extension of incoming uploads. Additionally, ensure the application fails securely and returns a 400 error without exposing stack traces when invalid files are blocked.
