"""AI provider adapters and failover routing for meal analysis."""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable


class ProviderError(RuntimeError):
    def __init__(self, message: str, *, provider: str, retriable: bool = False, code: str = "provider_error"):
        super().__init__(message)
        self.provider = provider
        self.retriable = retriable
        self.code = code


@dataclass(frozen=True)
class ProviderResponse:
    text: str
    provider: str
    model: str
    fallback_used: bool = False


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _image_data_url(image_path: str) -> str:
    mime_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"
    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


class AgyProvider:
    name = "agy"

    MODEL_ALIASES = {
        "gemini 3.5 flash (low)": "gemini-3.8-flash-low",
        "gemini 3.5 flash (medium)": "gemini-3.8-flash-medium",
        "gemini 3.5 flash (high)": "gemini-3.8-flash-high",
        "gemini-3.5-flash-low": "gemini-3.8-flash-low",
        "gemini-3.5-flash-medium": "gemini-3.8-flash-medium",
        "gemini-3.5-flash-high": "gemini-3.8-flash-high",
        "gemini 3.8 flash (low)": "gemini-3.8-flash-low",
        "gemini 3.8 flash (medium)": "gemini-3.8-flash-medium",
        "gemini 3.8 flash (high)": "gemini-3.8-flash-high",
    }

    def __init__(self, executable: str):
        self.executable = executable

    def model(self, has_image: bool) -> str:
        specific = "AGY_IMAGE_MODEL" if has_image else "AGY_TEXT_MODEL"
        legacy = "GEMINI_IMAGE_MODEL" if has_image else "GEMINI_TEXT_MODEL"
        configured = os.environ.get(specific) or os.environ.get(legacy) or "gemini-3.8-flash-low"
        return self.MODEL_ALIASES.get(configured.strip().lower(), configured.strip())

    def generate(self, prompt: str, image_path: str | None, schema: dict[str, Any], model: str | None = None) -> ProviderResponse:
        selected_model = model or self.model(bool(image_path))
        command = [self.executable, "-p", prompt, "--model", selected_model]
        if _env_bool("AGY_SKIP_PERMISSIONS", True):
            command.append("--dangerously-skip-permissions")
        if _env_bool("AGY_USE_JSON_SCHEMA", False):
            command.extend(["--output-format", "json", "--json-schema", json.dumps(schema, separators=(",", ":"))])

        child_env = os.environ.copy()
        child_env.setdefault("ALL_PROXY", "socks5://127.0.0.1:1080")
        timeout = float(os.environ.get("ANALYSIS_TIMEOUT_SECONDS", "300"))
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=child_env,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ProviderError(
                "Antigravity CLI timed out.", provider=self.name, retriable=True, code="timeout"
            ) from exc
        except OSError as exc:
            raise ProviderError(
                "Antigravity CLI could not be started.", provider=self.name, retriable=True, code="unavailable"
            ) from exc

        output = completed.stdout.strip()
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip()
            raise ProviderError(
                f"Antigravity CLI failed: {detail[-500:] or 'unknown error'}",
                provider=self.name,
                retriable=True,
                code="command_failed",
            )
        if not output:
            raise ProviderError(
                "Antigravity CLI returned an empty response.",
                provider=self.name,
                retriable=True,
                code="empty_response",
            )
        return ProviderResponse(text=output, provider=self.name, model=selected_model)

    def status(self) -> dict[str, Any]:
        executable = self.executable if os.path.isabs(self.executable) else shutil.which(self.executable)
        return {"configured": bool(executable and os.path.isfile(executable) and os.access(executable, os.X_OK))}


class JsonHttpProvider:
    name = "http"

    def __init__(self, opener: Callable[..., Any] = urllib.request.urlopen):
        self._opener = opener

    def _post(self, url: str, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", **headers},
            method="POST",
        )
        timeout = float(os.environ.get("ANALYSIS_TIMEOUT_SECONDS", "300"))
        try:
            with self._opener(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            retriable = exc.code in {408, 409, 425, 429} or exc.code >= 500
            raise ProviderError(
                f"{self.name} returned HTTP {exc.code}: {body[-500:]}",
                provider=self.name,
                retriable=retriable,
                code=f"http_{exc.code}",
            ) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise ProviderError(
                f"{self.name} request failed: {exc}",
                provider=self.name,
                retriable=True,
                code="network_error",
            ) from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProviderError(
                f"{self.name} returned malformed JSON.",
                provider=self.name,
                retriable=True,
                code="malformed_response",
            ) from exc


class OpenRouterProvider(JsonHttpProvider):
    name = "openrouter"

    def model(self, has_image: bool) -> str:
        key = "OPENROUTER_IMAGE_MODEL" if has_image else "OPENROUTER_TEXT_MODEL"
        model = os.environ.get(key) or os.environ.get("OPENROUTER_MODEL")
        if not model:
            raise ProviderError(
                f"{key} is not configured.", provider=self.name, code="configuration_error"
            )
        return model

    def generate(self, prompt: str, image_path: str | None, schema: dict[str, Any], model: str | None = None) -> ProviderResponse:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ProviderError(
                "OPENROUTER_API_KEY is not configured.", provider=self.name, code="configuration_error"
            )
        selected_model = model or self.model(bool(image_path))
        content: Any = prompt
        if image_path:
            content = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": _image_data_url(image_path)}},
            ]
        payload = {
            "model": selected_model,
            "messages": [{"role": "user", "content": content}],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "meal_analysis", "strict": True, "schema": schema},
            },
            "stream": False,
            "provider": {"require_parameters": True},
        }
        headers = {"Authorization": f"Bearer {api_key}"}
        if os.environ.get("OPENROUTER_SITE_URL"):
            headers["HTTP-Referer"] = os.environ["OPENROUTER_SITE_URL"]
        if os.environ.get("OPENROUTER_APP_NAME"):
            headers["X-OpenRouter-Title"] = os.environ["OPENROUTER_APP_NAME"]
        data = self._post(
            os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions"),
            headers,
            payload,
        )
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(
                "OpenRouter response did not contain message content.",
                provider=self.name,
                retriable=True,
                code="malformed_response",
            ) from exc
        if not isinstance(text, str):
            text = json.dumps(text)
        return ProviderResponse(text=text, provider=self.name, model=selected_model)

    def status(self) -> dict[str, Any]:
        return {
            "configured": bool(os.environ.get("OPENROUTER_API_KEY")),
            "text_model": bool(os.environ.get("OPENROUTER_TEXT_MODEL") or os.environ.get("OPENROUTER_MODEL")),
            "image_model": bool(os.environ.get("OPENROUTER_IMAGE_MODEL") or os.environ.get("OPENROUTER_MODEL")),
        }


class GoogleProvider(JsonHttpProvider):
    name = "google"

    def model(self, has_image: bool) -> str:
        key = "GOOGLE_IMAGE_MODEL" if has_image else "GOOGLE_TEXT_MODEL"
        return os.environ.get(key) or os.environ.get("GOOGLE_MODEL") or "gemini-3.8-flash"

    def generate(self, prompt: str, image_path: str | None, schema: dict[str, Any], model: str | None = None) -> ProviderResponse:
        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ProviderError(
                "GOOGLE_API_KEY or GEMINI_API_KEY is not configured.",
                provider=self.name,
                code="configuration_error",
            )
        selected_model = model or self.model(bool(image_path))
        parts: list[dict[str, Any]] = [{"text": prompt}]
        if image_path:
            data_url = _image_data_url(image_path)
            metadata, encoded = data_url.split(",", 1)
            mime_type = metadata[5:].split(";", 1)[0]
            parts.append({"inline_data": {"mime_type": mime_type, "data": encoded}})
        payload = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "responseFormat": {
                    "text": {"mimeType": "application/json", "schema": schema}
                }
            },
        }
        base_url = os.environ.get("GOOGLE_API_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
        data = self._post(
            f"{base_url.rstrip('/')}/models/{selected_model}:generateContent",
            {"x-goog-api-key": api_key},
            payload,
        )
        try:
            text = "".join(
                part.get("text", "")
                for part in data["candidates"][0]["content"]["parts"]
                if isinstance(part, dict)
            )
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(
                "Google response did not contain candidate text.",
                provider=self.name,
                retriable=True,
                code="malformed_response",
            ) from exc
        if not text:
            raise ProviderError(
                "Google returned empty candidate text.",
                provider=self.name,
                retriable=True,
                code="empty_response",
            )
        return ProviderResponse(text=text, provider=self.name, model=selected_model)

    def status(self) -> dict[str, Any]:
        return {"configured": bool(os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"))}


class ProviderRouter:
    def __init__(self, providers: dict[str, Any]):
        self.providers = providers

    def _provider_name(self, has_image: bool, requested_provider: str | None) -> str:
        if requested_provider:
            if not _env_bool("ALLOW_PROVIDER_OVERRIDE", False):
                raise ProviderError(
                    "Per-request provider overrides are disabled.",
                    provider="router",
                    code="provider_override_disabled",
                )
            return requested_provider.strip().lower()
        key = "ANALYSIS_IMAGE_PROVIDER" if has_image else "ANALYSIS_TEXT_PROVIDER"
        return (os.environ.get(key) or os.environ.get("ANALYSIS_PROVIDER") or "agy").strip().lower()

    def generate(
        self,
        prompt: str,
        image_path: str | None,
        schema: dict[str, Any],
        requested_provider: str | None = None,
        requested_model: str | None = None,
    ) -> ProviderResponse:
        primary_name = self._provider_name(bool(image_path), requested_provider)
        fallback_name = os.environ.get("ANALYSIS_FALLBACK_PROVIDER", "").strip().lower()
        attempts = [primary_name]
        if fallback_name and fallback_name != "none" and fallback_name != primary_name:
            attempts.append(fallback_name)

        last_error: ProviderError | None = None
        for index, name in enumerate(attempts):
            provider = self.providers.get(name)
            if provider is None:
                raise ProviderError(
                    f"Unknown analysis provider: {name}", provider="router", code="unknown_provider"
                )
            try:
                response = provider.generate(
                    prompt,
                    image_path,
                    schema,
                    model=requested_model if index == 0 else None,
                )
                if index:
                    return ProviderResponse(
                        text=response.text,
                        provider=response.provider,
                        model=response.model,
                        fallback_used=True,
                    )
                return response
            except ProviderError as exc:
                last_error = exc
                if not exc.retriable or index == len(attempts) - 1:
                    raise

        assert last_error is not None
        raise last_error

    def status(self) -> dict[str, Any]:
        return {name: provider.status() for name, provider in self.providers.items()}

    def readiness(self) -> dict[str, Any]:
        selected = {
            "text": self._provider_name(False, None),
            "image": self._provider_name(True, None),
        }
        statuses = self.status()
        checks: dict[str, bool] = {}
        for modality, provider_name in selected.items():
            provider_status = statuses.get(provider_name, {})
            configured = bool(provider_status.get("configured"))
            model_flag = provider_status.get(f"{modality}_model")
            checks[modality] = configured and (model_flag is None or bool(model_flag))
        return {
            "ready": all(checks.values()),
            "selected": selected,
            "checks": checks,
            "providers": statuses,
        }
