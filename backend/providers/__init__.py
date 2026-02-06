"""LLM provider integrations — direct API calls, no OpenRouter."""

from backend.providers.openai_provider import OpenAIProvider
from backend.providers.anthropic_provider import AnthropicProvider
from backend.providers.google_provider import GoogleProvider

PROVIDERS = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "google": GoogleProvider,
}


def get_provider(provider_name: str):
    provider_class = PROVIDERS.get(provider_name)
    if not provider_class:
        raise ValueError(f"Unknown provider: {provider_name}")
    return provider_class()
