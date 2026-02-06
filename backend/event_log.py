"""
Centralized event log for request/response tracking.
Stores events in memory and broadcasts via SSE to connected clients.
"""

import asyncio
import json
import time
from collections import deque
from typing import Optional


class LogEntry:
    __slots__ = ("timestamp", "level", "stage", "provider", "model", "direction", "content", "error", "duration_ms")

    def __init__(
        self,
        level: str,
        stage: str,
        provider: str,
        model: str,
        direction: str,  # "request" | "response" | "error" | "info"
        content: str,
        error: Optional[str] = None,
        duration_ms: Optional[float] = None,
    ):
        self.timestamp = time.time()
        self.level = level
        self.stage = stage
        self.provider = provider
        self.model = model
        self.direction = direction
        self.content = content
        self.error = error
        self.duration_ms = duration_ms

    def to_dict(self) -> dict:
        d = {
            "timestamp": self.timestamp,
            "level": self.level,
            "stage": self.stage,
            "provider": self.provider,
            "model": self.model,
            "direction": self.direction,
            "content": self.content,
        }
        if self.error:
            d["error"] = self.error
        if self.duration_ms is not None:
            d["duration_ms"] = round(self.duration_ms, 1)
        return d


# Global in-memory log — keeps last 500 entries
_log: deque[LogEntry] = deque(maxlen=500)

# SSE subscribers — each is an asyncio.Queue
_subscribers: list[asyncio.Queue] = []


def _broadcast(entry: LogEntry):
    """Push entry to all SSE subscribers."""
    data = json.dumps(entry.to_dict(), ensure_ascii=False)
    dead = []
    for q in _subscribers:
        try:
            q.put_nowait(data)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        _subscribers.remove(q)


def log_event(
    level: str,
    stage: str,
    provider: str,
    model: str,
    direction: str,
    content: str,
    error: str | None = None,
    duration_ms: float | None = None,
):
    entry = LogEntry(
        level=level,
        stage=stage,
        provider=provider,
        model=model,
        direction=direction,
        content=content,
        error=error,
        duration_ms=duration_ms,
    )
    _log.append(entry)
    _broadcast(entry)


def log_request(stage: str, provider: str, model: str, prompt_preview: str):
    """Log an outgoing LLM request."""
    log_event("info", stage, provider, model, "request", prompt_preview)


def log_response(stage: str, provider: str, model: str, response_preview: str, duration_ms: float):
    """Log a received LLM response."""
    log_event("info", stage, provider, model, "response", response_preview, duration_ms=duration_ms)


def log_error(stage: str, provider: str, model: str, error_msg: str, duration_ms: float | None = None):
    """Log an LLM error."""
    log_event("error", stage, provider, model, "error", error_msg, error=error_msg, duration_ms=duration_ms)


def log_info(stage: str, message: str):
    """Log a general info message."""
    log_event("info", stage, "", "", "info", message)


def get_log_history() -> list[dict]:
    """Return all stored log entries."""
    return [e.to_dict() for e in _log]


def subscribe() -> asyncio.Queue:
    """Create a new SSE subscriber queue."""
    q: asyncio.Queue = asyncio.Queue(maxsize=100)
    _subscribers.append(q)
    return q


def unsubscribe(q: asyncio.Queue):
    """Remove an SSE subscriber."""
    if q in _subscribers:
        _subscribers.remove(q)
