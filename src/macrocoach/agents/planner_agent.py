"""
PlannerAgent - Calculates daily energy expenditure and sets macro targets.
For v0.1: rule-based. Later: RL policy.
"""

from datetime import datetime, timedelta
from typing import Any

from ..core.context import ApplicationContext
from ..core.models import DailyPlan, HealthMetric, UserProfile


class PlannerAgent:
    """
    Calculates energy expenditure and macro targets.

    v0.1: Rule-based approach with simple weight-based adjustments
    v2.0: Will be replaced with PPO/SAC policy
    """

    def __init__(self, context: ApplicationContext):
        self.context = context

    def calculate_bmr(self, profile: UserProfile, weight: float | None = None) -> float:
        """
        Calculate Basal Metabolic Rate using Mifflin-St Jeor equation.

        Args:
            profile: User profile with age, gender, height
            weight: Current weight in kg (if None, uses target weight)
        """
        weight_kg = weight or profile.target_weight_kg or 70.0  # Default fallback
        height_cm = profile.height_cm
        age = profile.age

        if profile.gender.lower() == "male":
            # Men: BMR = 10 × weight + 6.25 × height - 5 × age + 5
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        else:
            # Women: BMR = 10 × weight + 6.25 × height - 5 × age - 161
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

        return max(bmr, 1000)  # Minimum BMR for safety

    def calculate_tdee(self, bmr: float, activity_level: str) -> float:
        """
        Calculate Total Daily Energy Expenditure.

        Activity factors:
        - sedentary: BMR × 1.2
        - lightly_active: BMR × 1.375
        - moderately_active: BMR × 1.55
        - very_active: BMR × 1.725
        - extremely_active: BMR × 1.9
        """
        activity_multipliers = {
            "sedentary": 1.2,
            "lightly_active": 1.375,
            "moderately_active": 1.55,
            "very_active": 1.725,
            "extremely_active": 1.9,
        }

        multiplier = activity_multipliers.get(activity_level, 1.375)
        return bmr * multiplier

    def get_weight_trend_adjustment(
        self, recent_weights: list[float], target_weight: float | None
    ) -> int:
        """
        Rule-based calorie adjustment based on weight trend.

        Returns calorie adjustment (-200 to +200):
        - If weight trending up from target: -200 kcal
        - If weight trending down from target: +200 kcal
        - If no clear trend or no target: 0
        """
        if not recent_weights or not target_weight or len(recent_weights) < 3:
            return 0

        # Calculate 7-day average weight trend
        avg_weight = sum(recent_weights) / len(recent_weights)
        weight_diff = avg_weight - target_weight

        # Simple thresholds (can be made more sophisticated)
        if weight_diff > 1.0:  # More than 1kg above target
            return -200  # Reduce calories
        elif weight_diff < -1.0:  # More than 1kg below target
            return +200  # Increase calories
        else:
            return 0  # Maintain current calories

    def calculate_macro_targets(
        self, target_kcal: int, profile: UserProfile
    ) -> dict[str, float]:
        """
        Calculate protein, carbs, and fat targets based on percentages.

        Returns grams for each macro.
        """
        # Ensure percentages add up to 100
        total_percent = (
            profile.protein_percent + profile.carbs_percent + profile.fat_percent
        )
        if abs(total_percent - 100.0) > 0.1:
            # Normalize if they don't add up to 100
            protein_pct = profile.protein_percent / total_percent * 100
            carbs_pct = profile.carbs_percent / total_percent * 100
            fat_pct = profile.fat_percent / total_percent * 100
        else:
            protein_pct = profile.protein_percent
            carbs_pct = profile.carbs_percent
            fat_pct = profile.fat_percent

        # Calculate grams (4 kcal/g for protein and carbs, 9 kcal/g for fat)
        protein_g = (target_kcal * protein_pct / 100) / 4
        carbs_g = (target_kcal * carbs_pct / 100) / 4
        fat_g = (target_kcal * fat_pct / 100) / 9

        return {
            "protein_g": round(protein_g, 1),
            "carbs_g": round(carbs_g, 1),
            "fat_g": round(fat_g, 1),
        }

    async def generate_daily_plan(
        self,
        user_id: str,
        profile: UserProfile,
        recent_metrics: list[HealthMetric],
        target_date: datetime | None = None,
    ) -> DailyPlan:
        """
        Generate a daily nutrition and activity plan.

        Args:
            user_id: User identifier
            profile: User profile with goals and preferences
            recent_metrics: Recent health metrics for trend analysis
            target_date: Date for the plan (default: tomorrow)
        """
        if target_date is None:
            target_date = datetime.now() + timedelta(days=1)

        # Get current weight (use most recent or fallback to target)
        current_weight = None
        recent_weights = []

        if recent_metrics:
            # Extract recent weights for trend analysis
            recent_weights = [m.weight for m in recent_metrics[-7:] if m.weight]
            current_weight = recent_weights[-1] if recent_weights else None

        weight_for_bmr = current_weight or profile.target_weight_kg or 70.0

        # Calculate energy needs
        bmr = self.calculate_bmr(profile, weight_for_bmr)
        tdee = self.calculate_tdee(bmr, profile.activity_level)

        # Apply goal-based adjustment
        goal_adjustment = 0
        if profile.target_kcal_deficit:
            goal_adjustment = profile.target_kcal_deficit
        elif profile.goal == "lose_weight":
            goal_adjustment = -300  # Default deficit
        elif profile.goal == "gain_weight" or profile.goal == "gain_muscle":
            goal_adjustment = +300  # Default surplus

        # Apply weight trend adjustment (rule-based for v0.1)
        trend_adjustment = self.get_weight_trend_adjustment(
            recent_weights, profile.target_weight_kg
        )

        # Calculate final calorie target
        target_kcal = int(tdee + goal_adjustment + trend_adjustment)
        target_kcal = max(target_kcal, int(bmr))  # Never go below BMR

        # Calculate macro targets
        macros = self.calculate_macro_targets(target_kcal, profile)

        # Determine activity targets based on profile
        target_steps = self._get_target_steps(profile)
        target_workout_minutes = self._get_target_workout_minutes(profile)

        # Generate reasoning
        adjustments_made = []
        reasoning_parts = [
            f"BMR: {int(bmr)} kcal (Mifflin-St Jeor)",
            f"TDEE: {int(tdee)} kcal ({profile.activity_level})",
        ]

        if goal_adjustment != 0:
            reasoning_parts.append(
                f"Goal adjustment: {goal_adjustment:+d} kcal ({profile.goal})"
            )
            adjustments_made.append(f"Goal-based: {goal_adjustment:+d} kcal")

        if trend_adjustment != 0:
            reasoning_parts.append(
                f"Weight trend adjustment: {trend_adjustment:+d} kcal"
            )
            adjustments_made.append(f"Weight trend: {trend_adjustment:+d} kcal")

        reasoning = ". ".join(reasoning_parts) + f". Final target: {target_kcal} kcal."

        return DailyPlan(
            user_id=user_id,
            date=target_date,
            target_kcal=target_kcal,
            target_protein_g=macros["protein_g"],
            target_carbs_g=macros["carbs_g"],
            target_fat_g=macros["fat_g"],
            target_steps=target_steps,
            target_workout_minutes=target_workout_minutes,
            plan_reasoning=reasoning,
            adjustments_made=adjustments_made,
            suggested_meals=[],  # Will be filled by MealGenAgent
        )

    def _get_target_steps(self, profile: UserProfile) -> int:
        """Get daily step target based on activity level."""
        step_targets = {
            "sedentary": 6000,
            "lightly_active": 8000,
            "moderately_active": 10000,
            "very_active": 12000,
            "extremely_active": 15000,
        }
        return step_targets.get(profile.activity_level, 10000)

    def _get_target_workout_minutes(self, profile: UserProfile) -> int:
        """Get daily workout target based on goal and activity level."""
        if profile.goal in ["gain_muscle", "lose_weight"]:
            return 45  # More intensive goals
        elif profile.activity_level in ["very_active", "extremely_active"]:
            return 60
        else:
            return 30

    def analyze_progress(
        self, profile: UserProfile, recent_metrics: list[HealthMetric], days: int = 7
    ) -> dict[str, Any]:
        """
        Analyze user's progress over the last N days.

        Returns insights about adherence, trends, and recommendations.
        """
        if not recent_metrics:
            return {"error": "No recent metrics available"}

        # Calculate averages
        daily_summaries = {}
        for metric in recent_metrics:
            date_str = metric.timestamp.date().isoformat()
            if date_str not in daily_summaries:
                daily_summaries[date_str] = {
                    "kcal_in": 0,
                    "kcal_out": 0,
                    "protein": 0,
                    "steps": 0,
                    "weight": None,
                    "workouts": 0,
                }

            summary = daily_summaries[date_str]
            summary["kcal_in"] += metric.kcal_in or 0
            summary["kcal_out"] += metric.kcal_out or 0
            summary["protein"] += metric.protein_g or 0
            summary["steps"] = max(summary["steps"], metric.steps or 0)

            if metric.weight:
                summary["weight"] = metric.weight
            if metric.workout_type:
                summary["workouts"] += 1

        # Calculate trends
        weights = [s["weight"] for s in daily_summaries.values() if s["weight"]]
        avg_kcal_in = sum(s["kcal_in"] for s in daily_summaries.values()) / len(
            daily_summaries
        )
        avg_steps = sum(s["steps"] for s in daily_summaries.values()) / len(
            daily_summaries
        )
        avg_protein = sum(s["protein"] for s in daily_summaries.values()) / len(
            daily_summaries
        )

        weight_trend = "stable"
        if len(weights) >= 3:
            weight_change = weights[-1] - weights[0]
            if weight_change > 0.5:
                weight_trend = "increasing"
            elif weight_change < -0.5:
                weight_trend = "decreasing"

        return {
            "period_days": len(daily_summaries),
            "avg_kcal_in": round(avg_kcal_in),
            "avg_steps": round(avg_steps),
            "avg_protein_g": round(avg_protein, 1),
            "weight_trend": weight_trend,
            "weight_change_kg": (
                round(weights[-1] - weights[0], 1) if len(weights) >= 2 else None
            ),
            "workout_days": sum(
                1 for s in daily_summaries.values() if s["workouts"] > 0
            ),
            "total_days": len(daily_summaries),
        }
