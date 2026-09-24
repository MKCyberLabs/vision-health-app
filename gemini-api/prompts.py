"""Prompt builders for the stable NutriSnap meal-analysis contract."""

from __future__ import annotations

import json

from analysis_contract import meal_analysis_schema


IMAGE_VALIDATION = (
    "First verify that the image contains identifiable food or drinks. If it clearly does not, "
    'return {"error":"NOT_FOOD","aiNote":"brief reason"}. Treat ingredients, fruit, raw '
    "vegetables, snacks, salads, and drinks as food. If uncertain, analyze it as food."
)


def _output_instructions(telegram: bool) -> str:
    schema = json.dumps(meal_analysis_schema(telegram), separators=(",", ":"))
    instructions = [
        "Return only one valid JSON object. Do not use Markdown fences or explanatory text.",
        "Treat the supplied description as the user's note; put your own feedback only in healthInsight.",
        "Break the meal into individual foodItems and estimate every required nutrient for every item.",
        "Use grams, not a weight field. Rate nutritional quality from 1 to 5.",
    ]
    if telegram:
        instructions.append(
            "Include calculatedTime as ISO 8601 UTC and calculatedCategory as exactly one of "
            "Breakfast, Lunch, Dinner, or Snacks."
        )
    instructions.append(f"The accepted JSON Schema is: {schema}")
    return " ".join(instructions)


def build_health_prompt(
    meal_description: str,
    meal_time: str,
    weight: str | int | float,
    image_path: str | None,
) -> str:
    parts = [
        f"Analyze this meal eaten at {meal_time or 'the supplied time'}.",
        f"Description: {meal_description or '(none provided)' }.",
    ]
    if weight:
        parts.append(
            f"The user explicitly specified {weight} grams; calculate values from that amount."
        )
    if image_path:
        parts.extend([f"Image: {image_path}", IMAGE_VALIDATION])
        if not meal_description:
            parts.append("Identify the food and estimate the portion without asking a follow-up question.")
    parts.append(_output_instructions(telegram=False))
    return " ".join(parts)


def build_telegram_prompt(
    meal_description: str,
    telegram_timestamp: str | int | float,
    user_local_time: str,
    weight: str | int | float,
    image_path: str | None,
) -> str:
    parts = [
        f"Telegram anchor timestamp: {telegram_timestamp}.",
        f"User local anchor time: {user_local_time}.",
        f"Description: {meal_description or '(none provided)' }.",
        "Determine when the meal was consumed from the description. If no time is implied, use the anchor time.",
        "Classify the meal using the calculated local time and description.",
    ]
    if weight:
        parts.append(
            f"The user explicitly specified {weight} grams; calculate values from that amount."
        )
    if image_path:
        parts.extend([f"Image: {image_path}", IMAGE_VALIDATION])
    parts.append(_output_instructions(telegram=True))
    return " ".join(parts)
