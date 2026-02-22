"""
Tests for PlannerAgent - rule-based calorie and macro calculations.
"""

from datetime import datetime

import pytest

from src.macrocoach.agents.planner_agent import PlannerAgent
from src.macrocoach.core.models import HealthMetric


class TestPlannerAgent:
    """Unit tests for PlannerAgent."""

    @pytest.fixture
    def planner(self, test_context):
        return PlannerAgent(test_context)

    # ------------------------------------------------------------------
    # BMR
    # ------------------------------------------------------------------

    def test_bmr_male(self, planner, test_user_profile):
        """Mifflin-St Jeor for a male."""
        # 10*70 + 6.25*175 - 5*25 + 5 = 700+1093.75-125+5 = 1673.75
        bmr = planner.calculate_bmr(test_user_profile, weight=70.0)
        assert abs(bmr - 1673.75) < 0.1

    def test_bmr_female(self, planner, test_user_profile):
        """Mifflin-St Jeor for a female."""
        test_user_profile.gender = "female"
        # 10*70 + 6.25*175 - 5*25 - 161 = 700+1093.75-125-161 = 1507.75
        bmr = planner.calculate_bmr(test_user_profile, weight=70.0)
        assert abs(bmr - 1507.75) < 0.1

    def test_bmr_minimum_floor(self, planner, test_user_profile):
        """BMR should never fall below 1000 kcal."""
        test_user_profile.age = 120  # extreme age to drive BMR very low
        bmr = planner.calculate_bmr(test_user_profile, weight=30.0)
        assert bmr >= 1000

    # ------------------------------------------------------------------
    # TDEE
    # ------------------------------------------------------------------

    def test_tdee_multipliers(self, planner):
        """Check each activity multiplier."""
        expected = {
            "sedentary": 1.2,
            "lightly_active": 1.375,
            "moderately_active": 1.55,
            "very_active": 1.725,
            "extremely_active": 1.9,
        }
        for level, factor in expected.items():
            assert planner.calculate_tdee(1000, level) == pytest.approx(1000 * factor)

    def test_tdee_unknown_activity_defaults(self, planner):
        """Unknown activity level defaults to lightly_active factor."""
        assert planner.calculate_tdee(1000, "unknown") == pytest.approx(1375.0)

    # ------------------------------------------------------------------
    # Weight trend adjustment
    # ------------------------------------------------------------------

    def test_weight_trend_reduce_calories(self, planner):
        """Weight well above target → -200 kcal adjustment."""
        adj = planner.get_weight_trend_adjustment([80, 81, 80.5], target_weight=75.0)
        assert adj == -200

    def test_weight_trend_increase_calories(self, planner):
        """Weight well below target → +200 kcal adjustment."""
        adj = planner.get_weight_trend_adjustment([65, 64.5, 64], target_weight=70.0)
        assert adj == 200

    def test_weight_trend_no_adjustment(self, planner):
        """Weight near target → 0 adjustment."""
        adj = planner.get_weight_trend_adjustment(
            [70.0, 70.2, 70.1], target_weight=70.0
        )
        assert adj == 0

    def test_weight_trend_insufficient_data(self, planner):
        """Fewer than 3 data points → 0 adjustment."""
        adj = planner.get_weight_trend_adjustment([70.0, 70.5], target_weight=70.0)
        assert adj == 0

    # ------------------------------------------------------------------
    # Macro targets
    # ------------------------------------------------------------------

    def test_macro_targets_sum_to_kcal(self, planner, test_user_profile):
        """Computed macro calories should approximately equal target_kcal."""
        macros = planner.calculate_macro_targets(2000, test_user_profile)
        total_kcal = (
            macros["protein_g"] * 4 + macros["carbs_g"] * 4 + macros["fat_g"] * 9
        )
        assert abs(total_kcal - 2000) < 5  # within 5 kcal rounding

    def test_macro_targets_proportions(self, planner, test_user_profile):
        """Verify each macro's calorie share matches profile percentages."""
        test_user_profile.protein_percent = 30
        test_user_profile.carbs_percent = 40
        test_user_profile.fat_percent = 30
        macros = planner.calculate_macro_targets(2000, test_user_profile)
        assert abs(macros["protein_g"] - 150.0) < 1
        assert abs(macros["carbs_g"] - 200.0) < 1
        assert abs(macros["fat_g"] - (2000 * 0.30 / 9)) < 1

    # ------------------------------------------------------------------
    # Daily plan generation
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_generate_daily_plan_defaults(self, planner, test_user_profile):
        """Generated plan should have sane defaults and respect the BMR floor."""
        plan = await planner.generate_daily_plan(
            user_id="test_user",
            profile=test_user_profile,
            recent_metrics=[],
        )
        assert plan.user_id == "test_user"
        assert plan.target_kcal > 0
        assert plan.target_protein_g > 0
        assert plan.target_carbs_g > 0
        assert plan.target_fat_g > 0
        # Never go below BMR
        bmr = planner.calculate_bmr(test_user_profile)
        assert plan.target_kcal >= int(bmr)

    @pytest.mark.asyncio
    async def test_generate_daily_plan_lose_weight_deficit(
        self, planner, test_user_profile
    ):
        """Lose-weight goal applies a calorie deficit."""
        test_user_profile.goal = "lose_weight"
        plan = await planner.generate_daily_plan(
            user_id="test_user",
            profile=test_user_profile,
            recent_metrics=[],
        )
        tdee = planner.calculate_tdee(
            planner.calculate_bmr(test_user_profile),
            test_user_profile.activity_level,
        )
        assert plan.target_kcal < tdee

    @pytest.mark.asyncio
    async def test_generate_daily_plan_with_weight_trend(
        self, planner, test_user_profile
    ):
        """Weight trend adjustment is applied in the plan."""
        base = datetime.now()
        # Weights clearly above the 70 kg target → negative adjustment
        weights = [80.0, 80.5, 81.0]
        metrics = [
            HealthMetric(
                timestamp=base,
                user_id="test_user",
                weight=w,
                source="test",
            )
            for w in weights
        ]
        plan_no_trend = await planner.generate_daily_plan(
            "test_user", test_user_profile, []
        )
        plan_with_trend = await planner.generate_daily_plan(
            "test_user", test_user_profile, metrics
        )
        # Weight is well above 70 kg target → negative (-200) adjustment applied
        assert plan_with_trend.target_kcal <= plan_no_trend.target_kcal

    # ------------------------------------------------------------------
    # Progress analysis
    # ------------------------------------------------------------------

    def test_analyze_progress_no_metrics(self, planner, test_user_profile):
        """Returns error dict when no metrics provided."""
        result = planner.analyze_progress(test_user_profile, [])
        assert "error" in result

    def test_analyze_progress_with_metrics(self, planner, test_user_profile):
        """Returns aggregated summary with metrics."""
        metrics = [
            HealthMetric(
                timestamp=datetime.now(),
                user_id="test_user",
                kcal_in=2000,
                steps=8000,
                protein_g=100,
                weight=72.0,
                source="test",
            )
        ]
        result = planner.analyze_progress(test_user_profile, metrics)
        assert result["avg_kcal_in"] == 2000
        assert result["avg_steps"] == 8000
        assert result["avg_protein_g"] == 100.0
