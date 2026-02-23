"""
MealGenAgent - Uses LLM + ingredients DB to propose meals hitting macro targets.
Constraint: Turkish pantry items preferred.
"""

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

import openai

from ..core.context import ApplicationContext
from ..core.models import DailyPlan, Meal, UserProfile

if TYPE_CHECKING:
    from ..vision.plate_recognizer import PlateRecognizer


class MealGenAgent:
    """
    Generates meal suggestions using LLM to hit macro targets.
    Prioritizes Turkish cuisine and available pantry items.
    """

    def __init__(self, context: ApplicationContext):
        self.context = context
        self.client = None
        if context.openai_api_key:
            self.client = openai.AsyncOpenAI(api_key=context.openai_api_key)

        # Turkish pantry staples (can be expanded)
        self.turkish_ingredients: dict[str, dict[str, float]] = {
            # Grains & Legumes
            "bulgur": {
                "protein_per_100g": 12,
                "carbs_per_100g": 76,
                "fat_per_100g": 1.3,
                "kcal_per_100g": 342,
            },
            "kuru fasulye": {
                "protein_per_100g": 21,
                "carbs_per_100g": 60,
                "fat_per_100g": 1.1,
                "kcal_per_100g": 333,
            },
            "mercimek": {
                "protein_per_100g": 24,
                "carbs_per_100g": 60,
                "fat_per_100g": 1.1,
                "kcal_per_100g": 353,
            },
            "nohut": {
                "protein_per_100g": 19,
                "carbs_per_100g": 61,
                "fat_per_100g": 6.0,
                "kcal_per_100g": 364,
            },
            "pirinç": {
                "protein_per_100g": 7,
                "carbs_per_100g": 78,
                "fat_per_100g": 0.7,
                "kcal_per_100g": 365,
            },
            # Proteins
            "tavuk göğsü": {
                "protein_per_100g": 31,
                "carbs_per_100g": 0,
                "fat_per_100g": 3.6,
                "kcal_per_100g": 165,
            },
            "dana eti": {
                "protein_per_100g": 26,
                "carbs_per_100g": 0,
                "fat_per_100g": 15,
                "kcal_per_100g": 250,
            },
            "balık": {
                "protein_per_100g": 22,
                "carbs_per_100g": 0,
                "fat_per_100g": 4,
                "kcal_per_100g": 120,
            },
            "yumurta": {
                "protein_per_100g": 13,
                "carbs_per_100g": 1.1,
                "fat_per_100g": 11,
                "kcal_per_100g": 155,
            },
            "lor peyniri": {
                "protein_per_100g": 11,
                "carbs_per_100g": 4,
                "fat_per_100g": 4,
                "kcal_per_100g": 98,
            },
            "beyaz peynir": {
                "protein_per_100g": 17,
                "carbs_per_100g": 1,
                "fat_per_100g": 21,
                "kcal_per_100g": 264,
            },
            # Vegetables
            "domates": {
                "protein_per_100g": 0.9,
                "carbs_per_100g": 3.9,
                "fat_per_100g": 0.2,
                "kcal_per_100g": 18,
            },
            "salatalık": {
                "protein_per_100g": 0.7,
                "carbs_per_100g": 3.6,
                "fat_per_100g": 0.1,
                "kcal_per_100g": 16,
            },
            "soğan": {
                "protein_per_100g": 1.1,
                "carbs_per_100g": 9.3,
                "fat_per_100g": 0.1,
                "kcal_per_100g": 40,
            },
            "biber": {
                "protein_per_100g": 1,
                "carbs_per_100g": 6,
                "fat_per_100g": 0.3,
                "kcal_per_100g": 31,
            },
            "patlıcan": {
                "protein_per_100g": 1,
                "carbs_per_100g": 6,
                "fat_per_100g": 0.2,
                "kcal_per_100g": 25,
            },
            "kabak": {
                "protein_per_100g": 1.2,
                "carbs_per_100g": 7,
                "fat_per_100g": 0.1,
                "kcal_per_100g": 17,
            },
            # Fats & Nuts
            "zeytinyağı": {
                "protein_per_100g": 0,
                "carbs_per_100g": 0,
                "fat_per_100g": 100,
                "kcal_per_100g": 884,
            },
            "tereyağı": {
                "protein_per_100g": 0.9,
                "carbs_per_100g": 0.1,
                "fat_per_100g": 81,
                "kcal_per_100g": 717,
            },
            "ceviz": {
                "protein_per_100g": 15,
                "carbs_per_100g": 14,
                "fat_per_100g": 65,
                "kcal_per_100g": 654,
            },
            "badem": {
                "protein_per_100g": 21,
                "carbs_per_100g": 22,
                "fat_per_100g": 49,
                "kcal_per_100g": 579,
            },
        }

    async def generate_meals_for_plan(
        self,
        plan: DailyPlan,
        profile: UserProfile,
        excluded_ingredients: list[str] | None = None,
    ) -> list[Meal]:
        """
        Generate complete meal plan for the day to hit macro targets.

        Args:
            plan: Daily plan with macro targets
            profile: User profile with preferences and restrictions
            excluded_ingredients: Ingredients to avoid
        """
        if not self.client:
            # Fallback: generate simple meals without LLM
            return self._generate_fallback_meals(plan, profile)

        try:
            meals = []

            # Distribute calories across meals
            meal_distribution = {
                "breakfast": 0.25,
                "lunch": 0.35,
                "dinner": 0.30,
                "snack": 0.10,
            }

            for meal_type, calorie_ratio in meal_distribution.items():
                target_kcal = int(plan.target_kcal * calorie_ratio)
                target_protein = plan.target_protein_g * calorie_ratio
                target_carbs = plan.target_carbs_g * calorie_ratio
                target_fat = plan.target_fat_g * calorie_ratio

                meal = await self._generate_single_meal(
                    meal_type=meal_type,
                    target_kcal=target_kcal,
                    target_protein=target_protein,
                    target_carbs=target_carbs,
                    target_fat=target_fat,
                    profile=profile,
                    excluded_ingredients=excluded_ingredients,
                )

                if meal:
                    meals.append(meal)

            return meals

        except Exception as e:
            print(f"Error generating meals with LLM: {e}")
            return self._generate_fallback_meals(plan, profile)

    async def _generate_single_meal(
        self,
        meal_type: str,
        target_kcal: int,
        target_protein: float,
        target_carbs: float,
        target_fat: float,
        profile: UserProfile,
        excluded_ingredients: list[str] | None = None,
    ) -> Meal | None:
        """Generate a single meal using GPT-4o function calling."""

        # Prepare Turkish ingredients list
        available_ingredients: list[dict[str, Any]] = []
        for ingredient, nutrition in self.turkish_ingredients.items():
            if excluded_ingredients and ingredient in excluded_ingredients:
                continue
            if ingredient not in profile.allergies:
                available_ingredients.append(
                    {"name": ingredient, "nutrition_per_100g": nutrition}
                )

        # Create prompt
        system_prompt = f"""
        Sen Türk mutfağında uzman bir beslenme koçusun. Kullanıcı için {meal_type} önerisi hazırlaman gerek.

        Hedef makrolar:
        - Kalori: {target_kcal} kcal
        - Protein: {target_protein:.1f}g
        - Karbonhidrat: {target_carbs:.1f}g
        - Yağ: {target_fat:.1f}g

        Kullanıcı profili:
        - Diyet kısıtlamaları: {', '.join(profile.dietary_restrictions) if profile.dietary_restrictions else 'Yok'}
        - Alerjiler: {', '.join(profile.allergies) if profile.allergies else 'Yok'}
        - Türk mutfağı tercihi: {'Evet' if profile.prefer_turkish_cuisine else 'Hayır'}

        Mevcut malzemeler: {', '.join([str(ing['name']) for ing in available_ingredients])}

        Lütfen bu malzemelerle, hedef makrolara yakın bir {meal_type} tarifi oluştur.
        Porsiyon miktarlarını gram olarak belirt.
        """

        try:
            assert self.client is not None
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{meal_type} için tarif öner"},
                ],
                functions=[
                    {
                        "name": "create_meal",
                        "description": "Yemek tarifi oluştur",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Yemek adı"},
                                "ingredients": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "amount": {"type": "number"},
                                            "unit": {"type": "string"},
                                        },
                                    },
                                },
                                "instructions": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "prep_time_minutes": {"type": "integer"},
                                "cook_time_minutes": {"type": "integer"},
                                "tags": {"type": "array", "items": {"type": "string"}},
                            },
                            "required": [
                                "name",
                                "ingredients",
                                "instructions",
                                "prep_time_minutes",
                                "cook_time_minutes",
                            ],
                        },
                    }
                ],
                function_call={"name": "create_meal"},
            )

            # Parse function call result
            function_call = response.choices[0].message.function_call
            assert function_call is not None
            meal_data = json.loads(function_call.arguments)

            # Calculate nutrition from ingredients
            nutrition = self._calculate_meal_nutrition(meal_data["ingredients"])

            meal = Meal(
                meal_id=f"{meal_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                name=meal_data["name"],
                meal_type=meal_type,
                kcal=nutrition["kcal"],
                protein_g=nutrition["protein_g"],
                carbs_g=nutrition["carbs_g"],
                fat_g=nutrition["fat_g"],
                ingredients=meal_data["ingredients"],
                instructions=meal_data["instructions"],
                prep_time_minutes=meal_data["prep_time_minutes"],
                cook_time_minutes=meal_data["cook_time_minutes"],
                tags=meal_data.get("tags", ["turkish"]),
                difficulty="easy",
            )

            return meal

        except Exception as e:
            print(f"Error generating meal with LLM: {e}")
            return None

    def _calculate_meal_nutrition(
        self, ingredients: list[dict[str, Any]]
    ) -> dict[str, float]:
        """Calculate total nutrition for a meal from ingredients."""
        total_kcal = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0

        for ingredient in ingredients:
            name = ingredient["name"].lower()
            amount = ingredient["amount"]
            unit = ingredient["unit"]

            # Convert to grams if needed
            if unit == "kg":
                amount *= 1000
            elif unit == "adet" and name == "yumurta":
                amount *= 50  # Average egg weight
            elif unit == "su bardağı":
                amount *= 200  # Approximate
            elif unit == "çay bardağı":
                amount *= 100
            elif unit != "g":
                amount *= 100  # Default fallback

            # Look up nutrition info
            if name in self.turkish_ingredients:
                nutrition = self.turkish_ingredients[name]
                factor = amount / 100  # Nutrition is per 100g

                total_kcal += nutrition["kcal_per_100g"] * factor
                total_protein += nutrition["protein_per_100g"] * factor
                total_carbs += nutrition["carbs_per_100g"] * factor
                total_fat += nutrition["fat_per_100g"] * factor

        return {
            "kcal": round(total_kcal),
            "protein_g": round(total_protein, 1),
            "carbs_g": round(total_carbs, 1),
            "fat_g": round(total_fat, 1),
        }

    def _generate_fallback_meals(
        self, plan: DailyPlan, profile: UserProfile
    ) -> list[Meal]:
        """Generate simple predefined meals when LLM is not available."""
        fallback_meals = [
            Meal(
                meal_id=f"breakfast_{datetime.now().strftime('%Y%m%d')}",
                name="Menemen with Cheese",
                meal_type="breakfast",
                kcal=int(plan.target_kcal * 0.25),
                protein_g=plan.target_protein_g * 0.25,
                carbs_g=plan.target_carbs_g * 0.25,
                fat_g=plan.target_fat_g * 0.25,
                ingredients=[
                    {"name": "yumurta", "amount": 2, "unit": "adet"},
                    {"name": "domates", "amount": 100, "unit": "g"},
                    {"name": "biber", "amount": 50, "unit": "g"},
                    {"name": "beyaz peynir", "amount": 30, "unit": "g"},
                    {"name": "zeytinyağı", "amount": 5, "unit": "g"},
                ],
                instructions=[
                    "Sebzeleri doğrayın",
                    "Tavada zeytinyağında soteleyin",
                    "Yumurtaları ekleyip karıştırın",
                    "Peyniri üzerine serpin",
                ],
                prep_time_minutes=5,
                cook_time_minutes=10,
                tags=["turkish", "quick", "vegetarian"],
            ),
            Meal(
                meal_id=f"lunch_{datetime.now().strftime('%Y%m%d')}",
                name="Grilled Chicken with Bulgur",
                meal_type="lunch",
                kcal=int(plan.target_kcal * 0.35),
                protein_g=plan.target_protein_g * 0.35,
                carbs_g=plan.target_carbs_g * 0.35,
                fat_g=plan.target_fat_g * 0.35,
                ingredients=[
                    {"name": "tavuk göğsü", "amount": 150, "unit": "g"},
                    {"name": "bulgur", "amount": 80, "unit": "g"},
                    {"name": "domates", "amount": 100, "unit": "g"},
                    {"name": "salatalık", "amount": 100, "unit": "g"},
                    {"name": "zeytinyağı", "amount": 10, "unit": "g"},
                ],
                instructions=[
                    "Tavuk göğsünü marine edin",
                    "Bulguru haşlayın",
                    "Tavuğu ızgarada pişirin",
                    "Salata hazırlayın",
                ],
                prep_time_minutes=15,
                cook_time_minutes=20,
                tags=["turkish", "high-protein", "balanced"],
            ),
        ]

        return fallback_meals[:2]  # Return first 2 meals for demo

    async def swap_meal(
        self, meal_id: str, plan: DailyPlan, profile: UserProfile
    ) -> Meal | None:
        """
        Generate a new meal to replace an existing one.
        Maintains the same calorie/macro targets.
        """
        # Find the meal to replace
        old_meal: Meal | dict[str, Any] | None = None
        for meal in plan.suggested_meals:
            if isinstance(meal, dict) and meal.get("meal_id") == meal_id:
                old_meal = meal
                break
            elif hasattr(meal, "meal_id") and meal.meal_id == meal_id:
                old_meal = meal
                break

        if not old_meal:
            return None

        # Extract targets from old meal
        if isinstance(old_meal, dict):
            target_kcal = old_meal.get("kcal", 400)
            target_protein = old_meal.get("protein_g", 20)
            target_carbs = old_meal.get("carbs_g", 40)
            target_fat = old_meal.get("fat_g", 15)
            meal_type = old_meal.get("meal_type", "snack")
        else:
            target_kcal = old_meal.kcal
            target_protein = old_meal.protein_g
            target_carbs = old_meal.carbs_g
            target_fat = old_meal.fat_g
            meal_type = old_meal.meal_type

        # Generate new meal with same targets
        new_meal = await self._generate_single_meal(
            meal_type=meal_type,
            target_kcal=target_kcal,
            target_protein=target_protein,
            target_carbs=target_carbs,
            target_fat=target_fat,
            profile=profile,
        )

        return new_meal

    async def analyze_image(
        self,
        image: Any,
        recognizer: "PlateRecognizer",
        profile: UserProfile | None = None,
    ) -> dict[str, Any]:
        """Analyze meal image and suggest ingredient swaps."""
        macros = await recognizer.recognize_plate(image)
        if profile is None:
            ratios = {"protein": 30.0, "carbs": 40.0, "fat": 30.0}
        else:
            ratios = {
                "protein": profile.protein_percent,
                "carbs": profile.carbs_percent,
                "fat": profile.fat_percent,
            }

        target_protein = macros["kcal"] * ratios["protein"] / 100 / 4
        target_carbs = macros["kcal"] * ratios["carbs"] / 100 / 4
        target_fat = macros["kcal"] * ratios["fat"] / 100 / 9

        gap = {
            "protein": target_protein - macros.get("protein_g", 0),
            "carbs": target_carbs - macros.get("carbs_g", 0),
            "fat": target_fat - macros.get("fat_g", 0),
        }

        swaps = self.get_ingredient_suggestions(gap)
        return {"macros": macros, "swaps": swaps}

    def get_ingredient_suggestions(self, macro_gap: dict[str, float]) -> list[str]:
        """
        Suggest ingredients to fill remaining macro gaps.

        Args:
            macro_gap: {"protein": X, "carbs": Y, "fat": Z} in grams
        """
        suggestions = []

        if macro_gap.get("protein", 0) > 10:
            suggestions.extend(["tavuk göğsü", "yumurta", "lor peyniri", "balık"])

        if macro_gap.get("carbs", 0) > 20:
            suggestions.extend(["bulgur", "pirinç", "mercimek", "nohut"])

        if macro_gap.get("fat", 0) > 5:
            suggestions.extend(["zeytinyağı", "ceviz", "badem", "tereyağı"])

        return suggestions[:3]  # Return top 3 suggestions
