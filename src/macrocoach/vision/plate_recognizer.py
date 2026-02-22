"""Plate recognition using GPT-4o vision API."""

from __future__ import annotations

import base64
import io
import json
from typing import Any

try:
    from PIL import Image  # type: ignore
except ImportError:  # pragma: no cover - pillow optional
    Image = None  # type: ignore

try:
    import openai
except ImportError:  # pragma: no cover - openai optional
    openai = None  # type: ignore


class PlateRecognizer:
    """Recognize meal macros from an image using GPT-4o."""

    def __init__(self, api_key: str | None = None) -> None:
        self.client = None
        if api_key and openai is not None:
            self.client = openai.AsyncOpenAI(api_key=api_key)

    async def recognize_plate(self, image: Any) -> dict[str, Any]:
        """Return macro estimation for the provided image."""
        if self.client is None:
            raise RuntimeError("OpenAI client not configured")
        if Image is None:
            raise RuntimeError("Pillow not installed")

        buf = io.BytesIO()
        image.save(buf, format="JPEG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        prompt = (
            "Estimate calories, protein_g, carbs_g and fat_g for the pictured meal. "
            "Respond in JSON with keys kcal, protein_g, carbs_g, fat_g, confidence."
        )
        resp = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                        },
                    ],
                }
            ],
            max_tokens=60,
        )
        content = resp.choices[0].message.content or "{}"
        try:
            return json.loads(content)
        except json.JSONDecodeError:  # pragma: no cover - invalid json fallback
            return {
                "kcal": 0,
                "protein_g": 0,
                "carbs_g": 0,
                "fat_g": 0,
                "confidence": 0,
            }
