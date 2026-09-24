def valid_meal_result(telegram=False):
    result = {
        "calories": 250,
        "protein": 12,
        "carbs": 30,
        "fat": 9,
        "fiber": 5,
        "saturatedFat": 2,
        "sugar": 4,
        "healthInsight": "A balanced meal.",
        "foodItems": [
            {
                "name": "Oats",
                "grams": 100,
                "calories": 250,
                "protein": 12,
                "carbs": 30,
                "fat": 9,
                "fiber": 5,
                "saturatedFat": 2,
                "sugar": 4,
                "rating": 4,
            }
        ],
    }
    if telegram:
        result.update(
            {
                "calculatedTime": "2026-09-24T02:30:00Z",
                "calculatedCategory": "Breakfast",
            }
        )
    return result
