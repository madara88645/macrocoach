"""
Tests for StateStoreAgent.
"""

from datetime import datetime, timedelta

import pytest

from src.macrocoach.agents.state_store_agent import StateStoreAgent
from src.macrocoach.core.models import HealthMetric, UserProfile


class TestStateStoreAgent:
    """Test cases for StateStoreAgent."""

    @pytest.mark.asyncio
    async def test_initialization(self, state_store: StateStoreAgent):
        """Test that the state store initializes properly."""
        # Should not raise any exceptions
        await state_store.initialize()

        # Test that tables exist by trying to query them
        conn = state_store.context.get_db_connection()
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            "health_metrics",
            "user_profiles",
            "daily_plans",
            "chat_messages",
        ]
        for table in expected_tables:
            assert table in tables

    @pytest.mark.asyncio
    async def test_store_and_retrieve_health_metric(
        self, state_store: StateStoreAgent, test_health_metric: HealthMetric
    ):
        """Test storing and retrieving health metrics."""
        # Store metric
        await state_store.store_health_metric(test_health_metric)

        # Retrieve metrics
        metrics = await state_store.get_health_metrics("test_user")

        assert len(metrics) == 1
        retrieved_metric = metrics[0]

        assert retrieved_metric.user_id == test_health_metric.user_id
        assert retrieved_metric.steps == test_health_metric.steps
        assert retrieved_metric.weight == test_health_metric.weight
        assert retrieved_metric.source == test_health_metric.source

    @pytest.mark.asyncio
    async def test_store_and_retrieve_user_profile(
        self, state_store: StateStoreAgent, test_user_profile: UserProfile
    ):
        """Test storing and retrieving user profiles."""
        # Store profile
        await state_store.store_user_profile(test_user_profile)

        # Retrieve profile
        retrieved_profile = await state_store.get_user_profile("test_user")

        assert retrieved_profile is not None
        assert retrieved_profile.user_id == test_user_profile.user_id
        assert retrieved_profile.age == test_user_profile.age
        assert retrieved_profile.goal == test_user_profile.goal
        assert (
            retrieved_profile.prefer_turkish_cuisine
            == test_user_profile.prefer_turkish_cuisine
        )

    @pytest.mark.asyncio
    async def test_daily_summary(self, state_store: StateStoreAgent):
        """Test daily summary calculation."""
        today = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)

        # Store multiple metrics for today
        metrics = [
            HealthMetric(
                timestamp=today.replace(hour=8),
                user_id="test_user",
                kcal_in=500.0,
                protein_g=25.0,
                source="breakfast",
            ),
            HealthMetric(
                timestamp=today.replace(hour=12),
                user_id="test_user",
                kcal_in=700.0,
                protein_g=35.0,
                steps=5000,
                source="lunch",
            ),
            HealthMetric(
                timestamp=today.replace(hour=18),
                user_id="test_user",
                kcal_in=600.0,
                protein_g=30.0,
                steps=8500,  # Should be the max
                weight=72.5,
                source="dinner",
            ),
        ]

        for metric in metrics:
            await state_store.store_health_metric(metric)

        # Get daily summary
        summary = await state_store.get_daily_summary("test_user", today)

        assert summary["total_metrics"] == 3
        assert summary["kcal_in"] == 1800.0  # Sum of all meals
        assert summary["protein_g"] == 90.0  # Sum of all protein
        assert summary["steps"] == 8500  # Max steps value
        assert summary["weight"] == 72.5  # Latest weight

    @pytest.mark.asyncio
    async def test_date_range_filtering(self, state_store: StateStoreAgent):
        """Test that date range filtering works correctly."""
        base_date = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)

        # Store metrics across multiple days
        for i in range(5):
            metric = HealthMetric(
                timestamp=base_date - timedelta(days=i),
                user_id="test_user",
                steps=1000 + i * 100,
                source=f"day_{i}",
            )
            await state_store.store_health_metric(metric)

        # Test date range query
        start_date = base_date - timedelta(days=2)
        end_date = base_date

        metrics = await state_store.get_health_metrics(
            "test_user", start_date=start_date, end_date=end_date
        )

        # Should return 3 metrics (days 0, 1, 2)
        assert len(metrics) == 3

        # Test limit
        limited_metrics = await state_store.get_health_metrics("test_user", limit=2)

        assert len(limited_metrics) == 2

    @pytest.mark.asyncio
    async def test_user_isolation(self, state_store: StateStoreAgent):
        """Test that users' data is properly isolated."""
        timestamp = datetime.now()

        # Store metrics for two different users
        metric1 = HealthMetric(
            timestamp=timestamp, user_id="user1", steps=5000, source="test"
        )

        metric2 = HealthMetric(
            timestamp=timestamp, user_id="user2", steps=8000, source="test"
        )

        await state_store.store_health_metric(metric1)
        await state_store.store_health_metric(metric2)

        # Each user should only see their own data
        user1_metrics = await state_store.get_health_metrics("user1")
        user2_metrics = await state_store.get_health_metrics("user2")

        assert len(user1_metrics) == 1
        assert len(user2_metrics) == 1
        assert user1_metrics[0].steps == 5000
        assert user2_metrics[0].steps == 8000
