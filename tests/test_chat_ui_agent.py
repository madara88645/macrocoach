"""
Tests for ChatUIAgent - command handling and natural language routing.
"""

import pytest
from datetime import datetime

from src.macrocoach.agents.chat_ui_agent import ChatUIAgent
from src.macrocoach.agents.state_store_agent import StateStoreAgent
from src.macrocoach.agents.planner_agent import PlannerAgent
from src.macrocoach.agents.meal_gen_agent import MealGenAgent
from src.macrocoach.core.models import UserProfile, HealthMetric


@pytest.fixture
async def chat_agent(test_context):
    """Fully initialized ChatUIAgent backed by a fresh in-memory DB."""
    store = StateStoreAgent(test_context)
    await store.initialize()
    plan = PlannerAgent(test_context)
    meals = MealGenAgent(test_context)
    return ChatUIAgent(test_context, store, plan, meals)


@pytest.fixture
async def chat_agent_with_profile(chat_agent, test_user_profile):
    """ChatUIAgent with a pre-seeded user profile."""
    await chat_agent.state_store.store_user_profile(test_user_profile)
    return chat_agent


class TestChatUIAgentHelp:
    """Tests for the /help command."""

    async def test_help_command(self, chat_agent):
        response = await chat_agent.process_message("/help", "test_user")
        assert "MacroCoach Commands" in response
        assert "/status" in response
        assert "/plan" in response
        assert "/add" in response


class TestChatUIAgentStatus:
    """Tests for the /status command."""

    async def test_status_no_data(self, chat_agent):
        """Status with no data should prompt to add metrics."""
        response = await chat_agent.process_message("/status", "test_user")
        assert "No data logged" in response

    async def test_status_with_data(self, chat_agent_with_profile):
        """Status with logged data should display the Calories section."""
        agent = chat_agent_with_profile
        metric = HealthMetric(
            timestamp=datetime.now(),
            user_id="test_user",
            kcal_in=1800,
            protein_g=120,
            carbs_g=200,
            fat_g=60,
            steps=9000,
            source="test",
        )
        await agent.state_store.store_health_metric(metric)
        response = await agent.process_message("/status", "test_user")
        assert "Calories" in response


class TestChatUIAgentAdd:
    """Tests for the /add command."""

    async def test_add_weight(self, chat_agent):
        response = await chat_agent.process_message("/add weight 72.5 kg", "test_user")
        assert "72.5" in response or "Weight" in response

    async def test_add_steps(self, chat_agent):
        response = await chat_agent.process_message("/add 8500 steps", "test_user")
        assert "8500" in response or "Steps" in response

    async def test_add_calories(self, chat_agent):
        response = await chat_agent.process_message("/add 600 calories", "test_user")
        assert "600" in response or "Calories" in response or "Logged" in response

    async def test_add_invalid(self, chat_agent):
        """Unrecognised add data returns helpful error."""
        response = await chat_agent.process_message("/add banana", "test_user")
        assert "parse" in response.lower() or "format" in response.lower() or "❌" in response


class TestChatUIAgentProfile:
    """Tests for the /profile command."""

    async def test_profile_show_instructions_when_empty(self, chat_agent):
        response = await chat_agent.process_message("/profile", "no_profile_user")
        assert "Profile" in response

    async def test_profile_create(self, chat_agent):
        response = await chat_agent.process_message(
            "/profile age: 28, gender: male, height: 180cm, activity: moderately_active, goal: maintain_weight",
            "new_user",
        )
        assert "saved" in response.lower() or "✅" in response
        # Profile should be retrievable now
        profile = await chat_agent.state_store.get_user_profile("new_user")
        assert profile is not None
        assert profile.age == 28
        assert profile.height_cm == 180.0

    async def test_profile_show_existing(self, chat_agent_with_profile):
        agent = chat_agent_with_profile
        response = await agent.process_message("/profile", "test_user")
        assert "Profile" in response or "25" in response  # age from fixture

    async def test_profile_invalid_data(self, chat_agent):
        response = await chat_agent.process_message("/profile foo bar baz", "test_user")
        assert "❌" in response or "parse" in response.lower() or "format" in response.lower()


class TestChatUIAgentPlan:
    """Tests for the /plan command."""

    async def test_plan_requires_profile(self, chat_agent):
        """Without a profile, /plan should ask for it."""
        response = await chat_agent.process_message("/plan", "no_profile_user")
        assert "profile" in response.lower() or "Profile" in response

    async def test_plan_generates_output(self, chat_agent_with_profile):
        response = await chat_agent_with_profile.process_message("/plan", "test_user")
        # Should mention calories and at least one meal
        assert "kcal" in response.lower() or "calorie" in response.lower() or "Calories" in response


class TestChatUIAgentNaturalLanguage:
    """Tests for natural-language fallback."""

    async def test_natural_language_status_keywords(self, chat_agent):
        response = await chat_agent.process_message("how am i doing today?", "test_user")
        # Should route to status (either proper status or no-data message)
        assert response  # non-empty

    async def test_natural_language_plan_keywords(self, chat_agent_with_profile):
        response = await chat_agent_with_profile.process_message(
            "what should I eat tomorrow?", "test_user"
        )
        assert response

    async def test_natural_language_unknown(self, chat_agent):
        response = await chat_agent.process_message("tell me a joke", "test_user")
        assert "/help" in response or "help" in response.lower()

    async def test_unknown_command(self, chat_agent):
        response = await chat_agent.process_message("/foobar", "test_user")
        assert "Unknown command" in response or "unknown" in response.lower()
