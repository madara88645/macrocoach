"""
FastAPI main application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import Dict, Any
import io
try:
    from PIL import Image  # type: ignore
except ImportError:  # pragma: no cover - pillow optional
    Image = None  # type: ignore
import os
try:
    from dotenv import load_dotenv
except ImportError:
    # dotenv is optional
    def load_dotenv():
        pass

from .agents.chat_ui_agent import ChatUIAgent
from .agents.state_store_agent import StateStoreAgent
from .agents.planner_agent import PlannerAgent
from .agents.meal_gen_agent import MealGenAgent
from .vision import PlateRecognizer
from .core.context import ApplicationContext
from .core.models import UserProfile

# Load environment variables
load_dotenv()

# Initialize application context and agents
context = ApplicationContext()
state_store = StateStoreAgent(context)
planner = PlannerAgent(context)
meal_gen = MealGenAgent(context)
chat_ui = ChatUIAgent(context, state_store, planner, meal_gen)


@asynccontextmanager
async def lifespan(app: FastAPI):
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


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with basic info."""
    return {
        "message": "Welcome to MacroCoach API v0.1",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
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
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/profile/{user_id}")
async def create_or_update_profile(user_id: str, profile: UserProfile) -> Dict[str, Any]:
    """Create or update a user profile."""
    try:
        profile.user_id = user_id
        await state_store.store_user_profile(profile)
        return {"status": "ok", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/profile/{user_id}")
async def get_profile(user_id: str) -> Dict[str, Any]:
    """Retrieve user profile."""
    try:
        profile = await state_store.get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile.dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/meal-image")
async def meal_image(
    file: UploadFile = File(...),
    recognizer: PlateRecognizer = Depends(get_plate_recognizer),
) -> Dict[str, Any]:
    """Estimate macros from an uploaded meal photo."""
    if Image is None:
        raise HTTPException(status_code=500, detail="Pillow not installed")
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    result = await meal_gen.analyze_image(image, recognizer)
    return result


@app.get("/api/status/{user_id}")
async def get_user_status(user_id: str) -> Dict[str, Any]:
    """Get detailed user status."""
    try:
        status = await chat_ui.get_user_status(user_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "true").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
