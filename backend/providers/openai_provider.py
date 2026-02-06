"""OpenAI API provider (direct, no OpenRouter)."""

import httpx
from backend.config import OPENAI_API_KEY
from backend.providers.base import BaseProvider

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIProvider(BaseProvider):
    async def generate(self, model: str, system_prompt: str, user_prompt: str) -> str:
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set")

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
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
            resp = await client.post(OPENAI_API_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
