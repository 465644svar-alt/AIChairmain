"""Base provider interface."""

from abc import ABC, abstractmethod


class BaseProvider(ABC):
    @abstractmethod
    async def generate(self, model: str, system_prompt: str, user_prompt: str) -> str:
        """Generate a response from the LLM.

        Args:
            model: Model identifier (e.g. "gpt-4o", "claude-3-5-sonnet-20241022")
            system_prompt: System message setting context
            user_prompt: User's message/query

        Returns:
            The model's text response.

        Raises:
            Exception on API errors.
        """
        ...
