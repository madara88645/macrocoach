"""
StateStoreAgent - Normalizes and persists health metrics to local SQLite DB.
"""

import json
from datetime import datetime, timedelta
from typing import Any

from ..core.context import ApplicationContext
from ..core.models import ChatMessage, DailyPlan, HealthMetric, UserProfile


class StateStoreAgent:
    """
    Manages data persistence and normalization.
    All health metrics are stored in a unified schema.
    """

    def __init__(self, context: ApplicationContext):
        self.context = context
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize database schema if not exists."""
        if self._initialized:
            return

        conn = self.context.get_db_connection()

        # Create tables
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS health_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_id TEXT NOT NULL,
                kcal_out REAL,
                heart_rate INTEGER,
                steps INTEGER,
                sleep_score INTEGER,
                weight REAL,
                protein_g REAL,
                carbs_g REAL,
                fat_g REAL,
                kcal_in REAL,
                workout_type TEXT,
                rpe INTEGER,
                workout_duration_minutes INTEGER,
                source TEXT,
                confidence REAL DEFAULT 1.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                age INTEGER NOT NULL,
                gender TEXT NOT NULL,
                height_cm REAL NOT NULL,
                activity_level TEXT NOT NULL,
                goal TEXT NOT NULL,
                target_weight_kg REAL,
                target_kcal_deficit INTEGER,
                protein_percent REAL DEFAULT 30.0,
                carbs_percent REAL DEFAULT 40.0,
                fat_percent REAL DEFAULT 30.0,
                dietary_restrictions TEXT, -- JSON array
                allergies TEXT, -- JSON array
                prefer_turkish_cuisine INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS daily_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                date TEXT NOT NULL,
                target_kcal INTEGER NOT NULL,
                target_protein_g REAL NOT NULL,
                target_carbs_g REAL NOT NULL,
                target_fat_g REAL NOT NULL,
                target_steps INTEGER DEFAULT 10000,
                target_workout_minutes INTEGER DEFAULT 30,
                suggested_meals TEXT, -- JSON array
                plan_reasoning TEXT,
                adjustments_made TEXT, -- JSON array
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, date)
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                command_type TEXT,
                context_data TEXT -- JSON
            );

            CREATE INDEX IF NOT EXISTS idx_health_metrics_user_timestamp
                ON health_metrics(user_id, timestamp);
            CREATE INDEX IF NOT EXISTS idx_daily_plans_user_date
                ON daily_plans(user_id, date);
            CREATE INDEX IF NOT EXISTS idx_chat_messages_user_timestamp
                ON chat_messages(user_id, timestamp);
        """)

        conn.commit()
        self._initialized = True

    async def store_health_metric(self, metric: HealthMetric) -> None:
        """Store a normalized health metric."""
        conn = self.context.get_db_connection()

        conn.execute(
            """
            INSERT INTO health_metrics (
                timestamp, user_id, kcal_out, heart_rate, steps, sleep_score,
                weight, protein_g, carbs_g, fat_g, kcal_in, workout_type,
                rpe, workout_duration_minutes, source, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                metric.timestamp.isoformat(),
                metric.user_id,
                metric.kcal_out,
                metric.heart_rate,
                metric.steps,
                metric.sleep_score,
                metric.weight,
                metric.protein_g,
                metric.carbs_g,
                metric.fat_g,
                metric.kcal_in,
                metric.workout_type,
                metric.rpe,
                metric.workout_duration_minutes,
                metric.source,
                metric.confidence,
            ),
        )

        conn.commit()

    async def get_health_metrics(
        self,
        user_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> list[HealthMetric]:
        """Retrieve health metrics for a user within date range."""
        conn = self.context.get_db_connection()

        query = "SELECT * FROM health_metrics WHERE user_id = ?"
        params = [user_id]

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()

        metrics = []
        for row in rows:
            metrics.append(
                HealthMetric(
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    user_id=row["user_id"],
                    kcal_out=row["kcal_out"],
                    heart_rate=row["heart_rate"],
                    steps=row["steps"],
                    sleep_score=row["sleep_score"],
                    weight=row["weight"],
                    protein_g=row["protein_g"],
                    carbs_g=row["carbs_g"],
                    fat_g=row["fat_g"],
                    kcal_in=row["kcal_in"],
                    workout_type=row["workout_type"],
                    rpe=row["rpe"],
                    workout_duration_minutes=row["workout_duration_minutes"],
                    source=row["source"],
                    confidence=row["confidence"],
                )
            )

        return metrics

    async def get_daily_summary(self, user_id: str, date: datetime) -> dict[str, Any]:
        """Get aggregated metrics for a specific day."""
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        # Use the last microsecond of the day to avoid bleeding into the next day.
        end_of_day = start_of_day + timedelta(days=1) - timedelta(microseconds=1)

        metrics = await self.get_health_metrics(user_id, start_of_day, end_of_day)

        if not metrics:
            return {"date": date.date(), "total_metrics": 0}

        # Aggregate metrics
        total_kcal_in = sum(m.kcal_in or 0 for m in metrics)
        total_kcal_out = sum(m.kcal_out or 0 for m in metrics)
        total_protein = sum(m.protein_g or 0 for m in metrics)
        total_carbs = sum(m.carbs_g or 0 for m in metrics)
        total_fat = sum(m.fat_g or 0 for m in metrics)

        # Get latest values for cumulative metrics
        latest_steps = max((m.steps or 0 for m in metrics), default=0)
        latest_weight = next((m.weight for m in metrics if m.weight), None)

        return {
            "date": date.date(),
            "total_metrics": len(metrics),
            "kcal_in": total_kcal_in,
            "kcal_out": total_kcal_out,
            "kcal_balance": total_kcal_in - total_kcal_out,
            "protein_g": total_protein,
            "carbs_g": total_carbs,
            "fat_g": total_fat,
            "steps": latest_steps,
            "weight": latest_weight,
            "workouts": [m for m in metrics if m.workout_type],
        }

    async def store_user_profile(self, profile: UserProfile) -> None:
        """Store or update user profile."""
        conn = self.context.get_db_connection()

        conn.execute(
            """
            INSERT OR REPLACE INTO user_profiles (
                user_id, age, gender, height_cm, activity_level, goal,
                target_weight_kg, target_kcal_deficit, protein_percent,
                carbs_percent, fat_percent, dietary_restrictions, allergies,
                prefer_turkish_cuisine, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                profile.user_id,
                profile.age,
                profile.gender,
                profile.height_cm,
                profile.activity_level,
                profile.goal,
                profile.target_weight_kg,
                profile.target_kcal_deficit,
                profile.protein_percent,
                profile.carbs_percent,
                profile.fat_percent,
                json.dumps(profile.dietary_restrictions),
                json.dumps(profile.allergies),
                1 if profile.prefer_turkish_cuisine else 0,
                datetime.now().isoformat(),
            ),
        )

        conn.commit()

    async def get_user_profile(self, user_id: str) -> UserProfile | None:
        """Retrieve user profile."""
        conn = self.context.get_db_connection()

        cursor = conn.execute(
            "SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)
        )
        row = cursor.fetchone()

        if not row:
            return None

        return UserProfile(
            user_id=row["user_id"],
            age=row["age"],
            gender=row["gender"],
            height_cm=row["height_cm"],
            activity_level=row["activity_level"],
            goal=row["goal"],
            target_weight_kg=row["target_weight_kg"],
            target_kcal_deficit=row["target_kcal_deficit"],
            protein_percent=row["protein_percent"],
            carbs_percent=row["carbs_percent"],
            fat_percent=row["fat_percent"],
            dietary_restrictions=json.loads(row["dietary_restrictions"] or "[]"),
            allergies=json.loads(row["allergies"] or "[]"),
            prefer_turkish_cuisine=bool(row["prefer_turkish_cuisine"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    async def store_daily_plan(self, plan: DailyPlan) -> None:
        """Store daily nutrition plan."""
        conn = self.context.get_db_connection()

        conn.execute(
            """
            INSERT OR REPLACE INTO daily_plans (
                user_id, date, target_kcal, target_protein_g, target_carbs_g,
                target_fat_g, target_steps, target_workout_minutes,
                suggested_meals, plan_reasoning, adjustments_made
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                plan.user_id,
                plan.date.date().isoformat(),
                plan.target_kcal,
                plan.target_protein_g,
                plan.target_carbs_g,
                plan.target_fat_g,
                plan.target_steps,
                plan.target_workout_minutes,
                json.dumps(
                    [
                        meal.model_dump() if hasattr(meal, "model_dump") else meal
                        for meal in plan.suggested_meals
                    ]
                ),
                plan.plan_reasoning,
                json.dumps(plan.adjustments_made),
            ),
        )

        conn.commit()

    async def store_chat_message(self, message: ChatMessage) -> None:
        """Store chat interaction."""
        conn = self.context.get_db_connection()

        conn.execute(
            """
            INSERT INTO chat_messages (
                user_id, message, response, timestamp, command_type, context_data
            ) VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                message.user_id,
                message.message,
                message.response,
                message.timestamp.isoformat(),
                message.command_type,
                json.dumps(message.context_data),
            ),
        )

        conn.commit()

    async def close(self) -> None:
        """Close database connection."""
        self.context.close_db_connection()
