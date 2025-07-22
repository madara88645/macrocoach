"""
ChatUIAgent - Exposes conversational endpoint for user interactions.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from ..core.context import ApplicationContext
from ..core.models import ChatMessage, UserProfile, HealthMetric, WorkoutType
from .state_store_agent import StateStoreAgent
from .planner_agent import PlannerAgent
from .meal_gen_agent import MealGenAgent


class ChatUIAgent:
    """
    Handles conversational interface and command processing.
    
    Supported commands:
    - /status: Get daily summary
    - /plan: Get tomorrow's plan  
    - /swap <meal_id>: Generate new meal
    - /add <metric>: Add health data
    - /profile: Update user profile
    """
    
    def __init__(
        self, 
        context: ApplicationContext,
        state_store: StateStoreAgent,
        planner: PlannerAgent,
        meal_gen: MealGenAgent
    ):
        self.context = context
        self.state_store = state_store
        self.planner = planner
        self.meal_gen = meal_gen
    
    async def process_message(self, message: str, user_id: str) -> str:
        """
        Process user message and return appropriate response.
        
        Args:
            message: User input message
            user_id: User identifier
        """
        message = message.strip()
        command_type = None
        context_data = {}
        
        try:
            # Parse command
            if message.startswith("/"):
                response = await self._handle_command(message, user_id)
                command_type = message.split()[0][1:]  # Remove '/' prefix
            else:
                response = await self._handle_natural_language(message, user_id)
                command_type = "chat"
            
            # Store chat interaction
            chat_message = ChatMessage(
                user_id=user_id,
                message=message,
                response=response,
                command_type=command_type,
                context_data=context_data
            )
            await self.state_store.store_chat_message(chat_message)
            
            return response
            
        except Exception as e:
            error_response = f"Sorry, I encountered an error: {str(e)}"
            
            # Still log the error interaction
            try:
                chat_message = ChatMessage(
                    user_id=user_id,
                    message=message,
                    response=error_response,
                    command_type="error",
                    context_data={"error": str(e)}
                )
                await self.state_store.store_chat_message(chat_message)
            except:
                pass  # Don't let logging errors break the response
            
            return error_response
    
    async def _handle_command(self, message: str, user_id: str) -> str:
        """Handle slash commands."""
        parts = message.split()
        command = parts[0][1:].lower()  # Remove '/' and lowercase
        
        if command == "status":
            return await self._handle_status_command(user_id)
        
        elif command == "plan":
            return await self._handle_plan_command(user_id)
        
        elif command == "swap" and len(parts) > 1:
            meal_id = parts[1]
            return await self._handle_swap_command(user_id, meal_id)
        
        elif command == "add":
            return await self._handle_add_command(user_id, " ".join(parts[1:]))
        
        elif command == "profile":
            return await self._handle_profile_command(user_id, " ".join(parts[1:]))
        
        elif command == "help":
            return self._get_help_text()
        
        else:
            return f"Unknown command: {command}. Type /help for available commands."
    
    async def _handle_status_command(self, user_id: str) -> str:
        """Handle /status command - show daily summary."""
        today = datetime.now()
        
        # Get today's summary
        summary = await self.state_store.get_daily_summary(user_id, today)
        
        if summary["total_metrics"] == 0:
            return "📊 No data logged for today yet. Use /add to log your first metrics!"
        
        # Get user profile for targets
        profile = await self.state_store.get_user_profile(user_id)
        
        # Format response
        response_parts = [
            f"📊 **Daily Status - {today.strftime('%B %d, %Y')}**\n",
            f"🔥 **Calories:** {summary['kcal_in']:.0f} in / {summary['kcal_out']:.0f} out",
            f"📈 **Balance:** {summary['kcal_balance']:+.0f} kcal\n",
            f"🥩 **Protein:** {summary['protein_g']:.1f}g",
            f"🍞 **Carbs:** {summary['carbs_g']:.1f}g", 
            f"🥑 **Fat:** {summary['fat_g']:.1f}g\n",
            f"👟 **Steps:** {summary['steps']:,}",
        ]
        
        if summary['weight']:
            response_parts.append(f"⚖️ **Weight:** {summary['weight']:.1f} kg")
        
        if summary['workouts']:
            workout_count = len(summary['workouts'])
            response_parts.append(f"💪 **Workouts:** {workout_count} completed")
        
        # Add progress insights if profile exists
        if profile:
            recent_metrics = await self.state_store.get_health_metrics(
                user_id, 
                start_date=today - timedelta(days=7),
                limit=50
            )
            
            if recent_metrics:
                progress = self.planner.analyze_progress(profile, recent_metrics)
                response_parts.extend([
                    "\n📈 **7-Day Progress:**",
                    f"• Weight trend: {progress['weight_trend']}",
                    f"• Avg calories: {progress['avg_kcal_in']}/day",
                    f"• Avg steps: {progress['avg_steps']:,.0f}/day",
                    f"• Workout days: {progress['workout_days']}/{progress['total_days']}"
                ])
        
        response_parts.append(f"\n💬 Type /plan for tomorrow's recommendations!")
        
        return "\n".join(response_parts)
    
    async def _handle_plan_command(self, user_id: str) -> str:
        """Handle /plan command - generate tomorrow's plan."""
        
        # Get user profile
        profile = await self.state_store.get_user_profile(user_id)
        if not profile:
            return ("🏃‍♂️ I need your profile first! Please tell me:\n"
                   "- Age, gender, height, weight\n"
                   "- Activity level (sedentary/lightly_active/moderately_active/very_active)\n"
                   "- Goal (lose_weight/maintain_weight/gain_weight/gain_muscle)\n\n"
                   "Example: 'I am 25 years old, male, 175cm, moderately active, want to lose weight'")
        
        # Get recent metrics for trend analysis
        recent_metrics = await self.state_store.get_health_metrics(
            user_id,
            start_date=datetime.now() - timedelta(days=14),
            limit=50
        )
        
        # Generate plan
        tomorrow = datetime.now() + timedelta(days=1)
        plan = await self.planner.generate_daily_plan(user_id, profile, recent_metrics, tomorrow)
        
        # Generate meals
        meals = await self.meal_gen.generate_meals_for_plan(plan, profile)
        plan.suggested_meals = meals
        
        # Store the plan
        await self.state_store.store_daily_plan(plan)
        
        # Format response
        response_parts = [
            f"📅 **Plan for {tomorrow.strftime('%B %d, %Y')}**\n",
            f"🎯 **Daily Targets:**",
            f"• Calories: {plan.target_kcal} kcal",
            f"• Protein: {plan.target_protein_g:.0f}g",
            f"• Carbs: {plan.target_carbs_g:.0f}g",
            f"• Fat: {plan.target_fat_g:.0f}g",
            f"• Steps: {plan.target_steps:,}",
            f"• Workout: {plan.target_workout_minutes} minutes\n",
            f"🍽️ **Suggested Meals:**"
        ]
        
        for i, meal in enumerate(meals[:3], 1):  # Show first 3 meals
            meal_obj = meal if hasattr(meal, 'name') else type('obj', (object,), meal)()
            response_parts.extend([
                f"\n**{i}. {meal_obj.name}** ({meal_obj.meal_type})",
                f"   • {meal_obj.kcal} kcal, {meal_obj.protein_g:.0f}g protein",
                f"   • Prep: {meal_obj.prep_time_minutes}min | Cook: {meal_obj.cook_time_minutes}min",
                f"   • ID: `{meal_obj.meal_id}`"
            ])
        
        response_parts.extend([
            f"\n🧠 **Plan Reasoning:**",
            f"{plan.plan_reasoning}",
            f"\n💡 Use /swap <meal_id> to replace any meal!"
        ])
        
        return "\n".join(response_parts)
    
    async def _handle_swap_command(self, user_id: str, meal_id: str) -> str:
        """Handle /swap command - replace a meal."""
        
        # Get user profile and recent plan
        profile = await self.state_store.get_user_profile(user_id)
        if not profile:
            return "❌ Please set up your profile first with /profile"
        
        # This is simplified - in a real app, you'd retrieve the actual plan
        # For now, create a dummy plan
        from ..core.models import DailyPlan
        dummy_plan = DailyPlan(
            user_id=user_id,
            date=datetime.now() + timedelta(days=1),
            target_kcal=2000,
            target_protein_g=150,
            target_carbs_g=200,
            target_fat_g=80,
            suggested_meals=[
                {"meal_id": meal_id, "name": "Original Meal", "meal_type": "lunch", 
                 "kcal": 600, "protein_g": 35, "carbs_g": 50, "fat_g": 20}
            ]
        )
        
        # Generate new meal
        new_meal = await self.meal_gen.swap_meal(meal_id, dummy_plan, profile)
        
        if not new_meal:
            return f"❌ Couldn't find meal with ID: {meal_id}"
        
        return (f"✅ **Meal Swapped Successfully!**\n\n"
               f"🆕 **New Meal:** {new_meal.name}\n"
               f"📊 **Nutrition:** {new_meal.kcal} kcal, {new_meal.protein_g:.0f}g protein\n"
               f"⏱️ **Time:** {new_meal.prep_time_minutes + new_meal.cook_time_minutes} minutes total\n"
               f"🆔 **New ID:** `{new_meal.meal_id}`\n\n"
               f"**Ingredients:**\n" + 
               "\n".join([f"• {ing['amount']}{ing['unit']} {ing['name']}" 
                         for ing in new_meal.ingredients[:5]]))
    
    async def _handle_add_command(self, user_id: str, data: str) -> str:
        """Handle /add command - add health metrics."""
        
        # Parse the data (simplified parsing for demo)
        metric = HealthMetric(
            timestamp=datetime.now(),
            user_id=user_id,
            source="manual"
        )
        
        # Simple parsing logic
        data_lower = data.lower()
        
        # Extract numbers and keywords
        if "weight" in data_lower or "kg" in data_lower:
            weight_match = re.search(r'(\d+\.?\d*)\s*kg', data_lower)
            if weight_match:
                metric.weight = float(weight_match.group(1))
        
        if "steps" in data_lower:
            steps_match = re.search(r'(\d+)\s*steps', data_lower)
            if steps_match:
                metric.steps = int(steps_match.group(1))
        
        if "calories" in data_lower or "kcal" in data_lower:
            cal_match = re.search(r'(\d+)\s*(calories|kcal)', data_lower)
            if cal_match:
                metric.kcal_in = float(cal_match.group(1))
        
        if "protein" in data_lower:
            protein_match = re.search(r'(\d+\.?\d*)\s*g.*protein', data_lower)
            if protein_match:
                metric.protein_g = float(protein_match.group(1))
        
        if "workout" in data_lower or "exercise" in data_lower:
            if "strength" in data_lower or "weights" in data_lower:
                metric.workout_type = WorkoutType.STRENGTH
            elif "cardio" in data_lower or "running" in data_lower:
                metric.workout_type = WorkoutType.CARDIO
            else:
                metric.workout_type = WorkoutType.OTHER
            
            # Extract RPE
            rpe_match = re.search(r'rpe\s*(\d+)', data_lower)
            if rpe_match:
                metric.rpe = int(rpe_match.group(1))
        
        # Store the metric
        await self.state_store.store_health_metric(metric)
        
        # Generate confirmation
        confirmations = []
        if metric.weight:
            confirmations.append(f"⚖️ Weight: {metric.weight} kg")
        if metric.steps:
            confirmations.append(f"👟 Steps: {metric.steps:,}")
        if metric.kcal_in:
            confirmations.append(f"🍽️ Calories: {metric.kcal_in} kcal")
        if metric.protein_g:
            confirmations.append(f"🥩 Protein: {metric.protein_g}g")
        if metric.workout_type:
            confirmations.append(f"💪 Workout: {metric.workout_type}")
            if metric.rpe:
                confirmations.append(f"🔥 RPE: {metric.rpe}/10")
        
        if confirmations:
            return f"✅ **Logged Successfully:**\n" + "\n".join(confirmations)
        else:
            return ("❌ Couldn't parse your data. Try formats like:\n"
                   "• 'weight 70.5 kg'\n"
                   "• '8500 steps'\n" 
                   "• '500 calories, 30g protein'\n"
                   "• 'strength workout, rpe 7'")
    
    async def _handle_profile_command(self, user_id: str, data: str) -> str:
        """Handle /profile command - update user profile."""
        
        # This is a simplified profile creation
        # In a real app, you'd have a proper profile setup flow
        
        return ("👤 **Profile Setup**\n\n"
               "Please provide your details in this format:\n"
               "`age: 25, gender: male, height: 175cm, activity: moderately_active, goal: lose_weight`\n\n"
               "**Activity levels:**\n"
               "• sedentary\n"
               "• lightly_active\n" 
               "• moderately_active\n"
               "• very_active\n"
               "• extremely_active\n\n"
               "**Goals:**\n"
               "• lose_weight\n"
               "• maintain_weight\n"
               "• gain_weight\n"
               "• gain_muscle")
    
    async def _handle_natural_language(self, message: str, user_id: str) -> str:
        """Handle natural language queries."""
        
        message_lower = message.lower()
        
        # Simple keyword matching for common queries
        if any(word in message_lower for word in ["status", "how am i", "progress", "today"]):
            return await self._handle_status_command(user_id)
        
        elif any(word in message_lower for word in ["plan", "tomorrow", "what should i eat"]):
            return await self._handle_plan_command(user_id)
        
        elif "help" in message_lower:
            return self._get_help_text()
        
        else:
            return ("🤔 I'm not sure how to help with that. Here are some things you can try:\n\n"
                   "• `/status` - See your daily progress\n"
                   "• `/plan` - Get tomorrow's meal plan\n"
                   "• `/add <data>` - Log health metrics\n"
                   "• `/help` - See all commands\n\n"
                   "Or ask me things like 'How am I doing today?' or 'What should I eat tomorrow?'")
    
    def _get_help_text(self) -> str:
        """Return help text with available commands."""
        return (
            "🤖 **MacroCoach Commands**\n\n"
            "**📊 Tracking:**\n"
            "• `/status` - Today's summary and progress\n"
            "• `/add <data>` - Log metrics (weight, steps, food, workouts)\n\n"
            "**🍽️ Planning:**\n"  
            "• `/plan` - Generate tomorrow's meal plan\n"
            "• `/swap <meal_id>` - Replace a suggested meal\n\n"
            "**👤 Profile:**\n"
            "• `/profile` - Set up or update your profile\n\n"
            "**💬 Natural Language:**\n"
            "You can also ask me questions like:\n"
            "• 'How am I doing today?'\n"
            "• 'What should I eat tomorrow?'\n"
            "• 'I weighed 70kg and walked 8000 steps'\n\n"
            "**Example Data Formats:**\n"
            "• Weight: 'weight 70.5 kg'\n"
            "• Steps: '8500 steps'\n"
            "• Food: '500 calories, 30g protein'\n"
            "• Workout: 'strength workout, rpe 7'"
        )
    
    async def get_user_status(self, user_id: str) -> Dict[str, Any]:
        """Get detailed user status for API endpoint."""
        
        today = datetime.now()
        summary = await self.state_store.get_daily_summary(user_id, today)
        profile = await self.state_store.get_user_profile(user_id)
        
        recent_metrics = await self.state_store.get_health_metrics(
            user_id,
            start_date=today - timedelta(days=7),
            limit=50
        )
        
        status = {
            "user_id": user_id,
            "date": today.isoformat(),
            "daily_summary": summary,
            "profile": profile.dict() if profile else None,
            "recent_metrics_count": len(recent_metrics)
        }
        
        if profile and recent_metrics:
            progress = self.planner.analyze_progress(profile, recent_metrics)
            status["progress"] = progress
        
        return status
