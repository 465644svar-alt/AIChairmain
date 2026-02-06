from __future__ import annotations

import logging
from collections import deque
from datetime import datetime
from pathlib import Path


class UIRingBufferHandler(logging.Handler):
    def __init__(self, capacity: int = 500):
        super().__init__()
        self.buffer = deque(maxlen=capacity)

    def emit(self, record: logging.LogRecord) -> None:
        self.buffer.append(self.format(record))

    def dump(self) -> list[str]:
        return list(self.buffer)


def setup_logging(log_dir: str = "logs") -> UIRingBufferHandler:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    file_name = Path(log_dir) / f"app_{datetime.now():%Y%m%d}.log"

    logger = logging.getLogger("aichairman")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    fh = logging.FileHandler(file_name, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    ui_handler = UIRingBufferHandler()
    ui_handler.setLevel(logging.INFO)
    ui_handler.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ui_handler)
    return ui_handler


def sanitize(text: str) -> str:
    for token in ("sk-", "Bearer "):
        if token in text:
            text = text.replace(token, "[REDACTED]")
    return text
