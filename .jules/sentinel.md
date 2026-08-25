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

## 2024-10-24 - Interactive CLI Injection via pexpect
**Vulnerability:** The Node.js and Flask backend passed unvalidated interactive input (`answer`) directly to a live pexpect CLI session (`child.sendline(answer)`). A malicious payload like `y\nrm -rf /` could send multiple commands if the underlying CLI passed it to a shell or improperly handled newlines.
**Learning:** Even when external tools are spawned safely (e.g. avoiding `shell=True`), interactive communication channels (like stdin via pexpect) remain a dangerous attack surface if inputs aren't strictly validated and bounded.
**Prevention:** Always apply strict allowlist validation to interactive CLI inputs. In this case, `answer` is explicitly restricted to exactly `'y'` or `'n'`.

## 2024-10-25 - Resource Exhaustion / Denial of Service via Orphaned Processes
**Vulnerability:** The backend spawned long-running CLI processes via `pexpect.spawn`. However, if the process timed out or encountered an exception, it was removed from internal trackers but the underlying process wasn't explicitly terminated, causing it to remain running in the background until it consumed all system resources (PIDs/memory), leading to a Denial of Service (DoS) vulnerability.
**Learning:** External or child processes managed by wrappers like `pexpect` do not automatically terminate when they fall out of Python scope or timeout. They can become orphaned and leak system resources heavily.
**Prevention:** Always explicitly terminate managed child processes in exception handlers, finally blocks, or timeout paths using explicit calls like `child.close(force=True)` after verifying they are still alive using `child.isalive()`.

## 2024-07-02 - Add Content-Security-Policy Header
**Vulnerability:** The application was missing a Content-Security-Policy (CSP) header, leaving it vulnerable to various code injection attacks, primarily Cross-Site Scripting (XSS).
**Learning:** Default Express configurations do not include security headers. While some basic headers (`X-Content-Type-Options`, etc.) were present, the critical CSP header was missing, which is a key defense-in-depth mechanism.
**Prevention:** Always implement a robust Content-Security-Policy header in the global application middleware to restrict the origins of executable scripts, stylesheets, and other resources.

## 2024-06-28 - Prevent DoS via Orphaned Child Processes
**Vulnerability:** In `gemini-api/app.py`, the backend spawned child processes using `pexpect.spawn`, but failed to explicitly close them in various execution paths (such as upon timeouts or unhandled exceptions in the `handle_cli_interaction` and `reply_gemini` methods). This left orphaned child processes running, consuming server resources, leading to potential Denial of Service (DoS) via resource exhaustion.
**Learning:** When using libraries like `pexpect.spawn` to manage child processes, the operating system's resources (like file descriptors and memory) can become depleted if processes are not explicitly terminated when an error occurs or when the parent process stops interacting with them. Trailing `pass` statements in `except` blocks do not manage this cleanup.
**Prevention:** Always ensure explicit termination of child processes (e.g., using `child.close(force=True)`) in all execution branches, particularly inside exception handlers and timeouts, to prevent resource exhaustion and Denial of Service (DoS) vulnerabilities.

## 2024-06-27 - Interactive CLI Injection in pexpect.spawn sendline
**Vulnerability:** The application was vulnerable to Interactive CLI Injection. The user-controlled `answer` parameter was passed directly to `child.sendline(answer)` in `pexpect` without validation. Attackers could send unescaped input, arbitrary commands, or multiple newline characters that the interactive CLI tool would interpret and execute under its active session context.
**Learning:** Even when `pexpect.spawn` is instantiated safely (e.g., using a list of arguments to avoid initial argument injection), dynamic interaction via `.sendline()` still poses a risk if the CLI prompt accepts multi-line input or command-like sequences. Untrusted user data should never be sent raw to a spawned terminal interface.
**Prevention:** Always apply strict allowlist validation to dynamic input before passing it to `child.sendline()` to ensure only expected inputs (e.g., `'y'`, `'n'`, `'yes'`, `'no'`) are sent to the spawned process.

## 2026-07-08 - DoS via Orphaned Processes in pexpect
**Vulnerability:** When a spawned `pexpect` process timed out or encountered an exception, it was not explicitly terminated in the error handlers. This allowed processes to persist as zombies or continue running in the background, consuming memory and file descriptors, leading to resource exhaustion DoS.
**Learning:** In Python, child processes managed by tools like `pexpect` are not automatically terminated when the managing object is discarded or an exception interrupts the flow, unless explicitly handled.
**Prevention:** Always explicitly terminate spawned processes using methods like `child.close(force=True)` inside exception and timeout handlers to guarantee resources are freed.

## 2024-06-27 - Interactive CLI Injection in pexpect
**Vulnerability:** User-provided answers in the `/reply` endpoint were being directly passed to a waiting CLI process via `child.sendline(answer)` without validation. If an attacker sent unexpected inputs (like newlines followed by other commands or escape characters), it could potentially manipulate the CLI's interactive state or execute unintended operations.
**Learning:** Sending untrusted input interactively to a spawned process (e.g., via `sendline`) is a form of injection. Even if shell injection during process creation (`spawn`) is prevented, the interactive input itself must be strictly validated.
**Prevention:** Always apply strict allowlisting to interactive inputs sent to spawned processes. Ensure the input only matches the exact expected choices (e.g., 'y', 'n') before sending it.

## 2024-10-24 - DoS via Orphaned pexpect Processes
**Vulnerability:** The Flask backend did not explicitly terminate the `pexpect` child processes in error handlers (e.g., timeouts, exceptions). If a timeout or error occurred, the process would remain alive in the background indefinitely, potentially leading to resource exhaustion (Denial of Service).
**Learning:** `pexpect` child processes continue running in the background even if the main thread encounters an exception or timeout. They must be explicitly terminated to release system resources.
**Prevention:** When using `pexpect.spawn` to manage child processes, always ensure explicit termination (e.g., using `child.close(force=True)`) in exception handlers and timeouts. Verify the process is still running by checking `child.isalive()` before calling `child.close(force=True)` to prevent errors.

## 2026-07-14 - Remove Unused Vulnerable Dependencies
**Vulnerability:** The application included an outdated version of the `uuid` package which contained a buffer bounds check vulnerability. Although it was imported in `index.js` (`const { v4: uuidv4 } = require('uuid');`), it was never actually used anywhere in the Node.js frontend.
**Learning:** Having unused dependencies in a project unnecessarily increases the attack surface and can trigger security alerts for vulnerabilities in code that isn't even executing.
**Prevention:** Regularly audit projects for unused dependencies (e.g., using `pnpm audit` or unused code checkers) and remove any unused modules entirely to minimize potential security risks and bundle sizes.

## 2024-10-26 - DoS via Missing Rate Limiting and Proxy Misconfiguration
**Vulnerability:** Backend API endpoints lacked rate limiting, allowing attackers to perform Denial of Service (DoS) by sending unlimited requests. Furthermore, because the app runs behind a reverse proxy (Traefik), default rate limiters based on `req.ip` would limit all traffic globally as they would only see the proxy's IP.
**Learning:** Publicly accessible API endpoints must be protected by rate limiters to prevent DoS. When an application is deployed behind a reverse proxy or load balancer, configuring `app.set('trust proxy', 1)` is crucial so the application trusts the `X-Forwarded-For` headers and accurately tracks the real client IP.
**Prevention:** Always implement rate limiting on sensitive API endpoints. Before deploying behind a proxy, explicitly configure the framework to trust proxy headers to maintain accurate client IP visibility for security and auditing purposes.

## 2024-10-26 - Add Rate Limiting & Trust Proxy for DoS Protection
**Vulnerability:** The application was missing rate limiting on sensitive endpoints (`/analyze` and `/reply`). The `/analyze` endpoint processes file uploads up to 5MB before sending them to the backend, opening a significant Denial of Service (DoS) vector by exhausting server disk space and memory via repeated malicious requests.
**Learning:** Adding rate limits is crucial for endpoints that handle file uploads. However, if the rate limiter itself uses an unbounded data structure (like a `Map`), it can introduce a memory leak over time. Furthermore, if the application sits behind a load balancer or reverse proxy like Traefik, `req.ip` will return the proxy's IP instead of the client's IP, effectively blacklisting all users when one is rate limited.
**Prevention:** Apply rate limiting middleware before the `multer` file upload middleware to reject abusive requests *before* the file is processed and stored. Always pair in-memory rate limiters with a cleanup mechanism (e.g. `setInterval`) to prevent memory leaks. Finally, when behind a reverse proxy, explicitly configure the Express app with `app.set('trust proxy', 1)` to accurately resolve and rate limit the real client IP.

## 2024-10-25 - Missing Rate Limiting & Proxy Configuration
**Vulnerability:** The Express gateway was missing rate limiting, making it vulnerable to brute force and denial of service (DoS) attacks. Additionally, it did not have `trust proxy` configured, which is necessary when deployed behind a reverse proxy/load balancer to correctly parse the client's IP address.
**Learning:** In-memory rate limiting implementation requires a periodic cleanup to prevent memory leaks from unbounded data structures. `req.ip` is inaccurate without `app.set('trust proxy', 1)` when the application is behind a proxy.
**Prevention:** Implement rate limiting (e.g., in-memory map with periodic cleanup) and configure `trust proxy` on all Express gateways to ensure accurate IP-based restrictions and prevent DoS.

## 2024-10-27 - Rate Limit Bypass via Path Variation
**Vulnerability:** The application's custom rate limiting middleware matched exactly against `req.path === '/analyze'`. However, Express's default routing is case-insensitive and ignores trailing slashes. Thus, requests to `/analyze/` or `/ANALYZE` bypassed the rate limiter entirely while still being processed by the route handler.
**Learning:** When implementing custom route-matching logic in Express middleware (e.g., for rate limiting), strict equality checks on `req.path` are insufficient because they don't mirror the underlying framework's forgiving route resolution, leading to trivial bypasses.
**Prevention:** Always normalize the request path (e.g., `req.path.toLowerCase().replace(/\/$/, '')`) before comparison in custom middleware to ensure consistency with how the framework will ultimately route the request.

## 2026-07-27 - Rate Limiter Bypass and DoS Risk
**Vulnerability:** The application was missing rate limiting on sensitive endpoints (`/analyze` and `/reply`) and lacked `app.set('trust proxy', 1)`, which is crucial when deployed behind reverse proxies like Traefik to correctly identify client IPs for rate limiting.
**Learning:** When deploying Express applications behind load balancers or proxies, `req.ip` resolves to the proxy's IP rather than the client's. Rate limiting must use `X-Forwarded-For` to function properly and mitigate DoS attacks effectively.
**Prevention:** Always implement rate limiting on endpoints handling file uploads or intensive processing, and explicitly configure `trust proxy` when the architecture includes reverse proxies.

## 2024-10-25 - Lack of Rate Limiting & Trust Proxy on Node.js Gateway
**Vulnerability:** The Express.js application was deployed behind a reverse proxy (Traefik) without `trust proxy` configured, and critical endpoints (`/analyze`, `/reply`) lacked rate limiting. This allowed abusive clients to bypass potential load balancer limits and spam the endpoints, potentially causing a Denial of Service (DoS) condition on the API.
**Learning:** When deploying behind a reverse proxy, `req.ip` is not accurate unless `app.set('trust proxy', 1)` is configured. Moreover, custom in-memory rate limiters using `Map` require periodic cleanup mechanisms (`setInterval`) to avoid unbounded memory growth (another form of DoS).
**Prevention:** Always configure `trust proxy` when deploying behind a proxy/load balancer. Implement robust rate limiting on exposed API endpoints, and ensure any custom in-memory state includes automatic expired entry cleanup.

## 2024-10-27 - Rate Limit Bypass via Path Normalization
**Vulnerability:** The Express rate limiting middleware used strict equality checks (`req.path === '/analyze'`) to identify protected endpoints. This allowed attackers to easily bypass rate limiting by requesting paths like `/analyze/` or `/ANALYZE`, which Express default routing handles interchangeably but the rate limiter did not match.
**Learning:** Default Express route handlers are case-insensitive and ignore trailing slashes, but raw request properties like `req.path` retain the original request's exact casing and slashes. Custom middleware implementing route-matching logic will fail if it uses strict equality on raw `req.path`.
**Prevention:** When implementing custom route-matching logic in Express middleware (e.g., for rate limiting), always normalize the request path (e.g., `req.path.toLowerCase().replace(/\/+$/, '')`) before comparison to ensure it aligns with the framework's routing behavior and cannot be bypassed via varied casing or trailing slashes.

## 2024-10-27 - Rate Limiter Bypass via Express Route Normalization
**Vulnerability:** The Express rate-limiting middleware in `index.js` performed strict string equality checks on `req.path` (`req.path === '/analyze'`). Since default Express route handlers (like `app.post('/analyze')`) are case-insensitive and ignore trailing slashes by default, attackers could bypass the rate limit simply by requesting `/Analyze` or `/analyze/`, leading to a Denial of Service.
**Learning:** Checking `req.path` strictly without normalizing it can leave security middlewares (like rate limiters or authorization checks) susceptible to trivial bypasses if the underlying framework treats those variations as equivalent for route matching.
**Prevention:** When implementing custom route-matching logic in Express middleware, always normalize the request path (e.g., `req.path.toLowerCase().replace(/\/$/, '')`) before comparison.

## 2026-08-07 - Rate Limit Bypass via Path Normalization
**Vulnerability:** The rate limiting middleware strictly matched request paths (`req.path === '/analyze'`). An attacker could bypass this by appending a trailing slash (`/analyze/`) or using different casing (`/ANALYZE`), allowing them to send unlimited requests and potentially cause a Denial of Service (DoS) condition.
**Learning:** Default Express routing behavior is case-insensitive and ignores trailing slashes, but strict equality checks (`===`) in custom middleware do not.
**Prevention:** When implementing custom route-matching logic in middleware (e.g., for rate limiting or authentication), always normalize the request path (e.g., `req.path.toLowerCase().replace(/\/$/, '')`) before comparing to prevent trivial bypasses.

## 2026-07-29 - Rate Limiting Bypass via Path Normalization
**Vulnerability:** The Node.js application contained a rate limit middleware that explicitly checked if `req.path === '/analyze' || req.path === '/reply'`. However, Express router matching by default handles routes in a case-insensitive manner and ignores trailing slashes. Therefore, an attacker could bypass the strict rate limit checks by sending requests to `/ANALYZE` or `/analyze/`, which would skip the rate limit middleware but still successfully hit the actual backend route handler.
**Learning:** Hardcoded, strictly case-sensitive and literal path matching strings (like `=== '/path'`) in Express middleware fail to account for how web frameworks parse and route requests under the hood, leaving security layers vulnerable to trivial path modification bypasses.
**Prevention:** Always normalize the request path before applying security checks like rate limits. Use `.toLowerCase()` and remove trailing slashes (e.g. `.replace(/\/$/, '')`) on `req.path`, or ideally, apply the rate limiting middleware directly on the specific route definition (e.g., `app.post('/analyze', rateLimiter, ...)`).

## 2024-10-26 - Express Rate Limit Bypass via Path Normalization
**Vulnerability:** The rate limiting middleware used strict equality (`req.path === '/analyze'`) to apply limits. Since Express routing is case-insensitive and ignores trailing slashes, an attacker could request `/Analyze` or `/analyze/` to bypass the rate limit while still hitting the expensive route handler, leading to a potential Denial of Service (DoS).
**Learning:** Default Express route handlers (`app.post('/path')`) are lenient with casing and slashes, but `req.path` retains the exact incoming path string. Using strict equality on `req.path` in middleware creates a discrepancy that attackers can exploit to bypass checks.
**Prevention:** When implementing custom route-matching logic in Express middleware (e.g., for rate limiting or authentication), always normalize the request path (e.g., `req.path.toLowerCase().replace(/\/$/, '')`) before comparison to ensure it matches the leniency of the underlying route handlers.

## 2024-10-26 - DoS via Rate Limiting Bypass in Path Normalization
**Vulnerability:** The rate limiter middleware matched endpoints using strict equality (`req.path === '/analyze'`). Attackers could bypass the rate limiter (leading to DoS) by appending a trailing slash or altering the case (e.g., `/Analyze`, `/analyze/`), because default Express route handlers ignore trailing slashes and casing.
**Learning:** Custom middleware performing route-specific logic must replicate or respect the framework's default routing behavior (case-insensitivity, trailing slash ignorance) to prevent trivial bypasses.
**Prevention:** Always normalize the request path (e.g., `req.path.toLowerCase().replace(/\/$/, '')`) before comparison in custom routing or security middleware.

## 2024-10-27 - Rate Limit Bypass via Path Variation
**Vulnerability:** The application's custom rate limiting middleware matched endpoints using strict string equality (e.g., `req.path === '/analyze'`). Since default Express route handlers are case-insensitive and ignore trailing slashes (treating `/analyze/` the same as `/analyze`), attackers could append trailing slashes or alter casing to completely bypass the rate limit while still hitting the target route.
**Learning:** When implementing custom route-matching logic in Express middleware (e.g., for rate limiting), strict path equality checks (`===`) are dangerous because Express routing normalizes paths before matching. Attackers can trivially exploit this discrepancy.
**Prevention:** Always normalize the request path (e.g., `req.path.toLowerCase().replace(/\/$/, '')`) before comparing it in custom middleware, or preferably use robust routing mechanics (like `app.post('/analyze', rateLimiter, handler)`) instead of custom global path checks.

## 2024-10-27 - Rate Limit Bypass via Path Normalization
**Vulnerability:** The Express.js rate-limiting middleware in `index.js` used strict equality to check request paths (e.g., `req.path === '/analyze'`). Because Express route handlers are case-insensitive and ignore trailing slashes by default, an attacker could request `/analyze/` or `/Analyze` to completely bypass the rate limit while still hitting the target endpoint, leading to a potential DoS.
**Learning:** When implementing custom route-matching logic in Express middleware (like rate limiters), relying on `req.path === '/path'` is insufficient because it doesn't match how Express natively resolves routes. Attackers can trivially bypass these checks using varied casing or trailing slashes.
**Prevention:** Always normalize the request path (e.g., `req.path.toLowerCase().replace(/\/$/, '')`) before comparison in custom middleware to ensure consistency with Express's default routing behavior, or use standard routing parameters (e.g., `app.use('/analyze', rateLimiter)`).

## 2024-10-27 - Rate Limiter Bypass via Express Route Mismatch
**Vulnerability:** A custom rate limiter in `index.js` was relying on strict equality against `req.path` (e.g., `req.path === '/analyze'`). Because Express route handlers inherently ignore trailing slashes and are case-insensitive, attackers could simply request `/Analyze` or `/analyze/` to bypass the rate limiter completely while still hitting the vulnerable endpoint. This opened up the application to Denial of Service (DoS).
**Learning:** Default Express route handlers normalize incoming paths, but `req.path` inside custom middleware does not reflect this normalization. Relying on strict string matching for security controls (like rate limits or authentication) in Express middleware is flawed.
**Prevention:** Always normalize the request path (e.g., `req.path.toLowerCase().replace(/\/+$/, '')`) before comparing it in custom routing logic or middleware, or apply middleware specifically to the route definition (`app.post('/analyze', rateLimiter, upload...)`) instead of a global `app.use` check.

## 2024-10-27 - Rate Limiter Bypass via Path Variations
**Vulnerability:** The rate limiter middleware used strict equality (`req.path === '/analyze'`) which could be easily bypassed by attackers appending a trailing slash or altering the case (e.g. `/analyze/` or `/Analyze`), while Express still matched and executed the underlying route.
**Learning:** Express default route handlers are case-insensitive and ignore trailing slashes. Custom middleware implementing route-matching logic must account for this behavior to avoid security checks being bypassed.
**Prevention:** When implementing custom route-matching logic in Express middleware (e.g., for rate limiting), always normalize the request path (e.g., `req.path.toLowerCase().replace(/\//$/, '')`) before comparison.

## 2024-10-26 - DoS via Missing Rate Limiting and Disk Exhaustion
**Vulnerability:** The Node.js gateway did not have any rate limiting, allowing attackers to spam requests and consume resources. Moreover, the file upload middleware (`multer`) was placed without protection, which meant attackers could upload large files repeatedly, leading to disk exhaustion before any validation or limits were hit. The lack of `trust proxy` configuration also meant the gateway would throttle the reverse proxy's IP instead of the actual client's IP.
**Learning:** Rate limiting is critical for preventing resource exhaustion DoS attacks, especially on endpoints handling file uploads. The rate limiting middleware must be placed *before* the file upload middleware. When implementing custom in-memory limiters, always include a cleanup mechanism to prevent memory leaks from unbounded data structures. Also, ensure `trust proxy` is set to correctly resolve client IPs when behind a reverse proxy.
**Prevention:** Implement rate limiting middleware (like the `apiRateLimiter`) and apply it before `upload.single(...)`. Include a `setInterval` or similar mechanism to clean up expired IP entries. Set `app.set('trust proxy', 1)` when the application is behind a reverse proxy or load balancer.

## 2024-10-27 - Rate Limiting Bypass via Path Normalization
**Vulnerability:** The rate limiting middleware in `index.js` checked the request path using strict equality (`req.path === '/analyze'`). Since default Express route handlers are case-insensitive and ignore trailing slashes, an attacker could trivially bypass the rate limit by using varied casing (e.g., `/Analyze`) or appending a trailing slash (e.g., `/analyze/`), sending unlimited requests to resource-intensive endpoints.
**Learning:** When implementing custom route-matching logic in Express middleware (such as for rate limiting or authentication), strict string equality checks on `req.path` are insufficient because the underlying framework's route matching is more permissive.
**Prevention:** Always normalize the request path (e.g., `req.path.toLowerCase().replace(/\/$/, '')`) before comparison in custom middleware, or use established libraries (like `express-rate-limit`) which handle path normalization automatically.

## 2024-10-25 - Prevent DoS and Brute Force via Rate Limiting and Proxy Config
**Vulnerability:** The Node.js frontend was exposed behind a Traefik load balancer but failed to set `app.set('trust proxy', 1)`, causing all requests to appear as originating from the proxy's IP. Additionally, sensitive endpoints like `/analyze` and `/reply` had no rate limiting, leaving them vulnerable to Denial of Service (DoS) and brute-force attacks.
**Learning:** When an Express application is behind a proxy, it must explicitly trust the proxy to correctly resolve `req.ip` from the `X-Forwarded-For` header. Without this, IP-based rate limiting is useless and can lock out all users if the single proxy IP gets blocked.
**Prevention:** Always configure `app.set('trust proxy', 1)` when deploying behind reverse proxies. Apply custom or library-based rate limiting to all public endpoints, especially those accepting files or making external API calls. Ensure custom memory-based rate limiters include periodic cleanup logic to avoid memory leaks.

## 2026-07-15 - Rate Limiting to prevent DoS
**Vulnerability:** The application was missing rate limiting on critical endpoints like `/analyze` and `/reply`. Specifically on `/analyze`, an attacker could repeatedly send large file uploads (up to 5MB each) to exhaust disk space (temp folder) or system memory (if processed simultaneously) leading to a Denial of Service.
**Learning:** File upload endpoints are particularly sensitive to DoS attacks since they consume disk I/O, storage, and processing power. Furthermore, when deployed behind a reverse proxy (like Traefik), `req.ip` will always resolve to the proxy's IP unless `trust proxy` is explicitly configured.
**Prevention:** Always implement rate limiting on public-facing APIs. Crucially, on endpoints handling file uploads (like `multer`), the rate limiter middleware must be placed *before* the file upload middleware to block excessive requests *before* the files are buffered or written to disk. Additionally, always explicitly set `app.set('trust proxy', 1)` when behind a reverse proxy to accurately track client IPs.

## 2026-07-20 - Missing Rate Limiting and Inaccurate IP Resolution
**Vulnerability:** The application was missing rate limiting on sensitive API endpoints (`/analyze`, `/reply`), allowing brute force or Denial of Service attacks. Furthermore, because it runs behind a proxy/load balancer (Traefik), `req.ip` incorrectly resolved to the internal proxy IP instead of the actual client IP, which would render IP-based rate limiting ineffective.
**Learning:** Default Express applications do not automatically implement rate limiting or correctly interpret the `X-Forwarded-For` header. Thus, malicious actors could exhaust system resources without restriction. In-memory data structures like `Map` used for manual rate limiting can cause memory leaks if expired entries are not periodically cleaned up.
**Prevention:** Always set `app.set('trust proxy', 1);` when deploying Express applications behind a proxy to ensure accurate client IP resolution. Implement rate limiters on sensitive endpoints, and if using custom in-memory solutions like a `Map`, always include a background cleanup mechanism (e.g., `setInterval`) to prune stale data and avoid memory leaks.

## 2024-10-26 - Add Rate Limiting to Sensitive Endpoints
**Vulnerability:** The Node.js frontend was missing rate limiting on its sensitive endpoints (`/analyze` and `/reply`), leaving it vulnerable to Denial of Service (DoS) and potential abuse by malicious clients making excessive requests.
**Learning:** Default Express configurations do not include built-in rate limiting. Furthermore, when deploying behind a reverse proxy (like Traefik in this architecture), `app.set('trust proxy', 1)` must be configured so `req.ip` correctly resolves the client's actual IP from the `X-Forwarded-For` header instead of the proxy's IP. Additionally, custom in-memory rate limiters (like `Map`) must include periodic cleanup mechanisms to prevent memory leaks from unbound growth.
**Prevention:** Always implement rate limiting on sensitive, resource-intensive, or stateful endpoints. Configure proxy trust properly in containerized architectures, and ensure in-memory tracking structures are actively cleaned up over time.

## 2024-10-25 - Prevent DoS via Missing Rate Limiting on File Uploads
**Vulnerability:** The Node.js gateway accepted file uploads on the `/analyze` endpoint without any rate limiting. An attacker could rapidly send large file upload requests (up to the 5MB limit each), quickly exhausting disk space in the `temp/` directory, memory (via concurrent file processing), or downstream API limits (Flask backend/Antigravity CLI), leading to a Denial of Service (DoS) for legitimate users.
**Learning:** Endpoints handling file uploads are particularly vulnerable to DoS attacks because they consume disproportionately more server resources (disk I/O, memory, temporary storage) per request compared to standard JSON endpoints.
**Prevention:** Always implement rate limiting on sensitive or resource-intensive endpoints. When using middleware like `multer` for file uploads, ensure the rate limiting middleware is applied *before* the file upload middleware in the route definition to reject abusive requests before any disk or memory resources are consumed by parsing the file payload.

## 2026-07-26 - Implement Proxy Trust and Route Rate Limiting
**Vulnerability:** The Node.js API Gateway was vulnerable to Denial of Service (DoS) attacks via disk space and memory exhaustion. The gateway accepted file uploads without rate limiting, and failed to correctly identify the client IP behind the Traefik proxy.
**Learning:** When an Express application operates behind a reverse proxy (like Traefik), `req.ip` will not resolve to the client's actual IP address unless `app.set('trust proxy', 1)` is explicitly configured. Furthermore, applying rate limiting to endpoints managing file uploads (e.g., via `multer`) is critical, and the rate limiter middleware must be placed before the file upload middleware to prevent malicious actors from exhausting server resources. Lastly, implementing custom in-memory rate limiters (e.g., using a `Map`) requires a periodic cleanup mechanism (like `setInterval`) to remove expired entries and prevent unbounded data structure growth.
**Prevention:** Explicitly set `app.set('trust proxy', 1)` when deploying behind reverse proxies or load balancers. Prioritize implementing rate limiting on resource-intensive endpoints, particularly those involving file uploads or external API calls, ensuring the rate limiter middleware precedes resource-heavy processing. For custom in-memory caching solutions, always include an automatic garbage collection mechanism.

## 2024-10-27 - Rate Limit Bypass via Path Normalization
**Vulnerability:** The Express rate limiter was implemented by strictly comparing `req.path === '/analyze'`. However, default Express route handlers are case-insensitive and ignore trailing slashes. This allowed attackers to trivially bypass the rate limiting by adding trailing slashes (e.g., `/analyze/`) or varying casing (e.g., `/AnAlyZe`), completely avoiding the rate limit while still hitting the expensive endpoints.
**Learning:** Custom middleware matching logic must mimic the underlying framework's route matching logic. When comparing paths for security controls, you cannot rely on strict equality if the application's actual routes are forgiving.
**Prevention:** Always normalize the request path (e.g., `req.path.toLowerCase().replace(/\/+$/, '')`) before applying custom route-matching logic in Express middleware, or use established middleware libraries (like `express-rate-limit`) which handle path matching inherently safely.

## 2024-10-27 - Rate Limit Bypass via Path Normalization
**Vulnerability:** The Express middleware for rate limiting used strict equality `req.path === '/analyze'` without normalizing the request path first. Because Express routing is case-insensitive and ignores trailing slashes, attackers could trivially bypass the rate limits by requesting `/Analyze` or `/analyze/`.
**Learning:** Default Express route handlers are forgiving with casing and trailing slashes, but strict string comparisons in custom middleware are not. This discrepancy allows attackers to bypass security controls like rate limiters if custom logic doesn't explicitly normalize paths the way the router does.
**Prevention:** When implementing custom route-matching logic in Express middleware (e.g., for rate limiting), always normalize the request path (e.g., `req.path.toLowerCase().replace(/\/$/, '')`) before comparison to ensure it aligns with the framework's routing behavior.

## 2024-10-27 - Rate Limiter Bypass via Path Normalization
**Vulnerability:** The rate limiter middleware checked paths using strict equality (`req.path === '/analyze'`). Since Express route handlers are case-insensitive and ignore trailing slashes by default, attackers could bypass the rate limiter by requesting `/Analyze`, `/analyze/`, or `/aNalyze`, while still hitting the target endpoint. This allowed Denial of Service attacks to evade the rate limit protection.
**Learning:** Custom route-matching logic in Express middleware must account for the framework's default routing behaviors (case-insensitivity, trailing slash tolerance). Relying on strict equality for `req.path` is fragile and easily bypassed.
**Prevention:** When implementing custom middleware that applies to specific paths (like rate limiting), always normalize the request path (e.g., `req.path.toLowerCase().replace(/\/$/, '')`) before comparison.

## 2024-10-26 - Rate Limiting Bypass via Path Manipulation
**Vulnerability:** The Express.js backend applied a custom rate limit based on strict string equality (`req.path === '/analyze'`). However, Express routing is case-insensitive and ignores trailing slashes by default. An attacker could bypass the rate limit by sending requests to `/aNaLyZe` or `/analyze/`, leading to a Denial of Service.
**Learning:** Default Express route handlers match flexibly (case-insensitive, optional trailing slash), but `req.path` reflects the exact parsed path string. Relying on strict equality without path normalization for security controls like rate limiting or authentication can easily lead to bypass vulnerabilities.
**Prevention:** Always normalize the request path (e.g., `req.path.toLowerCase().replace(/\/$/, '')`) when implementing custom route-matching logic in Express middleware for security controls. Alternatively, apply security middleware directly to the route definitions (`app.post('/analyze', rateLimiter, handler)`) instead of globally, to inherit Express's built-in matching logic.

## 2024-10-27 - Node.js Native Fetch Timeout DoS
**Vulnerability:** The native Node.js `fetch` requests inside the Express gateway (to `/ask` and `/reply`) lacked any timeout mechanisms. If the downstream Flask service hung or responded extremely slowly, the Node.js connections would hang indefinitely, exhausting server resources and potentially leading to a Denial of Service.
**Learning:** Unlike some older request libraries, the native `fetch` API in Node.js does not have a default timeout. Unbounded network requests can quickly lead to resource exhaustion if downstream dependencies become unresponsive.
**Prevention:** Always use `AbortSignal.timeout(ms)` when making server-to-server requests using the native Node.js `fetch` API to enforce a maximum connection duration and fail fast.
