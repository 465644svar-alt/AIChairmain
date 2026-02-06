"""Anthropic API provider (direct, no OpenRouter)."""

import httpx
from backend.config import ANTHROPIC_API_KEY
from backend.providers.base import BaseProvider

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


class AnthropicProvider(BaseProvider):
    async def generate(self, model: str, system_prompt: str, user_prompt: str) -> str:
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set")

        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt},
            ],
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(ANTHROPIC_API_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]
