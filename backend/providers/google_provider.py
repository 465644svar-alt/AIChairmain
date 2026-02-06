"""Google Gemini API provider (direct, no OpenRouter)."""

import httpx
from backend.config import GOOGLE_API_KEY
from backend.providers.base import BaseProvider

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GoogleProvider(BaseProvider):
    async def generate(self, model: str, system_prompt: str, user_prompt: str) -> str:
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not set")

        url = f"{GEMINI_API_URL}/{model}:generateContent?key={GOOGLE_API_KEY}"

        payload = {
            "system_instruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 4096,
            },
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
