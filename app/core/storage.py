from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any


class ConversationStorage:
    def __init__(self, root: str = "data/conversations"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, payload: dict[str, Any], conv_id: str | None = None) -> str:
        conv_id = conv_id or str(uuid.uuid4())
        path = self.root / f"{conv_id}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return conv_id

    def load(self, conv_id: str) -> dict[str, Any]:
        path = self.root / f"{conv_id}.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def list_ids(self) -> list[str]:
        return sorted([p.stem for p in self.root.glob("*.json")], reverse=True)

    def delete(self, conv_id: str) -> None:
        path = self.root / f"{conv_id}.json"
        if path.exists():
            path.unlink()
