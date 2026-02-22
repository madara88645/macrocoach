import types

import pytest

from src.macrocoach.vision import plate_recognizer


async def _mock_create(*args, **kwargs):
    class R:
        choices = [
            types.SimpleNamespace(
                message=types.SimpleNamespace(
                    content='{"kcal": 500, "protein_g": 30, "carbs_g": 50, "fat_g": 10, "confidence": 0.9}'
                )
            )
        ]

    return R()


class DummyClient:
    chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=_mock_create))


class FakeImage:
    def save(self, fp, format="JPEG"):
        fp.write(b"stub")


@pytest.mark.asyncio
async def test_plate_recognizer(monkeypatch):
    monkeypatch.setattr(
        plate_recognizer,
        "openai",
        types.SimpleNamespace(AsyncOpenAI=lambda api_key: DummyClient()),
    )

    recognizer = plate_recognizer.PlateRecognizer("key")
    result = await recognizer.recognize_plate(FakeImage())
    assert result["kcal"] == 500
    assert result["protein_g"] == 30
    assert result["carbs_g"] == 50
    assert result["fat_g"] == 10
    assert result["confidence"] == 0.9
