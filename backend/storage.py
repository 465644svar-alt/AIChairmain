"""JSON-based conversation storage."""

import json
import os
from backend.config import DATA_DIR
from backend.models import CouncilSession


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def save_session(session: CouncilSession):
    ensure_data_dir()
    path = os.path.join(DATA_DIR, f"{session.session_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session.model_dump(), f, ensure_ascii=False, indent=2)


def load_session(session_id: str) -> CouncilSession | None:
    path = os.path.join(DATA_DIR, f"{session_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return CouncilSession(**data)


def list_sessions() -> list[dict]:
    ensure_data_dir()
    sessions = []
    for fname in sorted(os.listdir(DATA_DIR), reverse=True):
        if fname.endswith(".json"):
            path = os.path.join(DATA_DIR, fname)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            sessions.append({
                "session_id": data["session_id"],
                "query": data["query"],
                "stage": data["stage"],
            })
    return sessions
