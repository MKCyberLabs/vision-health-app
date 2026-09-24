"""Shared meal-analysis response contract and parsing helpers."""

from __future__ import annotations

import json
import math
import re
from typing import Any


class AnalysisContractError(ValueError):
    """Raised when an AI provider returns an unusable meal analysis."""


NUTRIENT_FIELDS = (
    "calories",
    "protein",
    "carbs",
    "fat",
    "fiber",
    "saturatedFat",
    "sugar",
)

ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def _number_schema() -> dict[str, Any]:
    return {"type": "number", "minimum": 0}


def meal_analysis_schema(telegram: bool = False) -> dict[str, Any]:
    """Return the JSON Schema accepted from every analysis provider."""
    item_properties: dict[str, Any] = {
        "name": {"type": "string"},
        "grams": _number_schema(),
        **{field: _number_schema() for field in NUTRIENT_FIELDS},
        "rating": {"type": "integer", "minimum": 1, "maximum": 5},
    }
    item_required = ["name", "grams", *NUTRIENT_FIELDS, "rating"]

    properties: dict[str, Any] = {
        **{field: _number_schema() for field in NUTRIENT_FIELDS},
        "healthInsight": {"type": "string"},
        "foodItems": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": item_properties,
                "required": item_required,
                "additionalProperties": False,
            },
        },
    }
    required = [*NUTRIENT_FIELDS, "healthInsight", "foodItems"]

    if telegram:
        properties.update(
            {
                "calculatedTime": {"type": "string", "format": "date-time"},
                "calculatedCategory": {
                    "type": "string",
                    "enum": ["Breakfast", "Lunch", "Dinner", "Snacks"],
                },
            }
        )
        required = ["calculatedTime", "calculatedCategory", *required]

    success_schema = {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }
    not_food_schema = {
        "type": "object",
        "properties": {
            "error": {"type": "string", "enum": ["NOT_FOOD"]},
            "aiNote": {"type": "string"},
        },
        "required": ["error", "aiNote"],
        "additionalProperties": False,
    }
    return {"anyOf": [success_schema, not_food_schema]}


def extract_json_object(raw: Any) -> dict[str, Any]:
    """Extract the first complete JSON object without a greedy regex."""
    if isinstance(raw, dict):
        if isinstance(raw.get("result"), dict):
            return raw["result"]
        if isinstance(raw.get("response"), str):
            return extract_json_object(raw["response"])
        return raw
    if not isinstance(raw, str) or not raw.strip():
        raise AnalysisContractError("Provider returned an empty response.")

    cleaned = ANSI_ESCAPE.sub("", raw).strip()
    try:
        parsed = json.loads(cleaned)
        return extract_json_object(parsed)
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for index, character in enumerate(cleaned):
        if character != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(cleaned[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return extract_json_object(parsed)

    raise AnalysisContractError("Provider response did not contain a valid JSON object.")


def _require_number(container: dict[str, Any], field: str, location: str) -> None:
    value = container.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AnalysisContractError(f"{location}.{field} must be a number.")
    if not math.isfinite(value) or value < 0:
        raise AnalysisContractError(f"{location}.{field} must be finite and non-negative.")


def validate_meal_analysis(value: Any, telegram: bool = False) -> dict[str, Any]:
    """Validate the runtime fields consumed by NutriSnap."""
    result = extract_json_object(value)

    if result.get("error") == "NOT_FOOD":
        if not isinstance(result.get("aiNote"), str) or not result["aiNote"].strip():
            raise AnalysisContractError("NOT_FOOD responses require a non-empty aiNote.")
        return result

    for field in NUTRIENT_FIELDS:
        _require_number(result, field, "result")

    if not isinstance(result.get("healthInsight"), str):
        raise AnalysisContractError("result.healthInsight must be a string.")

    food_items = result.get("foodItems")
    if not isinstance(food_items, list):
        raise AnalysisContractError("result.foodItems must be an array.")

    for index, item in enumerate(food_items):
        location = f"result.foodItems[{index}]"
        if not isinstance(item, dict):
            raise AnalysisContractError(f"{location} must be an object.")
        if not isinstance(item.get("name"), str) or not item["name"].strip():
            raise AnalysisContractError(f"{location}.name must be a non-empty string.")
        _require_number(item, "grams", location)
        for field in NUTRIENT_FIELDS:
            _require_number(item, field, location)
        rating = item.get("rating")
        if isinstance(rating, bool) or not isinstance(rating, int) or not 1 <= rating <= 5:
            raise AnalysisContractError(f"{location}.rating must be an integer from 1 to 5.")

    if telegram:
        if not isinstance(result.get("calculatedTime"), str) or not result["calculatedTime"].strip():
            raise AnalysisContractError("result.calculatedTime must be a non-empty string.")
        if result.get("calculatedCategory") not in {"Breakfast", "Lunch", "Dinner", "Snacks"}:
            raise AnalysisContractError("result.calculatedCategory is invalid.")

    return result
