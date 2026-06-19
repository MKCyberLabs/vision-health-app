## 2024-06-17 - Argument Injection in pexpect.spawn
**Vulnerability:** Found an argument injection vulnerability where user-controlled input (`prompt_for_cli`) was being directly interpolated into a command string passed to `pexpect.spawn`. By injecting quotes, an attacker could add arbitrary arguments to the command being executed.
**Learning:** `pexpect.spawn` behaves like `subprocess.Popen(..., shell=False)` when given a list, but when given a string, it uses `shlex.split` under the hood. If user input containing quotes is placed inside a string command, `shlex.split` can interpret those quotes, allowing attackers to escape the intended argument and inject additional arguments.
**Prevention:** Always pass arguments to `pexpect.spawn` as a list rather than a single interpolated string, especially when handling user-controlled data.

## 2024-10-25 - DOM XSS via Backend Proxying
**Vulnerability:** Found a Cross-Site Scripting (XSS) vulnerability where a response from a backend CLI (`data.message`) was directly interpolated into the `innerHTML` of a DOM element in `public/index.html`. Even though the data originated from a "trusted" backend, it was still user-controlled via the prompt.
**Learning:** Trust boundaries must be strictly maintained at the presentation layer. Just because data passes through a backend service does not mean it is safe to render as HTML without sanitization. An attacker could craft a prompt that causes the CLI to output malicious HTML, which would then be executed in the user's browser.
**Prevention:** Always sanitize or escape dynamic content before inserting it into the DOM, or use safe properties like `textContent` instead of `innerHTML`.
