import json
import unittest

from analysis_contract import (
    AnalysisContractError,
    extract_json_object,
    meal_analysis_schema,
    validate_meal_analysis,
)
from tests.helpers import valid_meal_result


class ExtractJsonObjectTests(unittest.TestCase):
    def test_accepts_direct_object(self):
        value = {"answer": 1}
        self.assertIs(extract_json_object(value), value)

    def test_extracts_prefixed_json_without_greedy_matching(self):
        self.assertEqual(
            extract_json_object('thinking first\n{"answer":1}\ntrailing {noise}'),
            {"answer": 1},
        )

    def test_unwraps_structured_cli_envelope(self):
        raw = json.dumps({"response": json.dumps({"answer": 1})})
        self.assertEqual(extract_json_object(raw), {"answer": 1})

    def test_rejects_missing_json(self):
        with self.assertRaises(AnalysisContractError):
            extract_json_object("no object here")


class MealContractTests(unittest.TestCase):
    def test_validates_standard_result(self):
        result = valid_meal_result()
        self.assertEqual(validate_meal_analysis(result), result)

    def test_validates_telegram_result(self):
        result = valid_meal_result(telegram=True)
        self.assertEqual(validate_meal_analysis(result, telegram=True), result)

    def test_accepts_not_food_result(self):
        result = {"error": "NOT_FOOD", "aiNote": "The image is a bicycle."}
        self.assertEqual(validate_meal_analysis(result), result)

    def test_rejects_missing_nutrient(self):
        result = valid_meal_result()
        del result["fiber"]
        with self.assertRaisesRegex(AnalysisContractError, "result.fiber"):
            validate_meal_analysis(result)

    def test_rejects_invalid_item_rating(self):
        result = valid_meal_result()
        result["foodItems"][0]["rating"] = 6
        with self.assertRaisesRegex(AnalysisContractError, "rating"):
            validate_meal_analysis(result)

    def test_telegram_schema_requires_time_and_category(self):
        success_schema = meal_analysis_schema(telegram=True)["anyOf"][0]
        self.assertIn("calculatedTime", success_schema["required"])
        self.assertIn("calculatedCategory", success_schema["required"])


if __name__ == "__main__":
    unittest.main()
