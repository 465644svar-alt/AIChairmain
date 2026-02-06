from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication

from app.core.council import CouncilOrchestrator
from app.core.logging_config import setup_logging
from app.core.models.providers import AsyncProviderClient
from app.core.storage import ConversationStorage
from app.ui.main_window import MainWindow


def build_clients() -> dict[str, AsyncProviderClient]:
    return {
        "gpt": AsyncProviderClient("gpt", os.getenv("GPT_BASE_URL", "https://api.openai.com/v1"), os.getenv("OPENAI_API_KEY")),
        "deepseek": AsyncProviderClient("deepseek", os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"), os.getenv("DEEPSEEK_API_KEY")),
        "claude": AsyncProviderClient("claude", os.getenv("CLAUDE_BASE_URL", "https://api.anthropic.com/v1"), os.getenv("ANTHROPIC_API_KEY"), model_path="/messages"),
        "mistral": AsyncProviderClient("mistral", os.getenv("MISTRAL_BASE_URL", "https://api.mistral.ai/v1"), os.getenv("MISTRAL_API_KEY")),
        "groq": AsyncProviderClient("groq", os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"), os.getenv("GROQ_API_KEY")),
    }


def main() -> int:
    load_dotenv()
    Path("data/conversations").mkdir(parents=True, exist_ok=True)
    ui_handler = setup_logging()
    app = QApplication(sys.argv)
    orchestrator = CouncilOrchestrator(build_clients())
    storage = ConversationStorage()
    win = MainWindow(orchestrator, storage, ui_handler)
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
