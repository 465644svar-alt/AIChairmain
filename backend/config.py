"""
AIChairmain configuration.
Define council members, chairman model, and API keys.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# API Keys — set via environment variables or .env file
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")

# Council member definitions
# Each member has: id, name, provider, model
COUNCIL_MEMBERS = [
    {
        "id": "gpt4o",
        "name": "GPT-4o",
        "provider": "openai",
        "model": "gpt-4o",
    },
    {
        "id": "claude-sonnet",
        "name": "Claude 3.5 Sonnet",
        "provider": "anthropic",
        "model": "claude-3-5-sonnet-20241022",
    },
    {
        "id": "gemini-pro",
        "name": "Gemini 2.0 Flash",
        "provider": "google",
        "model": "gemini-2.0-flash",
    },
    {
        "id": "groq-llama",
        "name": "Llama 3.3 70B (Groq)",
        "provider": "groq",
        "model": "llama-3.3-70b-versatile",
    },
    {
        "id": "mistral-large",
        "name": "Mistral Large",
        "provider": "mistral",
        "model": "mistral-large-latest",
    },
]

# The chairman model synthesizes the final answer
CHAIRMAN_MODEL = {
    "id": "chairman",
    "name": "Chairman (Claude Opus)",
    "provider": "anthropic",
    "model": "claude-opus-4-0-20250514",
}

# Server settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "conversations")
