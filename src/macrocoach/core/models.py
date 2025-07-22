"""
Data models and schemas for the application.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class WorkoutType(str, Enum):
    """Supported workout types."""
    STRENGTH = "strength"
    CARDIO = "cardio"
    YOGA = "yoga"
    WALKING = "walking"
    RUNNING = "running"
    CYCLING = "cycling"
    SWIMMING = "swimming"
    OTHER = "other"


class HealthMetric(BaseModel):
    """
    Normalized health metrics schema.
    All agents work with this unified format.
    """
    timestamp: datetime
    user_id: str
    
    # Energy and activity
    kcal_out: Optional[float] = Field(None, description="Calories burned")
    heart_rate: Optional[int] = Field(None, description="Heart rate in BPM")
    steps: Optional[int] = Field(None, description="Daily step count")
    sleep_score: Optional[int] = Field(None, description="Sleep quality score 0-100")
    
    # Body metrics
    weight: Optional[float] = Field(None, description="Weight in kg")
    
    # Nutrition
    protein_g: Optional[float] = Field(None, description="Protein intake in grams")
    carbs_g: Optional[float] = Field(None, description="Carbohydrate intake in grams")
    fat_g: Optional[float] = Field(None, description="Fat intake in grams")
    kcal_in: Optional[float] = Field(None, description="Calories consumed")
    
    # Workout
    workout_type: Optional[WorkoutType] = Field(None, description="Type of workout performed")
    rpe: Optional[int] = Field(None, description="Rate of Perceived Exertion 1-10")
    workout_duration_minutes: Optional[int] = Field(None, description="Workout duration")
    
    # Metadata
    source: Optional[str] = Field(None, description="Data source (healthkit, health_connect, manual, etc.)")
    confidence: Optional[float] = Field(1.0, description="Data confidence 0-1")
    
    class Config:
        """Pydantic config."""
        use_enum_values = True


class UserProfile(BaseModel):
    """User profile and preferences."""
    user_id: str
    age: int
    gender: str  # "male", "female", "other"
    height_cm: float
    activity_level: str  # "sedentary", "lightly_active", "moderately_active", "very_active", "extremely_active"
    goal: str  # "lose_weight", "maintain_weight", "gain_weight", "gain_muscle"
    
    # Goal specifics
    target_weight_kg: Optional[float] = None
    target_kcal_deficit: Optional[int] = None  # negative for surplus
    
    # Macro preferences (percentages)
    protein_percent: float = 30.0
    carbs_percent: float = 40.0
    fat_percent: float = 30.0
    
    # Dietary restrictions
    dietary_restrictions: List[str] = Field(default_factory=list)  # ["vegetarian", "gluten_free", etc.]
    allergies: List[str] = Field(default_factory=list)
    
    # Turkish pantry preference
    prefer_turkish_cuisine: bool = True
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class DailyPlan(BaseModel):
    """Generated daily nutrition and activity plan."""
    user_id: str
    date: datetime
    
    # Calorie targets
    target_kcal: int
    target_protein_g: float
    target_carbs_g: float
    target_fat_g: float
    
    # Activity targets
    target_steps: int = 10000
    target_workout_minutes: int = 30
    
    # Meals
    suggested_meals: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Reasoning
    plan_reasoning: str = ""
    adjustments_made: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.now)


class Meal(BaseModel):
    """Individual meal suggestion."""
    meal_id: str
    name: str
    meal_type: str  # "breakfast", "lunch", "dinner", "snack"
    
    # Nutrition
    kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: Optional[float] = None
    
    # Recipe
    ingredients: List[Dict[str, Any]]  # [{"name": "bulgur", "amount": 100, "unit": "g"}]
    instructions: List[str]
    prep_time_minutes: int
    cook_time_minutes: int
    servings: int = 1
    
    # Tags
    tags: List[str] = Field(default_factory=list)  # ["turkish", "vegetarian", "quick"]
    difficulty: str = "easy"  # "easy", "medium", "hard"
    
    # Cost estimate (optional)
    estimated_cost_try: Optional[float] = None


class ChatMessage(BaseModel):
    """Chat message between user and system."""
    user_id: str
    message: str
    response: str
    timestamp: datetime = Field(default_factory=datetime.now)
    command_type: Optional[str] = None  # "status", "plan", "swap", etc.
    context_data: Dict[str, Any] = Field(default_factory=dict)
