"""
FastAPI main application entry point.
"""

import io
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from PIL import Image  # type: ignore
except ImportError:  # pragma: no cover - pillow optional
    Image = None  # type: ignore
import os

try:
    from dotenv import load_dotenv
except ImportError:
    # dotenv is optional
    def load_dotenv(**kwargs: Any) -> bool:  # type: ignore[misc]
        return False


from .agents.chat_ui_agent import ChatUIAgent
from .agents.meal_gen_agent import MealGenAgent
from .agents.planner_agent import PlannerAgent
from .agents.state_store_agent import StateStoreAgent
from .core.context import ApplicationContext
from .core.models import UserProfile
from .vision import PlateRecognizer

# Load environment variables
load_dotenv()

# Initialize application context and agents
context = ApplicationContext()
state_store = StateStoreAgent(context)
planner = PlannerAgent(context)
meal_gen = MealGenAgent(context)
chat_ui = ChatUIAgent(context, state_store, planner, meal_gen)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize and clean up application resources."""
    await state_store.initialize()
    print("MacroCoach API started successfully!")
    yield
    await state_store.close()
    print("MacroCoach API shut down.")


app = FastAPI(
    title="MacroCoach API",
    description="An open-source coaching service for health metrics and nutrition",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_plate_recognizer() -> PlateRecognizer:
    """Dependency returning a PlateRecognizer instance."""
    return PlateRecognizer(context.openai_api_key)


class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"


class ChatResponse(BaseModel):
    response: str
    status: str = "success"


class ProfileCreateRequest(BaseModel):
    """Request body for profile creation/update (user_id comes from the path)."""

    age: int
    gender: str
    height_cm: float
    activity_level: str
    goal: str
    target_weight_kg: float | None = None
    target_kcal_deficit: int | None = None
    protein_percent: float = 30.0
    carbs_percent: float = 40.0
    fat_percent: float = 30.0
    dietary_restrictions: list[str] = []
    allergies: list[str] = []
    prefer_turkish_cuisine: bool = True


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with basic info."""
    return {
        "message": "Welcome to MacroCoach API v0.1",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Main chat interface for user interactions.

    Supported commands:
    - /status: Get daily summary
    - /plan: Get tomorrow's plan
    - /swap <meal_id>: Generate new meal
    """
    try:
        response = await chat_ui.process_message(request.message, request.user_id)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/profile/{user_id}")
async def create_or_update_profile(
    user_id: str, body: ProfileCreateRequest
) -> dict[str, Any]:
    """Create or update a user profile."""
    try:
        profile = UserProfile(user_id=user_id, **body.model_dump())
        await state_store.store_user_profile(profile)
        return {"status": "ok", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/profile/{user_id}")
async def get_profile(user_id: str) -> dict[str, Any]:
    """Retrieve user profile."""
    try:
        profile = await state_store.get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile.model_dump(mode="json")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/meal-image")
async def meal_image(
    file: UploadFile = File(...),
    recognizer: PlateRecognizer = Depends(get_plate_recognizer),
) -> dict[str, Any]:
    """Estimate macros from an uploaded meal photo."""
    if Image is None:
        raise HTTPException(status_code=500, detail="Pillow not installed")
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    result = await meal_gen.analyze_image(image, recognizer)
    return result


@app.get("/api/status/{user_id}")
async def get_user_status(user_id: str) -> dict[str, Any]:
    """Get detailed user status."""
    try:
        status = await chat_ui.get_user_status(user_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "true").lower() == "true"

    uvicorn.run("main:app", host=host, port=port, reload=debug, log_level="info")
