"""
Test fixtures and configuration.
"""

import pytest
import tempfile
import os
from datetime import datetime
from typing import Generator

from src.macrocoach.core.context import ApplicationContext
from src.macrocoach.core.models import UserProfile, HealthMetric
from src.macrocoach.agents.state_store_agent import StateStoreAgent


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    yield f"sqlite:///{db_path}"
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def test_context(temp_db: str) -> ApplicationContext:
    """Create a test application context."""
    context = ApplicationContext()
    context.database_url = temp_db
    context.openai_api_key = "test_key"
    context.debug = True
    return context


@pytest.fixture
def test_user_profile() -> UserProfile:
    """Create a test user profile."""
    return UserProfile(
        user_id="test_user",
        age=25,
        gender="male",
        height_cm=175.0,
        activity_level="moderately_active",
        goal="lose_weight",
        target_weight_kg=70.0,
        protein_percent=30.0,
        carbs_percent=40.0,
        fat_percent=30.0,
        prefer_turkish_cuisine=True
    )


@pytest.fixture
def test_health_metric() -> HealthMetric:
    """Create a test health metric."""
    return HealthMetric(
        timestamp=datetime.now(),
        user_id="test_user",
        kcal_out=2200.0,
        heart_rate=75,
        steps=8500,
        weight=72.5,
        protein_g=120.0,
        carbs_g=250.0,
        fat_g=80.0,
        kcal_in=2000.0,
        source="test"
    )


@pytest.fixture
def state_store(test_context: ApplicationContext) -> StateStoreAgent:
    """Create a test state store."""
    store = StateStoreAgent(test_context)
    return store
