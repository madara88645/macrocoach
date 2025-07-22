"""
Demo data seeder for MacroCoach.
Creates sample users and health metrics for testing/demo purposes.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import random

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from macrocoach.core.context import ApplicationContext
from macrocoach.core.models import UserProfile, HealthMetric, WorkoutType
from macrocoach.agents.state_store_agent import StateStoreAgent
from macrocoach.agents.planner_agent import PlannerAgent


async def seed_demo_data():
    """Seed the database with demo data."""
    
    print("🌱 Seeding demo data for MacroCoach...")
    
    # Initialize context and agents
    context = ApplicationContext()
    state_store = StateStoreAgent(context)
    planner = PlannerAgent(context)
    
    await state_store.initialize()
    
    # Create demo users
    demo_users = [
        UserProfile(
            user_id="demo_user",
            age=28,
            gender="male",
            height_cm=175.0,
            activity_level="moderately_active",
            goal="lose_weight",
            target_weight_kg=75.0,
            protein_percent=35.0,
            carbs_percent=40.0,
            fat_percent=25.0,
            dietary_restrictions=[],
            allergies=[],
            prefer_turkish_cuisine=True
        ),
        UserProfile(
            user_id="fitness_enthusiast",
            age=25,
            gender="female",
            height_cm=165.0,
            activity_level="very_active",
            goal="gain_muscle",
            target_weight_kg=60.0,
            protein_percent=40.0,
            carbs_percent=35.0,
            fat_percent=25.0,
            dietary_restrictions=["vegetarian"],
            allergies=["nuts"],
            prefer_turkish_cuisine=False
        )
    ]
    
    # Store user profiles
    for user in demo_users:
        await state_store.store_user_profile(user)
        print(f"✅ Created user: {user.user_id}")
    
    # Generate 14 days of health metrics for each user
    for user in demo_users:
        print(f"📊 Generating metrics for {user.user_id}...")
        
        base_date = datetime.now() - timedelta(days=14)
        current_weight = (user.target_weight_kg or 70.0) + random.uniform(-3, 3)
        
        for day in range(14):
            date = base_date + timedelta(days=day)
            
            # Simulate gradual weight change toward goal
            if user.goal == "lose_weight":
                weight_change = -0.1 + random.uniform(-0.2, 0.1)
            elif user.goal == "gain_weight" or user.goal == "gain_muscle":
                weight_change = 0.1 + random.uniform(-0.1, 0.2)
            else:
                weight_change = random.uniform(-0.15, 0.15)
            
            current_weight += weight_change
            current_weight = max(40.0, min(120.0, current_weight))  # Reasonable bounds
            
            # Daily activity metrics
            base_steps = 7000 if user.activity_level == "sedentary" else 10000
            if user.activity_level == "very_active":
                base_steps = 14000
            
            daily_steps = base_steps + random.randint(-2000, 3000)
            daily_steps = max(2000, daily_steps)
            
            # Caloric intake (varies around target)
            bmr = planner.calculate_bmr(user, current_weight)
            tdee = planner.calculate_tdee(bmr, user.activity_level)
            
            if user.goal == "lose_weight":
                target_calories = tdee - 300
            elif user.goal in ["gain_weight", "gain_muscle"]:
                target_calories = tdee + 300
            else:
                target_calories = tdee
            
            daily_calories = target_calories + random.uniform(-200, 200)
            daily_calories = max(1200, daily_calories)
            
            # Macro distribution
            protein_calories = daily_calories * (user.protein_percent / 100)
            carbs_calories = daily_calories * (user.carbs_percent / 100)
            fat_calories = daily_calories * (user.fat_percent / 100)
            
            protein_g = protein_calories / 4
            carbs_g = carbs_calories / 4
            fat_g = fat_calories / 9
            
            # Create daily summary metric
            daily_metric = HealthMetric(
                timestamp=date.replace(hour=12, minute=0, second=0),
                user_id=user.user_id,
                source="demo",
                confidence=0.9,
                
                # Body metrics
                weight=round(current_weight, 1),
                
                # Activity
                steps=daily_steps,
                kcal_out=int(tdee + random.uniform(-100, 100)),
                heart_rate=random.randint(60, 80),  # Resting HR
                sleep_score=random.randint(65, 95),
                
                # Nutrition
                kcal_in=round(daily_calories),
                protein_g=round(protein_g, 1),
                carbs_g=round(carbs_g, 1),
                fat_g=round(fat_g, 1)
            )
            
            await state_store.store_health_metric(daily_metric)
            
            # Add workout data (60% chance for active users, 30% for others)
            workout_chance = 0.6 if user.activity_level in ["very_active", "extremely_active"] else 0.3
            
            if random.random() < workout_chance:
                if user.goal == "gain_muscle":
                    workout_types = [WorkoutType.STRENGTH, WorkoutType.STRENGTH, WorkoutType.CARDIO]
                elif user.goal == "lose_weight":
                    workout_types = [WorkoutType.CARDIO, WorkoutType.CARDIO, WorkoutType.STRENGTH]
                else:
                    workout_types = [WorkoutType.WALKING, WorkoutType.CARDIO, WorkoutType.STRENGTH]
                
                workout_metric = HealthMetric(
                    timestamp=date.replace(hour=18, minute=0, second=0),
                    user_id=user.user_id,
                    source="demo",
                    confidence=0.95,
                    
                    workout_type=random.choice(workout_types),
                    workout_duration_minutes=random.randint(30, 90),
                    heart_rate=random.randint(120, 170),  # Exercise HR
                    kcal_out=random.randint(200, 600),
                    rpe=random.randint(4, 9)
                )
                
                await state_store.store_health_metric(workout_metric)
            
            # Occasionally add meal-specific entries
            if random.random() < 0.4:  # 40% chance of detailed meal logging
                meals = ["breakfast", "lunch", "dinner"]
                meal_calories = [0.25, 0.35, 0.40]
                
                for meal, ratio in zip(meals, meal_calories):
                    hour = {"breakfast": 8, "lunch": 13, "dinner": 19}[meal]
                    
                    meal_metric = HealthMetric(
                        timestamp=date.replace(hour=hour, minute=0, second=0),
                        user_id=user.user_id,
                        source=f"demo_{meal}",
                        confidence=0.8,
                        
                        kcal_in=round(daily_calories * ratio),
                        protein_g=round(protein_g * ratio, 1),
                        carbs_g=round(carbs_g * ratio, 1),
                        fat_g=round(fat_g * ratio, 1)
                    )
                    
                    await state_store.store_health_metric(meal_metric)
        
        print(f"✅ Generated 14 days of data for {user.user_id}")
    
    # Generate some daily plans
    print("📅 Generating sample daily plans...")
    
    for user in demo_users:
        recent_metrics = await state_store.get_health_metrics(
            user.user_id,
            start_date=datetime.now() - timedelta(days=7),
            limit=50
        )
        
        # Generate plan for tomorrow
        tomorrow = datetime.now() + timedelta(days=1)
        plan = await planner.generate_daily_plan(user.user_id, user, recent_metrics, tomorrow)
        
        await state_store.store_daily_plan(plan)
        print(f"✅ Generated plan for {user.user_id}")
    
    await state_store.close()
    print("🎉 Demo data seeding completed!")


def create_sample_chat_history():
    """Create some sample chat interactions."""
    # This would create sample chat messages
    # Left as an exercise for more realistic demo data
    pass


if __name__ == "__main__":
    asyncio.run(seed_demo_data())
