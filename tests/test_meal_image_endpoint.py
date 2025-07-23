import types
import pytest
from fastapi.testclient import TestClient
from src.macrocoach.main import app, get_plate_recognizer
from src.macrocoach.vision import plate_recognizer


class DummyClient:
    class chat:
        class completions:
            @staticmethod
            async def create(*args, **kwargs):
                class Response:
                    choices = [types.SimpleNamespace(message=types.SimpleNamespace(content='{"kcal": 600, "protein_g": 35, "carbs_g": 55, "fat_g": 12, "confidence": 0.8}'))]
                return Response()


class FakeImage:
    def save(self, fp, format="JPEG"):
        fp.write(b"stub")


@pytest.mark.asyncio
async def test_meal_image_endpoint(monkeypatch):
    # Mock the PlateRecognizer completely
    class MockPlateRecognizer:
        def __init__(self, api_key=None):
            pass
            
        async def recognize_plate(self, image):
            return {
                "kcal": 600, 
                "protein_g": 35, 
                "carbs_g": 55, 
                "fat_g": 12, 
                "confidence": 0.8
            }
    
    # Mock PIL Image
    monkeypatch.setattr("src.macrocoach.main.Image", types.SimpleNamespace(open=lambda *a, **k: FakeImage()))

    # Override the dependency
    from src.macrocoach.main import app
    app.dependency_overrides[get_plate_recognizer] = lambda: MockPlateRecognizer()
    
    try:
        client = TestClient(app)
        with open("tests/fixtures/chicken_rice.jpg", "rb") as f:
            response = client.post("/meal-image", files={"file": ("chicken.jpg", f, "image/jpeg")})

        assert response.status_code == 200
        data = response.json()
        assert data["macros"]["kcal"] == 600
        assert data["macros"]["protein_g"] == 35
        assert data["macros"]["carbs_g"] == 55
        assert data["macros"]["fat_g"] == 12
    finally:
        # Clean up dependency override
        app.dependency_overrides.clear()
