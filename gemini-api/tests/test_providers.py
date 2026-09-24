import json
import os
import subprocess
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

from analysis_contract import meal_analysis_schema
from providers import (
    AgyProvider,
    GoogleProvider,
    OpenRouterProvider,
    ProviderError,
    ProviderResponse,
    ProviderRouter,
)
from tests.helpers import valid_meal_result


class FakeHttpResponse:
    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.value).encode("utf-8")


class StubProvider:
    def __init__(self, name, response=None, error=None):
        self.name = name
        self.response = response
        self.error = error
        self.calls = 0

    def generate(self, prompt, image_path, schema, model=None):
        self.calls += 1
        if self.error:
            raise self.error
        return ProviderResponse(json.dumps(self.response), self.name, model or "default")

    def status(self):
        return {"configured": True}


class AgyProviderTests(unittest.TestCase):
    def test_uses_new_model_id_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(AgyProvider("/usr/local/bin/agy").model(False), "gemini-3.8-flash-low")

    def test_keeps_legacy_environment_alias(self):
        with patch.dict(os.environ, {"GEMINI_TEXT_MODEL": "legacy-model"}, clear=True):
            self.assertEqual(AgyProvider("/usr/local/bin/agy").model(False), "legacy-model")

    def test_upgrades_removed_gemini_35_display_name(self):
        with patch.dict(
            os.environ, {"GEMINI_TEXT_MODEL": "Gemini 3.5 Flash (Low)"}, clear=True
        ):
            self.assertEqual(
                AgyProvider("/usr/local/bin/agy").model(False),
                "gemini-3.8-flash-low",
            )

    def test_meal_requests_are_stateless_print_calls(self):
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=json.dumps(valid_meal_result()), stderr=""
        )
        with patch.dict(os.environ, {}, clear=True), patch(
            "providers.subprocess.run", return_value=completed
        ) as run:
            response = AgyProvider("/usr/local/bin/agy").generate(
                "analyze", None, meal_analysis_schema()
            )
        command = run.call_args.args[0]
        self.assertIn("-p", command)
        self.assertNotIn("-c", command)
        self.assertEqual(response.model, "gemini-3.8-flash-low")


class OpenRouterProviderTests(unittest.TestCase):
    def test_builds_structured_multimodal_request(self):
        captured = {}

        def opener(request, timeout):
            captured["headers"] = dict(request.header_items())
            captured["payload"] = json.loads(request.data)
            return FakeHttpResponse(
                {"choices": [{"message": {"content": json.dumps(valid_meal_result())}}]}
            )

        with tempfile.NamedTemporaryFile(suffix=".jpg") as image:
            image.write(b"image-data")
            image.flush()
            with patch.dict(
                os.environ,
                {"OPENROUTER_API_KEY": "test-key", "OPENROUTER_IMAGE_MODEL": "vendor/vision"},
                clear=True,
            ):
                response = OpenRouterProvider(opener=opener).generate(
                    "analyze", image.name, meal_analysis_schema()
                )

        self.assertEqual(response.model, "vendor/vision")
        self.assertEqual(captured["payload"]["response_format"]["type"], "json_schema")
        image_url = captured["payload"]["messages"][0]["content"][1]["image_url"]["url"]
        self.assertTrue(image_url.startswith("data:image/jpeg;base64,"))
        self.assertEqual(captured["headers"]["Authorization"], "Bearer test-key")


class GoogleProviderTests(unittest.TestCase):
    def test_builds_google_structured_request(self):
        captured = {}

        def opener(request, timeout):
            captured["url"] = request.full_url
            captured["headers"] = dict(request.header_items())
            captured["payload"] = json.loads(request.data)
            return FakeHttpResponse(
                {"candidates": [{"content": {"parts": [{"text": json.dumps(valid_meal_result())}]}}]}
            )

        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}, clear=True):
            response = GoogleProvider(opener=opener).generate(
                "analyze", None, meal_analysis_schema()
            )

        self.assertEqual(response.model, "gemini-3.8-flash")
        self.assertIn("gemini-3.8-flash:generateContent", captured["url"])
        self.assertEqual(
            captured["payload"]["generationConfig"]["responseFormat"]["text"]["mimeType"],
            "application/json",
        )
        self.assertEqual(captured["headers"]["X-goog-api-key"], "test-key")


class ProviderRouterTests(unittest.TestCase):
    def test_uses_agy_by_default(self):
        agy = StubProvider("agy", valid_meal_result())
        router = ProviderRouter({"agy": agy})
        with patch.dict(os.environ, {}, clear=True):
            response = router.generate("prompt", None, meal_analysis_schema())
        self.assertEqual(response.provider, "agy")
        self.assertEqual(agy.calls, 1)

    def test_falls_back_after_retriable_failure(self):
        primary = StubProvider(
            "agy", error=ProviderError("down", provider="agy", retriable=True)
        )
        fallback = StubProvider("openrouter", valid_meal_result())
        router = ProviderRouter({"agy": primary, "openrouter": fallback})
        with patch.dict(
            os.environ,
            {"ANALYSIS_PROVIDER": "agy", "ANALYSIS_FALLBACK_PROVIDER": "openrouter"},
            clear=True,
        ):
            response = router.generate("prompt", None, meal_analysis_schema())
        self.assertTrue(response.fallback_used)
        self.assertEqual(response.provider, "openrouter")

    def test_does_not_fall_back_after_configuration_error(self):
        primary = StubProvider(
            "agy", error=ProviderError("bad config", provider="agy", retriable=False)
        )
        fallback = StubProvider("openrouter", valid_meal_result())
        router = ProviderRouter({"agy": primary, "openrouter": fallback})
        with patch.dict(
            os.environ,
            {"ANALYSIS_PROVIDER": "agy", "ANALYSIS_FALLBACK_PROVIDER": "openrouter"},
            clear=True,
        ):
            with self.assertRaises(ProviderError):
                router.generate("prompt", None, meal_analysis_schema())
        self.assertEqual(fallback.calls, 0)

    def test_rejects_request_override_by_default(self):
        router = ProviderRouter({"agy": StubProvider("agy", valid_meal_result())})
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ProviderError, "overrides are disabled"):
                router.generate(
                    "prompt", None, meal_analysis_schema(), requested_provider="openrouter"
                )

    def test_readiness_checks_selected_provider_and_modality(self):
        agy = StubProvider("agy", valid_meal_result())
        openrouter = StubProvider("openrouter", valid_meal_result())
        openrouter.status = lambda: {
            "configured": True,
            "text_model": True,
            "image_model": False,
        }
        router = ProviderRouter({"agy": agy, "openrouter": openrouter})
        with patch.dict(
            os.environ,
            {"ANALYSIS_TEXT_PROVIDER": "openrouter", "ANALYSIS_IMAGE_PROVIDER": "agy"},
            clear=True,
        ):
            readiness = router.readiness()
        self.assertTrue(readiness["ready"])
        self.assertEqual(readiness["selected"], {"text": "openrouter", "image": "agy"})


if __name__ == "__main__":
    unittest.main()
