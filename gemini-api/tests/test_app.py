import json
import unittest
from unittest.mock import patch

import app as application
from providers import ProviderError, ProviderResponse
from tests.helpers import valid_meal_result


class MealAnalysisRouteTests(unittest.TestCase):
    def setUp(self):
        application.app.config.update(TESTING=True)
        self.client = application.app.test_client()

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})

    def test_readiness_failure_returns_service_unavailable(self):
        readiness = {
            "ready": False,
            "selected": {"text": "openrouter", "image": "agy"},
            "checks": {"text": False, "image": True},
            "providers": {},
        }
        with patch.object(application.PROVIDER_ROUTER, "readiness", return_value=readiness):
            response = self.client.get("/ready")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["status"], "not_ready")

    def test_health_matrix_returns_legacy_and_structured_results(self):
        result = valid_meal_result()
        provider_response = ProviderResponse(
            text=f"result follows\n{json.dumps(result)}",
            provider="agy",
            model="gemini-3.8-flash-low",
        )
        with patch.object(application.PROVIDER_ROUTER, "generate", return_value=provider_response):
            response = self.client.post(
                "/health-matrix",
                json={"mealDescription": "oats", "mealTime": "08:00"},
            )
        body = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["result"], result)
        self.assertEqual(json.loads(body["response"]), result)
        self.assertEqual(body["meta"]["provider"], "agy")

    def test_telegram_contract_is_enforced(self):
        provider_response = ProviderResponse(
            text=json.dumps(valid_meal_result()),
            provider="agy",
            model="gemini-3.8-flash-low",
        )
        with patch.object(application.PROVIDER_ROUTER, "generate", return_value=provider_response):
            response = self.client.post(
                "/health-matrix-telegram",
                json={"mealDescription": "oats", "telegramTimestamp": 1},
            )
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.get_json()["code"], "invalid_provider_output")

    def test_provider_timeout_maps_to_gateway_timeout(self):
        error = ProviderError("timeout", provider="agy", retriable=True, code="timeout")
        with patch.object(application.PROVIDER_ROUTER, "generate", side_effect=error):
            response = self.client.post(
                "/health-matrix", json={"mealDescription": "oats"}
            )
        self.assertEqual(response.status_code, 504)
        self.assertEqual(response.get_json()["code"], "timeout")

    def test_missing_image_is_rejected_before_provider_call(self):
        with patch.object(application.PROVIDER_ROUTER, "generate") as generate:
            response = self.client.post(
                "/health-matrix", json={"imagePath": "/uploads/not-found.jpg"}
            )
        self.assertEqual(response.status_code, 400)
        generate.assert_not_called()

    def test_resolve_host_image_path_resolves_existing_file(self):
        import tempfile
        import os
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = os.path.join(tmp_dir, "meal-123.jpg")
            with open(test_file, "w") as f:
                f.write("image-bytes")
            with patch.object(application, "HOST_TEMP_DIR", tmp_dir):
                resolved = application.resolve_host_image_path("/uploads/meal-123.jpg")
                self.assertEqual(resolved, test_file)

    def test_resolve_host_image_path_fallback_to_default(self):
        import tempfile
        import os
        with tempfile.TemporaryDirectory() as empty_shared, tempfile.TemporaryDirectory() as fallback_dir:
            test_file = os.path.join(fallback_dir, "fallback-meal.jpg")
            with open(test_file, "w") as f:
                f.write("image-bytes")
            with patch.object(application, "HOST_TEMP_DIR", empty_shared), \
                 patch.object(application, "DEFAULT_TEMP_DIR", fallback_dir):
                resolved = application.resolve_host_image_path("/uploads/fallback-meal.jpg")
                self.assertEqual(resolved, test_file)


    def test_ready_endpoint_success(self):
        readiness = {
            "ready": True,
            "selected": {"text": "agy", "image": "agy"},
            "checks": {"text": True, "image": True},
            "providers": {"agy": {"configured": True}},
        }
        with patch.object(application.PROVIDER_ROUTER, "readiness", return_value=readiness):
            response = self.client.get("/ready")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ready")

    def test_resolve_host_image_path_returns_none_for_empty(self):
        self.assertIsNone(application.resolve_host_image_path(""))
        self.assertIsNone(application.resolve_host_image_path(None))

    def test_resolve_host_image_path_rejects_traversal(self):
        traversal_paths = [
            "../../etc/passwd",
            "/uploads/../../secret.txt",
            "..",
            "../meal.jpg",
            "/uploads/../temp/meal.jpg",
        ]
        for path in traversal_paths:
            with self.subTest(path=path):
                with self.assertRaises(ValueError) as ctx:
                    application.resolve_host_image_path(path)
                self.assertIn("traversal", str(ctx.exception).lower())

    def test_resolve_host_image_path_rejects_invalid_filename(self):
        invalid_paths = [".", "/"]
        for path in invalid_paths:
            with self.subTest(path=path):
                with self.assertRaises(ValueError) as ctx:
                    application.resolve_host_image_path(path)
                self.assertIn("invalid", str(ctx.exception).lower())

    def test_resolve_host_image_path_missing_file_raises_error(self):
        with self.assertRaises(ValueError) as ctx:
            application.resolve_host_image_path("/uploads/nonexistent-image.jpg")
        self.assertIn("not found", str(ctx.exception).lower())

    def test_health_matrix_traversal_image_returns_400(self):
        with patch.object(application.PROVIDER_ROUTER, "generate") as generate:
            response = self.client.post(
                "/health-matrix", json={"imagePath": "/uploads/../../etc/passwd"}
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())
        generate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
