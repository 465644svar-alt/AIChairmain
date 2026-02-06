from __future__ import annotations

import logging
import time
from json import JSONDecodeError
from typing import Any

import httpx

from ..types import LLMResult

logger = logging.getLogger("aichairman")


class AsyncProviderClient:
    def __init__(self, provider: str, base_url: str, api_key: str | None, model_path: str = "/chat/completions"):
        self.provider = provider
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model_path = model_path

    async def check_connectivity(self, timeout: float) -> tuple[bool, str | None, int, dict[str, Any] | None]:
        started = time.perf_counter()
        if not self.api_key:
            return False, "api key is not configured", 0, None

        headers = {"Authorization": f"Bearer {self.api_key}"}
        probe_url = f"{self.base_url}/models"

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(probe_url, headers=headers)
            latency = int((time.perf_counter() - started) * 1000)
            data = self._safe_json(resp)

            if resp.status_code in (401, 403):
                return False, f"auth error ({resp.status_code})", latency, data
            if resp.status_code >= 500:
                return False, f"provider unavailable ({resp.status_code})", latency, data
            return True, None, latency, data
        except httpx.TimeoutException:
            latency = int((time.perf_counter() - started) * 1000)
            return False, "timeout", latency, None
        except httpx.HTTPError as exc:
            latency = int((time.perf_counter() - started) * 1000)
            return False, f"network/http error: {exc}", latency, None

    async def chat(self, model: str, messages: list[dict], timeout: float) -> LLMResult:
        started = time.perf_counter()
        if not self.api_key:
            return LLMResult(self.provider, model, None, "api key is not configured", 0, None)

        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        payload = {"model": model, "messages": messages}
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                logger.info("Provider %s request started: %s", self.provider, model)
                resp = await client.post(f"{self.base_url}{self.model_path}", json=payload, headers=headers)
            latency = int((time.perf_counter() - started) * 1000)
            if resp.status_code in (401, 403):
                return LLMResult(self.provider, model, None, f"auth error ({resp.status_code})", latency, self._safe_json(resp))
            if resp.status_code == 429:
                return LLMResult(self.provider, model, None, "rate limit (429)", latency, self._safe_json(resp))
            resp.raise_for_status()
            data = self._safe_json(resp) or {}
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

    @staticmethod
    def _safe_json(resp: httpx.Response) -> dict[str, Any] | None:
        if not resp.content:
            return None
        try:
            parsed = resp.json()
        except JSONDecodeError:
            return {"raw": resp.text}

        if isinstance(parsed, dict):
            return parsed
        return {"data": parsed}
