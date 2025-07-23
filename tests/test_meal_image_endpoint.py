import types
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from src.macrocoach.main import app
from src.macrocoach.vision import plate_recognizer


class DummyClient:
    class chat:
        class completions:
            @staticmethod
            async def create(*args, **kwargs):
                class R:
                    choices = [types.SimpleNamespace(message=types.SimpleNamespace(content='{"kcal": 600, "protein_g": 35, "carbs_g": 55, "fat_g": 12, "confidence": 0.8}'))]
                return R()


class FakeImage:
    def save(self, fp, format="JPEG"):
        fp.write(b"stub")


@pytest.mark.asyncio
async def test_meal_image_endpoint(monkeypatch):
    # Mock openai and image processing 
    monkeypatch.setattr(
        plate_recognizer, "openai", types.SimpleNamespace(AsyncOpenAI=lambda api_key: DummyClient())
    )
    monkeypatch.setattr(plate_recognizer, "Image", types.SimpleNamespace(open=lambda *a, **k: FakeImage()))
    monkeypatch.setattr(
        "src.macrocoach.main.Image",
        types.SimpleNamespace(open=lambda *a, **k: FakeImage()),
    )
    
    # Mock the environment variable for testing
    monkeypatch.setenv("OPENAI_API_KEY", "test_key")

    with TestClient(app) as client:
        with open("tests/fixtures/chicken_rice.jpg", "rb") as f:
            response = client.post("/meal-image", files={"file": ("chicken.jpg", f, "image/jpeg")})

        assert response.status_code == 200
        data = response.json()
        assert data["macros"]["kcal"] == 600
        assert data["macros"]["protein_g"] == 35
        assert data["macros"]["carbs_g"] == 55
        assert data["macros"]["fat_g"] == 12
