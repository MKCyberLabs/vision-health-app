## 2024-06-17 - Argument Injection in pexpect.spawn
**Vulnerability:** Found an argument injection vulnerability where user-controlled input (`prompt_for_cli`) was being directly interpolated into a command string passed to `pexpect.spawn`. By injecting quotes, an attacker could add arbitrary arguments to the command being executed.
**Learning:** `pexpect.spawn` behaves like `subprocess.Popen(..., shell=False)` when given a list, but when given a string, it uses `shlex.split` under the hood. If user input containing quotes is placed inside a string command, `shlex.split` can interpret those quotes, allowing attackers to escape the intended argument and inject additional arguments.
**Prevention:** Always pass arguments to `pexpect.spawn` as a list rather than a single interpolated string, especially when handling user-controlled data.
## 2024-06-12 - Prevent Reflected DOM XSS in UI Prompts
**Vulnerability:** User input or external system text (like backend prompts) was inserted into HTML views using string interpolation with `innerHTML`.
**Learning:** Bypassing standard DOM methods and injecting directly via `innerHTML` can execute arbitrary scripts embedded within the backend data, causing a Reflected DOM XSS.
**Prevention:** Always use safe DOM APIs like `textContent` when injecting dynamic data originating from external inputs or proxies, ensuring it is rendered strictly as text, not executable HTML.
