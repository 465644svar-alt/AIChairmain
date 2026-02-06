from __future__ import annotations

import time
import logging
import httpx

from ..types import LLMResult

logger = logging.getLogger("aichairman")


class AsyncProviderClient:
    def __init__(self, provider: str, base_url: str, api_key: str | None, model_path: str = "/chat/completions"):
        self.provider = provider
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model_path = model_path

    async def chat(self, model: str, messages: list[dict], timeout: float) -> LLMResult:
        started = time.perf_counter()
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {"model": model, "messages": messages}
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                logger.info("Provider %s request started: %s", self.provider, model)
                resp = await client.post(f"{self.base_url}{self.model_path}", json=payload, headers=headers)
            latency = int((time.perf_counter() - started) * 1000)
            if resp.status_code in (401, 403):
                return LLMResult(self.provider, model, None, f"auth error ({resp.status_code})", latency, resp.json() if resp.content else None)
            if resp.status_code == 429:
                return LLMResult(self.provider, model, None, "rate limit (429)", latency, resp.json() if resp.content else None)
            resp.raise_for_status()
            data = resp.json()
            content = (
                data.get("choices", [{}])[0].get("message", {}).get("content")
                or data.get("content")
                or ""
            )
            logger.info("Provider %s request finished: %s (%d ms)", self.provider, model, latency)
            return LLMResult(self.provider, model, content, None, latency, data)
        except httpx.TimeoutException:
            latency = int((time.perf_counter() - started) * 1000)
            return LLMResult(self.provider, model, None, "timeout", latency, None)
        except httpx.HTTPError as exc:
            latency = int((time.perf_counter() - started) * 1000)
            return LLMResult(self.provider, model, None, f"network/http error: {exc}", latency, None)
        except Exception as exc:  # noqa: BLE001
            latency = int((time.perf_counter() - started) * 1000)
            logger.exception("Unexpected provider error")
            return LLMResult(self.provider, model, None, f"unexpected error: {exc}", latency, None)
