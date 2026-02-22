import types
import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from src.macrocoach.main import app, get_plate_recognizer
from src.macrocoach.vision import plate_recognizer


class FakeImage:
    def save(self, fp, format="JPEG"):
        fp.write(b"stub")


@pytest.mark.asyncio
async def test_meal_image_endpoint(monkeypatch):
    mock_recognizer = AsyncMock()
    mock_recognizer.recognize_plate.return_value = {
        "kcal": 600,
        "protein_g": 35,
        "carbs_g": 55,
        "fat_g": 12,
        "confidence": 0.8,
    }

    app.dependency_overrides[get_plate_recognizer] = lambda: mock_recognizer
    monkeypatch.setattr(
        "src.macrocoach.main.Image",
        types.SimpleNamespace(open=lambda *a, **k: FakeImage()),
    )

    try:
        client = TestClient(app)
        with open("tests/fixtures/chicken_rice.jpg", "rb") as f:
            response = client.post("/meal-image", files={"file": ("chicken.jpg", f, "image/jpeg")})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["macros"]["kcal"] == 600
    assert data["macros"]["protein_g"] == 35
    assert data["macros"]["carbs_g"] == 55
    assert data["macros"]["fat_g"] == 12
