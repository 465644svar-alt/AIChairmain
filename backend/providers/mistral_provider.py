"""Mistral API provider (direct, no OpenRouter)."""

import httpx
from backend.config import MISTRAL_API_KEY
from backend.providers.base import BaseProvider

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"


class MistralProvider(BaseProvider):
    async def generate(self, model: str, system_prompt: str, user_prompt: str) -> str:
        if not MISTRAL_API_KEY:
            raise ValueError("MISTRAL_API_KEY not set")

        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 4096,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(MISTRAL_API_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
